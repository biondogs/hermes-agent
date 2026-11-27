"""mock-model: OpenAI-compatible chat completions on twin internal network.

Listens on 0.0.0.0:8080, serves POST /v1/chat/completions (and /chat/completions).
Answers from a scripted fixtures file chosen per test via:
  POST /_test/set-fixtures  {"path": "/path/to/fixtures.json"}
  POST /_test/reset         (clear fixtures, back to default)

Fixtures format: JSON object mapping a substring of the last user message
to a response spec. Example:
{
  "hello": {"content": "Hi there!"},
  "do tool": {"tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "my_tool", "arguments": "{\\"x\\": 1}"}}]}
}

Unknown prompts get DEFAULT_ANSWER. Each response also supports "content" and "tool_calls".

Also handles GET /v1/models and GET /health for probes.
Python stdlib only.
"""
from __future__ import annotations
import json
import os
import time
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

DEFAULT_ANSWER = "MOCK-MODEL-DEFAULT: I am the twin mock model. No fixture matched your prompt."

FIXTURES_PATH = os.environ.get("MOCK_MODEL_FIXTURES", "")
FIXTURES: dict = {}
FIXTURES_LOCK = threading.Lock()
PORT = int(os.environ.get("MOCK_MODEL_PORT", "8080"))

def load_fixtures(path: str) -> dict:
    if not path:
        return {}
    with open(path, "r") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError("fixtures file must be a JSON object")
    return data


def match_fixture(messages: list) -> dict | None:
    # Find last user message content
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            c = m.get("content", "")
            if isinstance(c, list):
                # content can be list of parts
                c = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in c)
            last_user = str(c)
            break
    if not last_user and messages:
        # fallback: last message content
        c = messages[-1].get("content", "")
        if isinstance(c, list):
            c = " ".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in c)
        last_user = str(c)

    with FIXTURES_LOCK:
        fixtures = dict(FIXTURES)

    for key, spec in fixtures.items():
        if key.lower() in last_user.lower():
            return spec
    return None


def build_chat_response(model: str, spec: dict | None, prompt_text: str = "") -> dict:
    now = int(time.time())
    rid = f"chatcmpl-mock-{now}"
    if spec is None:
        content = DEFAULT_ANSWER
        tool_calls = None
    else:
        content = spec.get("content")
        tool_calls = spec.get("tool_calls")

    message: dict = {"role": "assistant"}
    if tool_calls:
        message["tool_calls"] = tool_calls
        # When tool_calls present, content may be empty string per OpenAI spec
        message["content"] = content if content is not None else ""
    else:
        message["content"] = content if content is not None else DEFAULT_ANSWER

    return {
        "id": rid,
        "object": "chat.completion",
        "created": now,
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": message,
                "finish_reason": "tool_calls" if tool_calls else "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 10, "total_tokens": 20},
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[mock-model] {self.client_address[0]} {format % args}", flush=True)

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
            return json.loads(self.rfile.read(length))
        return {}

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/health", "/v1/health", "/_health"):
            self._json(200, {"status": "ok", "service": "mock-model"})
        elif parsed.path in ("/v1/models", "/models"):
            self._json(200, {"object": "list", "data": [
                {"id": "mock-model", "object": "model", "owned_by": "twin"},
                {"id": "glm53", "object": "model", "owned_by": "twin"},
            ]})
        elif parsed.path == "/_test/fixtures":
            with FIXTURES_LOCK:
                self._json(200, {"fixtures": FIXTURES, "default": DEFAULT_ANSWER})
        elif parsed.path in ("/api/tags", "/api/version") or parsed.path.endswith("/props") or parsed.path.endswith("/version") or parsed.path.endswith("/health") or "models" in parsed.path:
            # LiteLLM/Ollama preflight probes — answer benignly so hermes worker proceeds to chat
            self._json(200, {"object": "list", "data": [{"id": "mock-model", "object": "model"}]})
        else:
            self._json(404, {"error": {"message": f"not found: {parsed.path}", "type": "not_found"}})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/v1/chat/completions", "/chat/completions", "/v1/completions"):
            body = self._read_json()
            messages = body.get("messages", [])
            model = body.get("model", "mock-model")
            stream = body.get("stream", False)
            if stream:
                self._json(400, {"error": {"message": "streaming not supported by mock-model", "type": "invalid_request"}})
                return
            spec = match_fixture(messages)
            resp = build_chat_response(model, spec)
            self._json(200, resp)
        elif parsed.path == "/_test/set-fixtures":
            body = self._read_json()
            # Accept either {"path": "..."} or direct fixture dict {"fixtures": {...}}
            if "fixtures" in body and isinstance(body["fixtures"], dict):
                with FIXTURES_LOCK:
                    FIXTURES.clear()
                    FIXTURES.update(body["fixtures"])
                self._json(200, {"ok": True, "count": len(FIXTURES)})
            elif "path" in body:
                path = body["path"]
                try:
                    data = load_fixtures(path)
                except Exception as e:
                    self._json(400, {"error": {"message": str(e), "type": "load_error"}})
                    return
                with FIXTURES_LOCK:
                    FIXTURES.clear()
                    FIXTURES.update(data)
                self._json(200, {"ok": True, "count": len(FIXTURES), "path": path})
            else:
                self._json(400, {"error": {"message": "need 'path' or 'fixtures'", "type": "invalid_request"}})
        elif parsed.path == "/_test/reset":
            with FIXTURES_LOCK:
                FIXTURES.clear()
            self._json(200, {"ok": True})
        else:
            self._json(404, {"error": {"message": f"not found: {parsed.path}", "type": "not_found"}})


def main():
    # Preload fixtures if env var set
    if FIXTURES_PATH:
        try:
            data = load_fixtures(FIXTURES_PATH)
            FIXTURES.update(data)
            print(f"[mock-model] preloaded {len(data)} fixtures from {FIXTURES_PATH}", flush=True)
        except Exception as e:
            print(f"[mock-model] preload failed: {e}", flush=True)

    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[mock-model] listening on 0.0.0.0:{PORT}  default={DEFAULT_ANSWER!r}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.shutdown()


if __name__ == "__main__":
    main()
