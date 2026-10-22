#!/usr/bin/env python3
"""Probe 4: full orb model list + muse chat via orb (no double /v1 this time)."""
import json, urllib.request

ORB_KEY = None
for line in open("/home/arch/.hermes/profiles/kanban-worker/.env"):
    if line.startswith("LITELLM_API_KEY="):
        ORB_KEY = line.split("=", 1)[1].strip()
        break

def req(url, key, payload=None, timeout=60):
    r = urllib.request.Request(url, headers={"Authorization": "Bearer " + key,
                                             "Content-Type": "application/json"})
    data = json.dumps(payload).encode() if payload is not None else None
    try:
        with urllib.request.urlopen(r, data=data, timeout=timeout) as resp:
            return resp.status, json.load(resp)
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return None, str(e)

code, d = req("https://orb.arch.jhu.edu/v1/models", ORB_KEY)
ids = [m["id"] for m in d["data"]] if code == 200 else d
print("orb /v1/models:", code, "count:", len(ids) if isinstance(ids, list) else "?", ids)
print("orb has muse:", isinstance(ids, list) and "muse" in ids)

code, d = req("https://orb.arch.jhu.edu/v1/chat/completions", ORB_KEY,
              {"model": "muse", "max_tokens": 30,
               "messages": [{"role": "user", "content": "Reply with exactly: MUSE-WIRING-V2 LIVE"}]})
if code == 200:
    msg = d["choices"][0]["message"]
    print("orb muse chat: model:", d.get("model"),
          "| content:", (msg.get("content") or "")[:100],
          "| reasoning:", (msg.get("reasoning_content") or "")[:60])
else:
    print("orb muse chat FAILED (expected until operator restart):", code, str(d)[:250])
