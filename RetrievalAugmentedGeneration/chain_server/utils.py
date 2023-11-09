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
from functools import lru_cache
from typing import TYPE_CHECKING, List, Optional

import torch
from llama_index.indices.postprocessor.types import BaseNodePostprocessor
from llama_index.schema import MetadataMode
from llama_index.utils import globals_helper
from llama_index.vector_stores import MilvusVectorStore
from llama_index import VectorStoreIndex, ServiceContext, set_global_service_context
from llama_index.llms import LangChainLLM
from llama_index import LangchainEmbedding
from langchain.text_splitter import SentenceTransformersTokenTextSplitter
from langchain.embeddings import HuggingFaceEmbeddings
from chain_server.trt_llm import TensorRTLLM
from chain_server import configuration

if TYPE_CHECKING:
    from llama_index.indices.base_retriever import BaseRetriever
    from llama_index.indices.query.schema import QueryBundle
    from llama_index.schema import NodeWithScore
    from chain_server.configuration_wizard import ConfigWizard

DEFAULT_MAX_CONTEXT = 1500
DEFAULT_NUM_TOKENS = 50


class LimitRetrievedNodesLength(BaseNodePostprocessor):
    """Llama Index chain filter to limit token lengths."""

    def postprocess_nodes(
        self, nodes: List["NodeWithScore"], query_bundle: Optional["QueryBundle"] = None
    ) -> List["NodeWithScore"]:
        """Filter function."""
        included_nodes = []
        current_length = 0
        limit = DEFAULT_MAX_CONTEXT

        for node in nodes:
            current_length += len(
                globals_helper.tokenizer(
                    node.node.get_content(metadata_mode=MetadataMode.LLM)
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
    vector_store = MilvusVectorStore(uri=config.milvus.url, dim=1024, overwrite=False)
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
    trtllm = TensorRTLLM(  # type: ignore
        server_url=settings.triton.server_url,
        model_name=settings.triton.model_name,
        tokens=DEFAULT_NUM_TOKENS,
    )
    return LangChainLLM(llm=trtllm)


@lru_cache
def get_embedding_model() -> LangchainEmbedding:
    """Create the embedding model."""
    model_kwargs = {"device": "cpu"}
    if torch.cuda.is_available():
        model_kwargs["device"] = "cuda:0"

    encode_kwargs = {"normalize_embeddings": False}
    hf_embeddings = HuggingFaceEmbeddings(
        model_name=get_config().embeddings.model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )

    # Load in a specific embedding model
    return LangchainEmbedding(hf_embeddings)


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
        model_name=get_config().embeddings.model_name,
        chunk_size=get_config().text_splitter.chunk_size,
        chunk_overlap=get_config().text_splitter.chunk_overlap,
    )
