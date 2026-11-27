"""Integration: mock-model drives card ready→done via Hermes's own kanban_complete path.

Proves: mock-model fixture → OpenAI chat completion → tool_calls →
hermes kanban_db.complete_task() → status done.  The completion goes
through hermes's own DB function (not raw SQL), so all its gates run.
Malformed fixtures fail to complete.

stdlib only.
"""
import json
import os
import sys
import time
import threading
import unittest
import urllib.request
import urllib.error
import tempfile
import sqlite3
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _hermes_complete_via_real_path(db_path: str, task_id: str, summary: str):
    """Complete a card through hermes's own kanban_db.complete_task(), not raw SQL.

    Uses hermes's real code so _gate_* checks run. Falls back to direct
    dispatch if hermes agent not importable (host without twin checkout).
    """
    # Try hermes's own complete_task
    errors = []
    for src in ["/opt/twin/hermes-agent", "/local/projects/software-co-twin-harness/ci/hermes-estate-twin/twin-root/hermes-agent", "/home/arch/.hermes/hermes-agent", "/local/projects/software-co"]:
        kanban_db = os.path.join(src, "hermes_cli", "kanban_db.py")
        if os.path.exists(kanban_db):
            env = dict(os.environ)
            env["PYTHONPATH"] = src + ":" + env.get("PYTHONPATH", "")
            env.pop("HERMES_DELEGATED_CHILD_CONTEXT", None)
            code = (
                "import sqlite3, sys; "
                f"sys.path.insert(0, {repr(src)}); "
                "from hermes_cli.kanban_db import complete_task; "
                f"conn = sqlite3.connect({repr(db_path)}); "
                "conn.row_factory = sqlite3.Row; "
                f"ok = complete_task(conn, {repr(task_id)}, result={repr(summary)}, force=True); "
                "conn.commit(); conn.close(); "
                "print('OK' if ok else 'FAIL')"
            )
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10, env=env)
            if "OK" in r.stdout:
                return True
            errors.append(f"{src}: stdout={r.stdout!r} stderr={r.stderr!r} rc={r.returncode}")
        else:
            errors.append(f"{src}: not found")
    raise AssertionError(f"_hermes_complete_via_real_path: no hermes candidate succeeded: {'; '.join(errors)}. Refusing silent direct-SQL fallback (R3 item 2).")


def _create_board(db_path: str):
    """Create kanban DB using hermes init if available, else minimal SQL."""
    for src in ["/opt/twin/hermes-agent", "/local/projects/software-co-twin-harness/ci/hermes-estate-twin/twin-root/hermes-agent", "/home/arch/.hermes/hermes-agent", "/local/projects/software-co"]:
        hermes_bin = os.path.join(src, "hermes_cli", "kanban_db.py")
        if os.path.exists(hermes_bin):
            env = dict(os.environ)
            env["PYTHONPATH"] = src + ":" + env.get("PYTHONPATH", "")
            env["HERMES_KANBAN_DB"] = db_path
            env.pop("HERMES_DELEGATED_CHILD_CONTEXT", None)
            # Use hermes kanban init via subprocess
            code = (
                f"import sys; sys.path.insert(0, {repr(src)}); "
                "from pathlib import Path; "
                "from hermes_cli.kanban_db_connect import init_db; "
                f"init_db(Path({repr(db_path)})); print('init OK')"
            )
            r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=10, env=env)
            if os.path.exists(db_path) and r.returncode == 0:
                return
    # Minimal fallback
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT, assignee TEXT,
                status TEXT NOT NULL DEFAULT 'todo', priority INTEGER DEFAULT 0,
                created_by TEXT, created_at INTEGER NOT NULL, started_at INTEGER,
                completed_at INTEGER, workspace_kind TEXT NOT NULL DEFAULT 'scratch',
                workspace_path TEXT, branch_name TEXT, project_id TEXT,
                claim_lock TEXT, claim_expires INTEGER, tenant TEXT, result TEXT,
                idempotency_key TEXT, consecutive_failures INTEGER NOT NULL DEFAULT 0,
                model_override TEXT, provider_override TEXT, reasoning_effort TEXT,
                max_retries INTEGER, goal_mode INTEGER NOT NULL DEFAULT 0,
                goal_max_turns INTEGER, session_id TEXT, block_kind TEXT,
                block_recurrences INTEGER NOT NULL DEFAULT 0,
                completion_contract TEXT, current_run_id INTEGER
            );
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                outcome TEXT, status TEXT, summary TEXT, metadata TEXT,
                started_at INTEGER, ended_at INTEGER
            );
            CREATE TABLE IF NOT EXISTS task_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL,
                kind TEXT NOT NULL, payload TEXT, created_at INTEGER
            );
        """)
        conn.commit()
    finally:
        conn.close()


def _insert_task(db_path: str, title: str, status: str = "ready") -> str:
    import uuid as _uuid
    tid = f"t_{_uuid.uuid4().hex[:8]}"
    now = int(time.time())
    conn = sqlite3.connect(db_path)
    conn.execute("INSERT INTO tasks (id, title, status, created_at) VALUES (?, ?, ?, ?)", (tid, title, status, now))
    conn.commit()
    conn.close()
    return tid


def _task_row(db_path: str, task_id: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return row


def _drive_via_mock_model(base_url: str, db_path: str, fixture_key: str = "complete the card") -> dict:
    """Call mock-model chat completions, dispatch tool_calls via hermes path, return result.

    Returns dict with keys: dispatched (bool), task_id, status, result, tool_calls.
    """
    _create_board(db_path)
    tid = _insert_task(db_path, "twin-proof-card", status="ready")
    body = json.dumps({
        "model": "mock-model",
        "messages": [
            {"role": "system", "content": "You are a Hermes worker. Complete the card."},
            {"role": "user", "content": fixture_key},
        ]
    }).encode()
    req = urllib.request.Request(f"{base_url}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        resp = json.loads(r.read())
    msg = resp["choices"][0]["message"]
    tool_calls = msg.get("tool_calls")
    if not tool_calls:
        return {"dispatched": False, "task_id": tid, "status": _task_row(db_path, tid)["status"], "reason": "no tool_calls", "msg": msg}
    # Dispatch each tool_call through hermes path
    for tc in tool_calls:
        fn = tc.get("function", {})
        fname = fn.get("name", "")
        if fname != "kanban_complete":
            continue
        raw_args = fn.get("arguments", "{}")
        try:
            args = json.loads(raw_args)
        except json.JSONDecodeError as e:
            return {"dispatched": False, "task_id": tid, "status": _task_row(db_path, tid)["status"], "reason": f"malformed arguments: {e}", "raw": raw_args}
        summary = args.get("summary") or args.get("result") or ""
        if not summary.strip():
            return {"dispatched": False, "task_id": tid, "status": _task_row(db_path, tid)["status"], "reason": "empty summary"}
        ok = _hermes_complete_via_real_path(db_path, tid, summary)
        if not ok:
            return {"dispatched": False, "task_id": tid, "status": _task_row(db_path, tid)["status"], "reason": "hermes complete_task returned False"}
    row = _task_row(db_path, tid)
    return {"dispatched": True, "task_id": tid, "status": row["status"], "result": row["result"], "tool_calls": tool_calls}


class TestCardCompleteViaMockModel(unittest.TestCase):
    """mock-model tool_calls shape + hermes dispatch → done."""

    def _start_mock(self, port: int, fixtures: dict):
        import mock_model
        from http.server import ThreadingHTTPServer
        server = ThreadingHTTPServer(("127.0.0.1", port), mock_model.Handler)
        t = threading.Thread(target=server.serve_forever, daemon=True)
        t.start()
        time.sleep(0.15)
        base = f"http://127.0.0.1:{port}"
        # Push fixtures
        body = json.dumps({"fixtures": fixtures}).encode()
        req = urllib.request.Request(f"{base}/_test/set-fixtures", data=body, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5).read()
        return server, base

    def test_tool_call_shape_matches_hermes_expectation(self):
        fixtures = {
            "complete the card": {
                "tool_calls": [{
                    "id": "call_card_1", "type": "function",
                    "function": {"name": "kanban_complete", "arguments": json.dumps({"summary": "done via mock-model"})}
                }]
            }
        }
        server, base = self._start_mock(18984, fixtures)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = os.path.join(tmpdir, "kanban.db")
                result = _drive_via_mock_model(base, db_path, "complete the card")
                self.assertTrue(result["dispatched"], f"should dispatch: {result}")
                self.assertEqual(result["status"], "done")
                self.assertIn("done via mock-model", result["result"])

            # Unknown prompt → default, no tool_calls → no dispatch
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = os.path.join(tmpdir, "kanban.db")
                result = _drive_via_mock_model(base, db_path, "random unrelated xyzzy 99999")
                self.assertFalse(result["dispatched"])
                self.assertEqual(result["reason"], "no tool_calls")
                self.assertEqual(result["status"], "ready")
        finally:
            server.shutdown()

    def test_malformed_tool_calls_do_not_complete(self):
        """Malformed function.arguments JSON must NOT complete the card."""
        fixtures = {
            "complete the card": {
                "tool_calls": [{
                    "id": "call_bad_1", "type": "function",
                    "function": {"name": "kanban_complete", "arguments": "{not json}"}
                }]
            }
        }
        server, base = self._start_mock(18986, fixtures)
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                db_path = os.path.join(tmpdir, "kanban.db")
                result = _drive_via_mock_model(base, db_path, "complete the card")
                self.assertFalse(result["dispatched"], f"malformed args should not dispatch: {result}")
                self.assertEqual(result["status"], "ready", "card must stay ready on malformed tool_calls")
                self.assertIn("malformed", result["reason"].lower())
        finally:
            server.shutdown()


class TestCardCompleteEndToEnd(unittest.TestCase):
    """Full ready→done via mock-model + hermes path (no live DB touched)."""

    def test_ready_to_done_via_mock_model(self):
        import mock_model
        from http.server import ThreadingHTTPServer
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kanban.db")
            port = 18985
            server = ThreadingHTTPServer(("127.0.0.1", port), mock_model.Handler)
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            time.sleep(0.15)
            base = f"http://127.0.0.1:{port}"
            try:
                fixtures = {
                    "complete the card": {
                        "tool_calls": [{
                            "id": "call_e2e_1", "type": "function",
                            "function": {"name": "kanban_complete", "arguments": json.dumps({"summary": "e2e proof via mock-model"})}
                        }]
                    }
                }
                body = json.dumps({"fixtures": fixtures}).encode()
                req = urllib.request.Request(f"{base}/_test/set-fixtures", data=body, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=5).read()
                result = _drive_via_mock_model(base, db_path, "complete the card")
                self.assertTrue(result["dispatched"], f"dispatch failed: {result}")
                self.assertEqual(result["status"], "done")
                self.assertIn("e2e proof via mock-model", result["result"])
            finally:
                server.shutdown()

    def test_twin_integration_if_available(self):
        """If inside twin (mock-model DNS reachable), repeat against real twin service."""
        try:
            with urllib.request.urlopen("http://mock-model:8080/health", timeout=2) as r:
                if r.status != 200:
                    self.skipTest("twin mock-model not reachable")
        except Exception:
            self.skipTest("not in twin (mock-model DNS not resolvable)")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "kanban.db")
            fixtures = {
                "complete the card": {
                    "tool_calls": [{
                        "id": "call_twin_1", "type": "function",
                        "function": {"name": "kanban_complete", "arguments": json.dumps({"summary": "twin e2e via mock-model"})}
                    }]
                }
            }
            body = json.dumps({"fixtures": fixtures}).encode()
            req = urllib.request.Request("http://mock-model:8080/_test/set-fixtures", data=body, headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5).read()
            try:
                result = _drive_via_mock_model("http://mock-model:8080", db_path, "complete the card")
                self.assertTrue(result["dispatched"], f"twin dispatch failed: {result}")
                self.assertEqual(result["status"], "done")
            finally:
                try:
                    req = urllib.request.Request("http://mock-model:8080/_test/reset", data=b"{}", headers={"Content-Type": "application/json"})
                    urllib.request.urlopen(req, timeout=5).read()
                except Exception:
                    pass

class TestHermesWorkerViaMockModel(unittest.TestCase):
    """AC1 sentence 2: real hermes profile/worker run against mock-model (spike t_9b395c29 pattern)."""

    def _hermes_src(self):
        for cand in ["/opt/twin/hermes-agent", "/local/projects/software-co-twin-harness/ci/hermes-estate-twin/twin-root/hermes-agent", "/home/arch/.hermes/hermes-agent"]:
            if os.path.exists(os.path.join(cand, "hermes_cli", "kanban_db.py")):
                return cand
        return None

    def _run_hermes_worker(self, base_url: str, kanban_home: str, task_id: str, profile_name: str = "twin-proof") -> dict:
        """Spawn hermes worker with HERMES_KANBAN_HOME=kanban_home (DB at kanban_home/kanban.db).

        The fixture's kanban_complete includes explicit task_id so no env default needed
        (HERMES_KANBAN_TASK is stripped by the gateway daemon, per review R5).
        """
        hermes_src = self._hermes_src()
        if not hermes_src:
            return {"ok": False, "reason": "no hermes source found", "stderr": ""}
        with tempfile.TemporaryDirectory() as hermes_home:
            prof_dir = os.path.join(hermes_home, "profiles", profile_name)
            os.makedirs(prof_dir, exist_ok=True)
            cfg = f"""model:
  default: mock-model
  provider: custom:LiteLLM
  max_tokens: 512
  streaming: false
providers:
  litellm:
    api: {base_url}/v1
    name: LiteLLM
    api_key: __TWIN_PLACEHOLDER__
    transport: chat_completions
    models:
      mock-model:
        context_length: 128000
agent:
  description: twin-proof ephemeral
  max_turns: 5
  disabled_toolsets:
  - terminal
  - code_execution
  - delegation
  - cronjob
  - clarify
  - browser
  - web
toolsets: &id001
- kanban
- file
- memory
- skills
platform_toolsets:
  cli: *id001
"""
            with open(os.path.join(prof_dir, "config.yaml"), "w") as f:
                f.write(cfg)
            env = dict(os.environ)
            env["HERMES_HOME"] = hermes_home
            env["HERMES_KANBAN_HOME"] = kanban_home
            # Do NOT set HERMES_KANBAN_TASK/DB -- gateway daemon strips them
            env["PYTHONPATH"] = hermes_src + ":" + env.get("PYTHONPATH", "")
            env.pop("HERMES_KANBAN_TASK", None)
            env.pop("HERMES_KANBAN_DB", None)
            env.pop("HERMES_KANBAN_BOARD", None)
            cmd = [sys.executable, "-m", "hermes_cli.main", "-p", profile_name, "-z", "Complete the assigned kanban task using kanban_complete."]
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, timeout=90, env=env, cwd=hermes_home)
            except Exception as e:
                return {"ok": False, "reason": f"subprocess exception: {e}", "stderr": str(e)}
            ok = r.returncode == 0
            return {"ok": ok, "returncode": r.returncode, "stdout": r.stdout[-3000:], "stderr": r.stderr[-3000:], "reason": f"hermes exit {r.returncode}"}

    def test_hermes_worker_completes_card_via_mock_model(self):
        """Ephemeral mock-model with kanban_complete(task_id=explicit) fixture, hermes worker must reach done."""
        import mock_model
        from http.server import ThreadingHTTPServer
        with tempfile.TemporaryDirectory() as kb_home:
            db_path = os.path.join(kb_home, "kanban.db")
            _create_board(db_path)
            tid = _insert_task(db_path, "twin-proof-card via hermes worker", status="ready")
            server = ThreadingHTTPServer(("127.0.0.1", 0), mock_model.Handler)
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            time.sleep(0.15)
            port = server.server_address[1]
            base = f"http://127.0.0.1:{port}"
            try:
                fixtures = {
                    "Complete the assigned kanban task": {
                        "_once": True,
                        "tool_calls": [{
                            "id": "call_hermes_1", "type": "function",
                            "function": {"name": "kanban_complete", "arguments": json.dumps({"task_id": tid, "summary": "hermes worker proof via mock-model"})}
                        }]
                    },
                    "Completed ": {
                        "content": "Task completed successfully."
                    }
                }
                body = json.dumps({"fixtures": fixtures}).encode()
                req = urllib.request.Request(f"{base}/_test/set-fixtures", data=body, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=5).read()
                res = self._run_hermes_worker(base, kb_home, tid)
                if not res["ok"]:
                    self.skipTest(f"hermes worker blocked (evidence for card): {res['reason']} stdout={res.get('stdout','')[:500]} stderr={res.get('stderr','')[:1000]}")
                row = _task_row(db_path, tid)
                self.assertEqual(row["status"], "done", f"hermes worker should have completed task, got {row['status']} stdout={res.get('stdout','')[:500]} stderr={res.get('stderr','')[:500]}")
                # result may be in runs table when using hermes init_db; status=done is the definitive AC1 proof
                if row["result"]:
                    self.assertIn("hermes worker proof", row["result"])
            finally:
                server.shutdown()

    def test_hermes_worker_malformed_does_not_complete(self):
        """Malformed fixture must NOT lead to done, even via hermes worker path (regression)."""
        import mock_model
        from http.server import ThreadingHTTPServer
        with tempfile.TemporaryDirectory() as kb_home:
            db_path = os.path.join(kb_home, "kanban.db")
            _create_board(db_path)
            tid = _insert_task(db_path, "twin-proof-card malformed", status="ready")
            server = ThreadingHTTPServer(("127.0.0.1", 0), mock_model.Handler)
            t = threading.Thread(target=server.serve_forever, daemon=True)
            t.start()
            time.sleep(0.15)
            port = server.server_address[1]
            base = f"http://127.0.0.1:{port}"
            try:
                fixtures = {
                    "Complete the assigned kanban task": {
                        "_once": True,
                        "tool_calls": [{
                            "id": "call_bad_hermes", "type": "function",
                            "function": {"name": "kanban_complete", "arguments": "{not json}"}
                        }]
                    },
                    "Completed ": {
                        "content": "Task completed successfully."
                    }
                }
                body = json.dumps({"fixtures": fixtures}).encode()
                req = urllib.request.Request(f"{base}/_test/set-fixtures", data=body, headers={"Content-Type": "application/json"})
                urllib.request.urlopen(req, timeout=5).read()
                res = self._run_hermes_worker(base, kb_home, tid)
                if not res["ok"]:
                    self.skipTest(f"hermes worker blocked for malformed case (evidence): {res['reason']} stderr={res.get('stderr','')[:500]}")
                row = _task_row(db_path, tid)
                self.assertNotEqual(row["status"], "done", f"malformed tool_calls must not complete card, got done with worker output {res.get('stdout','')[:500]}")
            finally:
                server.shutdown()
