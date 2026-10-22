#!/usr/bin/env bash
# Provision / validate the gaudi-butler Topology-B pilot-2 profile (board gaudi)
# + g01-butler bank-isolation retrofix. Re-runnable: each phase guarded.
#
# Phases:
#   stage-gaudi   — create profile dir + config.yaml + SOUL.md + .env shape (no tokens)
#   stage-retrofit— g01-butler: hindsight/config.json (bank g01-butler) + .env bank-var scrub
#   validate      — config check, tools list, description, safety assertions, env readback
#
# Card: t_fd8ca6f0. Design: docs/multi-bot-board-isolation-design-2026-10-22.md
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
BUTLER="gaudi-butler"
PHASE="${1:-validate}"

case "$PHASE" in
  stage-gaudi)
    "$VPY" "$HERE/provision_gaudi_butler.py"
    ;;
  stage-retrofit)
    "$VPY" "$HERE/retrofit_g01_butler_bank.py"
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
    echo "=== .env shape (secrets redacted) ==="
    sed -E 's/(TELEGRAM_BOT_TOKEN=).*/\1<redacted>/; s/(LITELLM_API_KEY=).*/\1<redacted>/' \
      "$HERMES_HOME/profiles/$BUTLER/.env"
    echo "=== hindsight config (bank pin) ==="
    cat "$HERMES_HOME/profiles/$BUTLER/hindsight/config.json"
    echo "=== g01-butler retrofix state readback ==="
    grep -c '^HINDSIGHT_BANK_ID=' "$HERMES_HOME/profiles/g01-butler/.env" \
      && { echo "FAIL: g01-butler .env still pins HINDSIGHT_BANK_ID"; exit 1; } \
      || echo "ok: g01-butler .env has no HINDSIGHT_BANK_ID pin"
    cat "$HERMES_HOME/profiles/g01-butler/hindsight/config.json"
    echo "=== globals untouched ==="
    [ "$(hermes config get gateway.multiplex_profiles)" = "true" ] && echo "multiplex_profiles: true (pinned)"
    hermes config get kanban.dispatch_profiles || true   # expect null / error = unset
    hermes config get kanban.orchestrator_profile
    hermes config get kanban.default_assignee
    ;;
  *)
    echo "usage: $0 {stage-gaudi|stage-retrofit|validate}" >&2; exit 2 ;;
esac
