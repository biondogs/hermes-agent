#!/bin/bash
# twin-eval.sh — scoped model gate: one real question through glm53 via LiteLLM.
# Off by default; only this script enables the gate.
# Reads key from host file ~/.hermes/secrets/twin-eval.env at runtime (never baked).
# With gate off, `make probe` shows no route out.
# With gate on, only glm53 answers; any other model/host is refused.
# If key file missing, reports "skipped: key not provisioned" (not failure).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TWIN_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
KEY_FILE="$HOME/.hermes/secrets/twin-eval.env"

echo "=== twin eval gate ===" >&2

if [ ! -f "$KEY_FILE" ]; then
  echo "skipped: key not provisioned (no $KEY_FILE)" >&2
  echo "skipped: key not provisioned"
  exit 0
fi

# Read key at runtime, never log it
set -a
# shellcheck disable=SC1090
source "$KEY_FILE"
set +a

if [ -z "${TWIN_EVAL_LITELLM_KEY:-}" ]; then
  echo "skipped: key not provisioned (TWIN_EVAL_LITELLM_KEY empty in $KEY_FILE)" >&2
  echo "skipped: key not provisioned"
  exit 0
fi

# Ensure twin + helpers are up
if ! docker ps --format '{{.Names}}' | grep -qx "hermes-estate-twin"; then
  echo "Starting twin..." >&2
  docker compose -f "$TWIN_DIR/docker-compose.yml" up -d
  sleep 3
fi

# Run eval-gate as ephemeral container on the twin network, with key injected via env
# (not file mount, not image layer, not log). Gate only lives for this command.
LITELLM_HOST="${LITELLM_HOST:-ga01}"
LITELLM_URL="https://${LITELLM_HOST}:4000"
EVAL_MODEL="glm53"
# ga01 loopback not reachable from container; use aistack service name
if [ "$LITELLM_HOST" = "ga01" ]; then
  LITELLM_URL="https://litellm:4000"
fi

echo "Gate: forwarding to $LITELLM_URL model $EVAL_MODEL (key from $KEY_FILE, not logged)" >&2

# Egress: gate needs route to LiteLLM; attach to aistack network for outbound
# (twin itself stays only on twin-internal → probe still PASS)
EGRESS_NET="aistack_default"

# Start gate container — twin-internal for inbound (eval-gate DNS) + aistack for outbound
GATE_NAME="hermes-estate-twin-eval-gate"
docker rm -f "$GATE_NAME" 2>/dev/null || true
docker run -d --name "$GATE_NAME" \
  --network hermes-estate-twin-internal \
  --hostname eval-gate \
  -e TWIN_EVAL_LITELLM_KEY="$TWIN_EVAL_LITELLM_KEY" \
  -e EVAL_GATE_ENABLED=1 \
  -e EVAL_GATE_MODEL="$EVAL_MODEL" \
  -e LITELLM_URL="$LITELLM_URL" \
  -e EVAL_GATE_PORT=8090 \
  -v "$TWIN_DIR/../estate-steward/twin-tools:/opt/twin-tools:ro" \
  -w /opt/twin-tools \
  python:3.14-slim-trixie python3 eval_gate.py >/dev/null
docker network connect "$EGRESS_NET" "$GATE_NAME" 2>/dev/null || true

# Wait for gate to be ready
for i in 1 2 3 4 5; do
  if docker exec "$GATE_NAME" bash -c "timeout 1 bash -c 'cat < /dev/null > /dev/tcp/127.0.0.1/8090'" 2>/dev/null; then
    break
  fi
  sleep 1
done

cleanup() {
  docker rm -f "$GATE_NAME" 2>/dev/null || true
}
trap cleanup EXIT

# Run one real question through the gate from inside twin
echo "Asking gate: 'What is 2+2? Answer in one short sentence.'" >&2
RESULT=$(docker exec hermes-estate-twin bash -c "
  python3 -c '
import json, urllib.request, sys, urllib.error
url = \"http://eval-gate:8090/v1/chat/completions\"
body = json.dumps({\"model\": \"glm53\", \"messages\": [{\"role\": \"user\", \"content\": \"What is 2+2? Answer in one short sentence.\"}], \"max_tokens\": 50}).encode()
req = urllib.request.Request(url, data=body, headers={\"Content-Type\": \"application/json\"})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
        data = json.loads(raw)
        model = data.get(\"model\", \"unknown\")
        text = data[\"choices\"][0][\"message\"][\"content\"] if data.get(\"choices\") else str(data)
        print(f\"model: {model}\")
        print(f\"answer: {text[:200]}\")
        print(f\"eval ok: model={model}\")
except urllib.error.HTTPError as e:
    body = e.read().decode(errors=\"replace\")[:500]
    print(f\"eval error: HTTP {e.code}: {body}\", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f\"eval error: {type(e).__name__}: {e}\", file=sys.stderr)
    sys.exit(1)
'
" 2>&1)
RC=$?
echo "$RESULT" >&2
echo "$RESULT"

# Also verify non-allowed model is refused
echo "--- Verifying gate refuses other models ---" >&2
docker exec hermes-estate-twin bash -c "
  python3 -c '
import json, urllib.request, urllib.error
url = \"http://eval-gate:8090/v1/chat/completions\"
body = json.dumps({\"model\": \"gpt-4\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}]}).encode()
req = urllib.request.Request(url, data=body, headers={\"Content-Type\": \"application/json\"})
try:
    urllib.request.urlopen(req, timeout=5)
    print(\"FAIL: gpt-4 should have been refused\")
    exit(1)
except urllib.error.HTTPError as e:
    if e.code == 403:
        print(\"PASS: gpt-4 correctly refused (403)\")
    else:
        print(f\"FAIL: expected 403 got {e.code}\")
        exit(1)
'
" 2>&1 || true

exit $RC
