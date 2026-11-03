"""LOCAL HOTFIX (t_1b6e0ed1): opt-in clarify delivery receipt.

When ``extra.clarify_receipt_path`` is set on a Telegram adapter instance, every
successful ``send_clarify`` appends one JSON line holding the Message Telegram
returned from sendMessage. Default off; a receipt failure never breaks the send.
"""

import json
import os
import stat
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

_repo = str(Path(__file__).resolve().parents[2])
if _repo not in sys.path:
    sys.path.insert(0, _repo)

from plugins.platforms.telegram.adapter import TelegramAdapter
from gateway.config import PlatformConfig


class _Msg:
    """Stand-in for the PTB Message returned by sendMessage."""

    message_id = 4242

    def to_dict(self):
        return {"message_id": 4242, "chat": {"id": -1004425748613, "type": "supergroup"},
                "text": "❓ Server-side text", "entities": [{"type": "bold", "offset": 0, "length": 1}],
                "reply_markup": {"inline_keyboard": [[{"text": "1", "callback_data": "cl:cid:0"}]]}}


def _make_adapter(extra=None):
    adapter = TelegramAdapter(PlatformConfig(enabled=True, token="test-token-SECRET", extra=extra or {}))
    bot = AsyncMock()
    bot.send_message = AsyncMock(return_value=_Msg())
    adapter._bot = bot
    adapter._app = MagicMock()
    return adapter


async def _send(adapter):
    return await adapter.send_clarify(chat_id="-1004425748613", question="Local text?", choices=["a", "b"],
                                      clarify_id="cid", session_key="sk")


@pytest.mark.asyncio
async def test_opt_in_appends_returned_message_verbatim(tmp_path):
    path = tmp_path / "sub" / "receipt.jsonl"
    adapter = _make_adapter({"clarify_receipt_path": str(path)})
    r1 = await _send(adapter)
    r2 = await _send(adapter)
    assert r1.success and r2.success
    lines = path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2  # one line per successful send, appended
    rec = json.loads(lines[0])
    assert set(rec) == {"ts", "clarify_id", "chat_id", "message"}
    assert rec["clarify_id"] == "cid" and rec["chat_id"] == "-1004425748613"
    assert rec["message"] == _Msg().to_dict()  # Telegram's returned object, not the locally built text
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert "SECRET" not in path.read_text(encoding="utf-8")
    assert adapter._clarify_state["cid"] == "sk"


@pytest.mark.asyncio
async def test_default_off_writes_nothing(tmp_path, monkeypatch):
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    monkeypatch.chdir(cwd)
    adapter = _make_adapter()
    assert adapter._clarify_receipt_path() == ""
    assert (await _send(adapter)).success
    assert list(cwd.iterdir()) == []


@pytest.mark.asyncio
async def test_receipt_failure_never_breaks_send(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    adapter = _make_adapter({"clarify_receipt_path": str(blocker / "nested" / "r.jsonl")})  # parent is a file
    result = await _send(adapter)
    assert result.success is True and result.message_id == "4242"
    assert adapter._clarify_state["cid"] == "sk"


@pytest.mark.asyncio
async def test_failed_send_writes_no_receipt(tmp_path):
    path = tmp_path / "r.jsonl"
    adapter = _make_adapter({"clarify_receipt_path": str(path)})
    adapter._bot = AsyncMock(send_message=AsyncMock(side_effect=RuntimeError("boom")))
    result = await _send(adapter)
    assert result.success is False
    assert not path.exists()


def test_tilde_path_expanded():
    adapter = _make_adapter({"clarify_receipt_path": "~/x.jsonl"})
    assert adapter._clarify_receipt_path() == os.path.expanduser("~/x.jsonl")


def test_nonjson_values_do_not_break_receipt(tmp_path):
    from datetime import UTC, datetime

    class _DatedMsg(_Msg):
        def to_dict(self):
            return {**super().to_dict(), "date": datetime(2026, 11, 3, 13, 0, tzinfo=UTC)}

    path = tmp_path / "r.jsonl"
    adapter = _make_adapter({"clarify_receipt_path": str(path)})
    adapter._write_clarify_receipt("c", -1004425748613, _DatedMsg())
    rec = json.loads(path.read_text(encoding="utf-8"))
    assert rec["message"]["text"] == "❓ Server-side text"
    assert rec["message"]["date"].startswith("2026-11-03")
    assert rec["chat_id"] == "-1004425748613"
