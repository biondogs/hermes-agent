"""Tests for decompose_triage_task — the DB-layer atomic fan-out
from the triage column. LLM-free by design.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli.kanban_db_graph import decompose_triage_task
from hermes_cli import kanban_db_connect as kbc


@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb.init_db()
    return home


def _create_triage(conn, title="rough idea", body=None, assignee=None, tenant=None):
    return kb.create_task(
        conn,
        title=title,
        body=body,
        assignee=assignee,
        tenant=tenant,
        triage=True,
    )


def test_decompose_creates_children_and_promotes_root(kanban_home):
    with kbc.connect() as conn:
        tid = _create_triage(conn, title="ship a feature")
        assert kb.get_task(conn, tid).status == "triage"

    children = [
        {"title": "research", "body": "look at prior art", "assignee": "researcher", "parents": []},
        {"title": "build it", "body": "write code", "assignee": "engineer", "parents": [0]},
    ]
    with kbc.connect() as conn:
        child_ids = decompose_triage_task(
            conn,
            tid,
            root_assignee="orchestrator",
            children=children,
            author="decomposer",
        )
    assert child_ids is not None
    assert len(child_ids) == 2

    with kbc.connect() as conn:
        root = kb.get_task(conn, tid)
        c0 = kb.get_task(conn, child_ids[0])
        c1 = kb.get_task(conn, child_ids[1])

    # Root flipped to todo with orchestrator assignee, gated by children.
    assert root.status == "todo"
    assert root.assignee == "orchestrator"
    # First child has no internal parents → ready on recompute_ready.
    assert c0.status == "ready"
    assert c0.assignee == "researcher"
    # Second child has parents=[0] → stays in todo until c0 completes.
    assert c1.status == "todo"
    assert c1.assignee == "engineer"


def test_decompose_records_audit_comment_and_event(kanban_home):
    with kbc.connect() as conn:
        tid = _create_triage(conn)
        child_ids = decompose_triage_task(
            conn,
            tid,
            root_assignee="orch",
            children=[{"title": "task A", "assignee": "researcher"}],
            author="alice",
        )
    assert child_ids is not None

    with kbc.connect() as conn:
        comments = kb.list_comments(conn, tid)
        events = kb.list_events(conn, tid)

    assert comments
    assert any(ev.kind == "decomposed" for ev in events)


def test_decompose_children_carry_idempotency_keys(kanban_home):
    """Every spawned child is keyed ``decompose:<root>:<idx>`` so the fan-out
    is traceable and dedupable even off the decompose tool path."""
    with kbc.connect() as conn:
        tid = _create_triage(conn, title="keyed fanout")
    children = [
        {"title": "first", "assignee": "researcher"},
        {"title": "second", "assignee": "engineer", "parents": [0]},
    ]
    with kbc.connect() as conn:
        child_ids = decompose_triage_task(
            conn, tid, root_assignee="orch", children=children, author="decomposer",
        )
    assert child_ids is not None
    with kbc.connect() as conn:
        for idx, cid in enumerate(child_ids):
            row = kb.get_task(conn, cid)
            assert row is not None
            assert row.idempotency_key == f"decompose:{tid}:{idx}"


def test_decompose_marker_deleted_reuses_children_backstop(kanban_home):
    """PRIMARY gate is the durable ``decomposed`` event marker; this backstop
    proves the idempotency keys hold when that marker is removed: a fresh
    decompose of the same root re-links the SAME children, never duplicates."""
    with kbc.connect() as conn:
        tid = _create_triage(conn, title="backstop")
    children = [{"title": "solo work", "assignee": "researcher"}]
    with kbc.connect() as conn:
        first = decompose_triage_task(
            conn, tid, root_assignee="orch", children=children, author="decomposer",
        )
    assert first is not None

    with kbc.connect() as conn:
        before_ids = [r["id"] for r in conn.execute("SELECT id FROM tasks ORDER BY id")]
        # Simulate the worst case: wipe the marker AND re-open the root to triage.
        with kb.write_txn(conn):
            conn.execute(
                "DELETE FROM task_events WHERE task_id = ? AND kind = 'decomposed'",
                (tid,),
            )
            conn.execute("UPDATE tasks SET status = 'triage' WHERE id = ?", (tid,))

    with kbc.connect() as conn:
        second = decompose_triage_task(
            conn, tid, root_assignee="orch", children=children, author="decomposer",
        )
    assert second is not None, "marker gone: fan-out proceeds, but must reuse"
    assert second == first, "backstop must return the existing children"

    with kbc.connect() as conn:
        after_ids = [r["id"] for r in conn.execute("SELECT id FROM tasks ORDER BY id")]
        assert after_ids == before_ids, "no duplicate tasks created"
        root_after = kb.get_task(conn, tid)
        assert root_after is not None and root_after.status == "todo"
        # Reuse is auditable on the child.
        evs = kb.list_events(conn, first[0])
        assert any(ev.kind == "decompose_child_reused" for ev in evs)


def test_decompose_repeat_still_refused_by_marker(kanban_home):
    """The marker remains the primary gate: an ordinary re-triage (marker
    intact) is refused outright, keys notwithstanding."""
    with kbc.connect() as conn:
        tid = _create_triage(conn, title="marker gate")
    children = [{"title": "only", "assignee": "researcher"}]
    with kbc.connect() as conn:
        first = decompose_triage_task(
            conn, tid, root_assignee="orch", children=children, author="decomposer",
        )
    assert first is not None
    with kbc.connect() as conn:
        with kb.write_txn(conn):
            conn.execute("UPDATE tasks SET status = 'triage' WHERE id = ?", (tid,))
    with kbc.connect() as conn:
        assert decompose_triage_task(
            conn, tid, root_assignee="orch", children=children, author="decomposer",
        ) is None





