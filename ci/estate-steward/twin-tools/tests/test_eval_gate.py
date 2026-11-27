"""Tests for eval-gate (scoped relay). No real network needed — tests gate logic."""
import json
import threading
import time
import unittest
import urllib.request
import urllib.error
import sys, os
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import eval_gate

def _start(port, enabled=False, model="glm53"):
    # Patch module globals for test
    orig_enabled = eval_gate.ENABLED
    orig_model = eval_gate.ALLOWED_MODEL
    eval_gate.ENABLED = enabled
    eval_gate.ALLOWED_MODEL = model
    s = ThreadingHTTPServer(("127.0.0.1", port), eval_gate.Handler)
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    return s, orig_enabled, orig_model

def _restore(s, orig_enabled, orig_model):
    s.shutdown()
    eval_gate.ENABLED = orig_enabled
    eval_gate.ALLOWED_MODEL = orig_model

def _post(url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read())

def _get(url):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, json.loads(resp.read())

class TestEvalGateOff(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 18982
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.server, cls.orig_e, cls.orig_m = _start(cls.port, enabled=False)

    @classmethod
    def tearDownClass(cls):
        _restore(cls.server, cls.orig_e, cls.orig_m)

    def test_health_shows_disabled(self):
        status, data = _get(f"{self.base}/health")
        self.assertFalse(data["enabled"])

    def test_chat_refused_when_off(self):
        body = json.dumps({"model": "glm53", "messages": [{"role": "user", "content": "hi"}]}).encode()
        req = urllib.request.Request(f"{self.base}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=5)
            self.fail("expected 403 when gate off")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)
            data = json.loads(e.read())
            self.assertIn("gate is off", data["error"]["message"])

class TestEvalGateModelAllowlist(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 18983
        cls.base = f"http://127.0.0.1:{cls.port}"
        # Enable but with no key — model check happens before upstream
        cls.server, cls.orig_e, cls.orig_m = _start(cls.port, enabled=True, model="glm53")
        # Ensure no key so we don't hit upstream
        cls.orig_key = eval_gate.LITELLM_KEY
        eval_gate.LITELLM_KEY = ""

    @classmethod
    def tearDownClass(cls):
        eval_gate.LITELLM_KEY = cls.orig_key
        _restore(cls.server, cls.orig_e, cls.orig_m)

    def test_wrong_model_refused(self):
        body = json.dumps({"model": "gpt-4", "messages": [{"role": "user", "content": "hi"}]}).encode()
        req = urllib.request.Request(f"{self.base}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=5)
            self.fail("expected 403 for wrong model")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 403)
            data = json.loads(e.read())
            self.assertIn("not allowed", data["error"]["message"])

    def test_no_key_returns_503(self):
        body = json.dumps({"model": "glm53", "messages": [{"role": "user", "content": "hi"}]}).encode()
        req = urllib.request.Request(f"{self.base}/v1/chat/completions", data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=5)
            self.fail("expected 503 when no key")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 503)
