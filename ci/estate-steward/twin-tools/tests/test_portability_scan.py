"""Tests for portability_scan."""
import unittest
import tempfile
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import portability_scan

class TestPortabilityScan(unittest.TestCase):
    def test_scan_finds_hardwired(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.py").write_text("host = 'ga01'\npath = '/local/projects/foo'\n")
            (root / "b.py").write_text("clean file, no hits\n")
            result = portability_scan.scan_directory(root, portability_scan.PATTERNS)
            self.assertEqual(result["files_scanned"], 2)
            self.assertGreater(result["total_hits"], 0)
            # a.py should have hits
            hit_files = {h["file"] for h in result["hits"]}
            self.assertIn("a.py", hit_files)
            self.assertNotIn("b.py", hit_files)

    def test_scan_clean(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.py").write_text("x = 1\nprint('hello')\n")
            result = portability_scan.scan_directory(root, portability_scan.PATTERNS)
            self.assertEqual(result["total_hits"], 0)

    def test_scan_skips_binary(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "image.png").write_text("ga01 inside png should be skipped")
            result = portability_scan.scan_directory(root, portability_scan.PATTERNS)
            self.assertEqual(result["total_hits"], 0)
