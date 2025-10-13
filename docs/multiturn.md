<!--
  SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Supporting Multi-Turn Conversations

The RAG API exposed by the Chain Server is OpenAI compatible.
You can access the [openapi_schema](./api_reference/openapi_schema.json) for more information.

The `/generate` API endpoint in the Chain Server of a RAG pipeline enables you to generate responses based on the provided prompts.
To support multi-turn conversations, the request body must include a sequence of messages that represent the conversation history.

## Parameters

**messages (array of Message objects, required)**

Description: A list of messages comprising the conversation so far. Each message should have a role and content.

* role (string, required): The role of the message, such as `user`, `assistant`, or `system`.
* content (string, required): The content of the message.

**use_knowledge_base (boolean, required)**

Description: Whether to use a knowledge base.

Default: False

### Example Request for Multi-Turn Conversations to the Generate Endpoint

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

In the preceding example, the LLM configuration includes:

- The system message sets the context for the assistant.
- The user and assistant messages form the conversation history.
- The last user message continues the conversation by asking for key features of FastAPI.
