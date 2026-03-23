#!/usr/bin/env bash
# Clean start workflow using Docker.
# Runs download + ingest inside the sim-agent container.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SIM_ROOT"

if [[ -z "${NVIDIA_API_KEY:-}" ]]; then
  echo "NVIDIA_API_KEY is not set. Export it before running:"
  echo "  export NVIDIA_API_KEY=\"your_key_here\""
  exit 1
fi

# Clean data dir first (optional: removes PDFs, opm-data to avoid large files in git)
if [[ -f data/clean_before_start.sh ]]; then
  echo "==> Cleaning data/knowledge_base"
  bash data/clean_before_start.sh
fi

echo "==> Building sim-agent and ocr-vllm images (if needed)"
docker compose build sim-agent ocr-vllm

echo "==> Starting Milvus and OCR service (etcd, minio, standalone, ocr-vllm)"
echo "    Note: ocr-vllm requires a GPU for manual ingestion."
docker compose --profile ocr up -d etcd minio standalone ocr-vllm

echo "==> Waiting for Milvus to be ready..."
for i in {1..60}; do
  if docker compose run --rm --no-deps sim-agent python -c "
from pymilvus import connections
try:
  connections.connect(host='standalone', port=19530, timeout=2)
  connections.disconnect('default')
  exit(0)
except Exception:
  exit(1)
" 2>/dev/null; then
    echo "    Milvus ready"
    break
  fi
  if [[ $i -eq 60 ]]; then
    echo "Error: Milvus did not become ready in 60s. Check: docker compose ps"
    exit 1
  fi
  sleep 2
done

echo "==> Waiting for OCR service (ocr-vllm) to be ready..."
echo "    This may take several minutes while the model loads (GPU required)."
for i in {1..120}; do
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/v1/models 2>/dev/null | grep -q 200; then
    echo "    OCR service ready"
    break
  fi
  if [[ $i -eq 120 ]]; then
    echo "Warning: OCR service did not become ready in 10 minutes. Skipping manual ingestion."
    echo "    You can run manual ingestion later: see sim_agent/README.md"
    SKIP_MANUAL_INGEST=1
    break
  fi
  sleep 5
done

echo "==> Downloading papers and examples (inside container)"
docker compose run --rm --no-deps sim-agent \
  bash -c "./scripts/knowledge_base/download_required.sh"

echo "==> Ingesting examples into simulator_input_examples"
echo "    This may take a few minutes..."
docker compose run --rm --no-deps sim-agent \
  python scripts/knowledge_base/ingest_opm_examples.py \
  --examples-dir data/knowledge_base/repos/opm-data \
  --collection-name simulator_input_examples \
  --milvus-uri http://standalone:19530 \
  --reset-collection

if [[ "${SKIP_MANUAL_INGEST:-0}" != "1" ]]; then
  echo "==> Ingesting papers into docs collection (PDF → PNG → OCR → Milvus)"
  echo "    Processes all PDFs in data/knowledge_base/papers/. Add your PDFs there and re-run to include them."
  echo "    This can take 15–30 minutes or more depending on PDF count/size and GPU. Please be patient."
  docker compose run --rm --no-deps sim-agent bash -c '
    ./scripts/knowledge_base/ingest_papers.sh
  '
else
  echo "==> Skipping manual ingestion (OCR service not ready)"
fi

echo "==> Verifying collections"
docker compose run --rm --no-deps sim-agent python - <<'PY'
from pymilvus import connections, Collection
connections.connect("default", host="standalone", port=19530)
for coll in ("simulator_input_examples", "docs"):
    try:
        n = Collection(coll).num_entities
        print(f"  {coll}: {n} entities")
    except Exception as e:
        print(f"  {coll}: (not found or error: {e})")
PY

echo ""
echo "==> Done. Start the assistant:"
echo "  docker compose --profile ocr up -d"
echo "  docker exec -it sim-agent bash"
echo "  python -m simulator_agent --interactive"
