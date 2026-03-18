#!/usr/bin/env bash
# Ingest all PDFs from a directory into Milvus (docs collection).
# Add your PDFs to the papers dir, then run this script.
#
# Usage:
#   ./scripts/knowledge_base/ingest_papers.sh
#   ./scripts/knowledge_base/ingest_papers.sh --papers-dir /path/to/pdfs
#   ./scripts/knowledge_base/ingest_papers.sh --append   # add to existing collection
#
# Requires: OCR service (ocr-vllm), Milvus. Run from sim_agent/ or repo root.
# In Docker: use OCR_VLLM_URLS=http://ocr-vllm:8080/v1 (set by docker-compose).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
KB_DIR="${SIM_ROOT}/data/knowledge_base"
PAPERS_DIR="${KB_DIR}/papers"
PDF2PNG_DIR="${SIM_ROOT}/data/pdf2png"
PNG2TXT_DIR="${SIM_ROOT}/data/png2txt"
DROP_COLLECTION=true

while [[ $# -gt 0 ]]; do
  case "$1" in
    --papers-dir)
      PAPERS_DIR="$2"
      shift 2
      ;;
    --append)
      DROP_COLLECTION=false
      shift
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

cd "$SIM_ROOT"

if [[ ! -d "$PAPERS_DIR" ]]; then
  echo "Error: Papers directory not found: $PAPERS_DIR"
  exit 1
fi

PDFS=()
while IFS= read -r -d '' f; do PDFS+=("$f"); done < <(find "$PAPERS_DIR" -maxdepth 1 -type f -name "*.pdf" -print0 2>/dev/null)

if [[ ${#PDFS[@]} -eq 0 ]]; then
  echo "No PDFs found in $PAPERS_DIR"
  echo "Add PDF files to that directory, then re-run this script."
  exit 0
fi

echo "==> Found ${#PDFS[@]} PDF(s) in $PAPERS_DIR"
for f in "${PDFS[@]}"; do
  echo "    - $(basename "$f")"
done
echo ""
echo "Starting data ingestion pipeline - expect ~25-35 minutes. Good time for a coffee break!"
# Step 1: PDF -> PNG
mkdir -p "$PDF2PNG_DIR"
echo "==> Step 1/3: Converting PDFs to PNG..."
for pdf in "${PDFS[@]}"; do
  echo "    Processing $(basename "$pdf")..."
  python "$SCRIPT_DIR/../ocr/pdf_to_png.py" --input-pdf "$pdf" -o "$PDF2PNG_DIR" || true
done
echo ""

# Step 2: PNG -> TXT (OCR)
mkdir -p "$PNG2TXT_DIR"
echo "==> Step 2/3: Running OCR (PNG -> TXT)..."
echo "    This may take a while. With --full setup, OCR (ocr-vllm) is already started and ready."
OCR_SCRIPT="$SCRIPT_DIR/../ocr/bulk_process_png2txt.sh"
if [[ ! -f "$OCR_SCRIPT" ]]; then
  echo "Error: OCR script not found: $OCR_SCRIPT"
  exit 1
fi
if ! OCR_INPUT_DIR="$PDF2PNG_DIR" OCR_OUTPUT_DIR="$PNG2TXT_DIR" \
  OCR_VLLM_URLS="${OCR_VLLM_URLS:-http://localhost:8080/v1}" \
  bash "$OCR_SCRIPT"; then
  echo "Error: OCR step failed. Check that OCR_VLLM_URLS is set (e.g. http://ocr-vllm:8080/v1 in Docker) and the OCR service is reachable."#
  exit 1
fi
echo ""

# Step 3: TXT -> Milvus
echo "==> Step 3/3: Embedding and inserting into Milvus..."
DROP_FLAG=""
if [[ "$DROP_COLLECTION" == "true" ]]; then
  DROP_FLAG="--drop"
fi
if ! (cd "$SCRIPT_DIR/../milvus" && python run_milvus_pipeline.py \
  --dir "$PNG2TXT_DIR" \
  --collection docs \
  --uri "${MILVUS_URI:-http://localhost:19530}" \
  $DROP_FLAG); then
  echo "Error: Milvus pipeline failed."
  exit 1
fi

echo ""
echo "==> Done. Ingested ${#PDFS[@]} PDF(s) into docs collection."
