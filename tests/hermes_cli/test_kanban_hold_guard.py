"""Operator-hold suppression in the triage automation (LOCAL HOTFIX t_7fd1c800).

Incident (gaudi t_9375396a, 2026-10-29): the block-loop breaker escalated an
operator-hold block into TRIAGE — the column the auto-decomposer and triage
specifier feed on — and the decomposer spec'd+promoted the held card out from
under the operator 3 times in ~50 minutes. These tests pin the guard: a card
whose CURRENT block episode is an operator hold can never be mutated or
promoted by specify/decompose, is excluded from both triage sweeps, and is
releasable only by an explicit unblock (which clears the hold).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from hermes_cli import kanban_db as kb
from hermes_cli import kanban_db_connect as kbc
from hermes_cli import kanban_specify, kanban_decompose
from hermes_cli.kanban_db_graph import decompose_triage_task


@pytest.fixture
def kanban_home(tmp_path, monkeypatch):
    """Isolated HERMES_HOME with an empty kanban DB and no stray env markers."""
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.delenv("HERMES_KANBAN_HOLD_MARKERS", raising=False)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    kb.init_db()
    return home


HOLD_REASON = (
    "OPERATOR HOLD 2026-10-29 (operator verbatim, relayed via gaudi-butler): "
    "Cancel the SWE re run entirely for now, I will reschedule later."
)
PLAIN_REASON = "Lane contention: muse BENCH.lock held by another card."


def _t(conn, tid):
    task = kb.get_task(conn, tid)
    assert task is not None
    return task


def _ready_card(conn, title="held work"):
    return kb.create_task(conn, title=title, body="do the thing", assignee="default")


def _hold_into_triage(conn, tid, reason=HOLD_REASON, kind="needs_input"):
    """block -> unblock -> re-block: recurrences 2 >= BLOCK_RECURRENCE_LIMIT
    routes the card to triage (the exact incident shape)."""
    assert kb.block_task(conn, tid, reason=reason, kind=kind) is True
    assert kb.unblock_task(conn, tid) is True
    assert kb.block_task(conn, tid, reason=reason, kind=kind) is True
    assert _t(conn, tid).status == "triage"


def _plain_triage(conn, title="rough idea"):
    return kb.create_task(conn, title=title, assignee="default", triage=True)


# --- Detection ---------------------------------------------------------------


def test_block_loop_hold_is_detected_in_triage(kanban_home):
    with kbc.connect() as conn:
        tid = _ready_card(conn)
        _hold_into_triage(conn, tid)
        assert "OPERATOR HOLD" in (kb.task_hold_reason(conn, tid) or "")


def test_no_block_history_means_not_held(kanban_home):
    with kbc.connect() as conn:
        tid = _plain_triage(conn)
        assert kb.task_hold_reason(conn, tid) is None


def test_non_hold_block_episode_is_not_held(kanban_home):
    with kbc.connect() as conn:
        tid = _ready_card(conn)
        # A hold block, released, then a NEW non-hold block episode: the newest
        # episode wins — this is not a hold. (block_kind/recurrences survive the
        # unblock by design, so this second block already escalates to triage.)
        assert kb.block_task(conn, tid, reason=HOLD_REASON, kind="needs_input")
        assert kb.unblock_task(conn, tid)
        assert kb.block_task(conn, tid, reason=PLAIN_REASON, kind="needs_input")
        assert _t(conn, tid).status == "triage"
        assert kb.task_hold_reason(conn, tid) is None


# --- Kernel guards -----------------------------------------------------------


def test_specify_triage_task_refuses_held_card(kanban_home):
    with kbc.connect() as conn:
        tid = _ready_card(conn)
        _hold_into_triage(conn, tid)
        before = _t(conn, tid)
        with pytest.raises(kb.TaskHeldError):
            kb.specify_triage_task(conn, tid, title="Mutated!", body="nope", author="auto-decomposer")
        after = _t(conn, tid)
        # Nothing mutated, nothing promoted.
        assert after.status == "triage"
        assert after.title == before.title
        assert after.body == before.body


def test_decompose_fanout_refuses_held_card(kanban_home):
    with kbc.connect() as conn:
        tid = _ready_card(conn)
        _hold_into_triage(conn, tid)
        with pytest.raises(kb.TaskHeldError):
            decompose_triage_task(
                conn, tid, root_assignee="default",
                children=[{"title": "frag A", "body": "b", "assignee": "default", "parents": []}],
            )
        assert _t(conn, tid).status == "triage"
        # No fragment children were created.
        kids = conn.execute(
            "SELECT COUNT(*) AS n FROM tasks WHERE id != ?", (tid,)
        ).fetchone()["n"]
        assert kids == 0


def test_plain_triage_still_specifies_and_decomposes(kanban_home):
    """The guard must not break the normal rough-idea pipeline."""
    with kbc.connect() as conn:
        tid = _plain_triage(conn)
        assert kb.specify_triage_task(conn, tid, title="A-spec", body="b", author="ace")
        assert _t(conn, tid).status in ("todo", "ready")

        tid2 = _plain_triage(conn, title="another idea")
        child_ids = decompose_triage_task(
            conn, tid2, root_assignee="default",
            children=[{"title": "frag", "body": "b", "assignee": "default", "parents": []}],
        )
        assert child_ids
        assert _t(conn, tid2).status in ("todo", "ready")


# --- Sweeps and module entry points ------------------------------------------


def test_both_triage_sweeps_skip_held_cards(kanban_home):
    with kbc.connect() as conn:
        held = _ready_card(conn)
        _hold_into_triage(conn, held)
        plain = _plain_triage(conn)
    assert kanban_decompose.list_triage_ids() == [plain]
    assert kanban_specify.list_triage_ids() == [plain]


def test_decompose_task_module_refuses_before_aux_call(kanban_home, monkeypatch):
    with kbc.connect() as conn:
        tid = _ready_card(conn)
        _hold_into_triage(conn, tid)

    def _no_aux(*args, **kwargs):
        raise AssertionError("aux LLM must not be called for a held card")

    monkeypatch.setattr(kanban_decompose, "_call_aux", _no_aux)
    outcome = kanban_decompose.decompose_task(tid, author="auto-decomposer")
    assert outcome.ok is False
    assert "operator hold" in outcome.reason.lower()


def test_specify_task_module_refuses_before_aux_call(kanban_home, monkeypatch):
    with kbc.connect() as conn:
        tid = _ready_card(conn)
        _hold_into_triage(conn, tid)

    def _no_aux(*args, **kwargs):
        raise AssertionError("aux LLM must not be called for a held card")

    monkeypatch.setattr(kanban_specify, "_call_aux", _no_aux)
    outcome = kanban_specify.specify_task(tid, author="auto-decomposer")
    assert outcome.ok is False
    assert "operator hold" in outcome.reason.lower()


# --- Release path -------------------------------------------------------------


def test_unblock_releases_held_triage_card_and_clears_hold(kanban_home):
    with kbc.connect() as conn:
        tid = _ready_card(conn)
        _hold_into_triage(conn, tid)
        assert kb.unblock_task(conn, tid) is True
        assert _t(conn, tid).status == "ready"
        assert kb.task_hold_reason(conn, tid) is None


def test_unblock_still_refuses_plain_triage(kanban_home):
    with kbc.connect() as conn:
        tid = _plain_triage(conn)
        assert kb.unblock_task(conn, tid) is False
        assert _t(conn, tid).status == "triage"


def test_custom_marker_config_is_honored(kanban_home, monkeypatch):
    monkeypatch.setenv("HERMES_KANBAN_HOLD_MARKERS", "FREEZE-IT")
    with kbc.connect() as conn:
        tid = _ready_card(conn)
        _hold_into_triage(conn, tid, reason="FREEZE-IT: operator wants this parked")
        assert "FREEZE-IT" in (kb.task_hold_reason(conn, tid) or "")
    # And the default marker no longer matches under this override.
    with kbc.connect() as conn:
        tid2 = _ready_card(conn, title="other work")
        _hold_into_triage(conn, tid2, reason="OPERATOR HOLD: parked")
        assert kb.task_hold_reason(conn, tid2) is None
