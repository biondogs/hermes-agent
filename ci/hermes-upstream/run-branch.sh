#!/usr/bin/env bash
set -euo pipefail
# run-branch.sh — run a branch/worktree's tests inside hermes-upstream:fresh
# Usage: ci/hermes-upstream/run-branch.sh <path-to-clone-or-worktree> [pytest-args...]
# Example: ci/hermes-upstream/run-branch.sh ./hermes-board-layers
#          ci/hermes-upstream/run-branch.sh /tmp/my-worktree -- -k test_kanban
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path-to-clone-or-worktree> [pytest-args...]" >&2
  echo "  Mounts the clone into hermes-upstream:fresh with a throwaway HERMES_HOME" >&2
  echo "  and runs its tests. No host ~/.hermes is touched." >&2
  exit 2
fi

CLONE_PATH="$1"; shift
# Resolve to absolute
if [[ "$CLONE_PATH" != /* ]]; then
  CLONE_PATH="$REPO_ROOT/$CLONE_PATH"
fi
# Also handle relative to cwd
if [[ ! -d "$CLONE_PATH" ]]; then
  CLONE_PATH="$(realpath -m "$CLONE_PATH" 2>/dev/null || echo "$CLONE_PATH")"
fi
if [[ ! -d "$CLONE_PATH/.git" && ! -f "$CLONE_PATH/.git" ]]; then
  echo "ERROR: not a git clone/worktree: $CLONE_PATH" >&2
  exit 2
fi

IMAGE="${HERMES_UPSTREAM_IMAGE:-hermes-upstream:fresh}"
if ! docker image inspect "$IMAGE" --format '{{.Id}}' >/dev/null 2>&1; then
  echo "WARNING: $IMAGE not found, falling back to hermes-upstream:candidate or building" >&2
  if docker image inspect hermes-upstream:candidate --format '{{.Id}}' >/dev/null 2>&1; then
    IMAGE="hermes-upstream:candidate"
  else
    echo "ERROR: no hermes-upstream image available — run ci/hermes-upstream/rebuild.sh first" >&2
    exit 2
  fi
fi

PYTEST_ARGS=("$@")
if [[ ${#PYTEST_ARGS[@]} -eq 0 ]]; then
  # Default: fast passing subset (matches rebuild.sh gate); override: pass explicit args
  PYTEST_ARGS=(tests/hermes_cli/test_kanban_boards.py tests/hermes_cli/test_kanban_db.py tests/hermes_cli/test_kanban_cli.py tests/hermes_cli/test_kanban_core_functionality.py)
fi
# Strip leading -- if caller used `-- -k foo` form
if [[ "${PYTEST_ARGS[0]:-}" == "--" ]]; then PYTEST_ARGS=("${PYTEST_ARGS[@]:1}"); fi

echo "[run-branch] clone=$CLONE_PATH image=$IMAGE pytest=${PYTEST_ARGS[*]}"

# Throwaway HERMES_HOME via tmpfs volumes (no host mount, no persistence)
docker run --rm \
  -v "$CLONE_PATH:/opt/hermes:rw" \
  -e HERMES_HOME=/tmp/hermes-home -e HERMES_RUNTIME_DIR=/tmp/hermes-runtime \
  -e TZ=UTC -e LANG=C.UTF-8 -e PYTHONHASHSEED=0 \
  -e OPENAI_API_KEY=sk-harness-stub-not-a-secret -e OPENAI_BASE_URL=http://127.0.0.1:1/v1 \
  --network none \
  "$IMAGE" bash -c '
    pip install -q --no-deps --no-build-isolation -e /opt/hermes 2>&1 | tail -3 || true
    exec python -m pytest "$@" --tb=short -q
  ' -- "${PYTEST_ARGS[@]}"
