"""fake-telegram: Bot API subset for the twin.

Listens on 0.0.0.0:8081.
Implements Bot API subset the steward needs:
  GET  /bot<token>/getMe
  POST /bot<token>/sendMessage
  GET  /bot<token>/getUpdates
  POST /bot<token>/getUpdates

Plus test-only control endpoints (no token prefix):
  POST /_test/inject   {"text": "hello", "chat_id": 123, "from": "operator"} -> inject operator message
  GET  /_test/sent     -> list what was sent via sendMessage
  POST /_test/clear    -> clear sent + updates
  POST /_test/mode     {"failing": true/false} -> switch to failing mode (sendMessage returns 500)
  GET  /_test/mode     -> current mode
  GET  /health

State is in-memory, thread-safe. Failing mode makes sendMessage fail to test
"sender has failed for 15 minutes" handling.

Python stdlib only.
"""
from __future__ import annotations
import json
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORT = int(os.environ.get("FAKE_TELEGRAM_PORT", "8081"))

# In-memory state
_lock = threading.Lock()
_sent: list[dict] = []
_updates: list[dict] = []
_update_id = 0
_failing = False
_message_id = 0


def _next_update_id() -> int:
    global _update_id
    _update_id += 1
    return _update_id

def _next_message_id() -> int:
    global _message_id
    _message_id += 1
    return _message_id


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[fake-telegram] {self.client_address[0]} {format % args}", flush=True)

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            raw = self.rfile.read(length)
            if raw:
                try:
                    return json.loads(raw)
                except Exception:
                    # maybe form-encoded
                    try:
                        qs = parse_qs(raw.decode())
                        return {k: v[0] if len(v) == 1 else v for k, v in qs.items()}
                    except Exception:
                        return {}
        return {}

    def _bot_path(self, path: str) -> str | None:
        """Strip /bot<token> prefix, return remainder or None if not a bot path."""
        if path.startswith("/bot"):
            # /botTOKEN/method
            slash = path.find("/", 4)
            if slash == -1:
                return None
            return path[slash:]
        return None

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        # Test endpoints
        if path == "/health" or path == "/_test/health":
            self._json(200, {"status": "ok", "service": "fake-telegram"})
            return
        if path == "/_test/sent":
            with _lock:
                data = list(_sent)
            self._json(200, {"ok": True, "sent": data, "count": len(data)})
            return
        if path == "/_test/mode":
            with _lock:
                self._json(200, {"ok": True, "failing": _failing})
            return
        if path == "/_test/updates":
            with _lock:
                data = list(_updates)
            self._json(200, {"ok": True, "updates": data})
            return

        # Bot API
        bot = self._bot_path(path)
        if bot is not None:
            if bot == "/getMe":
                self._json(200, {"ok": True, "result": {
                    "id": 123456789, "is_bot": True, "first_name": "FakeStewardBot",
                    "username": "fake_steward_bot", "can_read_all_group_messages": False,
                }})
                return
            if bot == "/getUpdates":
                # Support offset, limit, timeout via query
                offset = int(qs.get("offset", [0])[0] or 0)
                limit = int(qs.get("limit", [100])[0] or 100)
                with _lock:
                    if offset:
                        filtered = [u for u in _updates if u["update_id"] >= offset]
                    else:
                        filtered = list(_updates)
                    filtered = filtered[:limit]
                self._json(200, {"ok": True, "result": filtered})
                return
            self._json(404, {"ok": False, "error_code": 404, "description": f"Unknown method: {bot}"})
            return

        self._json(404, {"ok": False, "error_code": 404, "description": f"not found: {path}"})

    def do_POST(self):
        global _failing
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_json()

        # Test control endpoints
        if path == "/_test/inject":
            text = body.get("text", "")
            chat_id = int(body.get("chat_id", 999))
            from_name = body.get("from", "operator")
            from_id = int(body.get("from_id", 1001))
            with _lock:
                uid = _next_update_id()
                mid = _next_message_id()
                upd = {
                    "update_id": uid,
                    "message": {
                        "message_id": mid,
                        "from": {"id": from_id, "first_name": from_name, "is_bot": False},
                        "chat": {"id": chat_id, "type": "private"},
                        "date": int(time.time()),
                        "text": text,
                    }
                }
                _updates.append(upd)
            self._json(200, {"ok": True, "update_id": uid, "message_id": mid})
            return
        if path == "/_test/clear":
            with _lock:
                _sent.clear()
                _updates.clear()
            self._json(200, {"ok": True})
            return
        if path == "/_test/mode":
            failing = body.get("failing", False)
            # Accept string "true"/"false" too
            if isinstance(failing, str):
                failing = failing.lower() in ("1", "true", "yes", "on")
            with _lock:
                _failing = bool(failing)
                cur = _failing
            self._json(200, {"ok": True, "failing": cur})
            return
        if path == "/_test/reset":
            with _lock:
                _sent.clear()
                _updates.clear()
                _failing = False
            self._json(200, {"ok": True})
            return

        # Bot API
        bot = self._bot_path(path)
        if bot is not None:
            if bot == "/sendMessage":
                with _lock:
                    failing = _failing
                if failing:
                    self._json(500, {"ok": False, "error_code": 500, "description": "failing mode: sendMessage refused"})
                    return
                chat_id = body.get("chat_id", body.get("chatId", 0))
                text = body.get("text", "")
                parse_mode = body.get("parse_mode", None)
                with _lock:
                    mid = _next_message_id()
                    entry = {
                        "message_id": mid,
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": parse_mode,
                        "date": int(time.time()),
                    }
                    _sent.append(entry)
                self._json(200, {"ok": True, "result": {
                    "message_id": mid,
                    "chat": {"id": chat_id, "type": "private"},
                    "date": int(time.time()),
                    "text": text,
                }})
                return
            if bot == "/getUpdates":
                offset = int(body.get("offset", 0) or 0)
                limit = int(body.get("limit", 100) or 100)
                with _lock:
                    if offset:
                        filtered = [u for u in _updates if u["update_id"] >= offset]
                    else:
                        filtered = list(_updates)
                    filtered = filtered[:limit]
                self._json(200, {"ok": True, "result": filtered})
                return
            if bot == "/getMe":
                self._json(200, {"ok": True, "result": {
                    "id": 123456789, "is_bot": True, "first_name": "FakeStewardBot",
                    "username": "fake_steward_bot",
                }})
                return
            self._json(404, {"ok": False, "error_code": 404, "description": f"Unknown method: {bot}"})
            return

        self._json(404, {"ok": False, "error_code": 404, "description": f"not found: {path}"})


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[fake-telegram] listening on 0.0.0.0:{PORT}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.shutdown()


if __name__ == "__main__":
    main()
