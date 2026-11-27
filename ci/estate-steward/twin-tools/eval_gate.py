"""eval-gate: scoped relay from twin to single model glm53 via LiteLLM.

Off by default. When enabled (env EVAL_GATE_ENABLED=1 and a key is provided),
forwards POST /v1/chat/completions to the estate LiteLLM at LITELLM_URL
using the supplied API key, but only for the allowed model.

Security:
- Key is read from host file at container start via env var injected by
  `make eval` (never baked into image, compose file, or twin filesystem).
- Only model glm53 is allowed; any other model id is refused with 403.
- Only the configured LiteLLM host is allowed; no other host.
- No key is logged; responses are passed through without logging bodies.

Python stdlib only (http.server + http.client/urllib).
"""
from __future__ import annotations
import os
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse
import http.client
import ssl

PORT = int(os.environ.get("EVAL_GATE_PORT", "8090"))
ALLOWED_MODEL = os.environ.get("EVAL_GATE_MODEL", "glm53")
LITELLM_URL = os.environ.get("LITELLM_URL", "https://ga01:4000")
LITELLM_KEY = os.environ.get("TWIN_EVAL_LITELLM_KEY", os.environ.get("LITELLM_API_KEY", ""))
ENABLED = os.environ.get("EVAL_GATE_ENABLED", "0") in ("1", "true", "yes")

# Derive host/port from LITELLM_URL for allowlist check
_parsed = urlparse(LITELLM_URL)
LITELLM_HOST = _parsed.hostname or "ga01"
LITELLM_PORT = _parsed.port or (443 if _parsed.scheme == "https" else 80)
LITELLM_SCHEME = _parsed.scheme or "https"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Never log key or body
        print(f"[eval-gate] {self.client_address[0]} {format % args}", flush=True)

    def _json(self, code: int, obj: dict):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length", 0) or 0)
        if length:
            return self.rfile.read(length)
        return b""

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ("/health", "/_health", "/v1/health"):
            self._json(200, {"status": "ok", "service": "eval-gate", "enabled": ENABLED, "model": ALLOWED_MODEL})
            return
        if parsed.path == "/_test/info":
            self._json(200, {"enabled": ENABLED, "model": ALLOWED_MODEL, "litellm_host": LITELLM_HOST})
            return
        self._json(404, {"error": {"message": f"not found: {parsed.path}", "type": "not_found"}})

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path not in ("/v1/chat/completions", "/chat/completions"):
            self._json(404, {"error": {"message": f"not found: {parsed.path}", "type": "not_found"}})
            return

        if not ENABLED:
            self._json(403, {"error": {"message": "eval gate is off (set EVAL_GATE_ENABLED=1 via make eval)", "type": "gate_disabled"}})
            return
        raw = self._read_body()
        try:
            body = json.loads(raw) if raw else {}
        except Exception:
            self._json(400, {"error": {"message": "invalid JSON", "type": "invalid_request"}})
            return

        model = body.get("model", "")
        if model != ALLOWED_MODEL:
            self._json(403, {"error": {"message": f"model '{model}' not allowed; only '{ALLOWED_MODEL}' is permitted through eval gate", "type": "model_not_allowed"}})
            return

        if not LITELLM_KEY:
            self._json(503, {"error": {"message": "eval gate has no key (host file ~/.hermes/secrets/twin-eval.env not provisioned)", "type": "no_key"}})
            return

        # Forward to LiteLLM
        try:
            result = self._forward(raw)
        except Exception as e:
            self._json(502, {"error": {"message": f"upstream error: {e}", "type": "upstream_error"}})
            return

        # result is (status, headers, body)
        status, headers, resp_body = result
        self.send_response(status)
        # Pass through content-type
        ctype = headers.get("content-type", "application/json")
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(resp_body)))
        self.end_headers()
        self.wfile.write(resp_body)

    def _forward(self, body: bytes):
        """Forward POST /v1/chat/completions to LiteLLM, return (status, headers, body)."""
        path = "/v1/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LITELLM_KEY}",
            "Content-Length": str(len(body)),
        }
        # Use http.client directly to control TLS
        if LITELLM_SCHEME == "https":
            ctx = ssl.create_default_context()
            # ga01 uses self-signed cert for litellm
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            conn = http.client.HTTPSConnection(LITELLM_HOST, LITELLM_PORT, timeout=30, context=ctx)
        else:
            conn = http.client.HTTPConnection(LITELLM_HOST, LITELLM_PORT, timeout=30)
        conn.request("POST", path, body=body, headers=headers)
        resp = conn.getresponse()
        resp_body = resp.read()
        resp_headers = {k.lower(): v for k, v in resp.getheaders()}
        conn.close()
        return resp.status, resp_headers, resp_body


def main():
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"[eval-gate] listening on 0.0.0.0:{PORT}  enabled={ENABLED} model={ALLOWED_MODEL} upstream={LITELLM_HOST}:{LITELLM_PORT}", flush=True)
    if not ENABLED:
        print("[eval-gate] gate is OFF; all chat requests will be refused until enabled via make eval", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.shutdown()


if __name__ == "__main__":
    main()
