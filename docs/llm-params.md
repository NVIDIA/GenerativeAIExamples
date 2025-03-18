<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Customize LLM Parameters at Runtime

The RAG server exposes an OpenAI-compatible API, using which developers can customize different LLM parameters at runtime.
For full details, see [APIs for RAG Server](./api_reference/openapi_schema_rag_server.json).

Use the `/generate` endpoint in the RAG server of a RAG pipeline to generate responses to prompts.

To configure the behavior of the LLM dynamically at runtime, you can include or change the following parameters in the request body while trying out the generate API using [the notebook](../notebooks/retriever_api_usage.ipynb).

| Parameter   | Description | Type   | Valid Values | Default | Optional? |
|-------------|-------------|--------|--------------|---------|-----------|
| max_tokens | The maximum number of tokens to generate during inference. This limits the length of the generated text. | Integer | — | 1024 | Yes       |
| stop | A list of strings to use as stop tokens in the text generation. The text returned does not include the stop tokens. | Array | — | [] | Yes       |
| temperature | Adjusts the randomness of token selection. Higher values increase randomness and creativity; lower values promote deterministic and conservative output. | Number | 0.1 - 1.0 | 0.2 | Yes       |
| top_p | A threshold that selects from the most probable tokens until the cumulative probability exceeds p. | Number | 0.1 - 1.0 | 0.7 | Yes       |



## Example payload for customization

You can include or change the following parameters in the request body while trying out the generate API using [this notebook](../notebooks/retriever_api_usage.ipynb).

- max_tokens=150 — limits response length to 150 tokens
- stop=["\n"] — generation stops at the newline character
- temperature=0.3 — moderate randomness
- top_p=0.8 — considers tokens with cumulative probability up to 0.8

```json
{
   "messages": [
      {
         "role": "user",
         "content": "Explain the key features of FastAPI."
      }
   ],
   "max_tokens": 150,
   "stop": ["\n"],
   "temperature": 0.3,
   "top_p": 0.8,
   "use_knowledge_base": true
}
```
