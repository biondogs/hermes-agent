"""Tests for mock-model service (stdlib only, runnable with python3 -m unittest)."""
import json
import threading
import time
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
import sys
import os

# Import the handler by loading the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import mock_model

def _start_server(port):
    server = ThreadingHTTPServer(("127.0.0.1", port), mock_model.Handler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    return server

def _post(url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read())

def _get(url):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, json.loads(resp.read())


class TestMockModel(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 18980
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.server = _start_server(cls.port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        # Reset fixtures before each test
        _post(f"{self.base}/_test/reset", {})

    def test_health(self):
        status, data = _get(f"{self.base}/health")
        self.assertEqual(status, 200)
        self.assertEqual(data["service"], "mock-model")

    def test_models(self):
        status, data = _get(f"{self.base}/v1/models")
        self.assertEqual(status, 200)
        self.assertIn("data", data)

    def test_default_answer(self):
        status, data = _post(f"{self.base}/v1/chat/completions", {
            "model": "mock-model",
            "messages": [{"role": "user", "content": "unknown prompt xyz 12345"}]
        })
        self.assertEqual(status, 200)
        content = data["choices"][0]["message"]["content"]
        self.assertIn("MOCK-MODEL-DEFAULT", content)

    def test_fixture_match(self):
        _post(f"{self.base}/_test/set-fixtures", {"fixtures": {"hello mock": {"content": "Hi from fixture!"}}})
        status, data = _post(f"{self.base}/v1/chat/completions", {
            "model": "mock-model",
            "messages": [{"role": "user", "content": "hello mock please"}]
        })
        self.assertEqual(status, 200)
        self.assertIn("Hi from fixture!", data["choices"][0]["message"]["content"])

    def test_tool_calls(self):
        _post(f"{self.base}/_test/set-fixtures", {"fixtures": {
            "do tool": {"tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "my_tool", "arguments": "{}"}}]}
        }})
        status, data = _post(f"{self.base}/v1/chat/completions", {
            "model": "mock-model",
            "messages": [{"role": "user", "content": "do tool now"}]
        })
        self.assertEqual(status, 200)
        msg = data["choices"][0]["message"]
        self.assertIn("tool_calls", msg)
        self.assertEqual(msg["tool_calls"][0]["function"]["name"], "my_tool")
        self.assertEqual(data["choices"][0]["finish_reason"], "tool_calls")

    def test_set_fixtures_via_path(self):
        import tempfile, pathlib
        fixtures = {"path test": {"content": "path fixture hit"}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(fixtures, f)
            fpath = f.name
        try:
            status, data = _post(f"{self.base}/_test/set-fixtures", {"path": fpath})
            self.assertEqual(status, 200)
            status, data = _post(f"{self.base}/v1/chat/completions", {
                "model": "mock-model",
                "messages": [{"role": "user", "content": "path test hello"}]
            })
            self.assertIn("path fixture hit", data["choices"][0]["message"]["content"])
        finally:
            os.unlink(fpath)

    def test_reset_clears_fixtures(self):
        _post(f"{self.base}/_test/set-fixtures", {"fixtures": {"hello mock": {"content": "Hi"}}})
        _post(f"{self.base}/_test/reset", {})
        status, data = _post(f"{self.base}/v1/chat/completions", {
            "model": "mock-model",
            "messages": [{"role": "user", "content": "hello mock"}]
        })
        self.assertIn("MOCK-MODEL-DEFAULT", data["choices"][0]["message"]["content"])
