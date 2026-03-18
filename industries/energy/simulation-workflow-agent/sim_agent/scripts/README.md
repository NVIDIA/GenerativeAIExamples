# Scripts

Organized by purpose:

## knowledge_base/

Download and ingest knowledge base assets.

| Script | Purpose |
|--------|---------|
| `download_required.sh` | One-shot: OPM Flow manual PDF + opm-data repo |
| `download_opm_flow_manual.py` | Download OPM Flow Reference Manual (PDF) |
| `download_opm_data.py` | Fetch opm-data repo (zip from GitHub) |
| `ingest_opm_examples.py` | Ingest simulator input files into Milvus `simulator_input_examples` collection |
| `ingest_papers.sh` | Ingest all PDFs from `data/knowledge_base/papers/` into Milvus `docs` collection (PDF→PNG→OCR→embed) |

## ocr/

PDF → PNG → TXT pipeline (vLLM-based OCR).

| Script | Purpose |
|--------|---------|
| `pdf_to_png.py` | Split large PDF into per-page PNGs |
| `bulk_process_png2txt.sh` | Bulk OCR: PNGs → TXT via vLLM (parallel workers) |
| `ocr_client_vllm.py` | OCR client (OpenAI-compatible vLLM API) |
| `test_vllm_ocr.py` | Test OCR endpoint |

Run from sim_agent root, e.g. `./scripts/ocr/bulk_process_png2txt.sh`.

## milvus/

PDF text → Milvus vector DB pipeline (for `simulator_manual` / docs collection).

| Script | Purpose |
|--------|---------|
| `run_milvus_pipeline.py` | Full pipeline: txt files → embed → Milvus |
| `milvus_preprocess_pipeline.py` | Document preprocessing |
| `nvidia_embedding.py` | NVIDIA embedding model |
| `llm_extract_metadata.py` | LLM-based metadata extraction |
| `extract_capitalized_words.py` | Fast ALL-CAPS keyword extraction |

## Root

| Script | Purpose |
|--------|---------|
| `clean_start.sh` | Full setup: download + ingest + verify (Docker) |
| `run_agent_tests.py` | Run agent test suite |
