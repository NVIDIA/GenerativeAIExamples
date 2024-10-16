# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os

from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    perplexity_timeout: int = Field(
        default=20, description="Timeout in seconds for Perplexity API call"
    )
    source_field_name: str = Field(
        default="source_uri",
        description="Field name for source URI in document metadata",
    )
    display_field_name: str = Field(
        default="display_name",
        description="Field name for display name in document metadata",
    )
    n_messages_in_history: int = Field(
        default=6, description="Number of messages to include in chat history"
    )
    max_tokens_generated: int = Field(
        default=1024, description="Maximum number of tokens to generate in response"
    )
    context_window: int = Field(
        default=128_000, description="Size of the context window for the LLM"
    )

    chat_model_name: str = Field(
        default="mistralai/mistral-large-2-instruct",
        description="Model for final response synthesis. ",
    )
    routing_model_name: str = Field(
        default="meta/llama-3.1-8b-instruct",
        description="Model for performing query routing. Can be a bit dumber.",
    )
    perplexity_model_name: str = Field(
        default="llama-3.1-sonar-large-128k-online",
        description="Name of the Perplexity model; alternatives are huge and small.",
    )
    embedding_model_name: str = Field(
        default="nvidia/nv-embed-v1", description="Name of the embedding model"
    )
    embedding_model_dim: int = Field(
        default=4096, description="Dimension of the embedding model"
    )
    similarity_top_k: int = Field(
        default=5,
        description="Number of similar documents to return from vector search",
    )

    nvidia_api_key: str = Field(
        default=os.getenv("NVIDIA_API_KEY"), description="NVIDIA API key"
    )
    perplexity_api_key: str = Field(
        default=os.getenv("PERPLEXITY_API_KEY"),
        description="Perplexity API key (optional)",
    )

    data_dir: str = Field(
        default="data", description="Directory containing the documents to be indexed"
    )
    milvus_path: str = Field(
        default="db/milvus_lite.db", description="Path to the Milvus database"
    )

    def __init__(self, **data):
        super().__init__(**data)
        if not self.nvidia_api_key:
            raise ValueError("NVIDIA_API_KEY is required and must not be null")


config = WorkflowConfig()
