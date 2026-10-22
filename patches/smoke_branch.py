"""Branch smoke: create+archive roundtrip through tools.kanban_archive on a
throwaway HERMES_HOME. Prints the imported kanban_tools path to prove the
worktree copy (not the live install) executed."""
import json, os, sys, tempfile
from pathlib import Path

worktree = sys.argv[1]
home = tempfile.mkdtemp(prefix="kanban-archive-smoke-")
os.environ["HERMES_HOME"] = home
for key in ("HERMES_KANBAN_TASK", "HERMES_KANBAN_DB", "HERMES_KANBAN_BOARD",
            "HERMES_DELEGATED_CHILD_CONTEXT", "HERMES_KANBAN_RUN_ID"):
    os.environ.pop(key, None)
sys.path.insert(0, worktree)

from tools import kanban_tools as kt
print("kanban_tools imported from:", kt.__file__)

from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_connect as kbc
kb._INITIALIZED_PATHS.clear()
kb.init_db()

conn = kbc.connect()
tid = kb.create_task(conn, title="smoke-roundtrip", assignee="smoke")
conn.close()
print("created:", tid)

out = json.loads(kt._handle_archive({"task_id": tid}))
print("tool result:", out)
assert out.get("ok") is True and out.get("status") == "archived", out

conn = kbc.connect()
task = kb.get_task(conn, tid)
print("db status:", task.status)
assert task.status == "archived"
conn.close()

again = json.loads(kt._handle_archive({"task_id": tid}))
print("re-archive:", again)
assert again.get("error"), again

unknown = json.loads(kt._handle_archive({"task_id": "t_missing"}))
print("unknown id:", unknown)
assert unknown.get("error"), unknown

from tools.registry import registry
schema = registry.get_schema("kanban_archive")
print("schema registered: name=%s required=%s props=%s" % (
    schema["name"], schema["parameters"]["required"],
    sorted(schema["parameters"]["properties"])))
print("SMOKE PASS", home)
