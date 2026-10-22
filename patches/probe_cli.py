"""CLI regression probe: `hermes kanban create/archive` on a throwaway HERMES_HOME
against the patched live install. Proves the hot-applied tree keeps the CLI path
working identically."""
import json, os, subprocess, sys, tempfile

home = tempfile.mkdtemp(prefix="kanban-cli-probe-")
env = {k: v for k, v in os.environ.items()
       if k not in ("HERMES_KANBAN_DB", "HERMES_KANBAN_BOARD",
                    "HERMES_KANBAN_TASK", "HERMES_DELEGATED_CHILD_CONTEXT")}
env["HERMES_HOME"] = home

def run_json(*args):
    r = subprocess.run(["hermes", "kanban", *args, "--json"],
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

def run(*args):
    r = subprocess.run(["hermes", "kanban", *args],
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout.strip(), r.stderr.strip()

rc, out, err = run_json("create", "cli-probe-card", "--assignee", "probe")
assert rc == 0, (rc, err)
data = json.loads(out)
tid = data.get("task_id") or (data.get("task") or {}).get("id") or data.get("id")
assert tid, data
print("cli created:", tid)

rc, out, err = run("archive", tid)
print("cli archive rc=%s out=%.160s" % (rc, out))
assert rc == 0, (rc, err)

rc, out, err = run("archive", tid)
print("cli re-archive rc=%s out=%.160s err=%.160s" % (rc, out, err))
assert rc != 0, (rc, out)
print("CLI-PROBE PASS", home)
