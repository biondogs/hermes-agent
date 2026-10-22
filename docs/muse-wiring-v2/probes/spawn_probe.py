#!/usr/bin/env python3
"""Spawn a kanban-worker (-q, sanitized env) and capture its worker-reported model id.
This is the acceptance receipt: 'a wired profile's next spawned worker demonstrably
runs on muse (receipt: worker-reported model id)'."""
import os, subprocess, time

home = "/home/arch"
env = {
    "PATH": "/usr/local/bin:/usr/bin:/bin:" + home + "/.local/bin",
    "HOME": home,
    "USER": "arch",
    "LANG": "C.UTF-8",
    "TERM": "dumb",
    "SHELL": "/bin/bash",
    "XDG_RUNTIME_DIR": "/run/user/1000",
}
cmd = ["hermes", "-p", "kanban-worker", "chat", "--oneshot", "-q",
       "What model and provider are you running on right now? Answer in exactly this format "
       "on one line and nothing else: WORKER-MODEL-RECEIPT model=<model-id> provider=<provider> then stop."]
print("spawning...", flush=True)
t0 = time.time()
r = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=1200)
dt = time.time() - t0
print("exit:", r.returncode, "| elapsed: %.0fs" % dt)
print("--- stdout ---")
print(r.stdout[-3000:])
print("--- stderr (tail) ---")
print(r.stderr[-1500:])
