#!/usr/bin/env bash
# PROPOSED (review-only, not installed). Weekly capacity snapshot of /mnt/models on gpu417.
#
# Writes (1) a timestamped TSV receipt and (2) a node-exporter textfile-collector
# .prom file, so the Prometheus/Grafana stack sees the per-tree sizes even though
# node_filesystem_* only gives whole-mount totals.
#
# Suggested cron (root, on gpu417), NOT installed:
#   17 3 * * 0  /usr/local/sbin/models-capacity-snapshot.sh >>/var/log/models-capacity-snapshot.log 2>&1
#
# ASSUMPTIONS to confirm before install (no cluster access in this exercise):
#   RECEIPT_DIR  - placeholder; point it at wherever receipts are already kept.
#                  It MUST NOT be on the /mnt/models filesystem (guarded below).
#   TEXTFILE_DIR - must match node-exporter --collector.textfile.directory
#                  (a hostPath, never pod-ephemeral storage; see PROPOSAL.md s5).
set -euo pipefail

MODELS_DIR="${MODELS_DIR:-/mnt/models}"
RECEIPT_DIR="${RECEIPT_DIR:-/var/lib/receipts/models-capacity}"       # ASSUMPTION
TEXTFILE_DIR="${TEXTFILE_DIR:-/var/lib/node_exporter/textfile}"       # ASSUMPTION
DEPTH="${DEPTH:-2}"          # 2 => hf/rnd5-muse-spark, hf/<other>, etc. Keeps label cardinality small.
HOST="$(hostname -s)"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
EPOCH="$(date -u +%s)"

# One run at a time.
exec 9>"/run/models-capacity-snapshot.lock"
flock -n 9 || { echo "another snapshot running; exiting" >&2; exit 0; }

# Refuse to write receipts onto the filesystem we are monitoring.
models_dev="$(stat -c %d "$MODELS_DIR")"
mkdir -p "$RECEIPT_DIR" "$TEXTFILE_DIR"
[ "$(stat -c %d "$RECEIPT_DIR")" != "$models_dev" ] || {
  echo "RECEIPT_DIR is on the monitored filesystem; refusing" >&2; exit 1; }

# df numbers; kubelet computes imagefs.available/capacity, so use avail (not free).
read -r size used avail < <(df -B1 --output=size,used,avail "$MODELS_DIR" | tail -n1)
used_ratio="$(awk -v s="$size" -v a="$avail" 'BEGIN{printf "%.4f", 1 - a/s}')"

receipt="$RECEIPT_DIR/models-capacity-${HOST}-${TS}.tsv"
tmp_receipt="$(mktemp "$RECEIPT_DIR/.tmp.XXXXXX")"
tmp_prom="$(mktemp "$TEXTFILE_DIR/.tmp.XXXXXX")"
trap 'rm -f "$tmp_receipt" "$tmp_prom"' EXIT

# du: -x stay on this fs, apparent size off (real blocks), bytes. Low priority: tree is huge.
du_out="$(nice -n 19 ionice -c3 du -x -B1 -d "$DEPTH" "$MODELS_DIR" 2>/dev/null || true)"

{
  printf '# snapshot_utc\t%s\n# host\t%s\n# mount\t%s\n' "$TS" "$HOST" "$MODELS_DIR"
  printf '# df_size_bytes\t%s\n# df_used_bytes\t%s\n# df_avail_bytes\t%s\n# used_ratio\t%s\n' \
    "$size" "$used" "$avail" "$used_ratio"
  printf 'bytes\tpath\n'
  printf '%s\n' "$du_out" | sort -rn
} >"$tmp_receipt"

esc() { sed -e 's/\\/\\\\/g' -e 's/"/\\"/g'; }

{
  echo '# HELP models_tree_bytes du size of a tree under the models mount (weekly snapshot).'
  echo '# TYPE models_tree_bytes gauge'
  printf '%s\n' "$du_out" | while IFS=$'\t' read -r bytes path; do
    [ -n "${path:-}" ] || continue
    rel="${path#"$MODELS_DIR"}"; rel="${rel:-/}"
    printf 'models_tree_bytes{mount="%s",tree="%s"} %s\n' \
      "$(printf '%s' "$MODELS_DIR" | esc)" "$(printf '%s' "$rel" | esc)" "$bytes"
  done
  echo '# HELP models_snapshot_used_ratio used ratio (1 - avail/size) at snapshot time.'
  echo '# TYPE models_snapshot_used_ratio gauge'
  printf 'models_snapshot_used_ratio{mount="%s"} %s\n' "$MODELS_DIR" "$used_ratio"
  echo '# HELP models_snapshot_timestamp_seconds unix time of last successful snapshot.'
  echo '# TYPE models_snapshot_timestamp_seconds gauge'
  printf 'models_snapshot_timestamp_seconds{mount="%s"} %s\n' "$MODELS_DIR" "$EPOCH"
} >"$tmp_prom"

# Atomic publish (same dir => rename is atomic; node-exporter only reads *.prom).
chmod 0644 "$tmp_receipt" "$tmp_prom"
mv "$tmp_receipt" "$receipt"
mv "$tmp_prom" "$TEXTFILE_DIR/models_capacity.prom"
trap - EXIT
echo "ok: $receipt used_ratio=$used_ratio"
