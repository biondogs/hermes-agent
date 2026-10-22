#!/usr/bin/env python3
"""MUSE-WIRING-V2 fallback negative test (acceptance): simulate muse scaled-down by
pointing the orb deployment's api_base at an unroutable IP for the duration of one
spawned-worker probe, then RESTORE. Receipts printed at each step.
Steps:
  1. sanity: muse chat 200 now
  2. PATCH api_base -> http://10.255.255.1:9/v1  (unreachable; instant conn error)
  3. spawn kanban-worker chat --oneshot (sanitized env) -> expect Hermes
     fallback notice + reply from qwen38-flash-fp8
  4. PATCH api_base back -> http://10.99.192.6:30100/v1
  5. verify muse chat 200 again
"""
import json, os, subprocess, urllib.request, sys

def master_key():
    out = subprocess.run(["docker", "inspect", "aistack-litellm-1",
                          "--format", "{{json .Config.Env}}"],
                         capture_output=True, text=True, check=True).stdout
    for item in json.loads(out):
        if item.startswith("LITELLM_MASTER_KEY="):
            return item.split("=", 1)[1]
    raise SystemExit("no master key")

MASTER = master_key()
ORB = "https://orb.arch.jhu.edu"
MODEL_ID = "93ea75f5-b777-4b9d-bf6a-9c375fde132c"
GOOD = "http://10.99.192.6:30100/v1"
BAD = "http://10.255.255.1:9/v1"

def patch_api_base(val):
    r = urllib.request.Request(ORB + "/model/%s/update" % MODEL_ID,
                               headers={"Authorization": "Bearer " + MASTER,
                                        "Content-Type": "application/json"})
    r.get_method = lambda: "PATCH"
    data = json.dumps({"litellm_params": {"api_base": val}}).encode()
    try:
        with urllib.request.urlopen(r, data=data, timeout=60) as resp:
            return resp.status
    except urllib.error.HTTPError as e:
        return e.code

def muse_chat(timeout=90):
    ORB_KEY = None
    for line in open("/home/arch/.hermes/profiles/kanban-worker/.env"):
        if line.startswith("LITELLM_API_KEY="):
            ORB_KEY = line.split("=", 1)[1].strip()
            break
    r = urllib.request.Request(ORB + "/v1/chat/completions",
                               headers={"Authorization": "Bearer " + ORB_KEY,
                                        "Content-Type": "application/json"})
    data = json.dumps({"model": "muse", "max_tokens": 20,
                       "messages": [{"role": "user", "content": "say OK"}]}).encode()
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            d = json.load(resp)
            return resp.status, d.get("model")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:150]
    except Exception as e:
        return None, str(e)[:150]

def spawn_worker():
    env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin:/home/arch/.local/bin",
        "HOME": "/home/arch", "USER": "arch", "LANG": "C.UTF-8",
        "TERM": "dumb", "SHELL": "/bin/bash", "XDG_RUNTIME_DIR": "/run/user/1000",
    }
    cmd = ["hermes", "-p", "kanban-worker", "chat", "--oneshot", "-q",
           "Answer in exactly this format on one line and nothing else: "
           "FALLBACK-PROBE-REPLY model=<the model id that actually answered your turn> then stop."]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=900)
    return r.returncode, r.stdout

print("[1] sanity muse chat:", muse_chat(), flush=True)

print("[2] breaking api_base ->", BAD, "-> PATCH", patch_api_base(BAD), flush=True)
import time
time.sleep(2)
code, info = muse_chat()
print("    broken-state direct chat:", code, str(info)[:120], flush=True)

print("[3] spawning kanban-worker under broken muse...", flush=True)
rc, out = spawn_worker()
print("    exit:", rc, flush=True)
keep = [l for l in out.splitlines() if ("FALLBACK-PROBE-REPLY" in l or "fallback" in l.lower())]
for l in keep:
    print("    |", l.strip()[:200])
if not keep:
    print(out[-1500:])

print("[4] restoring api_base ->", GOOD, "-> PATCH", patch_api_base(GOOD), flush=True)
time.sleep(2)
code, info = muse_chat()
print("[5] restored muse chat:", (code, info if code == 200 else str(info)[:120]), flush=True)
