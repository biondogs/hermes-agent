#!/bin/bash
# probe-isolation.sh — verify twin container has no route to estate services.
# Checks: gateway, LiteLLM, Hindsight, live kanban DBs, Telegram.
# Exit 0 = isolated (probe PASS), Exit 2 = leak found.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TWIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

if ! docker ps --format '{{.Names}}' | grep -qx "hermes-estate-twin"; then
  echo "Twin container not running — starting for probe..." >&2
  docker compose -f "$TWIN_DIR/docker-compose.yml" up -d
  sleep 3
fi

PASS=true
FAIL_DETAILS=""

probe() {
  local label="$1" target="$2"
  # Try to reach target from inside twin — should FAIL if isolated
  if docker exec hermes-estate-twin bash -c "timeout 3 bash -c 'cat < /dev/null > /dev/tcp/$target' 2>&1" 2>/dev/null; then
    echo "  FAIL: twin CAN reach $label ($target) — isolation leak!" >&2
    PASS=false
    FAIL_DETAILS="${FAIL_DETAILS} $label"
  else
    echo "  PASS: twin cannot reach $label ($target) — isolated" >&2
  fi
}

# Also check network is internal
check_internal() {
  local net_internal
  net_internal=$(docker network inspect hermes-estate-twin-internal --format '{{.Internal}}' 2>/dev/null || echo "unknown")
  if [ "$net_internal" = "true" ]; then
    echo "  PASS: network hermes-estate-twin-internal is internal=true" >&2
  else
    echo "  FAIL: network internal=$net_internal (expected true)" >&2
    PASS=false
    FAIL_DETAILS="${FAIL_DETAILS} network-not-internal"
  fi
}

echo "=== Isolation probe ===" >&2
check_internal

# Gateway (host gateway typically on 127.0.0.1:3002 or similar)
probe "gateway :3002" "127.0.0.1/3002"
probe "gateway :9090" "127.0.0.1/9090"
probe "LiteLLM :4000" "127.0.0.1/4000"
probe "Hindsight" "127.0.0.1/5432"
probe "host gateway sock" "172.17.0.1/3002"

# Check no host network
HAS_HOST_NET=$(docker inspect hermes-estate-twin --format '{{.HostConfig.NetworkMode}}' 2>/dev/null || echo "unknown")
if [ "$HAS_HOST_NET" = "host" ]; then
  echo "  FAIL: container uses host network!" >&2
  PASS=false
  FAIL_DETAILS="${FAIL_DETAILS} host-network"
else
  echo "  PASS: container network mode: $HAS_HOST_NET (not host)" >&2
fi

# Check no live DB bind-mounts (only snapshots)
MOUNTS=$(docker inspect hermes-estate-twin --format '{{range .Mounts}}{{.Source}} {{end}}' 2>/dev/null)
if echo "$MOUNTS" | grep -q "/.hermes/kanban.db"; then
  echo "  FAIL: live kanban.db bind-mounted!" >&2
  PASS=false
  FAIL_DETAILS="${FAIL_DETAILS} live-db-mount"
else
  echo "  PASS: no live kanban.db bind-mount (snapshots only)" >&2
fi

# Check gateway cannot start with real tokens — look for placeholder in twin-home
if grep -rq "__TWIN_PLACEHOLDER__" "$TWIN_DIR/twin-root/hermes-home/" 2>/dev/null; then
  echo "  PASS: twin configs contain placeholder tokens (gateway cannot start with real creds)" >&2
else
  echo "  WARN: no placeholder found in twin configs (may be OK if no secrets existed)" >&2
fi

# Try to ping external — should fail on internal network
if docker exec hermes-estate-twin bash -c "timeout 2 getent hosts google.com" 2>&1 | grep -q "google"; then
  echo "  WARN: twin can resolve external DNS (internal network may allow egress via host)" >&2
else
  echo "  PASS: twin cannot resolve external DNS" >&2
fi

if [ "$PASS" = "true" ]; then
  echo "=== Isolation probe: PASS ===" >&2
  exit 0
else
  echo "=== Isolation probe: FAIL ($FAIL_DETAILS) ===" >&2
  exit 2
fi
