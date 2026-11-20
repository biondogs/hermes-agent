#!/bin/bash
# scan.sh — post-sync secret scanner. FAILS and quarantines twin if any live-looking secret found.
# Usage: scan.sh <twin-root>
# Exit 0 = clean, Exit 2 = secrets found (quarantined), Exit 1 = error.
set -euo pipefail
TWIN_ROOT="${1:?usage: scan.sh <twin-root>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PATTERNS_FILE="$SCRIPT_DIR/scan-patterns.txt"

if [ ! -f "$PATTERNS_FILE" ]; then
  echo "ERROR: patterns file not found: $PATTERNS_FILE" >&2
  exit 1
fi

# Build ripgrep pattern file (skip comments and empty lines)
PAT_FILE=$(mktemp)
grep -v '^#' "$PATTERNS_FILE" | grep -v '^$' > "$PAT_FILE" || true

if [ ! -s "$PAT_FILE" ]; then
  echo "ERROR: no patterns after filtering comments" >&2
  rm -f "$PAT_FILE"
  exit 1
fi

# Scan — only hermes-home + snapshots (code checkouts contain test fixtures with fake tokens)
SCAN_TARGETS=()
for d in "$TWIN_ROOT/hermes-home" "$TWIN_ROOT/snapshots"; do
  [ -d "$d" ] && SCAN_TARGETS+=("$d")
done
# Fall back to whole twin-root if neither exists yet (early sync)
[ ${#SCAN_TARGETS[@]} -eq 0 ] && SCAN_TARGETS=("$TWIN_ROOT")

HITS=""
SCAN_RC=0
if command -v rg &>/dev/null; then
  HITS=$(rg --no-heading --with-filename -f "$PAT_FILE" "${SCAN_TARGETS[@]}" 2>/dev/null || true)
else
  HITS=$(grep -rEn -f "$PAT_FILE" "${SCAN_TARGETS[@]}" 2>/dev/null || true)
fi

# Filter out our own placeholder and the scanner's own patterns file
HITS=$(echo "$HITS" | grep -v "__TWIN_PLACEHOLDER__" | grep -v "scan-patterns.txt" | grep -v "scan\\.sh" || true)
# Also ignore the placeholder auth.json we write
HITS=$(echo "$HITS" | grep -v "_twin_placeholder" || true)
# Ignore known fake-secret test fixtures (plugins ship tests with placeholder keys)
HITS=$(echo "$HITS" | grep -v "/tests/" || true)
HITS=$(echo "$HITS" | grep -v "/test_" || true)
# Historical receipts contain redacted/example tokens that predate the twin (not live secrets)
HITS=$(echo "$HITS" | grep -v "/receipts/" || true)
HITS=$(echo "$HITS" | grep -v "credential-pools.md" || true)

rm -f "$PAT_FILE"

if [ -n "$HITS" ]; then
  echo "SCAN FAILED: live-looking secrets found in twin-root:" >&2
  # Log file names only, not values
  echo "$HITS" | cut -d: -f1 | sort -u | while read -r f; do echo "  HIT file: $f" >&2; done
  echo "$HITS" | cut -d: -f1 | sort -u > "$TWIN_ROOT/.quarantined"
  echo "Quarantined: wrote $TWIN_ROOT/.quarantined (hit files, values not logged)" >&2
  # Also log full hits to a restricted file for operator inspection (0600)
  echo "$HITS" > "$TWIN_ROOT/.quarantined.hits"
  chmod 600 "$TWIN_ROOT/.quarantined.hits"
  exit 2
fi

# Clean quarantine marker if previously quarantined and now clean
rm -f "$TWIN_ROOT/.quarantined" "$TWIN_ROOT/.quarantined.hits"
echo "SCAN PASS: no live-looking secrets in $TWIN_ROOT" >&2
