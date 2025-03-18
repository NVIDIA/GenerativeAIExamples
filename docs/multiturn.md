<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Customizing Multi-Turn Conversations

The RAG server exposes an OpenAI-compatible API, using which developers can provide custom conversation history.
For full details, see [APIs for RAG Server](./api_reference/openapi_schema_rag_server.json).

Use the `/generate` endpoint in the RAG server of a RAG pipeline to generate responses to prompts using custom conversation history.

To support multi-turn conversations, include the following parameters in the request body.


| Parameter   | Description | Type   |
|-------------|-------------|--------|
| messages | A sequence of messages that form a conversation history. Each message contains a `role` field, which can be `user`, `assistant`, or `system`, and a `content` field that contains the message text. | Array |
| use_knowledge_base | `true` to use a knowledge base; otherwise `false`. | Boolean |



### Example payload for customization

The following example payload includes a `messages` parameter that passes a custom conversation history to `/generate` endpoint for better contextual answers. You can include or change the following parameters in the request body while trying out the generate API using [this notebook](../notebooks/retriever_api_usage.ipynb).


```json
{
    "messages": [
        {
            "role": "system",
            "content": "You are an assistant that provides information about FastAPI."
        },
        {
            "role": "user",
            "content": "What is FastAPI?"
        },
        {
            "role": "assistant",
            "content": "FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints."
        },
        {
            "role": "user",
            "content": "What are the key features of FastAPI?"
        }
    ],
    "use_knowledge_base": true
}
```

[!TIP]: For better accuracy of multi-turn queries, consider [enabling query rewriting](./query_rewriter.md).