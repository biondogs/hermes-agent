#!/usr/bin/env bash
set -euo pipefail
# health.sh — report age of fresh, last build result, drift
# Reads ci/hermes-upstream/status.json and docker state; exits 0 always (informational).
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
STATUS_JSON="$SCRIPT_DIR/status.json"
STATUS_MD="$SCRIPT_DIR/STATUS.md"

echo "=== hermes-upstream health ==="
echo ""

if [[ -f "$STATUS_JSON" ]]; then
  cat "$STATUS_JSON" | python3 -c "
import json, pathlib
d=json.load(open('$STATUS_JSON'))
for k in ['timestamp','upstream_sha','dated_tag','result','fresh_result','tests_passed','tests_failed','fresh_age','drift']:
    print(f\"{k:16s}: {d.get(k,'')}\")
"
else
  echo "status.json not found — no rebuild has run yet"
fi
echo ""
echo "--- docker images ---"
docker images --format '{{.Repository}}:{{.Tag}}  {{.CreatedAt}}  {{.Size}}' | grep hermes-upstream || echo "(no hermes-upstream images)"
echo ""
if [[ -f "$STATUS_MD" ]]; then
  echo "--- STATUS.md health line ---"
  grep -E 'Health|fresh|drift|Result' "$STATUS_MD" | head -10
fi

# Drift check live
UPSTREAM_CLONE="$(cd "$SCRIPT_DIR/../.." && pwd)/hermes-board-layers"
if [[ -d "$UPSTREAM_CLONE/.git" ]]; then
  echo ""
  echo "--- drift (live) ---"
  git -C "$UPSTREAM_CLONE" fetch origin main --quiet 2>&1 | tail -2 || true
  ORIGIN_SHA="$(git -C "$UPSTREAM_CLONE" rev-parse origin/main 2>/dev/null || echo unknown)"
  echo "origin/main = $ORIGIN_SHA"
  if docker image inspect hermes-upstream:fresh --format '{{.Id}}' >/dev/null 2>&1; then
    echo "fresh image exists: $(docker image inspect hermes-upstream:fresh --format '{{.Created}}')"
  else
    echo "fresh image MISSING"
  fi
fi
