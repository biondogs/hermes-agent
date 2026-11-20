#!/bin/bash
# twin entrypoint — install hermes-agent from bind-mounted source, then exec CMD.
set -euo pipefail
TWIN_SRC="${HERMES_AGENT_SRC:-/opt/twin/hermes-agent}"
# Fix git ownership for bind-mounted repos
git config --global --add safe.directory /opt/twin/hermes-agent 2>/dev/null || true
git config --global --add safe.directory /opt/twin/hermes-estate 2>/dev/null || true
git config --global --add safe.directory /opt/twin/hermes-home 2>/dev/null || true
if [ -f "$TWIN_SRC/pyproject.toml" ]; then
  # Deps are baked at build time (sync/requirements-twin-runtime.txt); install only
  # the package metadata without deps so this works offline on internal:true network.
  pip install --no-cache-dir --break-system-packages --no-deps --no-build-isolation -e "$TWIN_SRC" 2>&1 | tail -3 || true
fi
# Ensure HERMES_HOME exists and is writable
mkdir -p "${HERMES_HOME:-/opt/twin/hermes-home}"
exec "$@"
