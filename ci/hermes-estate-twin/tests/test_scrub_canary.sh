#!/bin/bash
# test_scrub_canary.sh — proves the scanner blocks when a live-looking secret leaks into twin.
# Seeds a canary secret file in twin-root, runs scan.sh, asserts it FAILS+quarantines,
# then cleans up and asserts scan PASSES again.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TWIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TWIN_ROOT="$TWIN_DIR/twin-root"
SYNC_DIR="$TWIN_DIR/sync"

CANARY_FILE="$TWIN_ROOT/hermes-home/canary_test_file.txt"
CANARY_VALUE="CANARY_SECRET_DO_NOT_COMMIT sk-ant-canary-1234567890abcdefghij"

echo "=== Canary secret test ==="

# Ensure twin-root exists
mkdir -p "$TWIN_ROOT/hermes-home"

# Clean any prior quarantine
rm -f "$TWIN_ROOT/.quarantined" "$TWIN_ROOT/.quarantined.hits" "$CANARY_FILE"

# Baseline: scan should PASS without canary
echo "Step 1: baseline scan (should PASS)..."
set +e
bash "$SYNC_DIR/scan.sh" "$TWIN_ROOT" 2>&1 | tail -3
RC=$?
set -e
if [ "$RC" -ne 0 ]; then
  echo "FAIL: baseline scan should PASS but got exit $RC" >&2
  exit 1
fi
echo "  baseline PASS ok"

# Seed canary
echo "Step 2: seeding canary secret at $CANARY_FILE"
echo "$CANARY_VALUE" > "$CANARY_FILE"

# Scan should now FAIL (exit 2) and quarantine
echo "Step 3: scan with canary (should FAIL + quarantine)..."
set +e
bash "$SYNC_DIR/scan.sh" "$TWIN_ROOT" 2>&1 | tail -5
RC=$?
set -e
if [ "$RC" -ne 2 ]; then
  echo "FAIL: scan with canary should exit 2 but got $RC" >&2
  rm -f "$CANARY_FILE" "$TWIN_ROOT/.quarantined" "$TWIN_ROOT/.quarantined.hits"
  exit 1
fi
if [ ! -f "$TWIN_ROOT/.quarantined" ]; then
  echo "FAIL: .quarantined not written" >&2
  rm -f "$CANARY_FILE"
  exit 1
fi
echo "  canary correctly blocked + quarantined"

# Clean up canary
echo "Step 4: removing canary, re-scanning (should PASS)..."
rm -f "$CANARY_FILE"
set +e
bash "$SYNC_DIR/scan.sh" "$TWIN_ROOT" 2>&1 | tail -3
RC=$?
set -e
if [ "$RC" -ne 0 ]; then
  echo "FAIL: post-cleanup scan should PASS but got $RC" >&2
  exit 1
fi
if [ -f "$TWIN_ROOT/.quarantined" ]; then
  echo "FAIL: .quarantined should be removed after clean scan" >&2
  exit 1
fi
echo "  post-cleanup PASS ok"

echo "=== Canary test: PASS ==="
