#!/usr/bin/env bash
# Setup script for simulation-workflow-assistant.
# Run from repo root: ./scripts/setup.sh [--full]
#
# --full: Also start Milvus, download papers/examples, and ingest into RAG.
#         Use this for sim_agent with documentation search.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

FULL_SETUP=false
for arg in "$@"; do
  if [[ "$arg" == "--full" ]]; then
    FULL_SETUP=true
    break
  fi
done

echo "==> Checking prerequisites"
if [[ -z "${NVIDIA_API_KEY:-}" ]]; then
  echo "Error: NVIDIA_API_KEY is not set."
  echo ""
  echo "  export NVIDIA_API_KEY=\"your_key_here\""
  echo ""
  echo "Get an API key at https://build.nvidia.com/explore/discover"
  exit 1
fi

echo "==> Building simulation-agent image"
docker build -f Dockerfile -t simulation-agent:latest .

if [[ "$FULL_SETUP" != "true" ]]; then
  echo ""
  echo "==> Done. Quick start:"
  echo "  docker compose run --rm agent"
  echo ""
  echo "For sim_agent with RAG (documentation search), run: ./scripts/setup.sh --full"
  exit 0
fi

echo ""
echo "==> Full setup: starting Milvus, OCR service, and ingesting knowledge base"
echo "    Note: ocr-vllm requires a GPU for manual ingestion."
docker compose -f docker-compose-full.yml up -d etcd minio standalone ocr-vllm

echo "==> Waiting for Milvus to be ready..."
for i in {1..60}; do
  if docker compose -f docker-compose-full.yml run --rm --no-deps agent python -c "
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
    echo "Error: Milvus did not become ready in 60s. Check: docker compose -f docker-compose-full.yml ps"
    exit 1
  fi
  sleep 2
done

echo "==> Waiting for OCR service (ocr-vllm) to be ready..."
echo "    This may take several minutes while the model loads (GPU required)."
SKIP_MANUAL_INGEST=0
for i in $(seq 1 120); do
  if curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/v1/models 2>/dev/null | grep -q 200; then
    echo "    OCR service ready"
    break
  fi
  if [ "$i" -eq 120 ]; then
    echo "Warning: OCR service did not become ready in 10 minutes. Skipping manual ingestion."
    echo "    You can run manual ingestion later: see sim_agent/README.md"
    SKIP_MANUAL_INGEST=1
    break
  fi
  sleep 5
done

echo "==> Downloading papers and examples"
docker compose -f docker-compose-full.yml run --rm --no-deps agent \
  bash -c "cd sim_agent && ./scripts/knowledge_base/download_required.sh"

echo "==> Ingesting examples into simulator_input_examples collection"
echo "    This may take a few minutes..."
docker compose -f docker-compose-full.yml run --rm --no-deps agent \
  python sim_agent/scripts/knowledge_base/ingest_opm_examples.py \
  --examples-dir sim_agent/data/knowledge_base/repos/opm-data \
  --collection-name simulator_input_examples \
  --milvus-uri http://standalone:19530 \
  --reset-collection

if [ "$SKIP_MANUAL_INGEST" -eq 0 ]; then
  echo "==> Ingesting papers into docs collection (PDF → PNG → OCR → Milvus)"
  echo "    Processes all PDFs in sim_agent/data/knowledge_base/papers/. Add your PDFs there and re-run to include them."
  echo "    This can take 15–30 minutes or more depending on PDF count/size and GPU. Please be patient."
  docker compose -f docker-compose-full.yml run --rm --no-deps -e OCR_VLLM_URLS=http://ocr-vllm:8080/v1 -e MILVUS_URI=http://standalone:19530 agent bash -c '
    cd sim_agent && ./scripts/knowledge_base/ingest_papers.sh
  '
else
  echo "==> Skipping manual ingestion (OCR service not ready)"
fi

echo ""
echo "==> Done. Start the assistant:"
echo "  docker compose -f docker-compose-full.yml run --rm agent"
echo ""
echo "Or run in background:"
echo "  docker compose -f docker-compose-full.yml up -d"
echo "  docker exec -it simulation-agent python -m orchestration_agent --interactive"
