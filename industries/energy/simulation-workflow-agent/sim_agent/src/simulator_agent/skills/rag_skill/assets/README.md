# Assets Directory

This directory contains static resources for the OPM RAG skill.

## Vector Database

The vector database containing embedded OPM manual and examples is managed separately
via `scripts/knowledge_base/ingest_opm_examples.py` (run from repo root). Vector DB setup is handled by docker-compose (e.g. docker compose --profile ocr).

## Manual Files

OPM Flow manual PDFs and extracted text are stored in the knowledge base.
See the main project documentation for vector database setup instructions.

