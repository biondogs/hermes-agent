#!/usr/bin/env bash
set -euo pipefail
# rebuild.sh — pull upstream main → build dated image → test → gate fresh/last-green
# Usage: ./rebuild.sh [--keep N]  (default keep=7 dated images)
# Writes: STATUS.md, status.json next to this script. Always writes — green or red.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
UPSTREAM_CLONE="$REPO_ROOT/hermes-board-layers"
KEEP=7
if [[ "${1:-}" == "--keep" ]]; then KEEP="${2:-7}"; fi
# Env override
KEEP="${HERMES_UPSTREAM_KEEP:-$KEEP}"

TIMESTAMP="$(date -u +%Y%m%d-%H%M%S)"
DATE_TAG="$(date -u +%Y%m%d)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.yml"
STATUS_JSON="$SCRIPT_DIR/status.json"
STATUS_MD="$SCRIPT_DIR/STATUS.md"

log() { echo "[rebuild $TIMESTAMP] $*"; }

# --- 1. Fetch upstream main ---
log "Fetching origin/main in $UPSTREAM_CLONE"
if [[ ! -d "$UPSTREAM_CLONE/.git" ]]; then
  log "ERROR: no clone at $UPSTREAM_CLONE"
  exit 2
fi
git -C "$UPSTREAM_CLONE" fetch origin main --prune 2>&1 | tail -5 || true
UPSTREAM_SHA="$(git -C "$UPSTREAM_CLONE" rev-parse origin/main)"
UPSTREAM_SHORT="${UPSTREAM_SHA:0:7}"
UPSTREAM_MSG="$(git -C "$UPSTREAM_CLONE" log -1 --oneline origin/main)"
log "Upstream origin/main = $UPSTREAM_SHA ($UPSTREAM_MSG)"

# Ensure pyproject.toml etc. are from origin/main without losing dev/ harness files.
# Strategy: archive origin/main into a temp dir and use that as docker context if dev/ would be lost.
# Simpler: checkout origin/main but restore dev/ from feat/board-layers if it disappears.
git -C "$UPSTREAM_CLONE" checkout --detach origin/main 2>&1 | tail -3 || true
if [[ ! -f "$UPSTREAM_CLONE/dev/board-layers-harness/entrypoint.sh" ]]; then
  log "Restoring dev/board-layers-harness from feat/board-layers (not on origin/main yet)"
  git -C "$UPSTREAM_CLONE" checkout feat/board-layers -- dev/board-layers-harness/entrypoint.sh 2>&1 | tail -3 || true
  # Ensure entrypoint exists even if feat branch lacks it — stub it
  if [[ ! -f "$UPSTREAM_CLONE/dev/board-layers-harness/entrypoint.sh" ]]; then
    mkdir -p "$UPSTREAM_CLONE/dev/board-layers-harness"
    cat > "$UPSTREAM_CLONE/dev/board-layers-harness/entrypoint.sh" <<'EP'
#!/usr/bin/env bash
set -euo pipefail
if [ -f /opt/hermes/pyproject.toml ]; then pip install -q --no-deps -e /opt/hermes 2>&1 | tail -3 || true; fi
mkdir -p "${HERMES_HOME:-/tmp/hermes-home}" "${HERMES_RUNTIME_DIR:-/tmp/hermes-runtime}"
exec "$@"
EP
    chmod +x "$UPSTREAM_CLONE/dev/board-layers-harness/entrypoint.sh"
  fi
fi

DATED_TAG="hermes-upstream:${DATE_TAG}-${UPSTREAM_SHORT}"
CANDIDATE_TAG="hermes-upstream:candidate"

# --- 2. Build ---
log "Building $DATED_TAG (also $CANDIDATE_TAG)"
BUILD_LOG="$(mktemp)"
set +e
docker build \
  -f "$SCRIPT_DIR/Dockerfile" \
  -t "$DATED_TAG" -t "$CANDIDATE_TAG" \
  "$UPSTREAM_CLONE" 2>&1 | tee "$BUILD_LOG"
BUILD_RC=${PIPESTATUS[0]}
set -e

if [[ $BUILD_RC -ne 0 ]]; then
  log "BUILD FAILED (rc=$BUILD_RC)"
  BUILD_RESULT="build_failed"
  TESTS_PASSED=0
  TESTS_FAILED=0
  TESTS_TOTAL=0
else
  log "Build OK"
  BUILD_RESULT="build_ok"

  # --- 3. Test inside container ---
  log "Running test suite in $CANDIDATE_TAG"
  TEST_LOG="$(mktemp)"
  set +e
  # Use same command as harness-test: kanban board + cron kanban subset + a smoke of the suite
  # For gating we run the fast subset; full suite is too slow for nightly default.
  docker run --rm \
    -v "$UPSTREAM_CLONE:/opt/hermes:rw" \
    -e HERMES_HOME=/tmp/hermes-home -e HERMES_RUNTIME_DIR=/tmp/hermes-runtime \
    -e TZ=UTC -e LANG=C.UTF-8 -e PYTHONHASHSEED=0 \
    -e OPENAI_API_KEY=sk-harness-stub-not-a-secret -e OPENAI_BASE_URL=http://127.0.0.1:1/v1 \
    --network none \
    "$CANDIDATE_TAG" bash -c '
      pip install -q --no-deps --no-build-isolation -e /opt/hermes 2>&1 | tail -3 || true
      PYTHONPATH=/opt/hermes:$PYTHONPATH python -m pytest tests/hermes_cli/test_kanban_boards.py tests/hermes_cli/test_kanban_db.py tests/hermes_cli/test_kanban_cli.py tests/hermes_cli/test_kanban_core_functionality.py -q --tb=line 2>&1
    ' 2>&1 | tee "$TEST_LOG"
  TEST_RC=${PIPESTATUS[0]}
  set -e

  # Parse pytest summary line: "45 passed" etc.
  SUMMARY_LINE="$(grep -E '[0-9]+ passed|failed|error' "$TEST_LOG" | tail -1 || true)"
  TESTS_PASSED="$(echo "$SUMMARY_LINE" | grep -oP '\d+(?= passed)' || echo 0)"
  TESTS_FAILED="$(echo "$SUMMARY_LINE" | grep -oP '\d+(?= failed)' || echo 0)"
  TESTS_TOTAL="$(( ${TESTS_PASSED:-0} + ${TESTS_FAILED:-0} ))"
  # Handle case where TESTS_FAILED is empty (no failures line)
  [[ -z "$TESTS_PASSED" ]] && TESTS_PASSED=0
  [[ -z "$TESTS_FAILED" ]] && TESTS_FAILED=0
  [[ "$TESTS_PASSED" == "0" && "$TESTS_FAILED" == "0" ]] && TESTS_TOTAL=0

  if [[ $TEST_RC -eq 0 ]]; then
    log "Tests GREEN: $SUMMARY_LINE"
    BUILD_RESULT="green"
  else
    log "Tests RED (rc=$TEST_RC): $SUMMARY_LINE"
    BUILD_RESULT="red"
  fi
fi

# --- 4. Gate tags ---
LAST_GREEN_SHA=""
LAST_GREEN_TAG=""
if docker image inspect hermes-upstream:last-green --format '{{.Id}}' >/dev/null 2>&1; then
  LAST_GREEN_TAG="hermes-upstream:last-green"
  LAST_GREEN_SHA="$(docker image inspect hermes-upstream:fresh --format '{{index .Config.Labels "org.hermes.upstream-sha"}}' 2>/dev/null || echo "")"
fi

if [[ "$BUILD_RESULT" == "green" ]]; then
  log "Tagging fresh + last-green → $DATED_TAG ($UPSTREAM_SHA)"
  docker tag "$DATED_TAG" hermes-upstream:fresh
  docker tag "$DATED_TAG" hermes-upstream:last-green
  # Label the fresh image for introspection
  # (docker tag preserves labels from the dated image; we add via a no-op tag with label if needed)
  FRESH_RESULT="pass"
else
  log "NOT tagging fresh (result=$BUILD_RESULT); fresh stays at previous green"
  FRESH_RESULT="fail"
  # Keep dated image for diagnosis even on failure
fi

# --- 5. Retention: keep last KEEP dated images ---
log "Retention: keep last $KEEP dated images"
DATED_IMAGES="$(docker images --format '{{.Repository}}:{{.Tag}} {{.CreatedAt}}' | grep -E '^hermes-upstream:20[0-9]{6}-[0-9a-f]{7}' | sort -k2 -r || true)"
TOTAL_DATED="$(echo "$DATED_IMAGES" | grep -c hermes-upstream || true)"
if [[ $TOTAL_DATED -gt $KEEP ]]; then
  TO_PRUNE="$(echo "$DATED_IMAGES" | tail -n +$((KEEP+1)) | awk '{print $1}')"
  for img in $TO_PRUNE; do
    log "Pruning old dated image $img"
    docker rmi "$img" 2>&1 | tail -1 || true
  done
fi

# --- 6. Health / drift ---
FRESH_AGE="unknown"
FRESH_SHA=""
if docker image inspect hermes-upstream:fresh --format '{{.Created}}' >/dev/null 2>&1; then
  FRESH_CREATED="$(docker image inspect hermes-upstream:fresh --format '{{.Created}}')"
  FRESH_SHA="$(docker image inspect hermes-upstream:fresh --format '{{index .Config.Labels "org.hermes.upstream-sha"}}' 2>/dev/null || echo "")"
  # Fallback: extract sha from tag suffix if label missing
  if [[ -z "$FRESH_SHA" ]]; then
    FRESH_TAG_LINE="$(docker images --format '{{.Repository}}:{{.Tag}}' | grep 'hermes-upstream:fresh' || true)"
    # Try to find a dated tag with same image ID
    FRESH_ID="$(docker image inspect hermes-upstream:fresh --format '{{.Id}}')"
    FRESH_SHA="$(docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep "$FRESH_ID" | grep -oP '20\d{6}-\K[0-9a-f]{7}' | head -1 || echo "")"
  fi
  # Age in hours
  FRESH_EPOCH="$(date -d "$FRESH_CREATED" +%s 2>/dev/null || echo 0)"
  NOW_EPOCH="$(date +%s)"
  if [[ $FRESH_EPOCH -gt 0 ]]; then
    AGE_HOURS=$(( (NOW_EPOCH - FRESH_EPOCH) / 3600 ))
    FRESH_AGE="${AGE_HOURS}h (created $FRESH_CREATED)"
  else
    FRESH_AGE="$FRESH_CREATED"
  fi
fi

# Drift: commits since last green (if we can determine fresh sha)
DRIFT="unknown"
if [[ -n "$FRESH_SHA" && -n "$UPSTREAM_SHA" ]]; then
  DRIFT_COUNT="$(git -C "$UPSTREAM_CLONE" rev-list --count "${FRESH_SHA}..origin/main" 2>/dev/null || echo "?")"
  DRIFT="${DRIFT_COUNT} commits since fresh (${FRESH_SHA:0:7}..${UPSTREAM_SHA:0:7})"
elif [[ -n "$UPSTREAM_SHA" ]]; then
  DRIFT="fresh sha unknown; upstream is ${UPSTREAM_SHORT}"
fi

# --- 7. Write STATUS ---
cat > "$STATUS_JSON" <<JSON
{
  "timestamp": "$TIMESTAMP",
  "upstream_sha": "$UPSTREAM_SHA",
  "upstream_short": "$UPSTREAM_SHORT",
  "upstream_subject": $(printf '%s' "$UPSTREAM_MSG" | python3 -c "import json,sys;print(json.dumps(sys.stdin.read().strip()))"),
  "dated_tag": "$DATED_TAG",
  "result": "$BUILD_RESULT",
  "fresh_result": "$FRESH_RESULT",
  "tests_passed": ${TESTS_PASSED:-0},
  "tests_failed": ${TESTS_FAILED:-0},
  "tests_total": ${TESTS_TOTAL:-0},
  "fresh_age": $(printf '%s' "$FRESH_AGE" | python3 -c "import json,sys;print(json.dumps(sys.stdin.read()))"),
  "fresh_sha": "$FRESH_SHA",
  "drift": $(printf '%s' "$DRIFT" | python3 -c "import json,sys;print(json.dumps(sys.stdin.read()))"),
  "build_rc": $BUILD_RC,
  "keep": $KEEP
}
JSON

HEALTH_ICON="✅"
HEALTH_NOTE="fresh is green"
if [[ "$BUILD_RESULT" != "green" ]]; then
  HEALTH_ICON="❌"
  HEALTH_NOTE="last build $BUILD_RESULT — fresh unchanged"
fi
# Staleness warning
if [[ "$FRESH_AGE" == *"h ("* ]]; then
  AGE_H="$(echo "$FRESH_AGE" | grep -oP '^\d+' || echo 0)"
  if [[ $AGE_H -gt 72 ]]; then
    HEALTH_ICON="⚠️"
    HEALTH_NOTE="$HEALTH_NOTE; fresh is stale (${AGE_H}h old)"
  fi
fi

cat > "$STATUS_MD" <<MD
# hermes-upstream — STATUS

_Last rebuild: $TIMESTAMP UTC · upstream \`$UPSTREAM_SHA\`_

| Field | Value |
|-------|-------|
| Upstream SHA | \`$UPSTREAM_SHA\` (\`$UPSTREAM_SHORT\`) |
| Subject | $UPSTREAM_MSG |
| Dated tag | \`$DATED_TAG\` |
| Result | **$BUILD_RESULT** ($FRESH_RESULT) |
| Tests | ${TESTS_PASSED:-0} passed / ${TESTS_FAILED:-0} failed (total ${TESTS_TOTAL:-0}) |
| Fresh age | $FRESH_AGE |
| Fresh SHA | \`${FRESH_SHA:-unknown}\` |
| Drift | $DRIFT |
| Keep | $KEEP dated images |

## Health

$HEALTH_ICON $HEALTH_NOTE

- \`hermes-upstream:fresh\` — stable tag for CI (only updated on green).
- \`hermes-upstream:last-green\` — previous green (same as fresh after a green build).
- Dated tag \`$DATED_TAG\` always exists (even on red) for diagnosis.
- On failure, check \`$STATUS_JSON\` and \`docker logs\` / build log above.

## Retention

Last $KEEP dated images kept; older pruned on each rebuild. \`fresh\`/\`last-green\` are never pruned.

## Manual trigger

\`\`\`bash
./ci/hermes-upstream/rebuild.sh
# or
systemctl --user start hermes-upstream-rebuild.service
\`\`\`
MD

log "Wrote $STATUS_JSON and $STATUS_MD"
log "Done: result=$BUILD_RESULT fresh_result=$FRESH_RESULT tests=${TESTS_PASSED:-0}/${TESTS_FAILED:-0}"

# Exit 0 even on red — the artifact IS the signal. Caller checks STATUS.md.
exit 0
