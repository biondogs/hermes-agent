"""BRP-v2 F2 schema-shape test: model-facing definition carries description + parameters."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest
import hermes_yaml as yaml

FROZEN_DESC = (
    "Send a message to a teammate on this board (board-fenced). Use it to ask a teammate "
    "a question you cannot answer from the card \u2014 a spec detail, a constraint, a blocker "
    "\u2014 instead of guessing or blocking on the operator."
)


def _load_plugin():
    p = Path(__file__).resolve().parent.parent / "plugins" / "board-rooms" / "__init__.py"
    spec = importlib.util.spec_from_file_location("board_rooms_plugin_schema", str(p))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _board_home(tmp_path: Path, slug: str, roles: list[str]) -> Path:
    bh = tmp_path / "boards" / slug
    bh.mkdir(parents=True, exist_ok=True)
    (bh / "board.json").write_text(json.dumps({"name": slug}), encoding="utf-8")
    (bh / "board.yaml").write_text(yaml.safe_dump({"version": 1, "roles": roles}), encoding="utf-8")
    return bh


def _make_profiles(tmp_path: Path, names: list[str]):
    pr = tmp_path / "profiles"
    pr.mkdir(parents=True, exist_ok=True)
    for n in names:
        pd = pr / n
        pd.mkdir(parents=True, exist_ok=True)
        (pd / "config.yaml").write_text("model: test\n", encoding="utf-8")
    return pr


@pytest.fixture
def schema_env(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    bh = _board_home(tmp_path, "board-alpha", ["sw-dev-a", "sw-dev-b"])
    _make_profiles(tmp_path, ["sw-dev-a", "sw-dev-b"])
    kb = tmp_path / "kanban" / "boards" / "board-alpha"
    kb.mkdir(parents=True, exist_ok=True)
    (kb / "board.json").write_text(json.dumps({"name": "board-alpha"}), encoding="utf-8")
    (kb / "board.yaml").write_text((tmp_path / "boards" / "board-alpha" / "board.yaml").read_text(encoding="utf-8"))
    monkeypatch.setenv("HERMES_KANBAN_BOARD", "board-alpha")
    monkeypatch.setenv("HERMES_PROFILE", "sw-dev-a")
    br = _load_plugin()
    from tools.registry import registry

    prev = registry.get_entry("message_peer")
    registry.register(
        name=br.TOOL_NAME,
        toolset=br.TOOLSET,
        schema=br.MESSAGE_PEER_SCHEMA,
        handler=br._handler,
        check_fn=br._check_fn,
        description=br.MESSAGE_PEER_DESCRIPTION,
    )
    # also ensure tool is discoverable via enabled_toolsets — need check_fn to pass
    yield br
    try:
        registry.deregister("message_peer")
        if prev:
            registry.register(
                name=prev.name,
                toolset=prev.toolset,
                schema=prev.schema,
                handler=prev.handler,
                check_fn=prev.check_fn,
                description=prev.description,
            )
    except Exception:
        pass


class TestSchemaShape:
    def test_frozen_description_byte_exact_in_plugin(self, schema_env):
        br = schema_env
        # constant holds frozen string
        assert br.MESSAGE_PEER_DESCRIPTION == FROZEN_DESC
        # schema description matches
        assert br.MESSAGE_PEER_SCHEMA["description"] == FROZEN_DESC
        assert br.MESSAGE_PEER_SCHEMA["description"].encode("utf-8") == FROZEN_DESC.encode("utf-8")
        # schema shape is OpenAI-function shape
        assert br.MESSAGE_PEER_SCHEMA["name"] == "message_peer"
        assert "parameters" in br.MESSAGE_PEER_SCHEMA
        params = br.MESSAGE_PEER_SCHEMA["parameters"]
        assert params["type"] == "object"
        assert set(params["properties"].keys()) == {"target", "message", "expects_reply"}
        assert params["required"] == ["target", "message"]
        # top-level must NOT have bare type/properties
        # the new shape's top-level keys are exactly name, description, parameters
        assert set(br.MESSAGE_PEER_SCHEMA.keys()) == {"name", "description", "parameters"}
        # no stray top-level type/properties (bare shape leakage)
        assert "type" not in br.MESSAGE_PEER_SCHEMA or br.MESSAGE_PEER_SCHEMA.get("type") != "object" or "parameters" in br.MESSAGE_PEER_SCHEMA

    def test_model_facing_via_registry_get_definitions(self, schema_env):
        from tools.registry import registry

        defs = registry.get_definitions({"message_peer"})
        assert len(defs) == 1
        fn = defs[0]["function"]
        # description is frozen
        assert fn["description"] == FROZEN_DESC
        # parameters present and correct
        assert "parameters" in fn
        params = fn["parameters"]
        assert params["type"] == "object"
        assert set(params["properties"].keys()) == {"target", "message", "expects_reply"}
        assert params["required"] == ["target", "message"]
        # no stray top-level type/properties inside function besides name/description/parameters
        assert "type" not in fn, "stray 'type' key inside function (bare shape leaked)"
        assert "properties" not in fn, "stray 'properties' key inside function (bare shape leaked)"
        assert "required" not in fn or fn.get("required") is None or isinstance(fn.get("parameters"), dict)
        # name present
        assert fn["name"] == "message_peer"

    def test_model_facing_via_model_tools_get_tool_definitions(self, schema_env):
        import model_tools

        defs = model_tools.get_tool_definitions(enabled_toolsets=["board_rooms"])
        # filter to message_peer
        mp = [d for d in defs if d.get("function", {}).get("name") == "message_peer"]
        assert len(mp) == 1, f"message_peer not in model_tools definitions; got {[d['function']['name'] for d in defs]}"
        fn = mp[0]["function"]
        assert fn["description"] == FROZEN_DESC
        params = fn["parameters"]
        assert set(params["properties"].keys()) == {"target", "message", "expects_reply"}
        assert params["required"] == ["target", "message"]
        assert "type" not in fn
        assert "properties" not in fn

    def test_no_stray_top_level_keys(self, schema_env):
        from tools.registry import registry

        defs = registry.get_definitions({"message_peer"})
        fn = defs[0]["function"]
        allowed = {"name", "description", "parameters"}
        # function dict should not have bare schema keys at top level
        stray = set(fn.keys()) - allowed
        # additionalProperties might be present? In old bare schema it was False.
        # In new shape, additionalProperties should be inside parameters, not top-level.
        assert "additionalProperties" not in fn, "stray additionalProperties at function top-level"
        assert "type" not in stray
        assert "properties" not in stray

    def test_constant_reused_for_register(self, schema_env):
        br = schema_env
        from tools.registry import registry

        entry = registry.get_entry("message_peer")
        assert entry is not None
        # ToolEntry.description comes from register_tool(description=...)
        assert entry.description == FROZEN_DESC
        # and schema description matches
        assert entry.schema["description"] == FROZEN_DESC
        # they are the same object/value (single constant)
        assert entry.schema["description"] == entry.description
