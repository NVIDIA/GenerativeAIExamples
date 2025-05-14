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
from typing import TYPE_CHECKING, Iterable
from typing import Callable
from typing import Dict
from typing import List
from typing import Any
from typing import Optional
from urllib.parse import urlparse

import requests
import yaml
import math
import aiohttp
import asyncio
import time

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
    from langchain_nvidia_ai_endpoints import register_model, Model
except Exception:
    logger.error("Optional langchain API Catalog connector langchain_nvidia_ai_endpoints not installed.")

try:
    from langchain_openai import ChatOpenAI
except Exception:
    logger.warning("Optional langchain_openai module not installed.")

try:
    from langchain_community.docstore.in_memory import InMemoryDocstore
    from langchain_community.embeddings import HuggingFaceEmbeddings
except Exception:
    logger.warning("Optional Langchain module langchain_community not installed.")

try:
    from langchain_milvus import Milvus, BM25BuiltInFunction
except Exception:
    logger.warning("Optional Langchain module langchain_milvus not installed.")

# pylint: disable=ungrouped-imports, wrong-import-position
from langchain.llms.base import LLM  # noqa: E402  # pylint: disable=no-name-in-module
from langchain_core.documents.compressor import BaseDocumentCompressor  # noqa: E402
from langchain_core.embeddings import Embeddings  # noqa: E402
from langchain_core.language_models.chat_models import SimpleChatModel  # noqa: E402
from pymilvus import connections, utility, Collection

try:
    from nv_ingest_client.client import NvIngestClient, Ingestor
    from nv_ingest_client.util.milvus import create_nvingest_collection
except Exception:
    logger.warning("Optional nv_ingest_client module not installed.")

from src.minio_operator import MinioOperator
from . import configuration  # noqa: E402

if TYPE_CHECKING:
    from .configuration_wizard import ConfigWizard

DEFAULT_MAX_CONTEXT = 1500
ENABLE_NV_INGEST_VDB_UPLOAD = True # When enabled entire ingestion would be performed using nv-ingest

# pylint: disable=unnecessary-lambda-assignment

def get_env_variable(
        variable_name: str,
        default_value: Any
    ) -> Any:
    """
    Get an environment variable with a fallback to a default value.
    Also checks if the variable is set, is not empty, and is not longer than 256 characters.

    Args:
        variable_name (str): The name of the environment variable to get

    Returns:
        Any: The value of the environment variable or the default value if the variable is not set
    """
    var = os.environ.get(variable_name)

    # Check if variable is set
    if var is None:
        logger.warning(f"Environment variable {variable_name} is not set. Using default value: {default_value}")
        var = default_value

    # Check min and max length of variable
    if len(var) > 256 or len(var) == 0:
        logger.warning(f"Environment variable {variable_name} is longer than 256 characters or empty. Using default value: {default_value}")
        var = default_value

    return var

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


def create_vectorstore_langchain(document_embedder, collection_name: str = "", vdb_endpoint: str = "") -> VectorStore:
    """Create the vector db index for langchain."""

    config = get_config()

    if vdb_endpoint == "":
        vdb_endpoint = config.vector_store.url

    if config.vector_store.name == "milvus":
        logger.debug("Trying to connect to milvus collection: %s", collection_name)
        if not collection_name:
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")

        # Connect to Milvus to check for collection availability
        from urllib.parse import urlparse
        url = urlparse(vdb_endpoint)
        connection_alias = f"milvus_{url.hostname}_{url.port}"
        connections.connect(connection_alias, host=url.hostname, port=url.port)

        # Check if the collection exists
        if not utility.has_collection(collection_name, using=connection_alias):
            logger.warning(f"Collection '{collection_name}' does not exist in Milvus. Aborting vectorstore creation.")
            connections.disconnect(connection_alias)
            return None

        logger.debug(f"Collection '{collection_name}' exists. Proceeding with vector store creation.")

        if config.vector_store.search_type == "hybrid":
            logger.info("Creating Langchain Milvus object for Hybrid search")
            vectorstore = Milvus(
                document_embedder,
                connection_args={
                    "uri": config.vector_store.url
                },
                builtin_function=BM25BuiltInFunction(
                    output_field_names="sparse",
                    enable_match=True
                ),
                collection_name=collection_name,
                vector_field=["vector", "sparse"] # Dense and Sparse fields set by NV-Ingest
            )
        elif config.vector_store.search_type == "dense":
            logger.debug("Index type for milvus: %s", config.vector_store.index_type)
            vectorstore = Milvus(document_embedder,
                                connection_args={
                                    "uri": vdb_endpoint
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
            logger.error("Invalid search_type: %s. Please select from ['hybrid', 'dense']",
                        config.vector_store.search_type)
            raise ValueError(
                f"{config.vector_store.search_type} search type is not supported" + \
                "Please select from ['hybrid', 'dense']"
            )
    else:
        raise ValueError(f"{config.vector_store.name} vector database is not supported")
    logger.debug("Vector store created and saved.")
    return vectorstore


def get_vectorstore(
        document_embedder: "Embeddings",
        collection_name: str = "",
        vdb_endpoint: str = "") -> VectorStore:
    """
    Send a vectorstore object.
    If a Vectorstore object already exists, the function returns that object.
    Otherwise, it creates a new Vectorstore object and returns it.
    """
    return create_vectorstore_langchain(document_embedder, collection_name, vdb_endpoint)


def create_collections(collection_names: List[str], vdb_endpoint: str, dimension: int = 768, collection_type: str = "text") -> Dict[str, any]:
    """
    Create multiple collections in the Milvus vector database.

    Args:
        vdb_endpoint (str): The Milvus database endpoint.
        collection_names (List[str]): List of collection names to be created.
        dimension (int): The dimension of the embedding vectors (default: 768).
        collection_type (str): The type of collection to be created. Reserved for future use.

    Returns:
        dict: Response with creation status.
    """
    config = get_config()
    try:
        if not len(collection_names):
            return {
                "message": "No collections to create. Please provide a list of collection names.",
                "successful": [],
                "failed": [],
                "total_success": 0,
                "total_failed": 0
            }

        # Parse endpoint and connect
        url = urlparse(vdb_endpoint)
        connection_alias = f"milvus_{url.hostname}_{url.port}"
        connections.connect(connection_alias, host=url.hostname, port=url.port)

        created_collections = []
        failed_collections = []

        for collection_name in collection_names:
            try:
                create_nvingest_collection(
                    collection_name = collection_name,
                    milvus_uri = vdb_endpoint,
                    sparse = (config.vector_store.search_type == "hybrid"),
                    recreate = False,
                    gpu_index = config.vector_store.enable_gpu_index,
                    gpu_search = config.vector_store.enable_gpu_search,
                    dense_dim = dimension
                )
                created_collections.append(collection_name)
                logger.info(f"Collection '{collection_name}' created successfully in {vdb_endpoint}.")

            except Exception as e:
                failed_collections.append(
                    {
                        "collection_name": collection_name,
                        "error_message": str(e)
                    }
                )
                logger.error(f"Failed to create collection {collection_name}: {str(e)}")

        # Disconnect from Milvus
        connections.disconnect(connection_alias)

        return {
            "message": "Collection creation process completed.",
            "successful": created_collections,
            "failed": failed_collections,
            "total_success": len(created_collections),
            "total_failed": len(failed_collections)
        }

    except Exception as e:
        logger.error(f"Failed to create collections due to error: {str(e)}")
        return {
            "message": f"Failed to create collections due to error: {str(e)}",
            "successful": [],
            "failed": collection_names,
            "total_success": 0,
            "total_failed": len(collection_names)
        }


def get_collection(vdb_endpoint: str = "") -> Dict[str, Any]:
    """get list of all collection in vectorstore along with the number of rows in each collection.
    """

    config = get_config()

    if config.vector_store.name == "milvus":
        url = urlparse(vdb_endpoint)
        connection_alias = f"milvus_{url.hostname}_{url.port}"
        connections.connect(connection_alias, host=url.hostname, port=url.port)

        # Get list of collections
        collections = utility.list_collections(using=connection_alias)

        # Get document count for each collection
        collection_info = []
        for collection in collections:
            collection_obj = Collection(collection, using=connection_alias)
            num_entities = collection_obj.num_entities
            collection_info.append({"collection_name": collection, "num_entities": num_entities})

        # Disconnect from Milvus
        connections.disconnect(connection_alias)
        return collection_info

    raise ValueError(f"{config.vector_store.name} vector database does not support collection name")


def delete_collections(vdb_endpoint: str, collection_names: List[str]) -> dict:
    """
    Delete a list of collections from the Milvus vector database.

    Args:
        vdb_endpoint (str): The Milvus database endpoint.
        collection_names (List[str]): List of collection names to be deleted.

    Returns:
        dict: Response with deletion status.
    """
    try:

        if not len(collection_names):
            return {
                "message": "No collections to delete. Please provide a list of collection names.",
                "successful": [],
                "failed": [],
                "total_success": 0,
                "total_failed": 0 }

        # Parse endpoint and connect
        url = urlparse(vdb_endpoint)
        connection_alias = f"milvus_{url.hostname}_{url.port}"
        connections.connect(connection_alias, host=url.hostname, port=url.port)

        deleted_collections = []
        failed_collections = []

        for collection in collection_names:
            try:
                if utility.has_collection(collection, using=connection_alias):
                    utility.drop_collection(collection, using=connection_alias)
                    deleted_collections.append(collection)
                    logger.info(f"Deleted collection: {collection}")
                else:
                    failed_collections.append(collection)
                    logger.warning(f"Collection {collection} not found.")
            except Exception as e:
                failed_collections.append(collection)
                logger.error(f"Failed to delete collection {collection}: {str(e)}")

        # Disconnect from Milvus
        connections.disconnect(connection_alias)

        return {
            "message": "Collection deletion process completed.",
            "successful": deleted_collections,
            "failed": failed_collections,
            "total_success": len(deleted_collections),
            "total_failed": len(failed_collections)
        }

    except Exception as e:
        logger.error(f"Failed to delete collections due to error: {str(e)}")
        return {
            "message": f"Failed to delete collections due to error: {str(e)}",
            "successful": [],
            "failed": collection_names,
            "total_success": 0,
            "total_failed": len(collection_names)
        }

@utils_cache
@lru_cache()
def get_llm(**kwargs) -> LLM | SimpleChatModel:
    """Create the LLM connection."""
    settings = get_config()

    # Sanitize the URL
    url = sanitize_nim_url(kwargs.get('llm_endpoint', ""), kwargs.get('model'), "llm")

    # Check if guardrails are enabled
    enable_guardrails = os.getenv("ENABLE_GUARDRAILS", "False").lower() == "true" and kwargs.get('enable_guardrails', False) == True

    logger.info("Using %s as model engine for llm. Model name: %s", settings.llm.model_engine, kwargs.get('model'))
    if settings.llm.model_engine == "nvidia-ai-endpoints":

        # Use ChatOpenAI with guardrails if enabled
        # TODO Add the ChatNVIDIA implementation when available
        if enable_guardrails:
            logger.info("Guardrails enabled, using ChatOpenAI with guardrails URL")
            guardrails_url = os.getenv("NEMO_GUARDRAILS_URL", "")
            if not guardrails_url:
                logger.warning("NEMO_GUARDRAILS_URL not set, falling back to default implementation")
            else:
                try:
                    # Parse URL and add scheme if missing
                    if not guardrails_url.startswith(('http://', 'https://')):
                        guardrails_url = 'http://' + guardrails_url

                    # Try to connect with a timeout of 5 seconds
                    response = requests.get(guardrails_url + "/v1/health", timeout=5)
                    response.raise_for_status()

                    x_model_authorization = {"X-Model-Authorization": os.environ.get("NGC_API_KEY", "")}
                    return ChatOpenAI(
                        model_name=kwargs.get('model'),
                        openai_api_base=f"{guardrails_url}/v1/guardrail",
                        openai_api_key="dummy-value",
                        default_headers=x_model_authorization,
                        temperature=kwargs.get('temperature', None),
                        top_p=kwargs.get('top_p', None),
                        max_tokens=kwargs.get('max_tokens', None)
                    )
                except (requests.RequestException, requests.ConnectionError) as e:
                    error_msg = f"Failed to connect to guardrails service at {guardrails_url}: {str(e)} Make sure the guardrails service is running and accessible."
                    logger.error(error_msg)
                    raise RuntimeError(error_msg)

        if url:
            logger.debug(f"Length of llm endpoint url string {url}")
            logger.info("Using llm model %s hosted at %s", kwargs.get('model'), url)
            return ChatNVIDIA(base_url=url,
                              model=kwargs.get('model'),
                              temperature=kwargs.get('temperature', None),
                              top_p=kwargs.get('top_p', None),
                              max_tokens=kwargs.get('max_tokens', None))

        logger.info("Using llm model %s from api catalog", kwargs.get('model'))
        return ChatNVIDIA(model=kwargs.get('model'),
                          temperature=kwargs.get('temperature', None),
                          top_p=kwargs.get('top_p', None),
                          max_tokens=kwargs.get('max_tokens', None))

    raise RuntimeError(
        "Unable to find any supported Large Language Model server. Supported engine name is nvidia-ai-endpoints.")


@lru_cache
def get_embedding_model(model: str, url: str) -> Embeddings:
    """Create the embedding model."""
    model_kwargs = {"device": "cpu"}
    if torch.cuda.is_available():
        model_kwargs["device"] = "cuda:0"

    encode_kwargs = {"normalize_embeddings": False}
    settings = get_config()

    # Sanitize the URL
    url = sanitize_nim_url(url, model, "embedding")

    logger.info("Using %s as model engine and %s and model for embeddings",
                settings.embeddings.model_engine,
                model)
    if settings.embeddings.model_engine == "huggingface":
        hf_embeddings = HuggingFaceEmbeddings(
            model_name=settings.embeddings.model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
        # Load in a specific embedding model
        return hf_embeddings

    if settings.embeddings.model_engine == "nvidia-ai-endpoints":
        if url:
            logger.info("Using embedding model %s hosted at %s",
                        model,
                        url)
            return NVIDIAEmbeddings(base_url=url,
                                    model=model,
                                    truncate="END")

        logger.info("Using embedding model %s hosted at api catalog", model)
        return NVIDIAEmbeddings(model=model, truncate="END")

    raise RuntimeError(
        "Unable to find any supported embedding model. Supported engine is huggingface and nvidia-ai-endpoints.")


@lru_cache
def _get_ranking_model(model="", url="", top_n=4) -> BaseDocumentCompressor:
    """Create the ranking model.

    Returns:
        BaseDocumentCompressor: Base class for document compressors.
    """

    settings = get_config()

    # Sanitize the URL
    url = sanitize_nim_url(url, model, "ranking")

    try:
        if settings.ranking.model_engine == "nvidia-ai-endpoints":
            if url:
                logger.info("Using ranking model hosted at %s", url)
                return NVIDIARerank(base_url=url,
                                    top_n=top_n,
                                    truncate="END")

            if model:
                logger.info("Using ranking model %s hosted at api catalog", model)
                return NVIDIARerank(model=model, top_n=top_n, truncate="END")
        else:
            logger.warning("Unable to find any supported ranking model. Supported engine is nvidia-ai-endpoints.")
    except Exception as e:
        logger.error("An error occurred while initializing ranking_model: %s", e)
    return None


def get_ranking_model(model="", url="", top_n=4) -> BaseDocumentCompressor:
    """Create the ranking model."""
    ranker = _get_ranking_model(model, url, top_n)
    if ranker is None:
        logger.warning("Cached ranking model was None — clearing cache and retrying.")
        _get_ranking_model.cache_clear()
        ranker = _get_ranking_model(model, url, top_n)
    return ranker

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
        # No API available in LangChain for listing the docs, thus using its private _dict
        extract_filename = lambda metadata: os.path.basename(metadata['source'] if type(metadata['source']) == str else metadata.get('source').get('source_name'))  # noqa: E731

        if settings.vector_store.name == "milvus":
            # Getting all the ID's > 0
            if vectorstore.col:
                milvus_data = vectorstore.col.query(expr="pk >= 0", output_fields=["pk", "source"])
                filenames = set(extract_filename(metadata) for metadata in milvus_data)
                return filenames
    except Exception as e:
        logger.error("Error occurred while retrieving documents: %s", e)
    return []


def del_docs_vectorstore_langchain(vectorstore: VectorStore, filenames: List[str], collection_name: str="") -> bool:
    """Delete documents from the vector index implemented in LangChain."""

    settings = get_config()
    upload_folder = f"/tmp-data/uploaded_files/{collection_name}"
    deleted = False
    try:
        for filename in filenames:
            source_value =  os.path.join(upload_folder, filename)
            if settings.vector_store.name == "milvus":
                # Delete Milvus Entities
                resp = vectorstore.col.delete(f"source['source_name'] == '{source_value}'")
                deleted = True
                if resp.delete_count == 0:
                    logger.info("File does not exist in the vectorstore")
                    return False
        if deleted and settings.vector_store.name == "milvus":
            # Force flush the vectorstore after deleting documents to ensure that the changes are reflected in the vectorstore
            vectorstore.col.flush()
        return True
    except Exception as e: #TODO - propagate the exception
        logger.error("Error occurred while deleting documents: %s", e)
        return False


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

def sanitize_nim_url(url:str, model_name:str, model_type:str) -> str:
    """
    Sanitize the NIM URL by adding http(s):// if missing and checking if the URL is hosted on NVIDIA's known endpoints.
    """

    logger.info(f"Sanitizing NIM URL: {url} for model: {model_name} of type: {model_type}")

    # Construct the URL - if url does not start with http(s)://, add it
    if url and not url.startswith("http://") and not url.startswith("https://"):
        url = "http://" + url + "/v1"
        logger.info(f"{model_type} URL does not start with http(s)://, adding it: {url}")

    # Register model only if URL is hosted on NVIDIA's known endpoints
    if url.startswith("https://integrate.api.nvidia.com") or \
       url.startswith("https://ai.api.nvidia.com") or \
       url.startswith("https://api.nvcf.nvidia.com"):

        if model_type == "embedding":
            client = "NVIDIAEmbeddings"
        elif model_type == "llm":
            client = "ChatNVIDIA"
        elif model_type == "ranking":
            client = "NVIDIARerank"

        register_model(Model(
            id=model_name,
            model_type=model_type,
            client=client,
            endpoint=url,
        ))
        logger.info(f"Registering custom model {model_name} with client {client} at endpoint {url}")
    return url

def get_nv_ingest_client():
    """
    Creates and returns NV-Ingest client
    """
    config = get_config()

    client = NvIngestClient(
        # Host where nv-ingest-ms-runtime is running
        message_client_hostname=config.nv_ingest.message_client_hostname,
        message_client_port=config.nv_ingest.message_client_port # REST port, defaults to 7670
    )
    return client

def get_nv_ingest_ingestor(
        nv_ingest_client_instance,
        filepaths: List[str],
        **kwargs
    ):
    """
    Prepare NV-Ingest ingestor instance based on nv-ingest configuration

    Returns:
        - ingestor: Ingestor - NV-Ingest ingestor instance with configured tasks
    """
    config = get_config()

    logger.debug("Preparing NV Ingest Ingestor instance for filepaths: %s", filepaths)
    # Prepare the ingestor using nv-ingest-client
    ingestor = Ingestor(client=nv_ingest_client_instance)

    # Add files to ingestor
    ingestor = ingestor.files(filepaths)

    # Add extraction task
    # Determine paddle_output_format
    paddle_output_format = "markdown" if config.nv_ingest.extract_tables else "pseudo_markdown"
    # Create kwargs for extract method
    extract_kwargs = {
        "extract_text": config.nv_ingest.extract_text,
        "extract_tables": config.nv_ingest.extract_tables,
        "extract_charts": config.nv_ingest.extract_charts,
        "extract_images": config.nv_ingest.extract_images,
        "extract_method": config.nv_ingest.pdf_extract_method,
        "text_depth": config.nv_ingest.text_depth,
        "paddle_output_format": paddle_output_format,
    }
    if config.nv_ingest.pdf_extract_method in ["None", "none"]:
        extract_kwargs.pop("extract_method")
    ingestor = ingestor.extract(**extract_kwargs)

    # Add splitting task (By default only works for text documents)
    split_options = kwargs.get("split_options", {})
    split_source_types = ["PDF", "text"] if config.nv_ingest.enable_pdf_splitter else ["text"]
    logger.info(f"Post chunk split status: {config.nv_ingest.enable_pdf_splitter}. Splitting by: {split_source_types}")
    ingestor = ingestor.split(
                    tokenizer=config.nv_ingest.tokenizer,
                    chunk_size=split_options.get("chunk_size", config.nv_ingest.chunk_size),
                    chunk_overlap=split_options.get("chunk_overlap", config.nv_ingest.chunk_overlap),
                    params={"split_source_types": split_source_types}
                )

    # Add captioning task if extract_images is enabled
    if config.nv_ingest.extract_images:
        logger.info("Adding captioning task to NV-Ingest Ingestor")
        ingestor = ingestor.caption(
                        api_key=get_env_variable(variable_name="NGC_API_KEY", default_value=""),
                        endpoint_url=config.nv_ingest.caption_endpoint_url,
                        model_name=config.nv_ingest.caption_model_name,
                    )

    # Add Embedding task
    if ENABLE_NV_INGEST_VDB_UPLOAD:
        ingestor = ingestor.embed()

    # Add Vector-DB upload task
    if ENABLE_NV_INGEST_VDB_UPLOAD:
        ingestor = ingestor.vdb_upload(
            # Milvus configurations
            collection_name=kwargs.get("collection_name"),
            milvus_uri=kwargs.get("vdb_endpoint", config.vector_store.url),

            # Minio configurations
            minio_endpoint=os.getenv("MINIO_ENDPOINT"),
            access_key=os.getenv("MINIO_ACCESSKEY"),
            secret_key=os.getenv("MINIO_SECRETKEY"),

            # Hybrid search configurations
            sparse=(config.vector_store.search_type == "hybrid"),

            # Additional configurations
            enable_images=config.nv_ingest.extract_images,
            recreate=False, # Don't re-create milvus collection
            dense_dim=config.embeddings.dimensions,

            gpu_index = config.vector_store.enable_gpu_index,
            gpu_search = config.vector_store.enable_gpu_search,
        )

    return ingestor

def get_minio_operator():
    """
    Prepares and return MinioOperator object

    Returns:
        - minio_operator: MinioOperator
    """
    minio_operator = MinioOperator(
        endpoint=os.getenv("MINIO_ENDPOINT"),
        access_key=os.getenv("MINIO_ACCESSKEY"),
        secret_key=os.getenv("MINIO_SECRETKEY"),
    )
    return minio_operator

def get_unique_thumbnail_id_collection_prefix(
        collection_name: str,
    ) -> str:
    """
    Prepares unique thumbnail id prefix based on input collection name
    Returns:
        - unique_thumbnail_id_prefix: str
    """
    prefix = f"{collection_name}_::"
    return prefix

def get_unique_thumbnail_id_file_name_prefix(
        collection_name: str,
        file_name: str,
    ) -> str:
    """
    Prepares unique thumbnail id prefix based on input collection name and file name
    Returns:
        - unique_thumbnail_id_prefix: str
    """
    collection_prefix = get_unique_thumbnail_id_collection_prefix(collection_name)
    prefix = f"{collection_prefix}_{file_name}_::"
    return prefix

def get_unique_thumbnail_id(
        collection_name: str,
        file_name: str,
        page_number: int,
        location: List[float] # Bbox information
    ) -> str:
    """
    Prepares unique thumbnail id based on input arguments
    Returns:
        - unique_thumbnail_id: str
    """
    # Round bbox values to reduce precision
    rounded_bbox = [round(coord, 4) for coord in location]
    prefix = get_unique_thumbnail_id_file_name_prefix(collection_name, file_name)
    # Create a string representation
    unique_thumbnail_id = f"{prefix}_{page_number}_" + \
                          "_".join(map(str, rounded_bbox))
    return unique_thumbnail_id

def format_document_with_source(doc) -> str:
    """Format document content with its source filename.

    Args:
        doc: Document object with metadata and page_content

    Returns:
        str: Formatted string with filename and content if ENABLE_SOURCE_METADATA is True,
             otherwise returns just the content
    """
    # Debug log before formatting
    logger.debug(f"Before format_document_with_source - Document: {doc}")

    # Check if source metadata is enabled via environment variable
    enable_metadata = os.getenv('ENABLE_SOURCE_METADATA', 'True').lower() == 'true'

    # Return just content if metadata is disabled or doc has no metadata
    if not enable_metadata or not hasattr(doc, 'metadata'):
        result = doc.page_content
        logger.debug(f"After format_document_with_source (metadata disabled) - Result: {result}")
        return result

    # Handle nested metadata structure
    source = doc.metadata.get('source', {})
    source_path = source.get('source_name', '') if isinstance(source, dict) else source

    # If no source path is found, return just the content
    if not source_path:
        result = doc.page_content
        logger.debug(f"After format_document_with_source (no source path) - Result: {result}")
        return result

    filename = os.path.splitext(os.path.basename(source_path))[0]
    logger.info(f"Before format_document_with_source - Filename: {filename}")
    result = f"File: {filename}\nContent: {doc.page_content}"

    # Debug log after formatting
    logger.debug(f"After format_document_with_source - Result: {result}")

    return result

def streaming_filter_think(chunks: Iterable[str]) -> Iterable[str]:
    """
    This generator filters content between think tags in streaming LLM responses.
    It handles both complete tags in a single chunk and tags split across multiple tokens.

    Args:
        chunks (Iterable[str]): Chunks from a streaming LLM response

    Yields:
        str: Filtered content with think blocks removed
    """
    # Complete tags
    FULL_START_TAG = "<think>"
    FULL_END_TAG = "</think>"

    # Multi-token tags - core parts without newlines for more robust matching
    START_TAG_PARTS = ["<th", "ink", ">"]
    END_TAG_PARTS = ["</", "think", ">"]

    # States
    NORMAL = 0
    IN_THINK = 1
    MATCHING_START = 2
    MATCHING_END = 3

    state = NORMAL
    match_position = 0
    buffer = ""
    output_buffer = ""
    chunk_count = 0

    for chunk in chunks:
        content = chunk.content
        chunk_count += 1

        # Let's first check for full tags - this is the most reliable approach
        buffer += content

        # Check for complete tags first - most efficient case
        while state == NORMAL and FULL_START_TAG in buffer:
            start_idx = buffer.find(FULL_START_TAG)
            # Extract content before tag
            before_tag = buffer[:start_idx]
            output_buffer += before_tag

            # Skip over the tag
            buffer = buffer[start_idx + len(FULL_START_TAG):]
            state = IN_THINK

        while state == IN_THINK and FULL_END_TAG in buffer:
            end_idx = buffer.find(FULL_END_TAG)
            # Discard everything up to and including end tag
            buffer = buffer[end_idx + len(FULL_END_TAG):]
            content = buffer
            state = NORMAL

        # For token-by-token matching, use the core content without worrying about exact whitespace
        # Strip whitespace for comparison to make matching more robust
        content_stripped = content.strip()

        if state == NORMAL:
            if content_stripped == START_TAG_PARTS[0].strip():
                # Save everything except this start token
                to_output = buffer[:-len(content)]
                output_buffer += to_output

                buffer = content  # Keep only the start token in buffer
                state = MATCHING_START
                match_position = 1
            else:
                output_buffer += content  # Regular content, save it
                buffer = ""  # Clear buffer, we've processed this chunk

        elif state == MATCHING_START:
            expected_part = START_TAG_PARTS[match_position].strip()
            if content_stripped == expected_part:
                match_position += 1
                if match_position >= len(START_TAG_PARTS):
                    # Complete start tag matched
                    state = IN_THINK
                    match_position = 0
                    buffer = ""  # Clear the buffer
            else:
                # False match, revert to normal and recover the partial match
                state = NORMAL
                output_buffer += buffer  # Recover saved tokens
                buffer = ""

                # Check if this content is a new start tag
                if content_stripped == START_TAG_PARTS[0].strip():
                    state = MATCHING_START
                    match_position = 1
                    buffer = content  # Keep this token in buffer
                else:
                    output_buffer += content  # Regular content

        elif state == IN_THINK:
            if content_stripped == END_TAG_PARTS[0].strip():
                state = MATCHING_END
                match_position = 1
                buffer = content  # Keep this token in buffer
            else:
                buffer = ""  # Discard content inside think block

        elif state == MATCHING_END:
            expected_part = END_TAG_PARTS[match_position].strip()
            if content_stripped == expected_part:
                match_position += 1
                if match_position >= len(END_TAG_PARTS):
                    # Complete end tag matched
                    state = NORMAL
                    match_position = 0
                    buffer = ""  # Clear buffer
            else:
                # False match, revert to IN_THINK
                state = IN_THINK
                buffer = ""  # Discard content

                # Check if this is a new end tag start
                if content_stripped == END_TAG_PARTS[0].strip():
                    state = MATCHING_END
                    match_position = 1
                    buffer = content  # Keep this token in buffer

        # Yield accumulated output before processing next chunk
        if output_buffer:
            yield output_buffer
            output_buffer = ""

    # Yield any remaining content if not in a think block
    if state == NORMAL:
        if buffer:
            yield buffer
        if output_buffer:
            yield output_buffer

    logger.info("Finished streaming_filter_think processing after %d chunks", chunk_count)

def get_streaming_filter_think_parser():
    """
    Creates and returns a RunnableGenerator for filtering think tokens based on configuration.

    If FILTER_THINK_TOKENS environment variable is set to "true" (case-insensitive),
    returns a parser that filters out content between <think> and </think> tags.
    Otherwise, returns a pass-through parser that doesn't modify the content.

    Returns:
        RunnableGenerator: A parser for filtering (or not filtering) think tokens
    """
    from langchain_core.runnables import RunnableGenerator, RunnablePassthrough

    # Check environment variable
    filter_enabled = os.getenv('FILTER_THINK_TOKENS', 'true').lower() == 'true'

    if filter_enabled:
        logger.info("Think token filtering is enabled")
        return RunnableGenerator(streaming_filter_think)
    else:
        logger.info("Think token filtering is disabled")
        # If filtering is disabled, use a passthrough that passes content as-is
        return RunnablePassthrough()

def normalize_relevance_scores(documents: List["Document"]) -> List["Document"]:
    """
    Normalize relevance scores in a list of documents to be between 0 and 1 using sigmoid function.

    Args:
        documents: List of Document objects with relevance_score in metadata

    Returns:
        The same list of documents with normalized scores
    """
    if not documents:
        return documents

    # Apply sigmoid normalization (1 / (1 + e^-x))
    for doc in documents:
        if 'relevance_score' in doc.metadata:
            original_score = doc.metadata['relevance_score']
            scaled_score = original_score * 0.1
            normalized_score = 1 / (1 + math.exp(-scaled_score))
            doc.metadata['relevance_score'] = normalized_score

    return documents

async def check_service_health(
    url: str,
    service_name: str,
    method: str = "GET",
    timeout: int = 5,
    headers: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Check health of a service endpoint asynchronously.

    Args:
        url: The endpoint URL to check
        service_name: Name of the service for reporting
        method: HTTP method to use (GET, POST, etc.)
        timeout: Request timeout in seconds
        headers: Optional HTTP headers
        json_data: Optional JSON payload for POST requests

    Returns:
        Dictionary with status information
    """
    start_time = time.time()
    status = {
        "service": service_name,
        "url": url,
        "status": "unknown",
        "latency_ms": 0,
        "error": None
    }

    if not url:
        status["status"] = "skipped"
        status["error"] = "No URL provided"
        return status

    try:
        # Add scheme if missing
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url

        async with aiohttp.ClientSession() as session:
            request_kwargs = {
                "timeout": aiohttp.ClientTimeout(total=timeout),
                "headers": headers or {}
            }

            if method.upper() == "POST" and json_data:
                request_kwargs["json"] = json_data

            async with getattr(session, method.lower())(url, **request_kwargs) as response:
                status["status"] = "healthy" if response.status < 400 else "unhealthy"
                status["http_status"] = response.status
                status["latency_ms"] = round((time.time() - start_time) * 1000, 2)

    except asyncio.TimeoutError:
        status["status"] = "timeout"
        status["error"] = f"Request timed out after {timeout}s"
    except aiohttp.ClientError as e:
        status["status"] = "error"
        status["error"] = str(e)
    except Exception as e:
        status["status"] = "error"
        status["error"] = str(e)

    return status

async def check_minio_health(endpoint: str, access_key: str, secret_key: str) -> Dict[str, Any]:
    """Check MinIO server health"""
    status = {
        "service": "MinIO",
        "url": endpoint,
        "status": "unknown",
        "error": None
    }

    if not endpoint:
        status["status"] = "skipped"
        status["error"] = "No endpoint provided"
        return status

    try:
        start_time = time.time()
        minio_operator = MinioOperator(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key
        )
        # Test basic operation - list buckets
        buckets = minio_operator.client.list_buckets()
        status["status"] = "healthy"
        status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        status["buckets"] = len(buckets)
    except Exception as e:
        status["status"] = "error"
        status["error"] = str(e)

    return status

async def check_milvus_health(url: str) -> Dict[str, Any]:
    """Check Milvus database health"""
    status = {
        "service": "Milvus",
        "url": url,
        "status": "unknown",
        "error": None
    }

    if not url:
        status["status"] = "skipped"
        status["error"] = "No URL provided"
        return status

    try:
        start_time = time.time()
        parsed_url = urlparse(url)
        connection_alias = f"health_check_{parsed_url.hostname}_{parsed_url.port}_{int(time.time())}"

        # Connect to Milvus
        connections.connect(
            connection_alias,
            host=parsed_url.hostname,
            port=parsed_url.port
        )

        # Test basic operation - list collections
        collections = utility.list_collections(using=connection_alias)

        # Disconnect
        connections.disconnect(connection_alias)

        status["status"] = "healthy"
        status["latency_ms"] = round((time.time() - start_time) * 1000, 2)
        status["collections"] = len(collections)
    except Exception as e:
        status["status"] = "error"
        status["error"] = str(e)

    return status

async def check_all_services_health() -> Dict[str, List[Dict[str, Any]]]:
    """
    Check health of all services used by the application

    Returns:
        Dictionary with service categories and their health status
    """
    config = get_config()

    # Create tasks for different service types
    tasks = []
    results = {
        "databases": [],
        "object_storage": [],
        "nim": [],  # New unified category for NIM services
    }

    # MinIO health check
    minio_endpoint = os.environ.get("MINIO_ENDPOINT", "")
    minio_access_key = os.environ.get("MINIO_ACCESSKEY", "")
    minio_secret_key = os.environ.get("MINIO_SECRETKEY", "")
    if minio_endpoint:
        tasks.append(("object_storage", check_minio_health(
            endpoint=minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key
        )))

    # Vector DB (Milvus) health check
    if config.vector_store.url:
        tasks.append(("databases", check_milvus_health(config.vector_store.url)))

    # LLM service health check
    if config.llm.server_url:
        llm_url = config.llm.server_url
        if not llm_url.startswith(('http://', 'https://')):
            llm_url = f"http://{llm_url}/v1/health/ready"
        else:
            llm_url = f"{llm_url}/v1/health/ready"
        tasks.append(("nim", check_service_health(
            url=llm_url,
            service_name=f"LLM ({config.llm.model_name})"
        )))
    else:
        # When URL is empty, assume the service is running via API catalog
        results["nim"].append({
            "service": f"LLM ({config.llm.model_name})",
            "url": "NVIDIA API Catalog",
            "status": "healthy",
            "latency_ms": 0,
            "message": "Using NVIDIA API Catalog"
        })

    query_rewriter_enabled = os.getenv('ENABLE_QUERYREWRITER', 'True').lower() == 'true'

    if query_rewriter_enabled:
        # Query rewriter LLM health check
        if config.query_rewriter.server_url:
            qr_url = config.query_rewriter.server_url
            if not qr_url.startswith(('http://', 'https://')):
                qr_url = f"http://{qr_url}/v1/health/ready"
            else:
                qr_url = f"{qr_url}/v1/health/ready"
            tasks.append(("nim", check_service_health(
                url=qr_url,
                service_name=f"Query Rewriter ({config.query_rewriter.model_name})"
            )))
        else:
            # When URL is empty, assume the service is running via API catalog
            results["nim"].append({
                "service": f"Query Rewriter ({config.query_rewriter.model_name})",
                "url": "NVIDIA API Catalog",
                "status": "healthy",
                "latency_ms": 0,
                "message": "Using NVIDIA API Catalog"
            })

    # Embedding service health check
    if config.embeddings.server_url:
        embed_url = config.embeddings.server_url
        if not embed_url.startswith(('http://', 'https://')):
            embed_url = f"http://{embed_url}/v1/health/ready"
        else:
            embed_url = f"{embed_url}/v1/health/ready"
        tasks.append(("nim", check_service_health(
            url=embed_url,
            service_name=f"Embeddings ({config.embeddings.model_name})"
        )))
    else:
        # When URL is empty, assume the service is running via API catalog
        results["nim"].append({
            "service": f"Embeddings ({config.embeddings.model_name})",
            "url": "NVIDIA API Catalog",
            "status": "healthy",
            "latency_ms": 0,
            "message": "Using NVIDIA API Catalog"
        })

    enable_reranker = os.getenv('ENABLE_RERANKER', 'True').lower() == 'true'
    # Ranking service health check
    if enable_reranker:
        if config.ranking.server_url:
            ranking_url = config.ranking.server_url
            if not ranking_url.startswith(('http://', 'https://')):
                ranking_url = f"http://{ranking_url}/v1/health/ready"
            else:
                ranking_url = f"{ranking_url}/v1/health/ready"
            tasks.append(("nim", check_service_health(
                url=ranking_url,
                service_name=f"Ranking ({config.ranking.model_name})"
            )))
        else:
            # When URL is empty, assume the service is running via API catalog
            results["nim"].append({
                "service": f"Ranking ({config.ranking.model_name})",
                "url": "NVIDIA API Catalog",
                "status": "healthy",
                "latency_ms": 0,
                "message": "Using NVIDIA API Catalog"
            })

    # NemoGuardrails health check
    enable_guardrails = os.getenv('ENABLE_GUARDRAILS', 'False').lower() == 'true'
    if enable_guardrails:
        guardrails_url = os.getenv('NEMO_GUARDRAILS_URL', '')
        if guardrails_url:
            if not guardrails_url.startswith(('http://', 'https://')):
                guardrails_url = f"http://{guardrails_url}/v1/health"
            else:
                guardrails_url = f"{guardrails_url}/v1/health"
            tasks.append(("nim", check_service_health(
                url=guardrails_url,
                service_name="NemoGuardrails"
            )))
        else:
            results["nim"].append({
                "service": "NemoGuardrails",
                "url": "Not configured",
                "status": "skipped",
                "message": "URL not provided"
            })

    # Reflection LLM health check
    enable_reflection = os.getenv('ENABLE_REFLECTION', 'False').lower() == 'true'
    if enable_reflection:
        reflection_llm = os.getenv('REFLECTION_LLM', '').strip('"').strip("'")
        reflection_url = os.getenv('REFLECTION_LLM_SERVERURL', '').strip('"').strip("'")
        if reflection_url:
            if not reflection_url.startswith(('http://', 'https://')):
                reflection_url = f"http://{reflection_url}/v1/health/ready"
            else:
                reflection_url = f"{reflection_url}/v1/health/ready"
            tasks.append(("nim", check_service_health(
                url=reflection_url,
                service_name=f"Reflection LLM ({reflection_llm})"
            )))
        else:
            # When URL is empty, assume the service is running via API catalog
            results["nim"].append({
                "service": f"Reflection LLM ({reflection_llm})",
                "url": "NVIDIA API Catalog",
                "status": "healthy",
                "latency_ms": 0,
                "message": "Using NVIDIA API Catalog"
            })

    # Execute all health checks concurrently
    for category, task in tasks:
        result = await task
        results[category].append(result)

    return results

def print_health_report(health_results: Dict[str, List[Dict[str, Any]]]) -> None:
    """
    Print health status for individual services

    Args:
        health_results: Results from check_all_services_health
    """
    logger.info("===== SERVICE HEALTH STATUS =====")

    for category, services in health_results.items():
        if not services:
            continue

        for service in services:
            if service["status"] == "healthy":
                logger.info(f"Service '{service['service']}' is healthy - Response time: {service.get('latency_ms', 'N/A')}ms")
            elif service["status"] == "skipped":
                logger.info(f"Service '{service['service']}' check skipped - Reason: {service.get('error', 'No URL provided')}")
            else:
                error_msg = service.get("error", "Unknown error")
                logger.info(f"Service '{service['service']}' is not healthy - Issue: {error_msg}")

    logger.info("================================")

async def check_and_print_services_health():
    """
    Check health of all services and print a report
    """
    health_results = await check_all_services_health()
    print_health_report(health_results)
    return health_results

def check_services_health():
    """
    Synchronous wrapper for checking service health
    """
    return asyncio.run(check_and_print_services_health())
