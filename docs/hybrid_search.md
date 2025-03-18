# Enable hybrid search support
Hybrid search enables higher accuracy for documents having more domain specific technical jargons. It combines sparse and dense representations to leverage the strengths of both retrieval methods—sparse models (e.g., BM25) excel at keyword matching, while dense embeddings (e.g., vector-based search) capture semantic meaning. This allows hybrid search to retrieve relevant documents even when technical jargon or synonyms are used.

Once you have followed [steps in quick start guide](./quickstart.md#deploy-with-docker-compose) to launch the blueprint, to enable hybrid search support for Milvus Vector Database, developers can follow below steps:

# Steps

1. Set the search type to `hybrid`
   ```bash
   export APP_VECTORSTORE_SEARCHTYPE="hybrid"
   ```

2. Relaunch the rag and ingestion services
   ```bash
   docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

**📝 Note:**
Preexisting collections in Milvus created using search type `dense` won't work, when the search type is changed to `hybrid`. If you are switching the search type, ensure you are creating new collection and re-uploading documents before doing retrieval.