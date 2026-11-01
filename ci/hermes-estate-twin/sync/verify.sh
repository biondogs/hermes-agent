#!/bin/bash
# verify.sh — post-sync verification: profiles, config, git sha.
# Usage: verify.sh <twin-root>
# Writes twin-root/STATUS.json and STATUS.md. Exit 0 even on check failures
# (records them in STATUS); exit 1 only on script error.
set -euo pipefail
TWIN_ROOT="${1:?usage: verify.sh <twin-root>}"
LIVE_AGENT="${HOME}/.hermes/hermes-agent"
LIVE_HOME="${HOME}/.hermes"

TWIN_AGENT="$TWIN_ROOT/hermes-agent"
TWIN_HOME="$TWIN_ROOT/hermes-home"

STATUS_JSON="$TWIN_ROOT/STATUS.json"
STATUS_MD="$TWIN_ROOT/STATUS.md"

timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
live_sha=$(git -C "$LIVE_AGENT" rev-parse HEAD 2>/dev/null || echo "unknown")
live_branch=$(git -C "$LIVE_AGENT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
twin_sha=$(git -C "$TWIN_AGENT" rev-parse HEAD 2>/dev/null || echo "unknown")
twin_branch=$(git -C "$TWIN_AGENT" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

git_match="false"
[ "$live_sha" = "$twin_sha" ] && git_match="true"

# Live profile set (from filesystem — hermes profile list has box-drawing/unicode)
live_profiles=$(ls -1 "$LIVE_HOME/profiles" 2>/dev/null | sort | tr '\n' ',' | sed 's/,$//' || echo "unknown")
live_count=$(echo "$live_profiles" | tr ',' '\n' | grep -c . || echo 0)

# Twin profile set (from twin-home directory listing)
twin_profiles=""
twin_count=0
if [ -d "$TWIN_HOME/profiles" ]; then
  twin_profiles=$(ls -1 "$TWIN_HOME/profiles" 2>/dev/null | sort | tr '\n' ',' | sed 's/,$//' || echo "")
  twin_count=$(echo "$twin_profiles" | tr ',' '\n' | grep -c . || echo 0)
fi

profiles_match="false"
[ "$live_profiles" = "$twin_profiles" ] && profiles_match="true"

# Config validation — yaml parse for each profile config
config_ok="true"
config_errors=""
if [ -d "$TWIN_HOME/profiles" ]; then
  for cfg in "$TWIN_HOME"/profiles/*/config.yaml "$TWIN_HOME/config.yaml"; do
    [ -f "$cfg" ] || continue
    if ! python3 -c "from ruamel.yaml import YAML; YAML().load(open('$cfg'))" 2>/dev/null; then
      if ! python3 -c "import yaml; yaml.safe_load(open('$cfg'))" 2>/dev/null; then
        config_ok="false"
        config_errors="${config_errors}${cfg} "
      fi
    fi
  done
  [ -z "$config_errors" ] || config_errors=$(echo "$config_errors" | xargs)
fi

# Try hermes profile list inside twin via docker if container is up
twin_hermes_profiles=""
twin_hermes_ok="unknown"
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "hermes-estate-twin"; then
  twin_hermes_profiles=$(docker exec hermes-estate-twin bash -c 'HERMES_HOME=/opt/twin/hermes-home hermes profile list 2>&1 | head -20' 2>/dev/null | awk 'NR>2 {print $1}' | sort | tr '\n' ',' | sed 's/,$//' || echo "exec-failed")
  if [ "$twin_hermes_profiles" = "$live_profiles" ]; then
    twin_hermes_ok="true"
  elif [ "$twin_hermes_profiles" = "exec-failed" ] || [ -z "$twin_hermes_profiles" ]; then
    twin_hermes_ok="unknown"
  else
    twin_hermes_ok="false"
  fi
fi

quarantined="false"
[ -f "$TWIN_ROOT/.quarantined" ] && quarantined="true"

overall="pass"
[ "$git_match" = "false" ] && overall="fail"
[ "$profiles_match" = "false" ] && overall="fail"
[ "$config_ok" = "false" ] && overall="fail"
[ "$quarantined" = "true" ] && overall="fail"

# Write STATUS.json
python3 <<PYEOF
import json, pathlib
data = {
    "timestamp": "$timestamp",
    "overall": "$overall",
    "live": {"sha": "$live_sha", "branch": "$live_branch", "profiles": "$live_profiles", "profile_count": $live_count},
    "twin": {"sha": "$twin_sha", "branch": "$twin_branch", "profiles": "$twin_profiles", "profile_count": $twin_count},
    "checks": {
        "git_match": "$git_match" == "true",
        "profiles_match": "$profiles_match" == "true",
        "config_ok": "$config_ok" == "true",
        "config_errors": "$config_errors",
        "twin_hermes_profiles": "$twin_hermes_profiles",
        "twin_hermes_ok": "$twin_hermes_ok",
        "quarantined": "$quarantined" == "true",
    }
}
pathlib.Path("$STATUS_JSON").write_text(json.dumps(data, indent=2) + "\n")
print(f"Wrote {len(json.dumps(data))} bytes to $STATUS_JSON")
PYEOF

# Write STATUS.md
cat > "$STATUS_MD" <<MDEOF
# Estate Twin STATUS — $timestamp

**Overall:** \`${overall^^}\`

| Check | Result | Detail |
|-------|--------|--------|
| git sha match | $git_match | live \`$live_sha\` ($live_branch) vs twin \`$twin_sha\` ($twin_branch) |
| profile set | $profiles_match | live $live_count profiles, twin $twin_count profiles |
| config parse | $config_ok | ${config_errors:-ok} |
| hermes in twin | $twin_hermes_ok | ${twin_hermes_profiles:-n/a} |
| quarantined | $quarantined | ${quarantined:+scanner hit — see .quarantined} |

Live profiles: \`$live_profiles\`
Twin profiles: \`$twin_profiles\`
MDEOF

echo "STATUS: overall=$overall git_match=$git_match profiles_match=$profiles_match config_ok=$config_ok quarantined=$quarantined" >&2
cat "$STATUS_JSON" >&2
