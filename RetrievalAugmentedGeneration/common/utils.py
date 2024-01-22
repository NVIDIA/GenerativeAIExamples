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

"""Utility functions for the LLM Chains."""
import os
import base64
import logging
from functools import lru_cache
from typing import TYPE_CHECKING, List, Optional

logger = logging.getLogger(__name__)

try:
    import torch
except Exception as e:
    logger.error(f"torch import failed with error: {e}")

try:
    import psycopg2
except Exception as e:
    logger.error(f"psycogp2 import failed with error: {e}")

try:
    from sqlalchemy import make_url
except Exception as e:
    logger.error(f"SQLalchemy import failed with error: {e}")

try:
    from llama_index.postprocessor.types import BaseNodePostprocessor
    from llama_index.schema import MetadataMode
    from llama_index.utils import globals_helper, get_tokenizer
    from llama_index.vector_stores import MilvusVectorStore, PGVectorStore
    from llama_index import VectorStoreIndex, ServiceContext, set_global_service_context
    from llama_index.llms import LangChainLLM
    from llama_index.embeddings import LangchainEmbedding
    if TYPE_CHECKING:
        from llama_index.indices.base_retriever import BaseRetriever
        from llama_index.indices.query.schema import QueryBundle
        from llama_index.schema import NodeWithScore
except Exception as e:
    logger.error(f"Llamaindex import failed with error: {e}")

try:
    from langchain.text_splitter import SentenceTransformersTokenTextSplitter
    from langchain.embeddings import HuggingFaceEmbeddings
except Exception as e:
    logger.error(f"Langchain import failed with error: {e}")

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
except Exception as e:
    logger.error(f"NVIDIA AI connector import failed with error: {e}")

from integrations.langchain.llms.triton_trt_llm import TensorRTLLM
from RetrievalAugmentedGeneration.common import configuration

if TYPE_CHECKING:
    from RetrievalAugmentedGeneration.common.configuration_wizard import ConfigWizard

DEFAULT_MAX_CONTEXT = 1500
DEFAULT_NUM_TOKENS = 150
TEXT_SPLITTER_EMBEDDING_MODEL = "intfloat/e5-large-v2"


class LimitRetrievedNodesLength(BaseNodePostprocessor):
    """Llama Index chain filter to limit token lengths."""

    def _postprocess_nodes(
        self, nodes: List["NodeWithScore"] = [], query_bundle: Optional["QueryBundle"] = None
    ) -> List["NodeWithScore"]:
        """Filter function."""
        included_nodes = []
        current_length = 0
        limit = DEFAULT_MAX_CONTEXT
        tokenizer = get_tokenizer()

        for node in nodes:
            current_length += len(
                tokenizer(
                    node.get_content(metadata_mode=MetadataMode.LLM)
                )
            )
            if current_length > limit:
                break
            included_nodes.append(node)

        return included_nodes


@lru_cache
def set_service_context() -> None:
    """Set the global service context."""
    service_context = ServiceContext.from_defaults(
        llm=get_llm(), embed_model=get_embedding_model()
    )
    set_global_service_context(service_context)


@lru_cache
def get_config() -> "ConfigWizard":
    """Parse the application configuration."""
    config_file = os.environ.get("APP_CONFIG_FILE", "/dev/null")
    config = configuration.AppConfig.from_file(config_file)
    if config:
        return config
    raise RuntimeError("Unable to find configuration.")


@lru_cache
def get_vector_index() -> VectorStoreIndex:
    """Create the vector db index."""
    config = get_config()
    vector_store = None

    logger.info(f"Using {config.vector_store.name} as vector store")
    if config.vector_store.name == "pgvector":
        connection_string = f"postgresql://{os.getenv('POSTGRES_USER', '')}:{os.getenv('POSTGRES_PASSWORD', '')}@{config.vector_store.url}"
        db_name = "vector_db"

        conn = psycopg2.connect(connection_string)
        conn.autocommit = True

        with conn.cursor() as c:
            # Check for database existence first
            c.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
            if not c.fetchone():  # Database doesn't exist
                c.execute(f"CREATE DATABASE {db_name}")

        url = make_url(connection_string)

        vector_store = PGVectorStore.from_params(
            database=db_name,
            host=url.host,
            password=url.password,
            port=url.port,
            user=url.username,
            table_name="document_store",
            embed_dim=config.embeddings.dimensions,
        )
    elif config.vector_store.name == "milvus":
        vector_store = MilvusVectorStore(uri=config.vector_store.url,
            dim=config.embeddings.dimensions,
            collection_name="document_store_ivfflat",
            index_config={"index_type": "IVF_FLAT", "nlist": config.vector_store.nlist},
            search_config={"nprobe": config.vector_store.nprobe},
            overwrite=False)
    else:
        raise RuntimeError("Unable to find any supported Vector Store DB. Supported engines are milvus and pgvector.")
    return VectorStoreIndex.from_vector_store(vector_store)


@lru_cache
def get_doc_retriever(num_nodes: int = 4) -> "BaseRetriever":
    """Create the document retriever."""
    index = get_vector_index()
    return index.as_retriever(similarity_top_k=num_nodes)


@lru_cache
def get_llm() -> LangChainLLM:
    """Create the LLM connection."""
    settings = get_config()

    logger.info(f"Using {settings.llm.model_engine} as model engine for llm. Model name: {settings.llm.model_name}")
    if settings.llm.model_engine == "triton-trt-llm":
        trtllm = TensorRTLLM(  # type: ignore
            server_url=settings.llm.server_url,
            model_name=settings.llm.model_name,
            tokens=DEFAULT_NUM_TOKENS,
        )
        return LangChainLLM(llm=trtllm)
    elif settings.llm.model_engine == "nv-ai-foundation":
        return ChatNVIDIA(model=settings.llm.model_name)
    else:
        raise RuntimeError("Unable to find any supported Large Language Model server. Supported engines are triton-trt-llm and nv-ai-foundation.")


@lru_cache
def get_embedding_model() -> LangchainEmbedding:
    """Create the embedding model."""
    model_kwargs = {"device": "cpu"}
    if torch.cuda.is_available():
        model_kwargs["device"] = "cuda:0"

    encode_kwargs = {"normalize_embeddings": False}
    settings = get_config()

    logger.info(f"Using {settings.embeddings.model_engine} as model engine for embeddings")
    if settings.embeddings.model_engine == "huggingface":
        hf_embeddings = HuggingFaceEmbeddings(
            model_name=settings.embeddings.model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
        # Load in a specific embedding model
        return LangchainEmbedding(hf_embeddings)
    elif settings.embeddings.model_engine == "nv-ai-foundation":
        return NVIDIAEmbeddings(model=settings.embeddings.model_name, model_type="passage")
    else:
        raise RuntimeError("Unable to find any supported embedding model. Supported engine is huggingface.")


@lru_cache
def is_base64_encoded(s: str) -> bool:
    """Check if a string is base64 encoded."""
    try:
        # Attempt to decode the string as base64
        decoded_bytes = base64.b64decode(s)
        # Encode the decoded bytes back to a string to check if it's valid
        decoded_str = decoded_bytes.decode("utf-8")
        # If the original string and the decoded string match, it's base64 encoded
        return s == base64.b64encode(decoded_str.encode("utf-8")).decode("utf-8")
    except Exception:  # pylint:disable = broad-exception-caught
        # An exception occurred during decoding, so it's not base64 encoded
        return False


def get_text_splitter() -> SentenceTransformersTokenTextSplitter:
    """Return the token text splitter instance from langchain."""
    return SentenceTransformersTokenTextSplitter(
        model_name=TEXT_SPLITTER_EMBEDDING_MODEL,
        tokens_per_chunk=get_config().text_splitter.chunk_size,
        chunk_overlap=get_config().text_splitter.chunk_overlap,
    )
