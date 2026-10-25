#!/usr/bin/env python3
"""test-tripwire.py — fake-change test for litellm-config-tripwire.py (t_2fa0d71d).

Proves the alert fires on a model-entry addition and removal — on a COPY of
the live config, never the live file. Also proves silence when unchanged and
that the live file is byte-identical before/after the whole test.
"""

import hashlib
import os
import subprocess
import sys
from pathlib import Path

WS = Path("/home/arch/.hermes/kanban/workspaces/t_2fa0d71d")
SCRATCH = WS / "tripwire-test"
LIVE = "/local/compose/aistack/litellm/config.yaml"
SCRIPT = "/home/arch/.hermes/scripts/litellm-config-tripwire.py"

SCRATCH.mkdir(parents=True, exist_ok=True)
COPY = SCRATCH / "config.yaml"
STATE = SCRATCH / "state.json"
if STATE.exists():
    STATE.unlink()
COPY.write_bytes(Path(LIVE).read_bytes())

live_sha_before = hashlib.sha256(Path(LIVE).read_bytes()).hexdigest()

def run() -> tuple[int, str]:
    env = dict(os.environ)
    env["LITELLM_TRIPWIRE_TARGET"] = str(COPY)
    env["LITELLM_TRIPWIRE_STATE"] = str(STATE)
    r = subprocess.run([sys.executable, SCRIPT], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout.strip()

FAKE = """
model_list:
  - model_name: fake-test-model-sim
    litellm_params:
      model: openai/fake-test-model-sim
      api_base: http://gpu-sim:30100/v1
      api_key: os.environ/SIM_KEY
"""

rc1, out1 = run()
print(f"RUN1 (baseline)  rc={rc1} stdout={'<silent>' if not out1 else out1!r}")
assert rc1 == 0 and out1 == "", "baseline run must be silent"

COPY.write_text(COPY.read_text() + FAKE, encoding="utf-8")
rc2, out2 = run()
print(f"RUN2 (add fake model) rc={rc2}")
print(out2)
assert "LITELLM TRIPWIRE" in out2 and "models ADDED: fake-test-model-sim" in out2, "addition must alert with the model name"
assert "SIM_KEY" not in out2 and "gpu-sim" not in out2, "alert must never contain other file contents"

rc3, out3 = run()
print(f"RUN3 (unchanged after alert) rc={rc3} stdout={'<silent>' if not out3 else out3!r}")
assert out3 == "", "same state must not re-alert"

COPY.write_bytes(Path(LIVE).read_bytes())
rc4, out4 = run()
print(f"RUN4 (revert = removal) rc={rc4}")
print(out4)
assert "models REMOVED: fake-test-model-sim" in out4, "revert must alert the removal"

live_sha_after = hashlib.sha256(Path(LIVE).read_bytes()).hexdigest()
print(f"live sha before: {live_sha_before}")
print(f"live sha after:  {live_sha_after}")
assert live_sha_before == live_sha_after, "live file must be untouched"

print("ALL TRIPWIRE TESTS PASS (on copy; live file untouched)")
print(f"state file after last alert: {STATE.read_text()}")
