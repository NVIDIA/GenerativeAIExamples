# Best practices for common Nvidia RAG Blueprint settings

These parameters allow fine-tuning RAG performance based on specific accuracy vs. latency trade-offs. Choose the configurations based on use case needs! The default values are kept considering a balance between accuracy and performance. The default values and the environment variables controlling these settings are mentioned in (brackets)

## Retrieval and Ranking

- **Reranking model**
  - ✅ This improves accuracy by selecting better documents for response generation.
  - ❌ Increases latency due to additional processing. Additional model deployment will be needed for on-prem setting of NIMS.
  - Controlled using `ENABLE_RERANKER` environment variable. Default is on.

- **Increase VDB TOP K and reranker TOP K**
  - ✅ VDB TOP K provides a larger candidate pool for reranking, which may improve accuracy. Reranker TOP K increases the probability of relevant context being part of the top-k contexts.
  - ❌ May increase retrieval latency as the value of TOP K increases.
  - Controlled using `VECTOR_DB_TOPK` and `APP_RETRIEVER_TOPK` environment variable.

- **Use a larger LLM model**
  - ✅ Higher accuracy with better reasoning and a larger context length.
  - ❌ Slower response time and higher inference cost. Also will have a higher GPU requirement.
  - Check out [this](./change-model.md) section to understand how to switch the inference models.

- **Enable Query rewriting**
  - ✅ Enhances retrieval accuracy for multi-turn scenario by rephrasing the query.
  - ❌ Adds an extra LLM call, increasing latency.
  - Check out [this](./query_rewriter.md) section to learn more. Default is off.

- **Enable Self-reflection**
  - ✅ May improve the response quality by refining intermediate retrieval and final LLM output.
  - ❌ Significantly higher latency due to multiple iterations of LLM model call.
  - ❌ May need a seperate judge LLM model to be deployed increasing GPU requirement.
  - Check out [this](./self-reflection.md) section to learn more. Default is off.

- **Enable Hybrid search in Milvus**
  - ✅ May provide better retrieval accuracy for domain-specific content
  - ❌ May induce slightly higher latency for large number of documents; default setting is dense search.

- **Enable NeMo Guardrails**
  - ✅ Applies input/output constraints for better safety and consistency
  - ❌ Significant increased processing overhead for additional LLM calls. It always needs additional GPUs to deploy the guardrails specific models on-prem.
  - Check out [this](./nemo-guardrails.md) section to learn more. Default is off.

## Ingestion and Chunking

- **Extracting tables and charts**
  - ✅ Improves accuracy for documents having images of tables and charts.
  - ❌ Increases ingestion time. You can turn these off in case there are no images present in the ingested doc. refer to [this](./text_only_ingest.md) section.
  - Controlled via `APP_NVINGEST_EXTRACTTABLES` and `APP_NVINGEST_EXTRACTCHARTS` environment variables. Default is on for both.

- **Enable Image captioning during ingestion**
  - ✅ Enhances multimodal retrieval accuracy for documents having images.
  - ❌ Additional call to a vision-language model increases processing time during ingestion and also requires additional GPU to be available for on-prem deployment of the VLM model.
  - Check out [this](./image_captioning.md) section to learn more. Default is off.

- **Customize Chunk size**
  - ✅ Larger chunks retain more context, improving coherence
  - ❌ Larger increases embedding size, slowing retrieval
  - ❌ Longer chunks may increase latency due to larger prompt size
  - Controlled via `APP_NVINGEST_CHUNKSIZE` environment variable. Default value is 1024.

- **Customize Chunk overlap**
  - ✅ More overlap ensures smooth transitions between chunks
  - ❌ May slightly increase processing overhead
  - Controlled via `APP_NVINGEST_CHUNKOVERLAP` environment variable. Default value is 150.

These parameters allow fine-tuning RAG performance based on specific accuracy vs. latency trade-offs. Choose the configurations based on use case needs!
