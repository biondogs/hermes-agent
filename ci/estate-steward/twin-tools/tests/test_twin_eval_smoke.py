"""Smoke test for twin-eval.sh missing-key path (R1 regression guard).

Runs the script with empty HOME and asserts stdout == 'skipped: key not provisioned'
exit 0. Requires no key, no docker, just bash + the script (fails on typo class).
"""
import os
import subprocess
import tempfile
import unittest


class TestTwinEvalSmoke(unittest.TestCase):

    def test_missing_key_exits_zero_with_skipped(self):
        # Locate twin-eval.sh from this file's position
        here = os.path.dirname(__file__)
        candidates = [
            os.path.join(here, "../../..", "hermes-estate-twin", "scripts", "twin-eval.sh"),
            os.path.join(here, "..", "..", "..", "hermes-estate-twin", "scripts", "twin-eval.sh"),
        ]
        # Resolve relative to actual file location (repo root agnostic)
        script = None
        for c in candidates:
            p = os.path.abspath(c)
            if os.path.exists(p):
                script = p
                break
        # Fallback: search from env or common locations
        if script is None:
            for p in [
                "/tmp/wt-twin-tools/ci/hermes-estate-twin/scripts/twin-eval.sh",
                "/local/projects/software-co/ci/hermes-estate-twin/scripts/twin-eval.sh",
                "/local/projects/software-co-twin-harness/ci/hermes-estate-twin/scripts/twin-eval.sh",
            ]:
                if os.path.exists(p):
                    script = p
                    break
        if script is None:
            self.skipTest("twin-eval.sh not found")
        # Syntax check first
        r = subprocess.run(["bash", "-n", script], capture_output=True, text=True, timeout=5)
        self.assertEqual(r.returncode, 0, f"bash -n failed: {r.stderr}")
        # Missing-key smoke
        tmp = tempfile.mkdtemp()
        try:
            env = dict(os.environ)
            env["HOME"] = tmp
            r = subprocess.run(["bash", script], capture_output=True, text=True, timeout=10, env=env)
            self.assertEqual(r.returncode, 0, f"exit code {r.returncode} stderr={r.stderr}")
            self.assertIn("skipped: key not provisioned", r.stdout, f"stdout={r.stdout!r} stderr={r.stderr!r}")
        finally:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
