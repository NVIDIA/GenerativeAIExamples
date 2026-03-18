# Papers (PDFs for RAG)

Place PDF files here to ingest them into the simulator manual (docs) collection. The ingestion pipeline will process all PDFs in this directory.

## Usage

1. **Add your PDFs** to this directory.
2. **Run ingestion**:
   ```bash
   cd sim_agent
   ./scripts/knowledge_base/ingest_papers.sh
   ```
   Or with Docker (OCR + Milvus running):
   ```bash
   docker compose run --rm sim-agent ./scripts/knowledge_base/ingest_papers.sh
   ```

3. **Options**:
   - `--append` — Add to existing collection instead of replacing
   - `--papers-dir /path` — Use a different directory

## Default content

The OPM Flow Reference Manual is downloaded here by `download_required.sh`. You can add additional manuals, papers, or documentation as needed.
