"""Tests for fake-telegram service."""
import json
import threading
import time
import unittest
import urllib.request
import urllib.error
import sys, os
from http.server import ThreadingHTTPServer

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import fake_telegram

def _start(port):
    s = ThreadingHTTPServer(("127.0.0.1", port), fake_telegram.Handler)
    t = threading.Thread(target=s.serve_forever, daemon=True)
    t.start()
    time.sleep(0.1)
    return s

def _post(url, data):
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return resp.status, json.loads(resp.read())

def _get(url):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.status, json.loads(resp.read())

class TestFakeTelegram(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.port = 18981
        cls.base = f"http://127.0.0.1:{cls.port}"
        cls.token = "test123"
        cls.bot = f"{cls.base}/bot{cls.token}"
        cls.server = _start(cls.port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        _post(f"{self.base}/_test/reset", {})

    def test_getMe(self):
        status, data = _get(f"{self.bot}/getMe")
        self.assertEqual(status, 200)
        self.assertTrue(data["ok"])
        self.assertTrue(data["result"]["is_bot"])

    def test_sendMessage_and_list(self):
        _post(f"{self.bot}/sendMessage", {"chat_id": 1, "text": "hello"})
        _post(f"{self.bot}/sendMessage", {"chat_id": 1, "text": "world"})
        status, data = _get(f"{self.base}/_test/sent")
        self.assertEqual(len(data["sent"]), 2)
        self.assertEqual(data["sent"][0]["text"], "hello")

    def test_getUpdates_empty(self):
        status, data = _get(f"{self.bot}/getUpdates")
        self.assertEqual(data["result"], [])

    def test_inject_and_getUpdates(self):
        _post(f"{self.base}/_test/inject", {"text": "operator says hi", "chat_id": 999})
        status, data = _get(f"{self.bot}/getUpdates")
        self.assertEqual(len(data["result"]), 1)
        self.assertEqual(data["result"][0]["message"]["text"], "operator says hi")

    def test_getUpdates_offset(self):
        _post(f"{self.base}/_test/inject", {"text": "msg1"})
        _post(f"{self.base}/_test/inject", {"text": "msg2"})
        status, data = _get(f"{self.base}/_test/sent")  # not relevant
        # getUpdates offset=2 should return only second
        status, data = _get(f"{self.bot}/getUpdates?offset=2")
        # update_ids are 1 and 2, so offset 2 returns second
        self.assertEqual(len(data["result"]), 1)

    def test_failing_mode(self):
        _post(f"{self.base}/_test/mode", {"failing": True})
        # sendMessage should fail
        body = json.dumps({"chat_id": 1, "text": "hi"}).encode()
        req = urllib.request.Request(f"{self.bot}/sendMessage", data=body, headers={"Content-Type": "application/json"})
        try:
            urllib.request.urlopen(req, timeout=5)
            self.fail("expected 500 in failing mode")
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 500)
        # turn off
        _post(f"{self.base}/_test/mode", {"failing": False})
        status, data = _post(f"{self.bot}/sendMessage", {"chat_id": 1, "text": "ok now"})
        self.assertTrue(data["ok"])

    def test_clear(self):
        _post(f"{self.bot}/sendMessage", {"chat_id": 1, "text": "to clear"})
        _post(f"{self.base}/_test/clear", {})
        status, data = _get(f"{self.base}/_test/sent")
        self.assertEqual(len(data["sent"]), 0)
