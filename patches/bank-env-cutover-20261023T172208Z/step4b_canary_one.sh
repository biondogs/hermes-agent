#!/bin/bash
# Remaining canary probes (continuation of step 4)
set -u
OUT=/home/arch/kanban-backups/env-bank-cutover-20261023T172208Z
probe() {
  local profile="$1" bank="$2" marker="$3" envname="$4"
  echo "=== $profile -> $bank ($marker)" | tee -a "$OUT/canary-probe-log.txt"
  env -i HOME=/home/arch USER=arch PATH=/home/arch/.local/bin:/usr/local/bin:/usr/bin:/bin \
    LANG=C.UTF-8 TERM=dumb \
    hermes -p "$profile" chat -q \
    "Please remember this fact permanently: ENV-BANK-CUTOVER canary marker $marker — canary verification for the $bank ($envname) memory bank cutover on 2026-10-23. Reply with only: canary noted" \
    >> "$OUT/canary-probe-log.txt" 2>&1
  echo "--- exit=$? for $profile" | tee -a "$OUT/canary-probe-log.txt"
}
probe "$1" "$2" "$3" "$4"
