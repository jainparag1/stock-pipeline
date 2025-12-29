#!/usr/bin/env bash
set -euo pipefail

# run_compaction_and_check.sh
# Wrapper to snapshot MinIO, run a compaction script, snapshot again, and assert file-count reduction.

usage() {
  cat <<EOF
Usage: $0 [--dry-run] --compaction-script PATH --base-path S3_BASE_PATH --partitions "k=v,k=v" --num-files N [--endpoint URL] [--access-key KEY] [--secret-key SECRET] [--bucket BUCKET] [--prefix PREFIX]

Flags:
  --dry-run            Show the commands that would run but don't execute compaction.
  --compaction-script  Path to your run_compaction.sh wrapper (required).
  --base-path          S3 base path (e.g. s3a://stock-data-local/streaming-output) used for compaction (required).
  --partitions         Partitions string passed to compaction script (e.g. "year=2025,month=8,day=30") (required).
  --num-files          Number of output files to compact to (required).
  --endpoint           MinIO endpoint URL (default http://localhost:9000)
  --access-key         MinIO access key (default env AWS_ACCESS_KEY_ID)
  --secret-key         MinIO secret key (default env AWS_SECRET_ACCESS_KEY)
  --bucket             MinIO bucket (default stock-data-local)
  --prefix             MinIO prefix (default streaming-output)
EOF
}

# defaults
ENDPOINT="http://localhost:9000"
ACCESS_KEY="${AWS_ACCESS_KEY_ID:-}"
SECRET_KEY="${AWS_SECRET_ACCESS_KEY:-}"
BUCKET="stock-data-local"
PREFIX="streaming-output"
DRY_RUN=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run) DRY_RUN=1; shift;;
    --compaction-script) COMP_SCRIPT="$2"; shift 2;;
    --base-path) BASE_PATH="$2"; shift 2;;
    --partitions) PARTITIONS="$2"; shift 2;;
    --num-files) NUM_FILES="$2"; shift 2;;
    --endpoint) ENDPOINT="$2"; shift 2;;
    --access-key) ACCESS_KEY="$2"; shift 2;;
    --secret-key) SECRET_KEY="$2"; shift 2;;
    --bucket) BUCKET="$2"; shift 2;;
    --prefix) PREFIX="$2"; shift 2;;
    -h|--help) usage; exit 0;;
    *) echo "Unknown arg: $1"; usage; exit 1;;
  esac
done

if [[ -z "${COMP_SCRIPT:-}" || -z "${BASE_PATH:-}" || -z "${PARTITIONS:-}" || -z "${NUM_FILES:-}" ]]; then
  echo "Missing required args" >&2
  usage
  exit 2
fi

SNAP_BEFORE=/tmp/minio_snapshot_before.json
SNAP_AFTER=/tmp/minio_snapshot_after.json

MINIO_CMD=(python3 "$(pwd)/infra/minio_compaction_check.py")
MINIO_ARGS=(--endpoint "$ENDPOINT")
if [[ -n "$ACCESS_KEY" ]]; then
  MINIO_ARGS+=(--access-key "$ACCESS_KEY")
fi
if [[ -n "$SECRET_KEY" ]]; then
  MINIO_ARGS+=(--secret-key "$SECRET_KEY")
fi
MINIO_ARGS+=(--bucket "$BUCKET" --prefix "$PREFIX")

echo "Snapshot before -> $SNAP_BEFORE"
if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN: ${MINIO_CMD[*]} snapshot ${MINIO_ARGS[*]} --out $SNAP_BEFORE"
else
  "${MINIO_CMD[@]}" snapshot "${MINIO_ARGS[@]}" --out "$SNAP_BEFORE"
fi

echo "Running compaction script: $COMP_SCRIPT $BASE_PATH $PARTITIONS $NUM_FILES"
if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN: bash $COMP_SCRIPT $BASE_PATH '$PARTITIONS' $NUM_FILES"
else
  bash "$COMP_SCRIPT" "$BASE_PATH" "$PARTITIONS" "$NUM_FILES"
fi

echo "Snapshot after -> $SNAP_AFTER"
if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN: ${MINIO_CMD[*]} snapshot ${MINIO_ARGS[*]} --out $SNAP_AFTER"
else
  "${MINIO_CMD[@]}" snapshot "${MINIO_ARGS[@]}" --out "$SNAP_AFTER"
fi

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN complete; no assertion performed."
  exit 0
fi

# run diff and fail if removed count is not positive
DIFF_OUT=$(python3 "$(pwd)/infra/minio_compaction_check.py" diff --a "$SNAP_BEFORE" --b "$SNAP_AFTER" --verbose || true)

# parse summary lines for counts
A_COUNT=$(echo "$DIFF_OUT" | awk '/Snapshot A/ {print $3}')
B_COUNT=$(echo "$DIFF_OUT" | awk '/Snapshot B/ {print $3}')

if [[ -z "$A_COUNT" || -z "$B_COUNT" ]]; then
  echo "Could not parse diff output:" >&2
  echo "$DIFF_OUT" >&2
  exit 3
fi

if (( B_COUNT >= A_COUNT )); then
  echo "Compaction assertion failed: before=$A_COUNT after=$B_COUNT" >&2
  echo "$DIFF_OUT" >&2
  exit 4
fi

echo "Compaction assertion passed: before=$A_COUNT after=$B_COUNT"
exit 0
