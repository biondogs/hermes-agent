#!/usr/bin/env python3
"""NO-SELF-GATE mechanical enforcer (fleet board-tooling layer, card t_ad14438a).

Law: NO-SELF-GATE (R6), docs/gate-wait-pattern-2026-10-28.md @ 31d5b4b,
operated as fleet law via GOVERNANCE G-02 extension (t_1a66c496, 2026-10-28).
"Rule A of gate integrity: THE AUTHOR NEVER GATES ITS OWN BYTES."
Operator GO 2026-10-28 via swco-butler DM ("I accept all your recommended
options"), card t_ad14438a scope items 1-2.

Kernel-level (0-second) refusal of a self-gate PASS is NOT possible from this
layer -- the kanban kernel lives in hermes-agent. That half is the upstream
Hermes feature request (routed through the distiller gate -> operator FINAL
GATE chain; see receipts on t_ad14438a). This script is the board-tooling
half: detection + mechanical enforcement within <=1 runtime tick (60s cron).

Every run (SYSTEM crontab, every minute, flock-guarded, gateway-independent):
  1. Read-only scan of ~/.hermes/kanban.db + every
     ~/.hermes/kanban/boards/<slug>/kanban.db (auto-discovered).
  2. Find cards whose title/body DECLARES a text/review gate (R6.1) and whose
     assignee is the author of the gated work per R6's definition of "author":
     the card's own creator ("never to yourself"), or the creator / assignee /
     completed-run profile of the gated work card (parents of the gate and
     task-ids referenced in the gate body). A null assignee counts as
     misassigned ("left unassigned"). Butler/orchestrator/default creators are
     not authors of bytes; they are filtered out.
  3. Enforce via supported `hermes kanban` CLI mutators only (never raw SQL):
     - INTAKE REFUSAL (active card, created >= LAW_TS): comment exactly the
       R6.4 refusal text + mechanically reassign to the independent gate
       profile (distiller for text gates, sw-reviewer for code-review gates),
       reclaiming a live run first -- the author's in-flight self-gate is
       refused before a verdict can land. Undeterminable target or
       already-gate-profile assignee => comment + block needs_input + alert.
     - SELF-PASS VOID (done card, completed >= activation timestamp): R6.3
       executed mechanically -- void annotation on the gate card and on every
       apply leg (child) it released; stop each leg (block needs_input);
       unlink the voided gate; re-file the gate independently as a fresh card
       assigned to the correct gate profile; make the new gate each stopped
       leg's true parent; unblock the legs (they stay todo-gated on the fresh
       gate). Operator alert via alert-sink.sh (fully gateway-independent,
       like the dead-man switch).
  4. Idempotent: acted cards are recorded in the state file and double-checked
     against prior `[NO-SELF-GATE-ENFORCER` comments. Skips archived cards,
     pre-law creations for the intake arm, pre-activation completions for the
     void arm, cards about the law itself, and the per-board EXCEPTIONS list.

R6.2 (check-set relaxation) is NOT mechanically detectable here -- no
structured check-set data exists at the board layer. Recorded as a known
residual gap; also named in the upstream FR.

Usage: no-self-gate-enforcer.py [--dry-run] [--selftest]
Exit codes: 0 clean, 1 enforcement actions taken, 2 fatal/selftest failure.
"""
from __future__ import annotations

import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
DEFAULT_DB = HOME / ".hermes/kanban.db"
BOARDS_ROOT = HOME / ".hermes/kanban/boards"
HERMES = HOME / ".local/bin/hermes"
STATE_FILE = HOME / ".hermes/state/nsg-enforcer.state"
ALERT_SINK = HOME / ".hermes/scripts/alert-sink.sh"

MARKER = "[NO-SELF-GATE-ENFORCER"
COMMENT_AUTHOR = "nsg-enforcer"

# Law timestamp: 2026-10-28 00:00 America/New_York (law in force that day)
LAW_TS = int(datetime(2026, 10, 28, 4, 0, tzinfo=timezone.utc).timestamp())

# Cards some lane owns enforcement authority over, or law/meta cards that talk
# about gates heavily. Board slug -> set of task ids.
EXCEPTIONS: dict[str, set[str]] = {
    "software-co": {"t_ad14438a", "t_a044b6aa", "t_1a66c496", "t_84b852b9", "t_0d825d76"},
}

# --- R6.1 gate-declaration detection -----------------------------------------
# Strong declarations only: declaration false-positives on non-gate work cards
# would cause wrong reassignments, so stay deliberately conservative; the
# authorship test gates the action set further.
GATE_TITLE_QUALED_RE = re.compile(
    r"(?i)(?:distiller|text|review|auditor|audit|ship|code|qa|re)\s*-?\s*gate\b\s*(?:[:\u2014-]|$)"
)
GATE_TITLE_BARE_RE = re.compile(r"(?i)\bgate\b\s*(?:[:\u2014])")
GATE_BODY_RE_LIST = [
    re.compile(r"(?im)^gate (?:card|for)\b"),
    re.compile(r"(?m)^## Assignee\s*\n\s*(distiller|sw-reviewer)\b"),
    re.compile(r"(?i)independent (?:text |code[- ]review |review )?gate on"),
    re.compile(r"(?i)^verdict: (?:pass|reject)"),
]
# Cards ABOUT the law / gate infrastructure never count as gate declarations.
LAW_META_RE = re.compile(
    r"(?i)no-?self-?gate|self-?gate|gate-?author|operator-final-gate|final gate law|"
    r"gate-wait|misassigned gate"
)
TASK_ID_RE = re.compile(r"\bt_[0-9a-f]{8}\b")

GATE_PROFILE_TEXT_RE = re.compile(r"(?i)distiller|text[- ]gate")
GATE_PROFILE_CODE_RE = re.compile(r"(?i)sw-reviewer|code[- ]?review|review[- ]gate")


def log(msg: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"{stamp} {msg}", flush=True)


def gate_declared(title: str, body: str) -> bool:
    if LAW_META_RE.search(title or ""):
        return False
    if GATE_TITLE_QUALED_RE.search(title or "") or GATE_TITLE_BARE_RE.search(title or ""):
        return True
    if not body:
        return False
    # law-quoting lines are not declarations; evaluate the cleaned body
    clean = "\n".join(l for l in body.splitlines() if not LAW_META_RE.search(l))
    for rx in GATE_BODY_RE_LIST:
        if rx.search(clean):
            return True
    return False


def gate_profile_for(title: str, body: str) -> str | None:
    text = f"{title}\n{body}"
    if GATE_PROFILE_TEXT_RE.search(text):
        return "distiller"
    if GATE_PROFILE_CODE_RE.search(text):
        return "sw-reviewer"
    return None


def _is_non_author(profile: str | None) -> bool:
    """Butlers/orchestrators/decomposers route, they do not author bytes."""
    if not profile or profile in ("default", "auto-decomposer", "none", "user"):
        return True
    return profile.endswith("-butler")


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except Exception:
        return {}


def save_state(st: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1, sort_keys=True))
    os.replace(tmp, STATE_FILE)


def already_acted(con: sqlite3.Connection, slug: str, task_id: str, st: dict) -> bool:
    if task_id in st.get("handled", {}).get(slug, {}):
        return True
    row = con.execute(
        "SELECT 1 FROM task_comments WHERE task_id=? AND body LIKE ? LIMIT 1",
        (task_id, f"{MARKER}%"),
    ).fetchone()
    return row is not None


def authors_of_work(con: sqlite3.Connection, work_id: str, seen: set[str]) -> set[str]:
    """Authoring profiles of a work card: creator, assignee, completed-run profile."""
    out: set[str] = set()
    if work_id in seen:
        return out
    seen.add(work_id)
    row = con.execute("SELECT created_by, assignee FROM tasks WHERE id=?", (work_id,)).fetchone()
    if not row:
        return out
    for v in (row["created_by"], row["assignee"]):
        if not _is_non_author(v):
            out.add(v)
    for r in con.execute(
        "SELECT DISTINCT profile FROM task_runs WHERE task_id=? AND status='done'", (work_id,)
    ):
        if not _is_non_author(r["profile"]):
            out.add(r["profile"])
    return out


def gated_authors(con: sqlite3.Connection, gate: sqlite3.Row) -> set[str]:
    """R6's 'author of the bytes under review', derived mechanically."""
    out: set[str] = set()
    if not _is_non_author(gate["created_by"]):
        # 'never to yourself': the gate's own creator is a creating-lane author
        out.add(gate["created_by"])
    parent_ids = [r[0] for r in con.execute(
        "SELECT parent_id FROM task_links WHERE child_id=?", (gate["id"],))]
    ref_ids = {m.group(0) for m in TASK_ID_RE.finditer((gate["body"] or ""))}
    seen: set[str] = set()
    for wid in list(parent_ids) + sorted(ref_ids):
        out |= authors_of_work(con, wid, seen)
    return out


def violation(gate: sqlite3.Row, authors: set[str]) -> str | None:
    """'self-assigned' | 'author-gate' | 'unassigned' or None."""
    asg = gate["assignee"]
    if not asg:
        return "unassigned"
    if asg == gate["created_by"]:
        return "self-assigned"
    if asg in authors:
        return "author-gate"
    return None


def verdict_excerpt(con: sqlite3.Connection, task_id: str) -> str:
    row = con.execute(
        "SELECT body FROM task_comments WHERE task_id=? AND body LIKE 'VERDICT:%' "
        "ORDER BY id DESC LIMIT 1", (task_id,)).fetchone()
    if row:
        return row["body"][:200].replace("\n", " | ")
    return "(no VERDICT comment found \u2014 completion itself is the recorded verdict)"


def cli(args: list[str], dry: bool) -> tuple[int, str]:
    cmd = [str(HERMES)] + args
    if dry:
        log(f"  [dry-run] would run: {' '.join(cmd[:10])}...")
        return 0, "dry-run"
    # This daemon IS the headless board-tooling layer (system crontab): scrub
    # any inherited delegate-child / board-scoping fence vars so its supported
    # CLI mutators have uniform authority regardless of the caller's env
    # (from crontab these vars do not exist; hand-running must match).
    env = {k: v for k, v in os.environ.items()
           if k not in ("HERMES_DELEGATED_CHILD_CONTEXT", "HERMES_KANBAN_DB",
                        "HERMES_KANBAN_BOARD", "HERMES_KANBAN_WORKSPACES_ROOT",
                        "HERMES_KANBAN_TASK")}
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
    out = (p.stdout or "") + (p.stderr or "")
    if p.returncode != 0:
        log(f"  CLI rc={p.returncode}: {' '.join(cmd[:8])} :: {out.strip()[:400]}")
    return p.returncode, out


def alert(title: str, body: str, dry: bool) -> None:
    if dry:
        log(f"  [dry-run] would alert: {title}")
        return
    if not ALERT_SINK.exists():
        log(f"  [alert-missing] {title}")
        return
    try:
        subprocess.run(
            ["bash", str(ALERT_SINK), "--tag", "nsg-enforcer", "--title", title, "--body", body],
            capture_output=True, text=True, timeout=60)
    except Exception as exc:  # never crash the watchdog on its alert path
        log(f"  [alert-failed] {exc}")


def enforce_intake(slug: str, gate: sqlite3.Row, authors: set[str], vkind: str, dry: bool) -> dict:
    tid = gate["id"]
    target = gate_profile_for(gate["title"], gate["body"] or "")
    actions: dict = {"action": "intake-refusal", "kind": vkind, "reassigned_to": target}
    if target and target != gate["assignee"]:
        r64 = f"misassigned gate \u2014 reassign to {target}"
    else:
        r64 = ("misassigned gate \u2014 reassign to an independent gate profile "
               "(text gates: distiller; code review: sw-reviewer)")
        target = None
    note = (f"{MARKER} R6.4 refusal] {r64}.\n"
            f"NO-SELF-GATE (R6, docs/gate-wait-pattern-2026-10-28.md @ 31d5b4b): this gate card's "
            f"assignee '{gate['assignee'] or '(unassigned)'}' is the author/creating lane of the "
            f"gated work (violation: {vkind}; authors: {sorted(authors) or ['creator']}). "
            f"A self-gate verdict is void (R6.3); this card is mechanically rerouted to an "
            f"independent gate profile. \u2014 enforced automatically (t_ad14438a).")
    if dry:
        log(f"  [dry-run] would comment on {tid}: {note[:120]}...")
    else:
        cli(["kanban", "--board", slug, "comment", tid, note, "--author", COMMENT_AUTHOR], dry)
    if target:
        args = ["kanban", "--board", slug, "reassign", tid, target]
        if gate["status"] == "running":
            args += ["--reclaim"]
        args += ["--reason",
                 "NO-SELF-GATE R6.1 mechanical intake reroute: author's in-flight self-gate run "
                 "refused/reclaimed before any verdict can land (t_ad14438a enforcer)"]
        if dry:
            log(f"  [dry-run] would reassign {tid} -> {target}")
        else:
            cli(args, dry)
    else:
        if dry:
            log(f"  [dry-run] would block {tid} needs_input (no determinable gate profile)")
        else:
            cli(["kanban", "--board", slug, "block", tid, "--kind", "needs_input",
                 f"{MARKER} R6.1] gate author-independence cannot be resolved mechanically (no "
                 f"determinable independent gate profile in title/body). Blocked for human routing."], dry)
    alert(f"[NSG-ENFORCER] misassigned gate refused on {slug}: {tid}",
          f"{(gate['title'] or '')[:100]}\nassignee={gate['assignee']} == author ({vkind}); "
          f"{'rerouted to ' + str(target) if target else 'blocked needs_input for routing'}.", dry)
    return actions


def enforce_void(slug: str, gate: sqlite3.Row, authors: set[str], vkind: str,
                 verdict: str, children: list[str], dry: bool) -> dict:
    tid = gate["id"]
    target = gate_profile_for(gate["title"], gate["body"] or "")
    actions: dict = {"action": "self-pass-void", "kind": vkind, "regate": None}

    note = (f"{MARKER} R6.3] SELF-PASS VOID \u2014 the PASS on this gate card is VOID: assignee "
            f"'{gate['assignee']}' authored the gated bytes (violation: {vkind}; authors: "
            f"{sorted(authors) or ['creator']}). Recorded verdict: {verdict}. NO-SELF-GATE "
            f"(R6, docs/gate-wait-pattern-2026-10-28.md @ 31d5b4b): a self-issued PASS is void "
            f"and not a negative verdict either \u2014 the bytes are UNVALIDATED. "
            + (f"{len(children)} apply leg(s) stopped and reparented to an independent re-gate which "
               f"must run the FULL check set fresh." if children else
               "No apply legs were released by this gate.")
            + " \u2014 enforced automatically (t_ad14438a).")
    if dry:
        log(f"  [dry-run] would comment VOID on {tid}: {note[:120]}...")
    else:
        cli(["kanban", "--board", slug, "comment", tid, note, "--author", COMMENT_AUTHOR], dry)

    if children:
        for c in children:
            cnote = (f"{MARKER} R6.3 apply-leg stop] the gate that released this card had a "
                     f"SELF-ISSUED PASS (void, NO-SELF-GATE R6.1/R6.3). Stopped and reparented to "
                     f"the independent re-gate. Do not proceed on the voided verdict.")
            if dry:
                log(f"  [dry-run] would comment+block leg {c}")
            else:
                cli(["kanban", "--board", slug, "comment", c, cnote, "--author", COMMENT_AUTHOR], dry)
                cli(["kanban", "--board", slug, "block", c, "--kind", "needs_input",
                     f"{MARKER}] stopped by NSG enforcer: self-pass void on gate {tid}"], dry)
                cli(["kanban", "--board", slug, "unlink", tid, c], dry)
        if target:
            body = (f"Independent re-gate filed mechanically per NO-SELF-GATE R6.3 "
                    f"(docs/gate-wait-pattern-2026-10-28.md @ 31d5b4b): the prior gate {tid} "
                    f"('{(gate['title'] or '')[:120]}') was assigned to the author of the gated "
                    f"bytes, so its PASS is void. This card re-gates the SAME bytes with the FULL "
                    f"check set fresh and never defers to the voided verdict.\n\n"
                    f"--- Original gate card body (verbatim below) ---\n{gate['body'] or ''}")
            if dry:
                regate_id = "(dry-run: would create)"
                log(f"  [dry-run] would create RE-GATE card assigned {target}, then link+unblock legs")
            else:
                title = f"RE-GATE (R6.3 mechanical, void of {tid}): {(gate['title'] or '')[:110]}"
                rc, out = cli(["kanban", "--board", slug, "create", title,
                               "--assignee", target, "--created-by", COMMENT_AUTHOR,
                               "--priority", str(gate["priority"] or 6),
                               "--body", body, "--json"], dry)
                regate_id = None
                if rc == 0:
                    try:
                        j = json.loads(out.strip().splitlines()[-1])
                        regate_id = (j.get("id") or j.get("task", {}).get("id")
                                     or (j.get("task") or {}).get("id"))
                    except Exception:
                        m = re.search(r"\bt_[0-9a-f]{8}\b", out)
                        regate_id = m.group(0) if m else None
                actions["regate"] = regate_id
                if regate_id:
                    for c in children:
                        cli(["kanban", "--board", slug, "link", regate_id, c], dry)
                    for c in children:
                        cli(["kanban", "--board", slug, "unblock", c, "--reason",
                             f"{MARKER}] reparented to independent re-gate {regate_id}; "
                             f"todo-gated until fresh PASS"], dry)
                else:
                    log(f"  [ERROR] re-gate creation failed for void of {tid}; legs stay blocked, alerting")
        else:
            for c in children:
                cnote2 = (f"{MARKER}] no independent gate profile determinable from the voided "
                          f"gate's title/body; this leg stays blocked for human routing to "
                          f"distiller or sw-reviewer (R6.3).")
                if not dry:
                    cli(["kanban", "--board", slug, "comment", c, cnote2, "--author", COMMENT_AUTHOR], dry)
                else:
                    log(f"  [dry-run] would annotate leg {c}: no determinable regate profile")
    alert(f"[NSG-ENFORCER] SELF-PASS VOIDED on {slug}: {tid}",
          f"{(gate['title'] or '')[:100]}\nassignee={gate['assignee']} == author ({vkind}); "
          f"void per R6.3; {len(children)} apply leg(s) stopped; regate={actions.get('regate')}.", dry)
    return actions


def scan_board(slug: str, db: Path, st: dict, activation_ts: int, dry: bool) -> list[dict]:
    results: list[dict] = []
    skip = EXCEPTIONS.get(slug, set())
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
        con.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        log(f"[{slug}] cannot open: {exc}")
        return results
    for gate in con.execute("SELECT * FROM tasks WHERE status != 'archived'"):
        tid = gate["id"]
        if tid in skip or already_acted(con, slug, tid, st):
            continue
        if not gate_declared(gate["title"] or "", gate["body"] or ""):
            continue
        authors = gated_authors(con, gate)
        vkind = violation(gate, authors)
        if not vkind:
            continue
        if gate["status"] == "done":
            if not gate["completed_at"] or gate["completed_at"] < activation_ts:
                continue  # retro exemption: pre-activation completions are doc-law territory
            children = [r[0] for r in con.execute(
                "SELECT child_id FROM task_links WHERE parent_id=?", (tid,))]
            verdict = verdict_excerpt(con, tid)
            log(f"[{slug}] VOID-ARM {tid} ({vkind}): {(gate['title'] or '')[:80]}")
            res = enforce_void(slug, gate, authors, vkind, verdict, children, dry)
        else:
            if not gate["created_at"] or gate["created_at"] < LAW_TS:
                continue  # pre-law creations are doc-law territory
            log(f"[{slug}] INTAKE-ARM {tid} ({vkind}): {(gate['title'] or '')[:80]}")
            res = enforce_intake(slug, gate, authors, vkind, dry)
        res.update({"board": slug, "id": tid, "title": gate["title"], "status": gate["status"],
                    "assignee": gate["assignee"], "created_by": gate["created_by"],
                    "authors": sorted(authors)})
        results.append(res)
    con.close()
    return results


def board_dbs() -> list[tuple[str, Path]]:
    out = [("default", DEFAULT_DB)]
    if BOARDS_ROOT.is_dir():
        for d in sorted(BOARDS_ROOT.iterdir()):
            if d.is_dir() and not d.name.startswith(("_", ".")) and (d / "kanban.db").exists():
                out.append((d.name, d / "kanban.db"))
    return out


def detect_only(slug: str, db: Path, st: dict, activation_ts: int) -> list[dict]:
    """Same scan + violation logic, no enforcement side effects (selftest/dry helpers)."""
    results: list[dict] = []
    skip = EXCEPTIONS.get(slug, set())
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=5)
        con.row_factory = sqlite3.Row
    except sqlite3.Error:
        return results
    for gate in con.execute("SELECT * FROM tasks WHERE status != 'archived'"):
        tid = gate["id"]
        if tid in skip or already_acted(con, slug, tid, st):
            continue
        if not gate_declared(gate["title"] or "", gate["body"] or ""):
            continue
        authors = gated_authors(con, gate)
        vkind = violation(gate, authors)
        if not vkind:
            continue
        if gate["status"] == "done":
            if not gate["completed_at"] or gate["completed_at"] < activation_ts:
                continue
        else:
            if not gate["created_at"] or gate["created_at"] < LAW_TS:
                continue
        results.append({"id": tid, "board": slug, "kind": vkind, "status": gate["status"],
                        "title": gate["title"], "assignee": gate["assignee"],
                        "created_by": gate["created_by"], "authors": sorted(authors)})
    con.close()
    return results


def selftest() -> int:
    """Fixture self-test against the t_fecde306 incident shape (no live DB writes)."""
    ok = True

    def check(name, cond):
        nonlocal ok
        print(("PASS " if cond else "FAIL ") + name)
        ok = ok and bool(cond)

    check("incident title declares gate",
          gate_declared("DISTILLER GATE: PR342-RETRO rework pack (4 bodies)", "Gate for 4 reworked bodies..."))
    check("skeleton title declares gate", gate_declared("DISTILLER GATE \u2014 mprov-cc-337 filing", ""))
    check("auditor gate colon declares", gate_declared("GAUDI-AUDITOR-GATE-1860-BATTERY-COMMENT: gate the draft", ""))
    check("plain 'GATE:' declares", gate_declared("GATE: distiller review \u2014 B2-4 bundle", ""))
    check("law card title excluded", not gate_declared(
        "MECH-A: mechanical no-self-gate enforcement in board tooling \u2014 gate PASS by the author of gated work is refused", "body"))
    check("operator-final-gate policy excluded", not gate_declared(
        "OPERATOR-FINAL-GATE: operator is last gate on all public filings", "body"))
    check("'gated' is not a gate decl", not gate_declared(
        "UPSTREAM-SUBMIT (OPERATOR-GATED): boards-list-counts PR", "x"))
    check("'gateway' is not a gate decl", not gate_declared("GATEWAY-BOUNCE-SKILL: codify restart", "x"))
    check("'dependency gate' EOS not strong", not gate_declared(
        "Purge superseded glm52 images behind dependency gate", "x"))
    check("body 'Gate for' declares (law-quoting line skipped)",
          gate_declared("x", "some intro\nNO-SELF-GATE law text line\nGate for 4 reworked bodies from t_ad0d3a55"))
    check("body quoting law alone is NOT a declaration",
          not gate_declared("CURATE-4-FOLDIN: refit x", "mentions NO-SELF-GATE and self-gate several times"))
    check("distiller target", gate_profile_for("DISTILLER GATE: x", "gate") == "distiller")
    check("code review target", gate_profile_for("REVIEW GATE: PR #12", "code review of diff") == "sw-reviewer")
    check("no target", gate_profile_for("SHIP GATE: x", "final assembly") is None)

    tmpdir = Path(tempfile.mkdtemp(prefix="nsg-selftest-"))
    tmp = tmpdir / "k.db"
    con = sqlite3.connect(tmp)
    con.executescript(
        "CREATE TABLE tasks (id TEXT PRIMARY KEY, title TEXT, body TEXT, assignee TEXT, status TEXT, "
        "created_by TEXT, created_at INTEGER, completed_at INTEGER);"
        "CREATE TABLE task_links (parent_id TEXT, child_id TEXT, PRIMARY KEY (parent_id, child_id));"
        "CREATE TABLE task_runs (id INTEGER PRIMARY KEY, task_id TEXT, profile TEXT, status TEXT, outcome TEXT);"
        "CREATE TABLE task_comments (id INTEGER PRIMARY KEY, task_id TEXT, author TEXT, body TEXT, created_at INTEGER);"
        "INSERT INTO tasks VALUES ('t_fecde306','DISTILLER GATE: PR342-RETRO rework pack (4 bodies)',"
        "'Gate for 4 reworked bodies from t_work000. Files byte-pinned.','sw-dev-b','done','sw-dev-b',"
        + str(LAW_TS + 1000) + "," + str(int(datetime.now(timezone.utc).timestamp()) + 100) + ");"
        "INSERT INTO tasks VALUES ('t_work000','PR342-RETRO rework','drafting','sw-dev-b','done','sw-dev-b',"
        + str(LAW_TS) + "," + str(LAW_TS + 500) + ");"
        "INSERT INTO task_links VALUES ('t_fecde306','t_apply000');"
        "INSERT INTO tasks VALUES ('t_apply000','APPLY: PR342-RETRO','apply the pack','sw-dev-b','ready','sw-dev-b',"
        + str(LAW_TS + 2000) + ",NULL);"
        "INSERT INTO task_runs VALUES (1,'t_work000','sw-dev-b','done','completed');"
        "INSERT INTO task_comments VALUES (1,'t_fecde306','sw-dev-b','VERDICT: PASS (relaxed checks)',0);"
    )
    con.row_factory = sqlite3.Row
    con.commit()

    class FakeCon:
        """Adapt detect_only to the fixture tables via a plain connection."""
        def __init__(self, c):
            self.c = c

    # run the real scan path against the fixture
    st: dict = {"handled": {}}
    res = detect_only("software-co", tmp, st, LAW_TS + 1000)
    check("incident shape detected", [r["id"] for r in res] == ["t_fecde306"])
    check("incident violation kind", bool(res) and res[0]["kind"] == "self-assigned")
    check("incident authors include work author", bool(res) and "sw-dev-b" in res[0]["authors"])

    # suppression tests on the fixture: acted-marker comment and idempotence
    con.execute("INSERT INTO task_comments VALUES (2,'t_fecde306','nsg-enforcer','"
                "[NO-SELF-GATE-ENFORCER R6.3] already voided',1)")
    con.commit()
    res2 = detect_only("software-co", tmp, {"handled": {}}, LAW_TS + 1000)
    check("marker comment suppresses re-action", res2 == [])
    con.close()
    print("\nSELFTEST:", "ALL PASS" if ok else "FAILURES")
    return 0 if ok else 2


def main() -> int:
    dry = "--dry-run" in sys.argv
    if "--selftest" in sys.argv:
        return selftest()
    st = load_state()
    if "activation_ts" not in st:
        st["activation_ts"] = int(datetime.now(timezone.utc).timestamp())
        save_state(st)
    activation_ts = int(st.get("activation_ts", LAW_TS))
    acted = st.setdefault("handled", {})
    all_results: list[dict] = []
    for slug, db in board_dbs():
        all_results += scan_board(slug, db, st, activation_ts, dry)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if all_results:
        for r in all_results:
            acted.setdefault(r["board"], {})[r["id"]] = {
                k: r.get(k) for k in ("action", "kind", "reassigned_to", "regate", "authors")}
        if not dry:
            save_state(st)
        log(f"enforced {len(all_results)} violation(s); state saved")
        return 1
    if st.get("last_beat_day") != today:
        st["last_beat_day"] = today
        if not dry:
            save_state(st)
        log(f"heartbeat: clean scan, 0 violations (activation_ts={activation_ts})")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        import traceback
        traceback.print_exc()
        sys.exit(2)
