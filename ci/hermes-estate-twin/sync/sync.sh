#!/bin/bash
# sync.sh — main estate-twin sync. Read-only against live estate.
# Mirrors: hermes-agent checkout, ~/.hermes tree, hermes-estate repo, kanban DB snapshots.
# Then scrubs, scans, and verifies.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TWIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
TWIN_ROOT="$TWIN_DIR/twin-root"

LIVE_AGENT="${HOME}/.hermes/hermes-agent"
LIVE_HOME="${HOME}/.hermes"
LIVE_ESTATE="${HOME}/hermes-estate"

LOG="$TWIN_ROOT/sync.log"
mkdir -p "$TWIN_ROOT"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
log() { echo "[$(ts)] $*" | tee -a "$LOG" >&2; }

log "=== twin sync start ==="

# --- 1. hermes-agent checkout (git, includes all branches + hotfix commits) ---
# FIX 2026-11-06 (BR-5): live checkout is a promisor/partial clone (origin.promisor=true,
# partialclonefilter=blob:none). Direct `git fetch` from twin against the live path can
# trigger a promisor fetch to GitHub (upload-pack) which failed 2026-11-05 with
# "could not fetch 0bdfa9b137... from promisor remote". Least-invasive hardening:
# host-side `git bundle create --all` materializes exactly the objects live already has
# (no network), written to twin-root on the host bind-mount; twin then `git fetch`
# from that bundle file — a local file URL, never hitting the promisor remote. Falls
# back to direct fetch if bundle creation fails. Bundle file is reused as host-side
# sync path for treatment branches (twin has no egress, ADR-0001 internal:true).
log "sync: hermes-agent checkout"
BUNDLE="$TWIN_ROOT/.sync-bundle.bundle"
BUNDLE_OK="false"
if git -C "$LIVE_AGENT" bundle create "$BUNDLE" --all 2>&1 | tail -3 | while read -r l; do log "  bundle create: $l"; done; then
  if git -C "$LIVE_AGENT" bundle verify "$BUNDLE" 2>&1 | tail -2 | while read -r l; do log "  bundle verify: $l"; done; then
    BUNDLE_OK="true"
    log "  bundle ready: $BUNDLE (avoids promisor fetch)"
  fi
fi
if [ ! -d "$TWIN_ROOT/hermes-agent/.git" ]; then
  if [ "$BUNDLE_OK" = "true" ]; then
    git clone --no-hardlinks "$BUNDLE" "$TWIN_ROOT/hermes-agent" 2>&1 | tail -3 | while read -r l; do log "  clone from bundle: $l"; done
    git -C "$TWIN_ROOT/hermes-agent" remote set-url origin "$LIVE_AGENT" 2>/dev/null || true
    git -C "$TWIN_ROOT/hermes-agent" remote add bundle "$BUNDLE" 2>/dev/null || git -C "$TWIN_ROOT/hermes-agent" remote set-url bundle "$BUNDLE" 2>/dev/null || true
  else
    git clone --no-hardlinks "$LIVE_AGENT" "$TWIN_ROOT/hermes-agent" 2>&1 | tail -3 | while read -r l; do log "  clone: $l"; done
  fi
else
  git -C "$TWIN_ROOT/hermes-agent" remote set-url origin "$LIVE_AGENT" 2>/dev/null || true
  if [ "$BUNDLE_OK" = "true" ]; then
    git -C "$TWIN_ROOT/hermes-agent" remote add bundle "$BUNDLE" 2>/dev/null || git -C "$TWIN_ROOT/hermes-agent" remote set-url bundle "$BUNDLE" 2>/dev/null || true
    git -C "$TWIN_ROOT/hermes-agent" fetch bundle --prune 2>&1 | tail -5 | while read -r l; do log "  fetch bundle: $l"; done || log "  bundle fetch failed, trying origin"
    # Also fetch from origin as fallback for any refs bundle missed (shouldn't happen with --all)
    git -C "$TWIN_ROOT/hermes-agent" fetch origin --prune 2>&1 | tail -5 | while read -r l; do log "  fetch origin: $l"; done || true
  else
    git -C "$TWIN_ROOT/hermes-agent" fetch origin --prune 2>&1 | tail -5 | while read -r l; do log "  fetch: $l"; done
  fi
fi
# Checkout the exact live HEAD (detached or branch)
LIVE_SHA=$(git -C "$LIVE_AGENT" rev-parse HEAD)
LIVE_BRANCH=$(git -C "$LIVE_AGENT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "HEAD")
log "  live HEAD: $LIVE_SHA ($LIVE_BRANCH)"
if [ "$BUNDLE_OK" = "true" ]; then
  git -C "$TWIN_ROOT/hermes-agent" fetch bundle "+refs/heads/*:refs/heads/*" 2>&1 | tail -2 | while read -r l; do log "  fetch branches from bundle: $l"; done || true
else
  git -C "$TWIN_ROOT/hermes-agent" fetch origin "+refs/heads/*:refs/remotes/origin/*" 2>&1 | tail -2 | while read -r l; do log "  fetch branches: $l"; done || true
  git -C "$LIVE_AGENT" for-each-ref --format='%(refname)' refs/heads/ | while read -r ref; do
    branch="${ref#refs/heads/}"
    git -C "$TWIN_ROOT/hermes-agent" fetch origin "$branch:$branch" 2>&1 | tail -1 | while read -r l; do log "  fetch branch $branch: $l"; done || true
  done
fi
git -C "$TWIN_ROOT/hermes-agent" checkout --force "$LIVE_SHA" 2>&1 | tail -2 | while read -r l; do log "  checkout: $l"; done

# --- 2. hermes-estate repo ---
if [ -d "$LIVE_ESTATE/.git" ]; then
  log "sync: hermes-estate repo"
  if [ ! -d "$TWIN_ROOT/hermes-estate/.git" ]; then
    git clone --no-hardlinks "$LIVE_ESTATE" "$TWIN_ROOT/hermes-estate" 2>&1 | tail -2 | while read -r l; do log "  clone estate: $l"; done
  else
    git -C "$TWIN_ROOT/hermes-estate" remote set-url origin "$LIVE_ESTATE" 2>/dev/null || true
    git -C "$TWIN_ROOT/hermes-estate" fetch origin --prune 2>&1 | tail -2 | while read -r l; do log "  fetch estate: $l"; done
    git -C "$TWIN_ROOT/hermes-estate" checkout --force "$(git -C "$LIVE_ESTATE" rev-parse HEAD)" 2>&1 | tail -1 | while read -r l; do log "  checkout estate: $l"; done || true
  fi
else
  log "sync: hermes-estate not found at $LIVE_ESTATE, skipping"
fi

# --- 3. ~/.hermes tree via rsync with exclude list ---
log "sync: ~/.hermes tree (rsync)"
mkdir -p "$TWIN_ROOT/hermes-home"
RSYNC_EXCLUDES=()
while IFS= read -r line || [[ -n "$line" ]]; do
  [[ "$line" =~ ^#.*$ ]] && continue
  [[ -z "$line" ]] && continue
  RSYNC_EXCLUDES+=(--exclude="$line")
done < "$SCRIPT_DIR/exclude-list.txt"

rsync -a --delete --delete-excluded "${RSYNC_EXCLUDES[@]}" "$LIVE_HOME/" "$TWIN_ROOT/hermes-home/" 2>&1 | tail -5 | while read -r l; do log "  rsync: $l"; done || {
  RC=$?
  if [ "$RC" -eq 24 ]; then
    log "  rsync exit 24 (vanished files, runtime churn) — treated as OK"
  else
    log "  rsync failed exit $RC"
    exit "$RC"
  fi
}

# --- 4. Kanban DB snapshots (consistent sqlite .backup) ---
log "sync: kanban DB snapshots"
mkdir -p "$TWIN_ROOT/snapshots"
for db in "$LIVE_HOME/kanban.db" "$LIVE_HOME"/kanban/boards/*/kanban.db "$LIVE_HOME/kanban-stream-state.db"; do
  [ -f "$db" ] || continue
  # Compute snapshot path mirroring structure
  rel="${db#$LIVE_HOME/}"
  snap="$TWIN_ROOT/snapshots/$rel"
  mkdir -p "$(dirname "$snap")"
  if command -v sqlite3 &>/dev/null; then
    sqlite3 "$db" ".backup '$snap'" 2>&1 | while read -r l; do log "  snapshot $rel: $l"; done || log "  snapshot $rel failed, trying cp"
    if [ ! -f "$snap" ]; then
      cp "$db" "$snap" 2>&1 | while read -r l; do log "  cp fallback $rel: $l"; done || true
    fi
  else
    cp "$db" "$snap" 2>&1 | while read -r l; do log "  cp $rel: $l"; done || true
  fi
  log "  snapshot: $rel"
done

# --- 5. Scrub secrets ---
log "sync: scrubbing secrets"
bash "$SCRIPT_DIR/scrub.sh" "$TWIN_ROOT/hermes-home" 2>&1 | while read -r l; do log "  $l"; done

# --- 6. Scan for live-looking secrets (fails + quarantines on hit) ---
log "sync: scanning for live-looking secrets"
set +e
bash "$SCRIPT_DIR/scan.sh" "$TWIN_ROOT" 2>&1 | while read -r l; do log "  $l"; done
SCAN_RC=${PIPESTATUS[0]}
set -e
if [ "$SCAN_RC" -eq 2 ]; then
  log "SCAN FAILED — twin quarantined, not usable until scrub fixed"
  # Still verify to record quarantined state
  bash "$SCRIPT_DIR/verify.sh" "$TWIN_ROOT" 2>&1 | while read -r l; do log "  verify: $l"; done || true
  exit 2
elif [ "$SCAN_RC" -ne 0 ]; then
  log "SCAN ERROR exit $SCAN_RC"
  exit "$SCAN_RC"
fi

# --- 7. Verify ---
log "sync: verifying"
bash "$SCRIPT_DIR/verify.sh" "$TWIN_ROOT" 2>&1 | while read -r l; do log "  $l"; done

log "=== twin sync done ==="
