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
class VectorStoreConfig(ConfigWizard):
    """Configuration class for the Vector Store connection.

    :cvar name: Name of vector store
    :cvar url: URL of Vector Store
    """

    name: str = configfield(
        "name",
        default="milvus", # supports pgvector, milvus
        help_txt="The name of vector store",
    )
    url: str = configfield(
        "url",
        default="http://milvus:19530", # for pgvector `pgvector:5432`
        help_txt="The host of the machine running Vector Store DB",
    )
    nlist: int = configfield(
        "nlist",
        default=64, # IVF Flat milvus
        help_txt="Number of cluster units",
    )
    nprobe: int = configfield(
        "nprobe",
        default=16, # IVF Flat milvus
        help_txt="Number of units to query",
    )


@configclass
class LLMConfig(ConfigWizard):
    """Configuration class for the llm connection.

    :cvar server_url: The location of the llm server hosting the model.
    :cvar model_name: The name of the hosted model.
    """

    server_url: str = configfield(
        "server_url",
        default="",
        help_txt="The location of the Triton server hosting the llm model.",
    )
    model_name: str = configfield(
        "model_name",
        default="ensemble",
        help_txt="The name of the hosted model.",
    )
    model_engine: str = configfield(
        "model_engine",
        default="nvidia-ai-endpoints",
        help_txt="The server type of the hosted model. Allowed values are nvidia-ai-endpoints",
    )
    model_name_pandas_ai: str = configfield(
        "model_name_pandas_ai",
        default="ai-mixtral-8x7b-instruct",
        help_txt="The name of the ai catalog model to be used with PandasAI agent",
    )

@configclass
class TextSplitterConfig(ConfigWizard):
    """Configuration class for the Text Splitter.

    :cvar chunk_size: Chunk size for text splitter. Tokens per chunk in token-based splitters.
    :cvar chunk_overlap: Text overlap in text splitter.
    """

    model_name: str = configfield(
        "model_name",
        default="Snowflake/snowflake-arctic-embed-l",
        help_txt="The name of Sentence Transformer model used for SentenceTransformer TextSplitter.",
    )
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
        default="snowflake/arctic-embed-l",
        help_txt="The name of huggingface embedding model.",
    )
    model_engine: str = configfield(
        "model_engine",
        default="nvidia-ai-endpoints",
        help_txt="The server type of the hosted model. Allowed values are hugginface",
    )
    dimensions: int = configfield(
        "dimensions",
        default=1024,
        help_txt="The required dimensions of the embedding model. Currently utilized for vector DB indexing.",
    )
    server_url: str = configfield(
        "server_url",
        default="",
        help_txt="The url of the server hosting nemo embedding model",
    )


@configclass
class RetrieverConfig(ConfigWizard):
    """Configuration class for the Retrieval pipeline.

    :cvar top_k: Number of relevant results to retrieve.
    :cvar score_threshold: The minimum confidence score for the retrieved values to be considered.
    """

    top_k: int = configfield(
        "top_k",
        default=4,
        help_txt="Number of relevant results to retrieve",
    )
    score_threshold: float = configfield(
        "score_threshold",
        default=0.25,
        help_txt="The minimum confidence score for the retrieved values to be considered",
    )
    nr_url: str = configfield(
        "nr_url",
        default='http://retrieval-ms:8000',
        help_txt="The nemo retriever microservice url",
    )
    nr_pipeline: str = configfield(
        "nr_pipeline",
        default='ranked_hybrid',
        help_txt="The name of the nemo retriever pipeline one of ranked_hybrid or hybrid",
    )


@configclass
class PromptsConfig(ConfigWizard):
    """Configuration class for the Prompts.

    :cvar chat_template: Prompt template for chat.
    :cvar rag_template: Prompt template for rag.
    :cvar multi_turn_rag_template: Prompt template for multi-turn rag.
    """

    chat_template: str = configfield(
        "chat_template",
        default=(
            "You are a helpful, respectful and honest assistant."
            "Always answer as helpfully as possible, while being safe."
            "Please ensure that your responses are positive in nature."
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
    multi_turn_rag_template: str = configfield(
        "multi_turn_rag_template",
        default=(
            "You are a document chatbot. Help the user as they ask questions about documents."
            " User message just asked: {input}\n\n"
            " For this, we have retrieved the following potentially-useful info: "
            " Conversation History Retrieved:\n{history}\n\n"
            " Document Retrieved:\n{context}\n\n"
            " Answer only from retrieved data. Make your response conversational."
        ),
        help_txt="Prompt template for rag.",
    )


@configclass
class AppConfig(ConfigWizard):
    """Configuration class for the application.

    :cvar vector_store: The configuration of the vector db connection.
    :type vector_store: VectorStoreConfig
    :cvar llm: The configuration of the backend llm server.
    :type llm: LLMConfig
    :cvar text_splitter: The configuration for text splitter
    :type text_splitter: TextSplitterConfig
    :cvar embeddings: The configuration for huggingface embeddings
    :type embeddings: EmbeddingConfig
    :cvar prompts: The Prompts template for RAG and Chat
    :type prompts: PromptsConfig
    """

    vector_store: VectorStoreConfig = configfield(
        "vector_store",
        env=False,
        help_txt="The configuration of the vector db connection.",
        default=VectorStoreConfig(),
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
    retriever: RetrieverConfig = configfield(
        "retriever",
        env=False,
        help_txt="The configuration of the retriever pipeline.",
        default=RetrieverConfig(),
    )
    prompts: PromptsConfig = configfield(
        "prompts",
        env=False,
        help_txt="Prompt templates for chat and rag.",
        default=PromptsConfig(),
    )
