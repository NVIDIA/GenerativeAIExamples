#!/usr/bin/env bash
# Download minimum required PDFs and examples.
# Run from repo root or from sim_agent/.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SIM_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
KB_DIR="$SIM_ROOT/data/knowledge_base"

cd "$SIM_ROOT"

echo "==> Downloading minimum required knowledge base assets"
echo ""

# 1. OPM Flow Reference Manual (required for RAG)
echo "==> 1/2 OPM Flow Reference Manual (PDF)"
python "$SCRIPT_DIR/download_opm_flow_manual.py" -o "$KB_DIR/papers/OPM_Flow_Reference_Manual_2025-10.pdf" || true

# 2. OPM datasets (examples for RAG + runnable cases)
echo ""
echo "==> 2/2 OPM datasets (opm-data)"
python "$SCRIPT_DIR/download_opm_data.py" --data-dir "$KB_DIR" --skip-existing

# Remove examples symlink (no longer used) and SPE10_TOPLAYER from opm-data (we use data/example_cases/SPE10)
rm -f "$KB_DIR/examples" 2>/dev/null || true
rm -rf "$KB_DIR/repos/opm-data/SPE10_TOPLAYER" 2>/dev/null || true

echo ""
echo "==> Done. PDFs in $KB_DIR/papers/, examples in $KB_DIR/repos/opm-data/"
echo "    Run ingestion:"
echo "      Examples: python scripts/knowledge_base/ingest_opm_examples.py --examples-dir $KB_DIR/repos/opm-data --collection-name simulator_input_examples"
echo "      Papers:   ./scripts/knowledge_base/ingest_papers.sh  (processes all PDFs in papers/)"
