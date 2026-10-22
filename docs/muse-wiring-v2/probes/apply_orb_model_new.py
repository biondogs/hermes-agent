#!/usr/bin/env python3
"""Make the muse alias LIVE on aistack orb via the designed admin path (/model/new),
zero-downtime, no container lifecycle ops. Key stays in-memory (fetched via docker inspect).
Idempotent: if muse already present in /v1/models, we skip the add and just verify."""
import json, subprocess, urllib.request

def inspect_env():
    out = subprocess.run(["docker", "inspect", "aistack-litellm-1",
                          "--format", "{{json .Config.Env}}"],
                         capture_output=True, text=True, check=True).stdout
    env = {}
    for item in json.loads(out):
        k, _, v = item.partition("=")
        env[k] = v
    return env

env = inspect_env()
print("STORE_MODEL_IN_DB =", env.get("STORE_MODEL_IN_DB", "<unset>"))
print("DATABASE_URL present:", bool(env.get("DATABASE_URL")))
MASTER = env.get("LITELLM_MASTER_KEY")
print("master key present:", bool(MASTER), "| suffix ...", MASTER[-4:] if MASTER else "?")

ORB = "https://orb.arch.jhu.edu"

def req(path, payload=None, key=None, timeout=60):
    k = key or MASTER
    r = urllib.request.Request(ORB + path, headers={"Authorization": "Bearer " + k,
                                                    "Content-Type": "application/json"})
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:400]
    except Exception as e:
        return None, str(e)

# 0. master key works as admin?
code, d = req("/v1/models")
print("admin /v1/models:", code)

# 1. already-live check (idempotency)
if code == 200:
    ids = [m["id"] for m in d["data"]]
    if "muse" in ids:
        print("muse already live on orb:", ids)
        raise SystemExit(0)
    print("pre-add ids:", len(ids), ids)

# 2. add the deployment — mirrors the committed file entry (commit 0ff1adb):
#    model_name muse -> openai/muse-spark-816b-nvfp4 @ http://gpu416:30100/v1
#    upstream key = fleet gateway master key (passthrough var MUSE_FLEET_MASTER_KEY)
fleet_key = open("/tmp/muse-wiring-v2/fleet-masterkey").read().strip()
payload = {
    "model_name": "muse",
    "litellm_params": {
        "model": "openai/muse-spark-816b-nvfp4",
        "api_base": "http://gpu416:30100/v1",
        "api_key": fleet_key,
    },
    "model_info": {
        "max_input_tokens": 262144,
        "max_tokens": 65536,
        "mode": "chat",
    },
}
code, d = req("/model/new", payload)
print("/model/new ->", code, str(d)[:400])

# 3. verify liveness + append-proof
code, d = req("/v1/models")
if code == 200:
    ids = [m["id"] for m in d["data"]]
    print("post-add ids:", len(ids), sorted(ids))
    print("append-only (original 7 intact):",
          set(["gemma4-fp4","readyart","glm52-int4","nail36-35b","qwen38-flash-fp8","qwen38","glm53"]).issubset(set(ids)))
else:
    print("post-add /v1/models FAILED:", code, d)

code, d = req("/v1/chat/completions",
              {"model": "muse", "max_tokens": 30,
               "messages": [{"role": "user", "content": "Reply with exactly: MUSE-WIRING-V2 LIVE"}]})
if code == 200:
    msg = d["choices"][0]["message"]
    print("orb muse chat: model:", d.get("model"),
          "| content:", (msg.get("content") or "")[:100].replace("\n", " "))
else:
    print("orb muse chat FAILED:", code, str(d)[:300])
