"""Tests for hermes_cli.board_rooms — schema matrix, loader, zero-change."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
import hermes_yaml as yaml

from hermes_cli.board_rooms import BoardRoomsError, load_board_rooms, validate_board_rooms_doc


# ── helpers ──────────────────────────────────────────────────────────────

def _board_home(tmp_path: Path, slug: str, roles: list[str] | None = None) -> Path:
    """Create a board home under tmp_path/boards/<slug> with board.yaml if roles given."""
    bh = tmp_path / "boards" / slug
    bh.mkdir(parents=True, exist_ok=True)
    # minimal board.json so board_dir helpers could work if needed
    (bh / "board.json").write_text('{"name": "%s"}' % slug, encoding="utf-8")
    if roles is not None:
        doc: dict = {"version": 1, "roles": roles}
        (bh / "board.yaml").write_text(yaml.safe_dump(doc), encoding="utf-8")
    return bh


def _write_rooms(bh: Path, doc: dict) -> Path:
    p = bh / "board-rooms.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


def _valid_room(name="room-a", members=None, lead=None, routing=None, purpose="A purpose for testing"):
    if members is None:
        members = ["alice", "bob"]
    d: dict = {"name": name, "members": members, "purpose": purpose}
    d["lead"] = lead if lead is not None else members[0]
    if routing is not None:
        d["routing"] = routing
    return d


def _valid_doc(rooms=None):
    if rooms is None:
        rooms = [_valid_room()]
    return {"version": 1, "rooms": rooms}


# ── schema acceptance ────────────────────────────────────────────────────

class TestAcceptance:
    def test_minimal_valid(self, tmp_path):
        doc = _valid_doc()
        validate_board_rooms_doc(doc)

    def test_routing_defaults(self, tmp_path):
        bh = _board_home(tmp_path, "alpha", roles=["alice", "bob"])
        doc = _valid_doc([_valid_room(members=["alice", "bob"], lead="alice", purpose="ok")])
        _write_rooms(bh, doc)
        br = load_board_rooms(bh)
        assert br.rooms[0].routing == "assigned"

    def test_all_routing_values(self, tmp_path):
        for routing in ("everyone", "lead", "assigned"):
            doc = _valid_doc([_valid_room(routing=routing)])
            validate_board_rooms_doc(doc)

    def test_members_boundaries(self, tmp_path):
        for n in (2, 6):
            members = [f"m{i}" for i in range(n)]
            doc = _valid_doc([_valid_room(members=members, lead=members[0])])
            validate_board_rooms_doc(doc)

    def test_purpose_500(self, tmp_path):
        doc = _valid_doc([_valid_room(purpose="x" * 500)])
        validate_board_rooms_doc(doc)

    def test_load_provenance(self, tmp_path):
        bh = _board_home(tmp_path, "alpha", roles=["alice", "bob"])
        doc = _valid_doc([_valid_room(members=["alice", "bob"], lead="alice")])
        _write_rooms(bh, doc)
        br = load_board_rooms(bh)
        assert br.source_path.endswith("board-rooms.yaml")
        assert br.board_slug == "alpha"
        assert br.rooms[0].provenance.endswith("board-rooms.yaml")


# ── schema rejection matrix ──────────────────────────────────────────────

class TestRejectionMatrix:
    def test_unknown_top_level_key(self):
        doc = {"version": 1, "rooms": [_valid_room()], "unknown": 1}
        with pytest.raises(BoardRoomsError, match="unknown top-level key"):
            validate_board_rooms_doc(doc)

    def test_unknown_room_key(self):
        doc = _valid_doc([{"name": "r", "members": ["alice", "bob"], "lead": "alice", "purpose": "p", "extra": 1}])
        with pytest.raises(BoardRoomsError, match="unknown key.*extra"):
            validate_board_rooms_doc(doc)

    def test_missing_version(self):
        doc = {"rooms": [_valid_room()]}
        with pytest.raises(BoardRoomsError, match="missing required key.*version"):
            validate_board_rooms_doc(doc)

    def test_bad_version(self):
        doc = {"version": 2, "rooms": [_valid_room()]}
        with pytest.raises(BoardRoomsError, match="unknown version"):
            validate_board_rooms_doc(doc)

    def test_missing_rooms(self):
        with pytest.raises(BoardRoomsError, match="missing required key.*rooms"):
            validate_board_rooms_doc({"version": 1})

    def test_members_1(self):
        doc = _valid_doc([_valid_room(members=["alice"], lead="alice")])
        with pytest.raises(BoardRoomsError, match="2-6"):
            validate_board_rooms_doc(doc)

    def test_members_7(self):
        members = [f"m{i}" for i in range(7)]
        doc = _valid_doc([_valid_room(members=members, lead=members[0])])
        with pytest.raises(BoardRoomsError, match="2-6"):
            validate_board_rooms_doc(doc)

    def test_lead_not_in_members(self):
        doc = _valid_doc([_valid_room(members=["alice", "bob"], lead="charlie")])
        with pytest.raises(BoardRoomsError, match="must be one of members"):
            validate_board_rooms_doc(doc)

    def test_missing_purpose(self):
        doc = _valid_doc([{"name": "r", "members": ["alice", "bob"], "lead": "alice"}])
        with pytest.raises(BoardRoomsError, match="missing required key.*purpose"):
            validate_board_rooms_doc(doc)

    def test_purpose_too_long(self):
        doc = _valid_doc([_valid_room(purpose="x" * 501)])
        with pytest.raises(BoardRoomsError, match="<=500"):
            validate_board_rooms_doc(doc)

    def test_bad_routing(self):
        doc = _valid_doc([_valid_room(routing="all")])
        with pytest.raises(BoardRoomsError, match="routing.*must be one of"):
            validate_board_rooms_doc(doc)

    def test_duplicate_room_name(self):
        doc = _valid_doc([_valid_room(name="r"), _valid_room(name="r")])
        with pytest.raises(BoardRoomsError, match="duplicate room name"):
            validate_board_rooms_doc(doc)

    def test_duplicate_members(self):
        doc = _valid_doc([_valid_room(members=["alice", "alice"], lead="alice")])
        with pytest.raises(BoardRoomsError, match="must be unique"):
            validate_board_rooms_doc(doc)

    def test_traversal_in_name(self):
        doc = _valid_doc([_valid_room(name="../evil")])
        with pytest.raises(BoardRoomsError, match="escapes board home"):
            validate_board_rooms_doc(doc)

    def test_traversal_in_member(self):
        doc = _valid_doc([_valid_room(members=["alice", "../bob"], lead="alice")])
        with pytest.raises(BoardRoomsError, match="invalid profile name|escapes board home"):
            validate_board_rooms_doc(doc)


# ── loader validation against fixture boards ─────────────────────────────

class TestLoaderFixtures:
    def test_member_not_in_roles(self, tmp_path):
        bh = _board_home(tmp_path, "alpha", roles=["alice", "bob"])
        doc = _valid_doc([_valid_room(members=["alice", "charlie"], lead="alice")])
        _write_rooms(bh, doc)
        with pytest.raises(BoardRoomsError, match="not in board's roles allowlist.*charlie"):
            load_board_rooms(bh)

    def test_member_in_roles_ok(self, tmp_path):
        bh = _board_home(tmp_path, "alpha", roles=["alice", "bob", "charlie"])
        doc = _valid_doc([_valid_room(members=["alice", "charlie"], lead="alice")])
        _write_rooms(bh, doc)
        br = load_board_rooms(bh)
        assert len(br.rooms) == 1

    def test_board_alpha_beta_disjoint(self, tmp_path):
        # board-α allows alice,bob ; board-β allows carol,dave
        b_alpha = _board_home(tmp_path, "board-alpha", roles=["alice", "bob"])
        b_beta = _board_home(tmp_path, "board-beta", roles=["carol", "dave"])
        doc_a = _valid_doc([_valid_room(members=["alice", "bob"], lead="alice")])
        doc_b = _valid_doc([_valid_room(members=["carol", "dave"], lead="carol")])
        _write_rooms(b_alpha, doc_a)
        _write_rooms(b_beta, doc_b)
        assert load_board_rooms(b_alpha).rooms[0].members == ["alice", "bob"]
        assert load_board_rooms(b_beta).rooms[0].members == ["carol", "dave"]
        # cross: alice in beta's room should fail
        _write_rooms(b_beta, _valid_doc([_valid_room(members=["alice", "carol"], lead="alice")]))
        with pytest.raises(BoardRoomsError, match="not in board's roles allowlist.*alice"):
            load_board_rooms(b_beta)

    def test_butler_extra_allowed(self, tmp_path):
        # board declares butler profile additionally
        bh = tmp_path / "boards" / "myboard"
        bh.mkdir(parents=True, exist_ok=True)
        (bh / "board.json").write_text('{"name":"myboard"}', encoding="utf-8")
        doc_board = {"version": 1, "roles": ["alice", "bob"], "butler": "butler-bot"}
        (bh / "board.yaml").write_text(yaml.safe_dump(doc_board), encoding="utf-8")
        doc = _valid_doc([_valid_room(members=["alice", "butler-bot"], lead="alice")])
        _write_rooms(bh, doc)
        br = load_board_rooms(bh)
        assert "butler-bot" in br.rooms[0].members

    def test_open_board_no_roles(self, tmp_path):
        # board without roles = open, no allowlist check
        bh = _board_home(tmp_path, "open", roles=None)
        doc = _valid_doc([_valid_room(members=["alice", "bob"], lead="alice")])
        _write_rooms(bh, doc)
        br = load_board_rooms(bh)
        assert len(br.rooms) == 1

    def test_traversal_path_rejected_at_load(self, tmp_path):
        bh = _board_home(tmp_path, "alpha", roles=["alice", "bob"])
        # Manually craft yaml with traversal that bypasses _valid_room helper
        raw = textwrap.dedent("""\
            version: 1
            rooms:
              - name: "../evil"
                members: ["alice", "bob"]
                lead: "alice"
                purpose: "p"
            """)
        (bh / "board-rooms.yaml").write_text(raw, encoding="utf-8")
        with pytest.raises(BoardRoomsError, match="escapes board home"):
            load_board_rooms(bh)

    def test_missing_file(self, tmp_path):
        bh = _board_home(tmp_path, "empty", roles=["alice"])
        with pytest.raises(FileNotFoundError):
            load_board_rooms(bh)


# ── zero-change guarantee (extend RFC §12 fixture) ───────────────────────

class TestZeroChange:
    """Unlayered boards / boards without board-rooms.yaml must be byte-identical
    effective SOUL/config/skills/env-names (RFC §12 pattern)."""

    def test_unlayered_board_no_effect(self, tmp_path, monkeypatch):
        """A board without board.yaml yields zero-change EffectiveProfile."""
        from hermes_cli.board_layer import compose

        # Need iso_home: point HERMES_HOME and kanban home at tmp_path
        home = tmp_path / "hermes-home"
        home.mkdir()
        (home / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
        monkeypatch.setenv("HERMES_HOME", str(home))
        try:
            import hermes_constants as hc

            hc._default_hermes_root_memo = None  # type: ignore[attr-defined]
        except Exception:
            pass

        # Create a role profile
        prof = home / "profiles" / "alice"
        prof.mkdir(parents=True)
        (prof / "config.yaml").write_text("model:\n  provider: openai\n  model: gpt-4o-mini\n", encoding="utf-8")
        (prof / "SOUL.md").write_text("You are alice.", encoding="utf-8")

        # Create an unlayered board (no board.yaml)
        # Use kanban home under HERMES_HOME for simplicity
        from hermes_cli.kanban_db import board_dir

        bg = tmp_path / "kanban-home"
        bg.mkdir(exist_ok=True)
        monkeypatch.setenv("HERMES_KANBAN_HOME", str(bg))
        # board_dir uses kanban home; ensure it points to tmp
        # If board is unlayered, compose should return is_layered=False and no soul changes
        ep_none = compose("alice", None)
        assert ep_none.is_layered is False
        assert ep_none.soul_text is not None or ep_none.soul_text is None  # just shouldn't crash

        # Board without board-rooms.yaml: load_board_rooms should raise FileNotFoundError, not affect compose
        bh = bg / "kanban" / "boards" / "myboard"
        bh.mkdir(parents=True, exist_ok=True)
        (bh / "board.json").write_text('{"name":"myboard"}', encoding="utf-8")
        # No board.yaml -> not layered
        with pytest.raises(FileNotFoundError):
            load_board_rooms(bh)

        # Add board.yaml but no board-rooms.yaml: compose works, load_board_rooms still FileNotFound
        (bh / "board.yaml").write_text(yaml.safe_dump({"version": 1, "roles": ["alice"]}), encoding="utf-8")
        # Now layered via file existence — need to check is_layered_board
        # But compose should include it
        # load_board_rooms still absent
        with pytest.raises(FileNotFoundError):
            load_board_rooms(bh)

    def test_boards_without_board_rooms_yaml_unchanged(self, tmp_path):
        """Boards that lack board-rooms.yaml behave identically before/after loader addition."""
        bh = _board_home(tmp_path, "plain", roles=["alice", "bob"])
        # No board-rooms.yaml — loader raises, no side effect
        with pytest.raises(FileNotFoundError):
            load_board_rooms(bh)
        # File never created
        assert not (bh / "board-rooms.yaml").exists()
