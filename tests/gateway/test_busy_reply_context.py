"""Regression: busy paths (steer/interrupt/queued/clarify) must keep [Replying to: ...] quote.

Card t_fc921696: operator's Telegram reply while mid-turn was delivered without
reply_to context, so the agent guessed. All busy-delivery paths must prepend
the same "[Replying to: ...]" prefix as the idle path and log the inbound line.
"""
import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.event import MessageEvent
from gateway.run import GatewayRunner
from gateway.session import SessionSource
from tools import clarify_gateway as clar


def _runner():
    r = object.__new__(GatewayRunner)
    r.config = GatewayConfig(platforms={Platform.TELEGRAM: PlatformConfig(enabled=True, token="fake")})
    r.adapters = {}
    r._model = "openai/gpt-4.1-mini"
    r._base_url = None
    # Minimal session registry for busy paths
    r._session_states = {}
    r._busy_state = {}
    r._busy_queue = {}
    r._busy_inflight = {}
    return r


def _src():
    return SessionSource(platform=Platform.TELEGRAM, chat_id="8158007517", chat_name="DM", chat_type="private", user_name="ops")


def _evt(reply_text="the fifth rule", message_id="12092", text="What's the deal with this one"):
    s = _src()
    return MessageEvent(text=text, source=s, message_id=message_id, reply_to_message_id="12084", reply_to_text=reply_text)


def _no_reply_evt(text="hello"):
    return MessageEvent(text=text, source=_src())


@pytest.mark.asyncio
async def test_busy_steer_text_carries_reply_quote():
    r = _runner()
    r._pending_event_audio_paths = MagicMock(return_value=[])
    r._delivery_adapter_for = MagicMock(return_value=None)
    evt = _evt()
    txt = await r._prepare_busy_steer_text(evt)
    assert '[Replying to: "the fifth rule"]' in txt
    assert txt.endswith(evt.text.strip())


@pytest.mark.asyncio
async def test_busy_steer_text_no_quote_when_no_reply():
    r = _runner()
    r._pending_event_audio_paths = MagicMock(return_value=[])
    evt = _no_reply_evt(text="plain follow-up")
    txt = await r._prepare_busy_steer_text(evt)
    assert "[Replying to:" not in txt
    assert txt == "plain follow-up"


@pytest.mark.asyncio
async def test_interrupt_carries_reply_quote():
    r = _runner()
    evt = _evt()
    # Fabricate a running agent with interrupt
    running = MagicMock()
    running.interrupt = MagicMock()
    running.steer = MagicMock(return_value=True)
    # _interrupt_running_agent_for_busy_event expects adapter and uses event fields
    r._pending_event_audio_paths = MagicMock(return_value=[])
    await r._interrupt_running_agent_for_busy_event(evt, MagicMock(), running)
    assert running.interrupt.called
    arg = running.interrupt.call_args[0][0]
    assert '[Replying to: "the fifth rule"]' in arg


@pytest.mark.asyncio
async def test_clarify_intercept_carries_reply_quote():
    r = _runner()
    src = _src()
    evt = _evt(reply_text="the fifth rule", text="second")
    # Need a pending clarify for this session key
    session_key = "telegram:8158007517"
    # Ensure clean state
    clar.clear_session(session_key)
    entry = clar.register("c-test-reply", session_key, "Pick one?", choices=["first", "second", "third"])
    try:
        r._pending_event_audio_paths = MagicMock(return_value=[])
        r._prepare_clarify_reply_text = AsyncMock(return_value="second")
        r._delivery_adapter_for = MagicMock(return_value=None)
        result = await r._hm_clarify_reply(evt, src, session_key)
        assert result == "", "clarify should be intercepted (return empty string)"
        # The stored response that the agent will read must carry the quote
        assert entry.response is not None
        assert '[Replying to: "the fifth rule"]' in entry.response
        assert entry.response.endswith("second")
    finally:
        # wait_for_response pops; but if still present clean up
        clar.clear_session(session_key)
        # Also ensure lock state clean: if entry still there, resolve it
        try:
            clar.resolve_gateway_clarify(entry.clarify_id, clar.CANCELLED)
        except Exception:
            pass


@pytest.mark.asyncio
async def test_busy_reply_prefix_matches_idle_shape():
    """Byte-for-byte same shape as idle path's _prepend_inbound_reply_context."""
    r = _runner()
    r._pending_event_audio_paths = MagicMock(return_value=[])
    evt = _evt(reply_text="quoted text", text="my answer")
    busy_prefix = r._busy_reply_prefix(evt)
    # Idle path prefix for same event
    idle = await r._prepare_inbound_message_text(event=MessageEvent(text="my answer", source=_src(), reply_to_message_id="1", reply_to_text="quoted text"), source=_src(), history=[])
    assert idle is not None
    assert idle.startswith(busy_prefix.strip())
