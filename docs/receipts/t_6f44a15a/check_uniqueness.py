#!/usr/bin/env python3
"""Unique-description check across all profiles (unique-first-line check)."""
import os

base = os.path.expanduser("~/.hermes/profiles")
descs = {}
for name in sorted(os.listdir(base)):
    cfg = os.path.join(base, name, "config.yaml")
    if not os.path.isfile(cfg):
        continue
    in_agent, d = False, None
    for ln in open(cfg):
        if ln.rstrip("\n") == "agent:":
            in_agent = True
            continue
        if in_agent:
            s = ln.strip()
            if s and not ln[0].isspace():
                in_agent = False
                continue
            if s.startswith("description:"):
                d = s.split("description:", 1)[1].strip()
                break
    if d:
        descs[name] = d

print("profiles with agent.description:", len(descs))

def collide(key):
    seen = {}
    for n, d in descs.items():
        seen.setdefault(key(d), []).append(n)
    return {k: v for k, v in seen.items() if len(v) > 1}

full = collide(lambda d: d)
first80 = collide(lambda d: d[:80])
first40 = collide(lambda d: d[:40])
print("full-text collisions :", full or "NONE")
print("first-80 collisions  :", first80 or "NONE")
print("first-40 collisions  :", first40 or "NONE")

for p in ("distiller", "kanban-board-architect", "sw-ux", "sw-dev-a", "sw-dev-b"):
    d = descs.get(p)
    print(f"\n{p}: {d[:100]}..." if d else f"\n{p}: (no description)")
