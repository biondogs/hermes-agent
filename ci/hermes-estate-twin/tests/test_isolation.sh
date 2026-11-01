#!/bin/bash
# test_isolation.sh — isolation probe test (wraps probe-isolation.sh with assertions)
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TWIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Isolation probe test ==="

# Check compose file declares internal network
if grep -q "internal: true" "$TWIN_DIR/docker-compose.yml"; then
  echo "  PASS: compose declares internal: true"
else
  echo "  FAIL: compose missing internal: true" >&2
  exit 1
fi

# Check no host network mode
if grep -q "network_mode: host" "$TWIN_DIR/docker-compose.yml"; then
  echo "  FAIL: compose uses host network!" >&2
  exit 1
else
  echo "  PASS: compose does not use host network"
fi

# Check no live DB bind-mounts in compose
if grep -q "\.hermes/kanban.db" "$TWIN_DIR/docker-compose.yml"; then
  echo "  FAIL: compose bind-mounts live kanban.db" >&2
  exit 1
else
  echo "  PASS: compose does not bind-mount live kanban.db"
fi

# Check no ports published
if grep -q "ports:" "$TWIN_DIR/docker-compose.yml"; then
  echo "  FAIL: compose publishes ports" >&2
  exit 1
else
  echo "  PASS: compose publishes no ports"
fi

# If container is running, do live probe
if docker ps --format '{{.Names}}' 2>/dev/null | grep -qx "hermes-estate-twin"; then
  echo "  container running — live probe:"
  bash "$TWIN_DIR/scripts/probe-isolation.sh" 2>&1
  echo "  live probe done"
else
  echo "  container not running — static checks only (run 'make up' then re-test for live probe)"
fi

# Verify gateway cannot start with real tokens: check placeholder in twin
if [ -d "$TWIN_DIR/twin-root/hermes-home" ]; then
  if grep -rq "__TWIN_PLACEHOLDER__" "$TWIN_DIR/twin-root/hermes-home" 2>/dev/null; then
    echo "  PASS: twin configs contain placeholder (gateway cannot start with real tokens)"
  else
    echo "  INFO: no placeholder in twin configs (may be OK if no secrets to scrub)"
  fi
fi

echo "=== Isolation test: PASS ==="
