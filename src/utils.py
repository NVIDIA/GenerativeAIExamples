# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""Utility functions used across different modules of the RAG."""
import logging
import os
from functools import lru_cache
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from urllib.parse import urlparse

import yaml

logger = logging.getLogger(__name__)

try:
    import torch
except Exception:
    logger.warning("Optional module torch not installed.")

try:
    from langchain.text_splitter import RecursiveCharacterTextSplitter  # pylint: disable=no-name-in-module
except Exception:
    logger.warning("Optional langchain module not installed for SentenceTransformersTokenTextSplitter.")

try:
    from langchain_core.vectorstores import VectorStore
except Exception:
    logger.warning("Optional Langchain module langchain_core not installed.")

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA
    from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
    from langchain_nvidia_ai_endpoints import NVIDIARerank
except Exception:
    logger.error("Optional langchain API Catalog connector langchain_nvidia_ai_endpoints not installed.")

try:
    from langchain_community.docstore.in_memory import InMemoryDocstore
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Milvus
except Exception:
    logger.warning("Optional Langchain module langchain_community not installed.")

# pylint: disable=ungrouped-imports, wrong-import-position
from langchain.llms.base import LLM  # noqa: E402  # pylint: disable=no-name-in-module
from langchain_core.documents.compressor import BaseDocumentCompressor  # noqa: E402
from langchain_core.embeddings import Embeddings  # noqa: E402
from langchain_core.language_models.chat_models import SimpleChatModel  # noqa: E402

from . import configuration  # noqa: E402

if TYPE_CHECKING:
    from .configuration_wizard import ConfigWizard

DEFAULT_MAX_CONTEXT = 1500

# pylint: disable=unnecessary-lambda-assignment


def utils_cache(func: Callable) -> Callable:
    """Use this to convert unhashable args to hashable ones"""

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Convert unhashable args to hashable ones
        args_hashable = tuple(tuple(arg) if isinstance(arg, (list, dict, set)) else arg for arg in args)
        kwargs_hashable = {
            key: tuple(value) if isinstance(value, (list, dict, set)) else value
            for key, value in kwargs.items()
        }
        return func(*args_hashable, **kwargs_hashable)

    return wrapper


# @lru_cache
def get_config() -> "ConfigWizard":
    """Parse the application configuration."""
    config_file = os.environ.get("APP_CONFIG_FILE", "/dev/null")
    config = configuration.AppConfig.from_file(config_file)
    if config:
        return config
    raise RuntimeError("Unable to find configuration.")


@lru_cache
def get_prompts() -> Dict:
    """Retrieves prompt configurations from YAML file and return a dict.
    """

    # default config taking from prompt.yaml
    default_config_path = os.path.join(os.environ.get("EXAMPLE_PATH", os.path.dirname(__file__)), "prompt.yaml")
    default_config = {}
    if Path(default_config_path).exists():
        with open(default_config_path, 'r', encoding="utf-8") as file:
            logger.info("Using prompts config file from: %s", default_config_path)
            default_config = yaml.safe_load(file)

    config_file = os.environ.get("PROMPT_CONFIG_FILE", "/prompt.yaml")

    config = {}
    if Path(config_file).exists():
        with open(config_file, 'r', encoding="utf-8") as file:
            logger.info("Using prompts config file from: %s", config_file)
            config = yaml.safe_load(file)

    config = _combine_dicts(default_config, config)
    return config


def create_vectorstore_langchain(document_embedder, collection_name: str = "") -> VectorStore:
    """Create the vector db index for langchain."""

    config = get_config()

    if config.vector_store.name == "milvus":
        logger.info("Using milvus collection: %s", collection_name)
        if not collection_name:
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")

        logger.info("Using milvus collection: %s", collection_name)
        url = urlparse(config.vector_store.url)
        logger.info("Inedx type for milvus: %s", config.vector_store.index_type)
        vectorstore = Milvus(document_embedder,
                             connection_args={
                                 "host": url.hostname, "port": url.port
                             },
                             collection_name=collection_name,
                             index_params={
                                 "index_type": config.vector_store.index_type,
                                 "metric_type": "L2",
                                 "nlist": config.vector_store.nlist
                             },
                             search_params={"nprobe": config.vector_store.nprobe},
                             auto_id=True)
    else:
        raise ValueError(f"{config.vector_store.name} vector database is not supported")
    logger.info("Vector store created and saved.")
    return vectorstore


def get_vectorstore(
        vectorstore: Optional["VectorStore"],  # pylint: disable=unused-argument
        document_embedder: "Embeddings",
        collection_name: str = "") -> VectorStore:
    """
    Send a vectorstore object.
    If a Vectorstore object already exists, the function returns that object.
    Otherwise, it creates a new Vectorstore object and returns it.
    """
    return create_vectorstore_langchain(document_embedder, collection_name)


def get_collection():
    """get list of all collection in vectorstore.
    """

    config = get_config()

    if config.vector_store.name == "milvus":
        from pymilvus import connections
        from pymilvus import utility
        url = urlparse(config.vector_store.url)
        connections.connect("default", host=url.hostname, port=url.port)

        # Get list of collections
        collections = utility.list_collections()

        # Disconnect from Milvus
        connections.disconnect("default")
        return collections

    raise ValueError(f"{config.vector_store.name} vector database does not support collection name")


@utils_cache
@lru_cache()
def get_llm(**kwargs) -> LLM | SimpleChatModel:
    """Create the LLM connection."""
    settings = get_config()

    logger.info("Using %s as model engine for llm. Model name: %s", settings.llm.model_engine, settings.llm.model_name)
    if settings.llm.model_engine == "nvidia-ai-endpoints":
        unused_params = [key for key in kwargs if key not in ['temperature', 'top_p', 'max_tokens']]
        if unused_params:
            logger.warning("The following parameters from kwargs are not supported: %s for %s",
                           unused_params,
                           settings.llm.model_engine)

        if settings.llm.server_url:
            logger.info("Using llm model %s hosted at %s", settings.llm.model_name, settings.llm.server_url)
            return ChatNVIDIA(base_url=f"http://{settings.llm.server_url}/v1",
                              model=settings.llm.model_name,
                              temperature=kwargs.get('temperature', None),
                              top_p=kwargs.get('top_p', None),
                              max_tokens=kwargs.get('max_tokens', None))

        logger.info("Using llm model %s from api catalog", settings.llm.model_name)
        return ChatNVIDIA(model=settings.llm.model_name,
                          temperature=kwargs.get('temperature', None),
                          top_p=kwargs.get('top_p', None),
                          max_tokens=kwargs.get('max_tokens', None))

    raise RuntimeError(
        "Unable to find any supported Large Language Model server. Supported engine name is nvidia-ai-endpoints.")


@lru_cache
def get_embedding_model() -> Embeddings:
    """Create the embedding model."""
    model_kwargs = {"device": "cpu"}
    if torch.cuda.is_available():
        model_kwargs["device"] = "cuda:0"

    encode_kwargs = {"normalize_embeddings": False}
    settings = get_config()

    logger.info("Using %s as model engine and %s and model for embeddings",
                settings.embeddings.model_engine,
                settings.embeddings.model_name)
    if settings.embeddings.model_engine == "huggingface":
        hf_embeddings = HuggingFaceEmbeddings(
            model_name=settings.embeddings.model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
        # Load in a specific embedding model
        return hf_embeddings

    if settings.embeddings.model_engine == "nvidia-ai-endpoints":
        if settings.embeddings.server_url:
            logger.info("Using embedding model %s hosted at %s",
                        settings.embeddings.model_name,
                        settings.embeddings.server_url)
            return NVIDIAEmbeddings(base_url=f"http://{settings.embeddings.server_url}/v1",
                                    model=settings.embeddings.model_name,
                                    truncate="END")

        logger.info("Using embedding model %s hosted at api catalog", settings.embeddings.model_name)
        return NVIDIAEmbeddings(model=settings.embeddings.model_name, truncate="END")

    raise RuntimeError(
        "Unable to find any supported embedding model. Supported engine is huggingface and nvidia-ai-endpoints.")


@lru_cache
def get_ranking_model() -> BaseDocumentCompressor:
    """Create the ranking model.

    Returns:
        BaseDocumentCompressor: Base class for document compressors.
    """

    settings = get_config()

    try:
        if settings.ranking.model_engine == "nvidia-ai-endpoints":
            if settings.ranking.server_url:
                logger.info("Using ranking model hosted at %s", settings.ranking.server_url)
                return NVIDIARerank(base_url=f"http://{settings.ranking.server_url}/v1",
                                    top_n=settings.retriever.top_k,
                                    truncate="END")

            if settings.ranking.model_name:
                logger.info("Using ranking model %s hosted at api catalog", settings.ranking.model_name)
                return NVIDIARerank(model=settings.ranking.model_name, top_n=settings.retriever.top_k, truncate="END")
        else:
            logger.warning("Unable to find any supported ranking model. Supported engine is nvidia-ai-endpoints.")
    except Exception as e:
        logger.error("An error occurred while initializing ranking_model: %s", e)
    return None


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """Return the token text splitter instance from langchain."""

    return RecursiveCharacterTextSplitter(
        chunk_size=get_config().text_splitter.chunk_size,
        chunk_overlap=get_config().text_splitter.chunk_overlap,
    )


def get_docs_vectorstore_langchain(vectorstore: VectorStore) -> List[str]:
    """Retrieves filenames stored in the vector store implemented in LangChain."""

    settings = get_config()
    try:
        # No API availbe in LangChain for listing the docs, thus usig its private _dict
        extract_filename = lambda metadata: os.path.basename(metadata['source'])  # noqa: E731

        if settings.vector_store.name == "milvus":
            # Getting all the ID's > 0
            if vectorstore.col:
                milvus_data = vectorstore.col.query(expr="pk >= 0", output_fields=["pk", "source"])
                filenames = set(extract_filename(metadata) for metadata in milvus_data)
                return filenames
    except Exception as e:
        logger.error("Error occurred while retrieving documents: %s", e)
    return []


def del_docs_vectorstore_langchain(vectorstore: VectorStore, filenames: List[str]) -> bool:
    """Delete documents from the vector index implemented in LangChain."""

    settings = get_config()
    try:
        # No other API availbe in LangChain for listing the docs, thus usig its private _dict
        extract_filename = lambda metadata: os.path.basename(metadata['source'])  # noqa: E731
        if settings.vector_store.name == "milvus":
            # Getting all the ID's > 0
            milvus_data = vectorstore.col.query(expr="pk >= 0", output_fields=["pk", "source"])
            for filename in filenames:
                ids_list = [metadata["pk"] for metadata in milvus_data if extract_filename(metadata) == filename]
                if len(ids_list) == 0:
                    logger.info("File does not exist in the vectorstore")
                    return False
                vectorstore.col.delete(f"pk in {ids_list}")
                logger.info("Deleted documents with filenames %s", filename)
                return True
    except Exception as e:
        logger.error("Error occurred while deleting documents: %s", e)
        return False
    return True


def _combine_dicts(dict_a, dict_b):
    """Combines two dictionaries recursively, prioritizing values from dict_b.

    Args:
        dict_a: The first dictionary.
        dict_b: The second dictionary.

    Returns:
        A new dictionary with combined key-value pairs.
    """

    combined_dict = dict_a.copy()  # Start with a copy of dict_a

    for key, value_b in dict_b.items():
        if key in combined_dict:
            value_a = combined_dict[key]
            # Remove the special handling for "command"
            if isinstance(value_a, dict) and isinstance(value_b, dict):
                combined_dict[key] = _combine_dicts(value_a, value_b)
            # Otherwise, replace the value from A with the value from B
            else:
                combined_dict[key] = value_b
        else:
            # Add any key not present in A
            combined_dict[key] = value_b

    return combined_dict
