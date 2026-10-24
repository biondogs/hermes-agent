#!/usr/bin/env python3
"""PERF-PORT R6c token/session measurement (t_f7c462b2, 2026-10-24).

Metric (IDENTICAL at baseline and 1-week recheck — do not change without
re-recording both):
  For each lane profile, sessions in the profile's state.db with
  last_activity_at inside the window AND input_tokens > 0.
  Report: n, avg/median/p90/max of the per-session cumulative input_tokens.

Windows: trailing 72h (aligns with the original study figure,
architect avg 5.09M, n=97) and trailing 7d (baseline vs recheck window).

Usage: python3 measure_r6c_tokens.py [--json]
Read-only: opens every state.db in mode=ro.
"""
import datetime as dt
import json
import sqlite3
import sys
from pathlib import Path

PROFILES_ROOT = Path("/home/arch/.hermes/profiles")
LANES = [
    "kanban-board-architect",
    "sw-architect", "sw-dev-a", "sw-dev-b", "sw-devops",
    "sw-docs", "sw-pm", "sw-qa", "sw-reviewer", "sw-ux",
]
WINDOWS = {"72h": 3 * 86400, "7d": 7 * 86400}


def pctl(vals, p):
    if not vals:
        return 0
    vals = sorted(vals)
    k = min(len(vals) - 1, max(0, int(round((p / 100.0) * (len(vals) - 1)))))
    return vals[k]


def measure(profile: str):
    db = PROFILES_ROOT / profile / "state.db"
    if not db.exists():
        return {"error": "no state.db"}
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True, timeout=10)
    rows = con.execute(
        "SELECT last_activity_at, started_at, input_tokens, output_tokens, "
        "message_count, source FROM sessions WHERE input_tokens > 0"
    ).fetchall()
    con.close()
    now = dt.datetime.now().timestamp()
    out = {}
    for wname, wsec in WINDOWS.items():
        vals = [r[2] for r in rows if r[0] and (now - float(r[0])) <= wsec]
        n = len(vals)
        out[wname] = {
            "n": n,
            "avg": round(sum(vals) / n) if n else 0,
            "median": round(pctl(vals, 50)),
            "p90": round(pctl(vals, 90)),
            "max": max(vals) if vals else 0,
        }
    return out


def main():
    as_json = "--json" in sys.argv
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result = {"measured_at_utc": stamp, "lanes": {}}
    for p in LANES:
        result["lanes"][p] = measure(p)
    if as_json:
        print(json.dumps(result, indent=2))
        return
    print(f"# R6c tokens/session measurement — {stamp}")
    print(f"| profile | 72h n | 72h avg | 72h med | 72h p90 | 72h max | 7d n | 7d avg | 7d med | 7d max |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for p, d in result["lanes"].items():
        if "error" in d:
            print(f"| {p} | ERROR: {d['error']} |")
            continue
        w3, w7 = d["72h"], d["7d"]
        fmt = lambda v: f"{v/1e6:.2f}M" if v >= 1e6 else f"{v/1e3:.0f}K"
        print(f"| {p} | {w3['n']} | {fmt(w3['avg'])} | {fmt(w3['median'])} | {fmt(w3['p90'])} | {fmt(w3['max'])} | "
              f"{w7['n']} | {fmt(w7['avg'])} | {fmt(w7['median'])} | {fmt(w7['max'])} |")


if __name__ == "__main__":
    main()
