#!/usr/bin/env bash
# Provision / validate the g01-butler Topology-B pilot profile.
# Re-runnable: each phase is guarded; validation phases always run.
#
# Phases:
#   stage    — create profile dir + config.yaml + SOUL.md + .env shape (no tokens)
#   validate — config check, tools list, description, safety assertions
#
# Card: t_bd78a263. Design: docs/multi-bot-board-isolation-design-2026-10-22.md
set -euo pipefail

HERMES_HOME="${HERMES_HOST_HOME:-${HERMES_HOME:-$HOME/.hermes}}"
# (inside a profile session HERMES_HOME points at the profile home; the host root
#  is two levels up when that happens)
case "$HERMES_HOME" in
  */profiles/*) HERMES_HOME="${HERMES_HOME%/profiles/*}" ;;
esac
VPY="${VPY:-$HERMES_HOME/hermes-agent/venv/bin/python3}"
if [ ! -x "$VPY" ]; then VPY="$(command -v python3)"; fi
HERE="$(cd "$(dirname "$0")" && pwd)"
BUTLER="g01-butler"
PHASE="${1:-validate}"

case "$PHASE" in
  stage)
    "$VPY" "$HERE/provision_g01_butler.py"
    ;;
  validate)
    echo "=== hermes profile list: $BUTLER present ==="
    hermes profile list | grep -E "^\s*${BUTLER}\s" || { echo "MISSING $BUTLER"; exit 1; }
    echo "=== config check ==="
    hermes -p "$BUTLER" config check
    echo "=== tools list (expect exactly the kanban/mem/ss/web surface) ==="
    hermes -p "$BUTLER" tools list
    echo "=== description readback ==="
    hermes profile describe "$BUTLER"
    echo "=== .env shape (token redacted) ==="
    sed -E 's/(TELEGRAM_BOT_TOKEN=).*/\1<redacted>/' "$HERMES_HOME/profiles/$BUTLER/.env"
    echo "=== globals untouched ==="
    [ "$(hermes config get gateway.multiplex_profiles)" = "true" ] && echo "multiplex_profiles: true (pinned)"
    hermes config get kanban.dispatch_profiles || true   # expect null / error = unset
    hermes config get kanban.orchestrator_profile
    hermes config get kanban.default_assignee
    ;;
  *)
    echo "usage: $0 {stage|validate}" >&2; exit 2 ;;
esac
