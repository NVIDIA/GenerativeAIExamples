<!--
  SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Customizing LLM Parameters at Runtime

The RAG API exposed by the Chain Server is OpenAI compatible.
You can access the [openapi_schema](./api_reference/openapi_schema.json) for more information.

The `/generate` API endpoint in the Chain Server of a RAG pipeline enables you to generate responses based on the provided prompts.
You can configure the behavior of the language model (LLM) dynamically at runtime by specifying various parameters in the request body.

To tailor the behavior of the language model, you can include the following parameters in the request body.

## Parameters

**temperature (number, optional)**

Description: Controls the randomness of the generated text. A higher value results in more random outputs, while a lower value makes the output more deterministic.

Range: `0.1` to `1`

Default: `0.2`

**top_p (number, optional)**

Description: Defines the cumulative probability for token selection. The top-p value determines the most likely tokens considered during sampling.

Range: `0.1` to `1`

Default: `0.7`

**max_tokens (integer, optional)**

Description: Specifies the maximum number of tokens to generate in the response. This limits the length of the generated text.

Default: `1024`

**stop (array of strings, optional)**

Description: A list of strings where the API will stop generating further tokens. The returned text does not include the stop sequences.

Default: []

## Example Request for Runtime LLM Configuration to the Generate Endpoint

```json
{
    "messages": [
        {
            "role": "user",
            "content": "Explain the key features of FastAPI."
        }
    ],
    "use_knowledge_base": true,
    "temperature": 0.3,
    "top_p": 0.8,
    "max_tokens": 150,
    "stop": ["\n"]
}
```

In the preceding example, the LLM configuration includes:

- temperature: 0.3 (moderate randomness)
- top_p: 0.8 (considers tokens with cumulative probability up to 0.8)
- max_tokens: 150 (limits response length to 150 tokens)
- stop: ["\n"] (generation stops at newline character)
