#!/usr/bin/env python3
"""Portability scan baseline.

Lists hard-wired host names, paths, user names and addresses in the estate
tree as described in design §5.1.

Scans the live estate root (hermes-estate + scripts) for patterns that indicate
non-portable, host-specific values (hostnames like ga01, absolute /local paths,
user names, telegram chat ids, etc.).

Usage:
  python3 portability_scan.py [--root /path/to/estate] [--out /path/to/out.json]
  make scan  (via twin or host wrapper)

Outputs a JSON report with count, patterns, hits per file, and timestamp/command.
Baseline only: nothing is fixed.
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

# Patterns considered "hard-wired" per §5.1
PATTERNS = {
    "hostname_ga01": r"\bga01\b",
    "hostname_gh": r"\bgh20[0-9]\b",
    "hostname_skipjack": r"\bskipjack\b",
    "hostname_gargantua": r"\bgargantua0[12]\b",
    "path_local": r"/local/(projects|compose|backup)",
    "path_home_arch": r"/home/arch\b",
    "path_hermes_home": r"\.hermes\b",
    "user_arch": r"\barch\b.*(?:user|account|owner)",
    "telegram_chat_id": r"\b\d{8,12}\b.*(?:chat|telegram|bot)",
    "ip_private": r"\b10\.\d+\.\d+\.\d+\b|\b192\.168\.\d+\.\d+\b",
}

# Directories to scan (relative to estate root)
SCAN_DIRS = ["scripts", "docs", "ci", "hermes-estate"]  # fallback to whatever exists
# Alternative: scan the live estate repo
DEFAULT_ROOTS = [
    Path.home() / "hermes-estate",
    Path("/local/projects/software-co"),
]


def scan_directory(root: Path, patterns: dict[str, str]) -> dict:
    compiled = {name: re.compile(pat) for name, pat in patterns.items()}
    hits: list[dict] = []
    files_scanned = 0

    # Use ripgrep if available for speed, else walk
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip obvious non-source dirs
        dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__", ".venv", "node_modules", "twin-root", ".hermes")]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            # Skip binary-ish extensions
            if fpath.suffix in (".png", ".jpg", ".jpeg", ".gif", ".ico", ".woff", ".woff2", ".ttf", ".pyc", ".pyo", ".db", ".sqlite", ".bundle"):
                continue
            try:
                text = fpath.read_text(errors="ignore")
            except Exception:
                continue
            files_scanned += 1
            for lineno, line in enumerate(text.splitlines(), 1):
                for pname, pat in compiled.items():
                    if pat.search(line):
                        hits.append({
                            "file": str(fpath.relative_to(root) if fpath.is_relative_to(root) else fpath),
                            "line": lineno,
                            "pattern": pname,
                            "snippet": line.strip()[:200],
                        })
                        break  # one hit per line

    return {"files_scanned": files_scanned, "hits": hits, "total_hits": len(hits)}


def main():
    ap = argparse.ArgumentParser(description="Portability scan baseline")
    ap.add_argument("--root", type=str, default=None, help="Estate root to scan")
    ap.add_argument("--out", type=str, default=None, help="Output JSON path")
    ap.add_argument("--patterns", type=str, default=None, help="Custom patterns file")
    args = ap.parse_args()

    # Determine root
    if args.root:
        roots = [Path(args.root)]
    else:
        roots = [p for p in DEFAULT_ROOTS if p.exists()]
        if not roots:
            roots = [Path.cwd()]

    all_hits: list[dict] = []
    total_files = 0
    for root in roots:
        if not root.exists():
            print(f"skip missing root: {root}", file=sys.stderr)
            continue
        result = scan_directory(root, PATTERNS)
        # Prefix file paths with root name
        for h in result["hits"]:
            h["root"] = str(root)
        all_hits.extend(result["hits"])
        total_files += result["files_scanned"]

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "command": " ".join(sys.argv),
        "roots": [str(r) for r in roots],
        "patterns": PATTERNS,
        "files_scanned": total_files,
        "total_hits": len(all_hits),
        "hits": all_hits[:500],  # cap output size
        "truncated": len(all_hits) > 500,
    }

    out_text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(out_text + "\n")
        print(f"Scan: {len(all_hits)} hits in {total_files} files -> {args.out}")
    else:
        print(out_text)

    # Also print summary line for make scan
    print(f"\nPortability scan baseline: {len(all_hits)} hard-wired references in {total_files} files (run: {' '.join(sys.argv)})", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
