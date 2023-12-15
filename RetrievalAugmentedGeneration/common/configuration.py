# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""The definition of the application configuration."""
from RetrievalAugmentedGeneration.common.configuration_wizard import ConfigWizard, configclass, configfield


@configclass
class MilvusConfig(ConfigWizard):
    """Configuration class for the Weaviate connection.

    :cvar url: URL of Milvus DB
    """

    url: str = configfield(
        "url",
        default="http://localhost:19530",
        help_txt="The host of the machine running Milvus DB",
    )


@configclass
class LLMConfig(ConfigWizard):
    """Configuration class for the Triton connection.

    :cvar server_url: The location of the Triton server hosting the llm model.
    :cvar model_name: The name of the hosted model.
    """

    server_url: str = configfield(
        "server_url",
        default="localhost:8001",
        help_txt="The location of the Triton server hosting the llm model.",
    )
    model_name: str = configfield(
        "model_name",
        default="ensemble",
        help_txt="The name of the hosted model.",
    )
    model_engine: str = configfield(
        "model_engine",
        default="triton-trt-llm",
        help_txt="The server type of the hosted model. Allowed values are triton-trt-llm and nemo-infer",
    )


@configclass
class TextSplitterConfig(ConfigWizard):
    """Configuration class for the Text Splitter.

    :cvar chunk_size: Chunk size for text splitter.
    :cvar chunk_overlap: Text overlap in text splitter.
    """

    chunk_size: int = configfield(
        "chunk_size",
        default=510,
        help_txt="Chunk size for text splitting.",
    )
    chunk_overlap: int = configfield(
        "chunk_overlap",
        default=200,
        help_txt="Overlapping text length for splitting.",
    )


@configclass
class EmbeddingConfig(ConfigWizard):
    """Configuration class for the Embeddings.

    :cvar model_name: The name of the huggingface embedding model.
    """

    model_name: str = configfield(
        "model_name",
        default="intfloat/e5-large-v2",
        help_txt="The name of huggingface embedding model.",
    )
    model_engine: str = configfield(
        "model_engine",
        default="huggingface",
        help_txt="The server type of the hosted model. Allowed values are hugginface",
    )
    dimensions: int = configfield(
        "dimensions",
        default=1024,
        help_txt="The required dimensions of the embedding model. Currently utilized for vector DB indexing.",
    )


@configclass
class PromptsConfig(ConfigWizard):
    """Configuration class for the Prompts.

    :cvar chat_template: Prompt template for chat.
    :cvar rag_template: Prompt template for rag.
    """

    chat_template: str = configfield(
        "chat_template",
        default=(
            "<s>[INST] <<SYS>>"
            "You are a helpful, respectful and honest assistant."
            "Always answer as helpfully as possible, while being safe."
            "Please ensure that your responses are positive in nature."
            "<</SYS>>"
            "[/INST] {context_str} </s><s>[INST] {query_str} [/INST]"
        ),
        help_txt="Prompt template for chat.",
    )
    rag_template: str = configfield(
        "rag_template",
        default=(
            "<s>[INST] <<SYS>>"
            "Use the following context to answer the user's question. If you don't know the answer,"
            "just say that you don't know, don't try to make up an answer."
            "<</SYS>>"
            "<s>[INST] Context: {context_str} Question: {query_str} Only return the helpful"
            " answer below and nothing else. Helpful answer:[/INST]"
        ),
        help_txt="Prompt template for rag.",
    )


@configclass
class AppConfig(ConfigWizard):
    """Configuration class for the application.

    :cvar milvus: The configuration of the Milvus vector db connection.
    :type milvus: MilvusConfig
    :cvar triton: The configuration of the backend Triton server.
    :type triton: TritonConfig
    :cvar text_splitter: The configuration for text splitter
    :type text_splitter: TextSplitterConfig
    :cvar embeddings: The configuration for huggingface embeddings
    :type embeddings: EmbeddingConfig
    :cvar prompts: The Prompts template for RAG and Chat
    :type prompts: PromptsConfig
    """

    milvus: MilvusConfig = configfield(
        "milvus",
        env=False,
        help_txt="The configuration of the Milvus connection.",
        default=MilvusConfig(),
    )
    llm: LLMConfig = configfield(
        "llm",
        env=False,
        help_txt="The configuration for the server hosting the Large Language Models.",
        default=LLMConfig(),
    )
    text_splitter: TextSplitterConfig = configfield(
        "text_splitter",
        env=False,
        help_txt="The configuration for text splitter.",
        default=TextSplitterConfig(),
    )
    embeddings: EmbeddingConfig = configfield(
        "embeddings",
        env=False,
        help_txt="The configuration of embedding model.",
        default=EmbeddingConfig(),
    )
    prompts: PromptsConfig = configfield(
        "prompts",
        env=False,
        help_txt="Prompt templates for chat and rag.",
        default=PromptsConfig(),
    )
