#!/usr/bin/env python3
"""Point the orb muse deployment's upstream model at the FLEET GATEWAY alias 'muse'
(gateway /v1/models: qwen38, glm53, muse, qwen38-flash-fp8 — the raw served name
muse-spark-816b-nvfp4 is NOT a gateway alias; via the gateway hop the alias keeps the
fleet-internal muse->qwen38 fallback chain in play, per the task's stated preference)."""
import json, subprocess, urllib.request

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

def req(path, payload=None, method="PATCH", timeout=90):
    r = urllib.request.Request(ORB + path, headers={"Authorization": "Bearer " + MASTER,
                                                    "Content-Type": "application/json"})
    r.get_method = lambda: method
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return None, str(e)

code, d = req("/model/%s/update" % MODEL_ID,
              {"litellm_params": {"model": "openai/muse"}})
print("PATCH model ->", code, str(d)[:200])

ORB_KEY = None
for line in open("/home/arch/.hermes/profiles/kanban-worker/.env"):
    if line.startswith("LITELLM_API_KEY="):
        ORB_KEY = line.split("=", 1)[1].strip()
        break

def creq(path, payload=None, timeout=180):
    r = urllib.request.Request(ORB + path, headers={"Authorization": "Bearer " + ORB_KEY,
                                                    "Content-Type": "application/json"})
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return None, str(e)

code, d = creq("/v1/chat/completions",
               {"model": "muse", "max_tokens": 60,
                "messages": [{"role": "user", "content": "Reply with exactly: MUSE-WIRING-V2 LIVE and nothing else."}]})
if code == 200:
    msg = d["choices"][0]["message"]
    print("orb muse chat via CLIENT key: model:", d.get("model"),
          "| usage:", d.get("usage", {}).get("completion_tokens"),
          "| content:", (msg.get("content") or "")[:150].replace("\n", " "))
else:
    print("orb muse chat FAILED:", code, str(d)[:300])
