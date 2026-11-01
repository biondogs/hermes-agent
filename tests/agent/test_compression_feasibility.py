"""Tests for _check_compression_model_feasibility() — warns when the
auxiliary compression model's context is smaller than the main model's
compression threshold.

Two-phase design:
  1. __init__  → runs the check, prints via _vprint (CLI), stores warning
  2. run_conversation (first call) → replays stored warning through
     status_callback (gateway platforms)
"""

from unittest.mock import MagicMock, patch

import pytest

from run_agent import AIAgent
from agent.context_compressor import ContextCompressor


@pytest.fixture(autouse=True)
def _stable_aux_provider_config():
    """Keep feasibility tests independent from the developer's config.yaml."""
    with patch(
        "agent.auxiliary_client._resolve_task_provider_model",
        return_value=("auto", None, None, None, None),
    ):
        yield


def _make_agent(
    *,
    compression_enabled: bool = True,
    threshold_percent: float = 0.50,
    main_context: int = 200_000,
) -> AIAgent:
    """Build a minimal AIAgent with a compressor, skipping __init__."""
    agent = AIAgent.__new__(AIAgent)
    agent.model = "test-main-model"
    agent.provider = "openrouter"
    agent.base_url = "https://openrouter.ai/api/v1"
    agent.api_key = "sk-test"
    agent.api_mode = "chat_completions"
    agent.quiet_mode = True
    agent.log_prefix = ""
    agent.compression_enabled = compression_enabled
    agent._print_fn = None
    agent.suppress_status_output = False
    agent._stream_consumers = []
    agent._executing_tools = False
    agent._mute_post_response = False
    agent.status_callback = None
    agent.tool_progress_callback = None
    agent._compression_warning = None
    agent._aux_compression_context_length_config = None
    agent._custom_providers = []
    agent.tools = []

    compressor = MagicMock(spec=ContextCompressor)
    compressor.context_length = main_context
    compressor.threshold_tokens = int(main_context * threshold_percent)
    compressor.summary_target_ratio = 0.20
    compressor.tail_token_budget = int(
        compressor.threshold_tokens * compressor.summary_target_ratio
    )
    agent.context_compressor = compressor

    return agent


@pytest.mark.parametrize("main_context,aux_context", [(1_000_000, 512_000), (400_000, 80_000)])
def test_aux_sync_keeps_lean_tail_policy(main_context, aux_context):
    """Feasibility probe must not lower trigger: summariser input is bounded independent of main threshold."""
    agent = _make_agent(main_context=main_context)
    compressor = agent.context_compressor = ContextCompressor(
        "test-main-model", config_context_length=main_context,
        threshold_percent=0.85, quiet_mode=True,
    )
    before_threshold = compressor.threshold_tokens
    before = compressor.tail_token_budget
    agent._emit_status = lambda message: None
    client = MagicMock(base_url="http://localhost/v1", api_key="test-key")
    with patch("agent.auxiliary_client.get_text_auxiliary_client", return_value=(client, "aux")), \
         patch("agent.model_metadata.get_model_context_length", return_value=aux_context):
        agent._check_compression_model_feasibility()
        assert compressor.threshold_tokens == before_threshold
        assert compressor._aux_context_ceiling is None
        assert compressor.tail_token_budget == before
        # Repeated feasibility and subsequent model recalibration retain policy.
        agent._check_compression_model_feasibility()
        assert compressor.threshold_tokens == before_threshold
        assert compressor.tail_token_budget == before
        compressor.update_model("test-main-model", context_length=main_context)
        assert compressor.threshold_tokens == before_threshold
        assert compressor.tail_token_budget == before


def test_aux_sync_legacy_tail_follows_lowered_threshold():
    """Legacy tail mode also no longer has its trigger lowered by the probe — input is bounded in all modes."""
    agent = _make_agent(main_context=1_000_000)
    compressor = agent.context_compressor = ContextCompressor(
        "test-main-model", config_context_length=1_000_000,
        threshold_percent=0.85, tail_mode="legacy", quiet_mode=True,
    )
    before_threshold = compressor.threshold_tokens
    before = compressor.tail_token_budget
    agent._emit_status = lambda message: None
    client = MagicMock(base_url="http://localhost/v1", api_key="test-key")
    with patch("agent.auxiliary_client.get_text_auxiliary_client", return_value=(client, "aux")), \
         patch("agent.model_metadata.get_model_context_length", return_value=512_000):
        agent._check_compression_model_feasibility()
    assert compressor.threshold_tokens == before_threshold
    assert compressor.tail_token_budget == before


def test_fallback_activation_on_never_probed_session_stays_lazy():
    """A session that never ran the feasibility probe does not resolve an auxiliary client while a
    fallback is being activated; the compaction-time probe still owns the first verdict (#114707)."""
    from agent.chat_completion_helpers import _update_fallback_context_compressor

    agent = _make_agent(main_context=200_000)
    agent.context_compressor = ContextCompressor(
        "test-main-model", config_context_length=200_000, threshold_percent=0.50, quiet_mode=True,
    )
    agent._config_context_length = None
    agent.model = "fallback-model"
    with patch("agent.auxiliary_client.get_text_auxiliary_client") as aux_client, \
         patch("agent.model_metadata.get_model_context_length", return_value=1_000_000):
        _update_fallback_context_compressor(agent)
    aux_client.assert_not_called()
    assert getattr(agent, "_compression_feasibility_checked", False) is False


def test_fallback_activation_reprobes_aux_ceiling_and_keeps_it_durable():
    """Re-probe on fallback no longer installs a ceiling: input is bounded independent of threshold (#126767)."""
    from agent.chat_completion_helpers import _update_fallback_context_compressor

    agent = _make_agent(main_context=200_000)
    compressor = agent.context_compressor = ContextCompressor(
        "test-main-model", config_context_length=200_000, threshold_percent=0.50, quiet_mode=True,
    )
    notices = 0

    def _count(_message):
        nonlocal notices
        notices += 1

    agent._emit_status = _count
    agent._config_context_length = None
    agent._compression_feasibility_checked = True  # probed on the primary; aux fit there
    agent.model = "fallback-model"
    client = MagicMock(base_url="http://localhost/v1", api_key="test-key")
    with patch("agent.auxiliary_client.get_text_auxiliary_client", return_value=(client, "aux")), \
         patch("agent.model_metadata.get_model_context_length", side_effect=[1_000_000, 80_000]):
        _update_fallback_context_compressor(agent)
    assert compressor.context_length == 1_000_000
    # No longer clamped to aux window: bounded input fits any aux >= MINIMUM_CONTEXT_LENGTH
    assert compressor._aux_context_ceiling is None
    assert compressor.threshold_tokens == 500_000  # 1M * 0.50, no floor since >= 512K
    assert agent._compression_feasibility_checked is True
    # Same-runtime window correction keeps threshold from main window
    compressor.update_model(
        "fallback-model", context_length=800_000, base_url=agent.base_url, api_key=agent.api_key,
        provider=agent.provider, api_mode=agent.api_mode,
    )
    assert compressor.threshold_tokens == 400_000  # 800K * 0.50
    # No clamp installed, so no notice was emitted
    assert notices == 0


def test_unclamp_clears_stale_clamp_warning():
    """Re-probe no longer installs a clamp; stale ceiling from a prior manual clamp is not reinstalled."""
    from agent.chat_completion_helpers import _update_fallback_context_compressor

    agent = _make_agent(main_context=200_000)
    compressor = agent.context_compressor = ContextCompressor(
        "test-main-model", config_context_length=200_000, threshold_percent=0.50, quiet_mode=True,
    )
    agent._emit_status = lambda message: None
    agent._config_context_length = None
    agent._compression_feasibility_checked = True
    client = MagicMock(base_url="http://localhost/v1", api_key="test-key")
    for main_ctx, aux_ctx, label in ((1_000_000, 80_000, "big"), (100_000, 80_000, "small")):
        agent.model = label
        with patch("agent.auxiliary_client.get_text_auxiliary_client", return_value=(client, "aux")), \
             patch("agent.model_metadata.get_model_context_length", side_effect=[main_ctx, aux_ctx]):
            _update_fallback_context_compressor(agent)
    assert compressor._aux_context_ceiling is None
    assert agent._compression_warning is None
    assert getattr(agent, "_last_feasibility_notice", None) is None


def test_near_threshold_probe_clamps_before_first_compaction():
    """A fresh instance probes at MINIMUM_CONTEXT_LENGTH to check aux minimum gate;
    below that stays probe-free (#28957). No threshold clamping occurs (bounded input)."""
    from agent.conversation_compression import ensure_compression_feasibility_checked
    from agent.model_metadata import MINIMUM_CONTEXT_LENGTH

    agent = _make_agent(main_context=1_000_000)
    compressor = agent.context_compressor = ContextCompressor(
        "test-main-model", config_context_length=1_000_000, threshold_percent=0.75, quiet_mode=True,
    )
    before = compressor.threshold_tokens
    agent._emit_status = lambda message: None
    agent._compression_feasibility_checked = False
    client = MagicMock(base_url="http://localhost/v1", api_key="test-key")
    with patch("agent.auxiliary_client.get_text_auxiliary_client", return_value=(client, "aux")) as aux_client, \
         patch("agent.model_metadata.get_model_context_length", return_value=80_000):
        ensure_compression_feasibility_checked(agent, MINIMUM_CONTEXT_LENGTH - 1)
        aux_client.assert_not_called()
        assert agent._compression_feasibility_checked is False
        ensure_compression_feasibility_checked(agent, MINIMUM_CONTEXT_LENGTH)
        ensure_compression_feasibility_checked(agent, 200_000)
    assert aux_client.call_count == 1
    assert agent._compression_feasibility_checked is True
    assert compressor.threshold_tokens == before
    assert compressor._aux_context_ceiling is None
    assert compressor.should_compress(200_000) is False  # 200K < threshold (750K)


# ── Core warning logic ──────────────────────────────────────────────


@patch("agent.model_metadata.get_model_context_length", return_value=80_000)
@patch("agent.auxiliary_client.get_text_auxiliary_client")
def test_auto_corrects_threshold_when_aux_context_below_threshold(mock_get_client, mock_ctx_len):
    """Aux above MINIMUM but below old threshold no longer triggers auto-lower: bounded input fits (#126767)."""
    agent = _make_agent(main_context=200_000, threshold_percent=0.50)
    mock_client = MagicMock()
    mock_client.base_url = "https://openrouter.ai/api/v1"
    mock_client.api_key = "sk-aux"
    mock_get_client.return_value = (mock_client, "google/gemini-3-flash-preview")

    before = agent.context_compressor.threshold_tokens
    messages = []
    agent._emit_status = lambda msg: messages.append(msg)

    agent._check_compression_model_feasibility()

    assert len(messages) == 0  # no warning: 80K aux fits bounded prompt
    assert agent._compression_warning is None
    assert agent.context_compressor.threshold_tokens == before


@patch("agent.model_metadata.get_model_context_length", return_value=32_768)
@patch("agent.auxiliary_client.get_text_auxiliary_client")
def test_rejects_aux_below_minimum_context(mock_get_client, mock_ctx_len):
    """Hard floor: aux context < MINIMUM_CONTEXT_LENGTH (64K) → session
    refuses to start (ValueError), mirroring the main-model rejection."""
    agent = _make_agent(main_context=200_000, threshold_percent=0.50)
    mock_client = MagicMock()
    mock_client.base_url = "https://openrouter.ai/api/v1"
    mock_client.api_key = "sk-aux"
    mock_get_client.return_value = (mock_client, "tiny-aux-model")

    agent._emit_status = lambda msg: None

    with pytest.raises(ValueError) as exc_info:
        agent._check_compression_model_feasibility()

    assert "tiny-aux-model" in str(exc_info.value)




def test_feasibility_check_passes_live_main_runtime():
    """Compression feasibility should probe using the live session runtime."""
    agent = _make_agent(main_context=200_000, threshold_percent=0.50)
    agent.model = "gpt-5.4"
    agent.provider = "openai-codex"
    agent.base_url = "https://chatgpt.com/backend-api/codex"
    agent.api_key = "codex-token"
    agent.api_mode = "codex_responses"

    mock_client = MagicMock()
    mock_client.base_url = "https://chatgpt.com/backend-api/codex"
    mock_client.api_key = "codex-token"

    with patch("agent.auxiliary_client.get_text_auxiliary_client", return_value=(mock_client, "gpt-5.4")) as mock_get_client, \
         patch("agent.model_metadata.get_model_context_length", return_value=200_000):
        agent._emit_status = lambda msg: None
        agent._check_compression_model_feasibility()

    mock_get_client.assert_called_once_with(
        "compression",
        main_runtime={
            "model": "gpt-5.4",
            "provider": "openai-codex",
            "base_url": "https://chatgpt.com/backend-api/codex",
            "api_key": "codex-token",
            "api_mode": "codex_responses",
            "auth_mode": "",
            "session_id": "",
        },
    )


@patch("agent.model_metadata.get_model_context_length", return_value=1_000_000)
@patch("agent.auxiliary_client.get_text_auxiliary_client")
def test_feasibility_check_passes_config_context_length(mock_get_client, mock_ctx_len):
    """auxiliary.compression.context_length from config is forwarded to
    get_model_context_length so custom endpoints that lack /models still
    report the correct context window (fixes #8499)."""
    agent = _make_agent(main_context=200_000, threshold_percent=0.85)
    agent._aux_compression_context_length_config = 1_000_000
    mock_client = MagicMock()
    mock_client.base_url = "http://custom-endpoint:8080/v1"
    mock_client.api_key = "sk-custom"
    mock_get_client.return_value = (mock_client, "custom/big-model")

    agent._emit_status = lambda msg: None
    agent._check_compression_model_feasibility()

    mock_ctx_len.assert_called_once_with(
        "custom/big-model",
        base_url="http://custom-endpoint:8080/v1",
        api_key="sk-custom",
        config_context_length=1_000_000,
        provider="openrouter",
        custom_providers=[],
    )






@patch("agent.auxiliary_client.get_text_auxiliary_client")
def test_warns_when_no_auxiliary_provider(mock_get_client):
    """Warning emitted when no auxiliary provider is configured."""
    agent = _make_agent()
    mock_get_client.return_value = (None, None)

    messages = []
    agent._emit_status = lambda msg: messages.append(msg)

    agent._check_compression_model_feasibility()

    assert len(messages) == 1
    assert agent._compression_warning is not None


def test_no_unavailable_warning_when_configured_fallback_chain_resolves():
    """Primary compression provider can be down if configured fallback works."""
    agent = _make_agent(main_context=200_000, threshold_percent=0.50)
    fallback_client = MagicMock()
    fallback_client.base_url = "https://chatgpt.com/backend-api/codex"
    fallback_client.api_key = "codex-oauth-token"

    messages = []
    agent._emit_status = lambda msg: messages.append(msg)

    with patch(
        "agent.auxiliary_client._resolve_task_provider_model",
        return_value=("ollama-cloud", "deepseek-v4-flash:cloud", None, None, None),
    ), patch(
        "agent.auxiliary_client.get_text_auxiliary_client",
        return_value=(None, None),
    ), patch(
        "agent.auxiliary_client._try_configured_fallback_for_unavailable_client",
        return_value=(fallback_client, "gpt-5.4-mini", "fallback_chain[0](openai-codex)"),
    ) as mock_fallback, patch(
        "agent.model_metadata.get_model_context_length",
        return_value=200_000,
    ) as mock_ctx_len:
        agent._check_compression_model_feasibility()

    assert messages == []
    assert agent._compression_warning is None
    mock_fallback.assert_called_once_with("compression", "ollama-cloud")
    mock_ctx_len.assert_called_once()
    assert mock_ctx_len.call_args.args == ("gpt-5.4-mini",)
    assert mock_ctx_len.call_args.kwargs["provider"] == "openai-codex"










# ── Two-phase: __init__ + run_conversation replay ───────────────────


@patch("agent.model_metadata.get_model_context_length", return_value=80_000)
@patch("agent.auxiliary_client.get_text_auxiliary_client")
def test_warning_stored_for_gateway_replay(mock_get_client, mock_ctx_len):
    """No auto-lower warning is emitted: bounded input fits any aux >= MINIMUM (#126767)."""
    agent = _make_agent(main_context=200_000, threshold_percent=0.50)
    mock_client = MagicMock()
    mock_client.base_url = "https://openrouter.ai/api/v1"
    mock_client.api_key = "sk-aux"
    mock_get_client.return_value = (mock_client, "google/gemini-3-flash-preview")

    vprint_messages = []
    agent._emit_status = lambda msg: vprint_messages.append(msg)
    agent._check_compression_model_feasibility()

    assert len(vprint_messages) == 0
    assert agent._compression_warning is None

    callback_events = []
    agent.status_callback = lambda ev, msg: callback_events.append((ev, msg))
    agent._replay_compression_warning()

    assert len(callback_events) == 0


@patch("agent.model_metadata.get_model_context_length", return_value=200_000)
@patch("agent.auxiliary_client.get_text_auxiliary_client")
def test_no_replay_when_no_warning(mock_get_client, mock_ctx_len):
    """_replay_compression_warning is a no-op when there's no stored warning."""
    agent = _make_agent(main_context=200_000, threshold_percent=0.50)
    mock_client = MagicMock()
    mock_client.base_url = "https://openrouter.ai/api/v1"
    mock_client.api_key = "sk-aux"
    mock_get_client.return_value = (mock_client, "big-model")

    agent._emit_status = lambda msg: None
    agent._check_compression_model_feasibility()

    assert agent._compression_warning is None

    callback_events = []
    agent.status_callback = lambda ev, msg: callback_events.append((ev, msg))
    agent._replay_compression_warning()

    assert len(callback_events) == 0






# ── #67422: threshold suggestion must survive the small-context floor ────────




@patch("agent.model_metadata.get_model_context_length", return_value=300_000)
@patch("agent.auxiliary_client.get_text_auxiliary_client")
def test_threshold_suggestion_kept_for_large_context_main(mock_get_client, mock_ctx_len):
    """No auto-lower occurs even for large main windows: bounded input fits (#126767)."""
    agent = _make_agent(main_context=1_000_000, threshold_percent=0.50)
    mock_client = MagicMock()
    mock_client.base_url = "https://openrouter.ai/api/v1"
    mock_client.api_key = "sk-aux"
    mock_get_client.return_value = (mock_client, "google/gemini-3-flash-preview")

    before = agent.context_compressor.threshold_tokens
    messages = []
    agent._emit_status = lambda msg: messages.append(msg)

    agent._check_compression_model_feasibility()

    assert len(messages) == 0
    assert agent.context_compressor.threshold_tokens == before




