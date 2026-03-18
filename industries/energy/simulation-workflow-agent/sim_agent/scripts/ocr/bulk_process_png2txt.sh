#!/usr/bin/env bash
# Orchestrator: discover PNGs in OCR_INPUT_DIR, split by number of vLLM URLs,
# and run one OCR client per URL (each processes its chunk in parallel).
#
# Usage:
#   ./bulk_process_png2txt.sh
#   OCR_INPUT_DIR=/path/to/pngs OCR_OUTPUT_DIR=/path/to/txt ./bulk_process_png2txt.sh
#   OCR_VLLM_URLS="http://localhost:8080/v1,http://localhost:8081/v1,..." ./bulk_process_png2txt.sh
#
# OCR_INPUT_DIR and OCR_OUTPUT_DIR override the defaults when set (e.g. inline as above).
# Worker mode (called internally): when OCR_IMAGE_LIST is set, run the client for that chunk only.
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Worker mode: process only the images in OCR_IMAGE_LIST with the single URL in OCR_VLLM_URLS
if [[ -n "${OCR_IMAGE_LIST:-}" && -f "$OCR_IMAGE_LIST" ]]; then
    exec python3 ocr_client_vllm.py "$@"
fi

# --- Orchestrator mode ---
# Honor OCR_INPUT_DIR / OCR_OUTPUT_DIR when set (overwrite defaults)
INPUT_DIR="${OCR_INPUT_DIR:-$REPO_ROOT/data/pdf2png}"
OUTPUT_DIR="${OCR_OUTPUT_DIR:-$REPO_ROOT/data/png2txt}"
URLS_STR="${OCR_VLLM_URLS:-http://localhost:8080/v1}"
# Split URLs into array (comma-separated, trimmed)
URL_ARR=()
for u in ${URLS_STR//,/ }; do
    u="${u// /}"
    [[ -n "$u" ]] && URL_ARR+=("$u")
done
NUM_URLS=${#URL_ARR[@]}

if [[ $NUM_URLS -eq 0 ]]; then
    echo "Error: OCR_VLLM_URLS is empty or invalid (e.g. http://localhost:8080/v1,http://localhost:8081/v1)" >&2
    exit 1
fi

# Discover PNGs (sorted)
mapfile -t PNG_LIST < <(find "$INPUT_DIR" -maxdepth 1 -type f -name "*.png" 2>/dev/null | sort)
TOTAL=${#PNG_LIST[@]}

if [[ $TOTAL -eq 0 ]]; then
    echo "Error: No *.png files in $INPUT_DIR" >&2
    exit 1
fi

# With one URL: single worker processes all images with OCR_MAX_WORKERS concurrent requests
CHUNK_SIZE=$(( (TOTAL + NUM_URLS - 1) / NUM_URLS ))
if [[ $NUM_URLS -eq 1 ]]; then
  echo "[run_ocr_vllm] Total images: $TOTAL | single vLLM instance | parallel requests: OCR_MAX_WORKERS (default 8)"
else
  echo "[run_ocr_vllm] Total images: $TOTAL | vLLM instances: $NUM_URLS | Chunk size: ~$CHUNK_SIZE (contiguous ranges)"
fi

# Temp dir for chunk files
CHUNK_DIR=$(mktemp -d)
trap 'rm -rf "$CHUNK_DIR"' EXIT

# Chunk i = indices [i*CHUNK_SIZE, min((i+1)*CHUNK_SIZE, TOTAL) )
for i in $(seq 0 $((NUM_URLS - 1))); do
    CHUNK_FILE="$CHUNK_DIR/chunk_$i.txt"
    START=$(( i * CHUNK_SIZE ))
    END=$(( (i + 1) * CHUNK_SIZE ))
    if [[ $END -gt $TOTAL ]]; then
        END=$TOTAL
    fi
    if [[ $START -ge $TOTAL ]]; then
        > "$CHUNK_FILE"
        continue
    fi
    > "$CHUNK_FILE"
    for j in $(seq $START $((END - 1))); do
        echo "${PNG_LIST[j]}" >> "$CHUNK_FILE"
    done
done

# Launch one client per chunk (one URL per chunk). Single URL = one process, all images, internal parallelism via OCR_MAX_WORKERS
echo "[run_ocr_vllm] Launching $NUM_URLS worker(s)..., this is gonna take a while ~15 mins, please be patient..."
for i in $(seq 0 $((NUM_URLS - 1))); do
    CHUNK_FILE="$CHUNK_DIR/chunk_$i.txt"
    CHUNK_COUNT=$(wc -l < "$CHUNK_FILE" | tr -d ' ')
    if [[ "$CHUNK_COUNT" -eq 0 ]]; then
        echo "[run_ocr_vllm] Skipping worker $((i+1)): empty chunk"
        continue
    fi
    URL="${URL_ARR[i]}"
    echo "[run_ocr_vllm] Worker $((i+1))/$NUM_URLS → $URL ($CHUNK_COUNT images)"
    (
        export OCR_IMAGE_LIST="$CHUNK_FILE"
        export OCR_VLLM_URLS="$URL"
        export OCR_INPUT_DIR="$INPUT_DIR"
        export OCR_OUTPUT_DIR="$OUTPUT_DIR"
        export OCR_WORKER_INDEX="$i"
        python3 -u ocr_client_vllm.py "$@"
    ) &
done
STARTED_MSG="[run_ocr_vllm] All workers started. Waiting for completion..."
echo "$STARTED_MSG"
wait
echo "[run_ocr_vllm] All workers finished."
