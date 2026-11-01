#!/bin/bash
# scrub.sh — replace secret values with placeholders per scrub-rules.yaml.
# Usage: scrub.sh <twin-root/hermes-home>
# Never logs secret VALUES, only key names and file paths.
set -euo pipefail
TWIN_HOME="${1:?usage: scrub.sh <twin_hermes_home>}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PLACEHOLDER="__TWIN_PLACEHOLDER__"

scrub_env_file() {
  local f="$1"
  # Replace every non-empty, non-comment value with placeholder
  # Keep keys and structure, drop values.
  local tmp
  tmp=$(mktemp)
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^[[:space:]]*# ]] || [[ "$line" =~ ^[[:space:]]*$ ]]; then
      echo "$line" >> "$tmp"
    elif [[ "$line" =~ ^([^=]+)=(.*) ]]; then
      local key="${BASH_REMATCH[1]}"
      local val="${BASH_REMATCH[2]}"
      if [[ -n "$val" && "$val" != "$PLACEHOLDER" ]]; then
        echo "${key}=${PLACEHOLDER}" >> "$tmp"
        echo "  scrub: $f key=$key" >&2
      else
        echo "$line" >> "$tmp"
      fi
    else
      echo "$line" >> "$tmp"
    fi
  done < "$f"
  mv "$tmp" "$f"
}

scrub_yaml_keys() {
  local f="$1"
  # Replace values for known secret keys in YAML (simple line-based, preserves structure)
  # Matches: key: value  or  key: "value"  with common secret key names
  local secret_keys="LITELLM_MASTER_KEY|TELEGRAM_BOT_TOKEN|ANTHROPIC_API_KEY|OPENAI_API_KEY|GITHUB_TOKEN|HF_TOKEN|api_key|bot_token|bearer_token|kubeconfig|api_keys|ANTHROPIC_AUTH_TOKEN|OPENROUTER_API_KEY"
  local tmp
  tmp=$(mktemp)
  # Use python for correct YAML handling if available, else sed fallback
  if python3 -c "import ruamel.yaml" 2>/dev/null; then
    python3 - "$f" "$tmp" "$PLACEHOLDER" <<PYEOF
import sys
from ruamel.yaml import YAML
from pathlib import Path

src, dst, placeholder = sys.argv[1], sys.argv[2], sys.argv[3]
secret_keys = {"LITELLM_MASTER_KEY","TELEGRAM_BOT_TOKEN","ANTHROPIC_API_KEY","OPENAI_API_KEY","GITHUB_TOKEN","HF_TOKEN","api_key","bot_token","bearer_token","kubeconfig","api_keys","ANTHROPIC_AUTH_TOKEN","OPENROUTER_API_KEY","token","secret","password"}

yaml = YAML()
yaml.preserve_quotes = True
try:
    data = yaml.load(Path(src).read_text())
except Exception as e:
    # Not valid YAML or empty — fall back to line scrub
    print(f"  scrub: {src} not valid YAML ({e}), using line scrub", file=sys.stderr)
    import re, shutil
    text = Path(src).read_text()
    sk_pat = "|".join(re.escape(k) for k in secret_keys)
    def repl(m):
        print(f"  scrub: {src} key={m.group(1)}", file=sys.stderr)
        return f"{m.group(1)}: \"{placeholder}\""
    text = re.sub(rf'^(\s*(?:{sk_pat})\s*:\s*).*$', repl, text, flags=re.MULTILINE)
    Path(dst).write_text(text)
    sys.exit(0)

def scrub_obj(obj, path=""):
    if isinstance(obj, dict):
        for k, v in list(obj.items()):
            if k in secret_keys and v not in (None, "", placeholder):
                print(f"  scrub: {src} key={path}.{k}" if path else f"  scrub: {src} key={k}", file=sys.stderr)
                obj[k] = placeholder
            elif isinstance(v, (dict, list)):
                scrub_obj(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for item in obj:
            if isinstance(item, (dict, list)):
                scrub_obj(item, path)

if data is not None:
    scrub_obj(data)
    with open(dst, 'w') as out:
        yaml.dump(data, out)
else:
    Path(dst).write_text(Path(src).read_text())
PYEOF
    mv "$tmp" "$f"
  else
    # Fallback: line-based sed for known keys
    while IFS= read -r line || [[ -n "$line" ]]; do
      if echo "$line" | grep -qE "^\s*(LITELLM_MASTER_KEY|TELEGRAM_BOT_TOKEN|ANTHROPIC_API_KEY|OPENAI_API_KEY|GITHUB_TOKEN|HF_TOKEN|api_key|bot_token)\s*:"; then
        local key
        key=$(echo "$line" | sed -E 's/^\s*([^:]+)\s*:.*/\1/' | xargs)
        echo "  scrub: $f key=$key" >&2
        echo "$line" | sed -E "s/^(\s*[^:]+\s*:\s*).*/\1\"${PLACEHOLDER}\"/" >> "$tmp"
      else
        echo "$line" >> "$tmp"
      fi
    done < "$f"
    mv "$tmp" "$f"
  fi
}

# --- Main: walk twin-home for files that need scrubbing ---

# 1. All .env files (any depth)
while IFS= read -r -d '' envfile; do
  scrub_env_file "$envfile"
done < <(find "$TWIN_HOME" -name ".env" -type f -print0 2>/dev/null)

# 2. config.yaml files
while IFS= read -r -d '' cfg; do
  scrub_yaml_keys "$cfg"
done < <(find "$TWIN_HOME" -name "config.yaml" -type f -print0 2>/dev/null)

# 3. auth.json — replace with minimal placeholder that still parses
while IFS= read -r -d '' aj; do
  echo "  scrub: $aj (replaced with placeholder)" >&2
  echo '{"_twin_placeholder": true, "_note": "scrubbed — real auth.json never enters twin"}' > "$aj"
done < <(find "$TWIN_HOME" -name "auth.json" -type f -print0 2>/dev/null)

# 4. Any file that literally contains a canary/secret marker left by accident
# (belt-and-suspenders — scan.sh will also catch it)

echo "Scrub complete for $TWIN_HOME" >&2
