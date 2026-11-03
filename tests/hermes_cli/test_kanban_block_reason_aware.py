"""Reason-aware block-loop breaker + escalated-decision hold + atomic relay/unblock
(LOCAL HOTFIX t_0ba77c1e).

Incident (Specimen B, 2026-11-02): ``_route_block`` compared block KIND only,
so every multi-stage operator flow (needs_input GO-1 -> unblock -> work ->
needs_input GO-2) tripped ``block_loop_detected`` and landed in triage, where
the auto-decomposer re-planned it with no human involved (gaudi t_8d898b44
fanned into 6 cards, t_35f2ab06 into 5). All 49 historical block-loop events
fleet-wide were needs_input. Specimen A: the relay comment and the unblock
were two separate calls; the relay sat on a still-blocked card for 3h41m.

Pinned here:
* a needs_input re-block with a DIFFERENT normalized reason is a new decision
  (stays ``blocked``, recurrences reset to 1); same-reason re-blocks,
  missing reasons, re-kinded dependency waits and every other kind escalate;
* a ``block_loop_detected`` needs_input episode is a kernel-level hold
  (marker-independent): no specify/decompose/sweep touches it, unblock frees it;
* ``unblock_task(comment=...)``, the CLI ``--reason`` and the
  ``kanban_unblock(comment=...)`` tool write relay + release atomically.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from hermes_cli import kanban as kanban_cli
from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_connect as kbc
from hermes_cli import kanban_decompose, kanban_specify
from hermes_cli.kanban_db_graph import decompose_triage_task


@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    # A marker nothing below uses: proves the escalated-decision hold is
    # kernel-level and does not ride on the configured hold markers.
    monkeypatch.setenv("HERMES_KANBAN_HOLD_MARKERS", "NO-SUCH-MARKER-XYZ")
    monkeypatch.delenv("HERMES_KANBAN_TASK", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb._INITIALIZED_PATHS.clear()
    kb.init_db()
    return home


GO1 = "Ready for operator GO-1: approve the migration plan (doc v1, sha256 aaaa)."
GO2 = "Ready for operator GO-2: approve the cut-over window (diff v2, sha256 bbbb)."
GO3 = "Ready for operator GO-3: confirm rollback drill results."


def _card(conn, title="decision card"):
    return kb.create_task(conn, title=title, body="multi-stage", assignee="default")


def _t(conn, tid):
    task = kb.get_task(conn, tid)
    assert task is not None
    return task


def _last(conn, tid, kind) -> dict:
    events = [e for e in kb.list_events(conn, tid) if e.kind == kind]
    assert events, f"expected a {kind} event"
    return events[-1].payload or {}


# --- Normalization ------------------------------------------------------------


def test_block_reason_hash_normalizes_noise_but_not_content():
    h = kb.block_reason_hash
    assert h("Need GO-2  for\n the cut-over") == h("  need go-2 for the CUT-OVER ")
    assert h("need GO-1") != h("need GO-2")
    assert h(None) is None and h("") is None and h("   \n") is None
    assert len(h("x") or "") == 12


# --- Breaker semantics ----------------------------------------------------------


def test_multi_stage_operator_flow_never_escalates(kanban_home):
    """GO-1 -> unblock -> GO-2 -> unblock -> GO-3: each a new decision."""
    with kbc.connect() as conn:
        tid = _card(conn)
        for reason in (GO1, GO2, GO3):
            assert kb.block_task(conn, tid, reason=reason, kind="needs_input") is True
            task = _t(conn, tid)
            assert (task.status, task.block_kind, task.block_recurrences) == ("blocked", "needs_input", 1)
            assert kb.unblock_task(conn, tid) is True
        assert not [e for e in kb.list_events(conn, tid) if e.kind == "block_loop_detected"]
        second = [e.payload or {} for e in kb.list_events(conn, tid) if e.kind == "blocked"][1]
        assert second["new_decision"] is True
        assert second["reason_hash"] == kb.block_reason_hash(GO2)
        assert second["prev_reason_hash"] == kb.block_reason_hash(GO1)


def test_needs_input_same_reason_still_escalates(kanban_home):
    """Whitespace/case-only variation is the SAME reason: still a loop."""
    with kbc.connect() as conn:
        tid = _card(conn)
        assert kb.block_task(conn, tid, reason=GO1, kind="needs_input")
        assert kb.unblock_task(conn, tid)
        assert kb.block_task(conn, tid, reason="  " + GO1.upper() + "\n", kind="needs_input")
        assert _t(conn, tid).status == "triage"
        loop = _last(conn, tid, "block_loop_detected")
        assert loop["recurrences"] == kb.BLOCK_RECURRENCE_LIMIT
        assert loop["reason_hash"] == kb.block_reason_hash(GO1)
        assert "new_decision" not in loop


def test_needs_input_missing_reason_still_escalates(kanban_home):
    with kbc.connect() as conn:
        tid = _card(conn)
        assert kb.block_task(conn, tid, reason=GO1, kind="needs_input")
        assert kb.unblock_task(conn, tid)
        assert kb.block_task(conn, tid, reason=None, kind="needs_input")
        assert _t(conn, tid).status == "triage"


@pytest.mark.parametrize("kind", ["capability", "transient", None])
def test_other_kinds_with_different_reasons_still_escalate(kanban_home, kind):
    """Only needs_input is reason-aware; flaps of other kinds keep the old breaker."""
    with kbc.connect() as conn:
        tid = _card(conn)
        assert kb.block_task(conn, tid, reason="flaky A", kind=kind)
        assert kb.unblock_task(conn, tid)
        assert kb.block_task(conn, tid, reason="flaky B", kind=kind)
        assert _t(conn, tid).status == "triage"


def test_kind_change_still_resets_as_before(kanban_home):
    with kbc.connect() as conn:
        tid = _card(conn)
        assert kb.block_task(conn, tid, reason=GO1, kind="capability")
        assert kb.unblock_task(conn, tid)
        assert kb.block_task(conn, tid, reason=GO1, kind="needs_input")
        assert (_t(conn, tid).status, _t(conn, tid).block_recurrences) == ("blocked", 1)


def test_legacy_block_event_without_hash_compares_by_stored_reason(kanban_home):
    """Events written before the hotfix carry no ``reason_hash``: the previous
    reason is re-hashed from the payload, so history compares correctly."""
    with kbc.connect() as conn:
        same = _card(conn, "legacy same")
        diff = _card(conn, "legacy diff")
        for tid in (same, diff):
            assert kb.block_task(conn, tid, reason=GO1, kind="needs_input")
            with kb.write_txn(conn):
                row = conn.execute(
                    "SELECT id, payload FROM task_events WHERE task_id=? AND kind='blocked' "
                    "ORDER BY id DESC LIMIT 1", (tid,)).fetchone()
                payload = json.loads(row["payload"])
                payload.pop("reason_hash", None)
                conn.execute("UPDATE task_events SET payload=? WHERE id=?", (json.dumps(payload), row["id"]))
            assert kb.unblock_task(conn, tid)
        assert kb.block_task(conn, same, reason=GO1, kind="needs_input")
        assert kb.block_task(conn, diff, reason=GO2, kind="needs_input")
        assert _t(conn, same).status == "triage"
        assert _t(conn, diff).status == "blocked"


def test_operator_hold_marker_escape_hatch_still_escalates_and_holds(kanban_home, monkeypatch):
    """The t_7fd1c800 path is intact: a same-reason marker hold re-block goes
    to triage and is held by the marker (here kind=capability so only the
    marker can be the reason it is held)."""
    monkeypatch.setenv("HERMES_KANBAN_HOLD_MARKERS", "OPERATOR HOLD")
    with kbc.connect() as conn:
        tid = _card(conn)
        reason = "OPERATOR HOLD: parked until the operator reschedules"
        assert kb.block_task(conn, tid, reason=reason, kind="capability")
        assert kb.unblock_task(conn, tid)
        assert kb.block_task(conn, tid, reason=reason, kind="capability")
        assert _t(conn, tid).status == "triage"
        assert kb.task_hold_reason(conn, tid) == reason


# --- Escalated decision = kernel-level hold -----------------------------------------


def _escalate(conn, tid):
    assert kb.block_task(conn, tid, reason=GO2, kind="needs_input")
    assert kb.unblock_task(conn, tid)
    assert kb.block_task(conn, tid, reason=GO2, kind="needs_input")
    assert _t(conn, tid).status == "triage"


def test_escalated_needs_input_loop_is_held_without_markers(kanban_home):
    with kbc.connect() as conn:
        tid = _card(conn)
        _escalate(conn, tid)
        held = kb.task_hold_reason(conn, tid)
        assert held and "ESCALATED OPERATOR DECISION" in held and "GO-2" in held


def test_escalated_decision_refuses_specify_and_decompose(kanban_home, monkeypatch):
    with kbc.connect() as conn:
        tid = _card(conn)
        _escalate(conn, tid)
        with pytest.raises(kb.TaskHeldError):
            kb.specify_triage_task(conn, tid, title="re-planned", body="nope", author="auto-decomposer")
        with pytest.raises(kb.TaskHeldError):
            decompose_triage_task(
                conn, tid, root_assignee="default",
                children=[{"title": "frag", "body": "b", "assignee": "default", "parents": []}],
            )
        assert _t(conn, tid).status == "triage"
        assert conn.execute("SELECT COUNT(*) AS n FROM tasks WHERE id != ?", (tid,)).fetchone()["n"] == 0

    def _no_aux(*args, **kwargs):
        raise AssertionError("aux LLM must not be called for an escalated decision")

    monkeypatch.setattr(kanban_decompose, "_call_aux", _no_aux)
    monkeypatch.setattr(kanban_specify, "_call_aux", _no_aux)
    assert kanban_decompose.decompose_task(tid, author="auto-decomposer").ok is False
    assert kanban_specify.specify_task(tid, author="auto-decomposer").ok is False


def test_sweeps_skip_escalated_decision_but_not_plain_triage(kanban_home):
    with kbc.connect() as conn:
        held = _card(conn)
        _escalate(conn, held)
        plain = kb.create_task(conn, title="rough idea", assignee="default", triage=True)
    assert kanban_decompose.list_triage_ids() == [plain]
    assert kanban_specify.list_triage_ids() == [plain]


def test_unblock_releases_escalated_decision(kanban_home):
    with kbc.connect() as conn:
        tid = _card(conn)
        _escalate(conn, tid)
        assert kb.unblock_task(conn, tid) is True
        assert _t(conn, tid).status == "ready"
        assert kb.task_hold_reason(conn, tid) is None


# --- Atomic relay + unblock -----------------------------------------------------------


def test_unblock_with_comment_writes_both_in_order(kanban_home):
    with kbc.connect() as conn:
        tid = _card(conn)
        assert kb.block_task(conn, tid, reason=GO1, kind="needs_input")
        assert kb.unblock_task(conn, tid, comment="  Operator GO-1 received: approved.  ",
                               author="default-butler") is True
        comments = kb.list_comments(conn, tid)
        assert [(c.author, c.body) for c in comments] == [("default-butler", "Operator GO-1 received: approved.")]
        kinds = [e.kind for e in kb.list_events(conn, tid)]
        assert kinds.index("commented") < kinds.index("unblocked")
        assert _t(conn, tid).status == "ready"


def test_refused_unblock_writes_no_comment(kanban_home):
    with kbc.connect() as conn:
        tid = _card(conn)  # ready, not blocked -> unblock is refused
        assert kb.unblock_task(conn, tid, comment="relay", author="x") is False
        assert kb.list_comments(conn, tid) == []
        plain = kb.create_task(conn, title="idea", assignee="default", triage=True)
        assert kb.unblock_task(conn, plain, comment="relay", author="x") is False
        assert kb.list_comments(conn, plain) == []


def test_unblock_comment_requires_author(kanban_home):
    with kbc.connect() as conn:
        tid = _card(conn)
        assert kb.block_task(conn, tid, reason=GO1, kind="needs_input")
        with pytest.raises(ValueError):
            kb.unblock_task(conn, tid, comment="relay", author=None)
        assert _t(conn, tid).status == "blocked"
        # blank comment == no comment: plain unblock
        assert kb.unblock_task(conn, tid, comment="   ") is True
        assert kb.list_comments(conn, tid) == []


def test_cli_unblock_reason_is_atomic(kanban_home):
    with kbc.connect() as conn:
        blocked = _card(conn, "blocked one")
        assert kb.block_task(conn, blocked, reason=GO1, kind="needs_input")
        not_blocked = _card(conn, "ready one")
    rc = kanban_cli._cmd_unblock(argparse.Namespace(task_ids=[blocked, not_blocked], reason="proof relayed"))
    assert rc != 0  # one of the two was refused
    with kbc.connect() as conn:
        assert _t(conn, blocked).status == "ready"
        assert [c.body for c in kb.list_comments(conn, blocked)] == ["UNBLOCK: proof relayed"]
        # The refused card got NO orphan "UNBLOCK:" comment (pre-hotfix it did).
        assert kb.list_comments(conn, not_blocked) == []


def test_tool_unblock_comment_param(kanban_home, monkeypatch):
    monkeypatch.setenv("HERMES_PROFILE", "orchestrator")
    from tools import kanban_tools as kt
    from tools.kanban_tools_schemas import KANBAN_UNBLOCK_SCHEMA

    schema = KANBAN_UNBLOCK_SCHEMA.get("parameters") or KANBAN_UNBLOCK_SCHEMA.get("function", {}).get("parameters")
    assert "comment" in schema["properties"]
    assert "comment" not in schema.get("required", [])
    desc = KANBAN_UNBLOCK_SCHEMA.get("description") or KANBAN_UNBLOCK_SCHEMA.get("function", {}).get("description")
    assert "never post the relay and the unblock as separate calls" in desc

    with kbc.connect() as conn:
        tid = _card(conn)
        assert kb.block_task(conn, tid, reason=GO1, kind="needs_input")
    out = json.loads(kt._handle_unblock({"task_id": tid, "comment": "GO-1 relayed from butler"}))
    assert out["ok"] is True and out["commented"] is True and out["status"] == "ready"
    with kbc.connect() as conn:
        comments = kb.list_comments(conn, tid)
        assert [c.body for c in comments] == ["GO-1 relayed from butler"]
        assert comments[0].author == "orchestrator"  # runtime identity, never caller args

    # Refused unblock via the tool: error, and no comment left behind.
    out = json.loads(kt._handle_unblock({"task_id": tid, "comment": "second relay"}))
    assert out.get("ok") is not True
    with kbc.connect() as conn:
        assert len(kb.list_comments(conn, tid)) == 1
