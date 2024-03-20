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
from functools import lru_cache, wraps
from urllib.parse import urlparse
from typing import TYPE_CHECKING, Callable, List, Optional

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
    from sqlalchemy.engine.url import make_url
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
    from langchain.vectorstores import FAISS
except Exception as e:
    logger.error(f"Langchain import failed with error: {e}")

try:
    from langchain_core.vectorstores import VectorStore
except Exception as e:
    logger.error(f"Langchain core import failed with error: {e}")

try:
    from langchain_community.vectorstores import PGVector
    from langchain_community.vectorstores import Milvus
except Exception as e:
    logger.error(f"Langchain community import failed with error: {e}")

try:
    from langchain_community.chat_models import ChatOpenAI
except Exception as e:
    logger.error(f"NVIDIA AI connector import failed with error: {e}")

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain.llms.base import LLM
from integrations.langchain.llms.triton_trt_llm import TensorRTLLM
from integrations.langchain.llms.nemo_infer import NemoInfer
from integrations.langchain.embeddings.nemo_embed import NemoEmbeddings
from RetrievalAugmentedGeneration.common import configuration

if TYPE_CHECKING:
    from RetrievalAugmentedGeneration.common.configuration_wizard import ConfigWizard

DEFAULT_MAX_CONTEXT = 1500
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

def utils_cache(func: Callable) -> Callable:
    """Use this to convert unhashable args to hashable ones"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Convert unhashable args to hashable ones
        args_hashable = tuple(tuple(arg) if isinstance(arg, (list, dict, set)) else arg for arg in args)
        kwargs_hashable = {key: tuple(value) if isinstance(value, (list, dict, set)) else value for key, value in kwargs.items()}
        return func(*args_hashable, **kwargs_hashable)
    return wrapper

@utils_cache
@lru_cache
def set_service_context(**kwargs) -> None:
    """Set the global service context."""
    llm = LangChainLLM(get_llm(**kwargs))
    embedding = LangchainEmbedding(get_embedding_model())
    service_context = ServiceContext.from_defaults(
        llm=llm, embed_model=embedding
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
def get_vector_index(collection_name: str = "") -> VectorStoreIndex:
    """Create the vector db index."""
    config = get_config()
    vector_store = None

    logger.info(f"Using {config.vector_store.name} as vector store")

    if config.vector_store.name == "pgvector":
        db_name = os.getenv('POSTGRES_DB', None)
        if not collection_name:
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")
        connection_string = f"postgresql://{os.getenv('POSTGRES_USER', '')}:{os.getenv('POSTGRES_PASSWORD', '')}@{config.vector_store.url}/{db_name}"
        logger.info(f"Using PGVector collection: {collection_name}")

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
            table_name=collection_name,
            embed_dim=config.embeddings.dimensions
        )
    elif config.vector_store.name == "milvus":
        if not collection_name:
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")
        logger.info(f"Using milvus collection: {collection_name}")
        vector_store = MilvusVectorStore(uri=config.vector_store.url,
            dim=config.embeddings.dimensions,
            collection_name=collection_name,
            index_config={"index_type": "GPU_IVF_FLAT", "nlist": config.vector_store.nlist},
            search_config={"nprobe": config.vector_store.nprobe},
            overwrite=False)
    else:
        raise RuntimeError("Unable to find any supported Vector Store DB. Supported engines are milvus and pgvector.")
    vector_store_index = VectorStoreIndex.from_vector_store(vector_store)
    return vector_store_index


def get_vectorstore_langchain(documents, document_embedder, collection_name: str = "") -> VectorStore:
    """Create the vector db index for langchain."""

    config = get_config()

    if config.vector_store.name == "faiss":
        vectorstore = FAISS.from_documents(documents, document_embedder)
    elif config.vector_store.name == "pgvector":
        db_name = os.getenv('POSTGRES_DB', None)
        if not collection_name:
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")
        logger.info(f"Using PGVector collection: {collection_name}")
        connection_string = f"postgresql://{os.getenv('POSTGRES_USER', '')}:{os.getenv('POSTGRES_PASSWORD', '')}@{config.vector_store.url}/{db_name}"
        vectorstore = PGVector.from_documents(
            embedding=document_embedder,
            documents=documents,
            collection_name=collection_name,
            connection_string=connection_string,
        )
    elif config.vector_store.name == "milvus":
        if not collection_name:
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")
        logger.info(f"Using milvus collection: {collection_name}")
        url = urlparse(config.vector_store.url)
        vectorstore = Milvus.from_documents(
            documents,
            document_embedder,
            collection_name=collection_name,
            connection_args={"host": url.hostname, "port": url.port}
        )
    else:
        raise ValueError(f"{config.vector_store.name} vector database is not supported")
    logger.info("Vector store created and saved.")
    return vectorstore


@lru_cache
def get_doc_retriever(num_nodes: int = 4) -> "BaseRetriever":
    """Create the document retriever."""
    index = get_vector_index()
    return index.as_retriever(similarity_top_k=num_nodes)


@utils_cache
@lru_cache()
def get_llm(**kwargs) -> LLM | SimpleChatModel:
    """Create the LLM connection."""
    settings = get_config()

    logger.info(f"Using {settings.llm.model_engine} as model engine for llm. Model name: {settings.llm.model_name}")
    if settings.llm.model_engine == "triton-trt-llm":
        trtllm = TensorRTLLM(  # type: ignore
            server_url=settings.llm.server_url,
            model_name=settings.llm.model_name,
            temperature = kwargs.get('temperature', None),
            top_p = kwargs.get('top_p', None),
            tokens = kwargs.get('max_tokens', None)
        )
        unused_params = [key for key in kwargs.keys() if key not in ['temperature', 'top_p', 'max_tokens', 'stream']]
        if unused_params:
            logger.warning(f"The following parameters from kwargs are not supported: {unused_params} for {settings.llm.model_engine}")
        return trtllm
    elif settings.llm.model_engine == "nv-ai-foundation":
        from langchain_nvidia_ai_endpoints import ChatNVIDIA

        unused_params = [key for key in kwargs.keys() if key not in ['temperature', 'top_p', 'max_tokens']]
        if unused_params:
            logger.warning(f"The following parameters from kwargs are not supported: {unused_params} for {settings.llm.model_engine}")
        return ChatNVIDIA(model=settings.llm.model_name,
                          temperature = kwargs.get('temperature', None),
                          top_p = kwargs.get('top_p', None),
                          max_tokens = kwargs.get('max_tokens', None))
    elif settings.llm.model_engine == "nv-api-catalog":
        # Import custom ChatNVIDIA for api catalog
        from integrations.langchain.llms.nv_api_catalog import ChatNVIDIA

        unused_params = [key for key in kwargs.keys() if key not in ['temperature', 'top_p', 'max_tokens']]
        if unused_params:
            logger.warning(f"The following parameters from kwargs are not supported: {unused_params} for {settings.llm.model_engine}")
        return ChatNVIDIA(model=settings.llm.model_name,
                          temperature = kwargs.get('temperature', None),
                          top_p = kwargs.get('top_p', None),
                          max_tokens = kwargs.get('max_tokens', None))
    elif settings.llm.model_engine == "nemo-infer":
        unused_params = [key for key in kwargs.keys() if key not in ['temperature', 'top_p', 'max_tokens',  'stream']]
        if unused_params:
            logger.warning(f"The following parameters from kwargs are not supported: {unused_params} for {settings.llm.model_engine}")
        nemo_infer = NemoInfer(
            server_url=f"http://{settings.llm.server_url}/v1/completions",
            model=settings.llm.model_name,
            temperature = kwargs.get('temperature', None),
            top_p = kwargs.get('top_p', None),
            tokens = kwargs.get('max_tokens', None)
        )
        return nemo_infer
    elif settings.llm.model_engine == "nemo-infer-openai":
        unused_params = [key for key in kwargs.keys() if key not in ['temperature', 'max_tokens',  'stream']]
        if unused_params:
            logger.warning(f"The following parameters from kwargs are not supported: {unused_params} for {settings.llm.model_engine}")
        nemo_infer = ChatOpenAI(
            openai_api_base=f"http://{settings.llm.server_url}/v1/",
            openai_api_key="xyz",
            model_name=settings.llm.model_name,
            temperature = kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', None)
        )
        return nemo_infer
    else:
        raise RuntimeError("Unable to find any supported Large Language Model server. Supported engines are triton-trt-llm, nv-ai-foundation, nv-api-catalog, nemo-infer and nemo-infer-openai.")


@lru_cache
def get_embedding_model() -> Embeddings:
    """Create the embedding model."""
    model_kwargs = {"device": "cpu"}
    if torch.cuda.is_available():
        model_kwargs["device"] = "cuda:0"

    encode_kwargs = {"normalize_embeddings": False}
    settings = get_config()

    logger.info(f"Using {settings.embeddings.model_engine} as model engine and {settings.embeddings.model_name} and model for embeddings")
    if settings.embeddings.model_engine == "huggingface":
        hf_embeddings = HuggingFaceEmbeddings(
            model_name=settings.embeddings.model_name,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
        # Load in a specific embedding model
        return hf_embeddings
    elif settings.embeddings.model_engine == "nv-ai-foundation":
        from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
        return NVIDIAEmbeddings(model=settings.embeddings.model_name, model_type="passage")
    elif settings.embeddings.model_engine == "nv-api-catalog":
        from integrations.langchain.llms.nv_api_catalog import NVIDIAEmbeddings
        return NVIDIAEmbeddings(model=settings.embeddings.model_name, model_type="passage")
    elif settings.embeddings.model_engine == "nemo-embed":
        nemo_embed = NemoEmbeddings(
            server_url=f"http://{settings.embeddings.server_url}/v1/embeddings",
            model_name=settings.embeddings.model_name,
        )
        return nemo_embed
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

    embedding_model_name = TEXT_SPLITTER_EMBEDDING_MODEL
    if get_config().text_splitter.model_name:
        embedding_model_name = get_config().text_splitter.model_name

    return SentenceTransformersTokenTextSplitter(
        model_name=embedding_model_name,
        tokens_per_chunk=get_config().text_splitter.chunk_size - 2,
        chunk_overlap=get_config().text_splitter.chunk_overlap,
    )


def get_docs_vectorstore_langchain(vectorstore: VectorStore) -> List[str]:
    """Retrieves filenames stored in the vector store implemented in LangChain."""

    settings = get_config()
    try:
        # No API availbe in LangChain for listing the docs, thus usig its private _dict 
        extract_filename = lambda metadata : os.path.splitext(os.path.basename(metadata['source']))[0]
        if settings.vector_store.name == "faiss":
            in_memory_docstore = vectorstore.docstore._dict
            filenames = [extract_filename(doc.metadata) for doc in in_memory_docstore.values()]
            filenames = list(set(filenames))
            return filenames
        elif settings.vector_store.name == "pgvector":
            # No API availbe in LangChain for listing the docs, thus usig its private _make_session 
            with vectorstore._make_session() as session:
                embedding_doc_store = session.query(vectorstore.EmbeddingStore.custom_id, vectorstore.EmbeddingStore.document, vectorstore.EmbeddingStore.cmetadata).all()
                filenames = set([extract_filename(metadata) for _, _, metadata in embedding_doc_store])
                return filenames
        elif settings.vector_store.name == "milvus":
            # Getting all the ID's > 0
            milvus_data = vectorstore.col.query(expr="pk >= 0", output_fields=["pk","source", "text"])
            filenames = set([extract_filename(metadata) for metadata in milvus_data])
            return filenames
    except Exception as e:
        logger.error(f"Error occurred while retrieving documents: {e}")
        return []
    

def del_docs_vectorstore_langchain(vectorstore: VectorStore, filenames: List[str]):
    """Delete documents from the vector index implemented in LangChain."""

    settings = get_config()
    try:
        # No other API availbe in LangChain for listing the docs, thus usig its private _dict
        extract_filename = lambda metadata : os.path.splitext(os.path.basename(metadata['source']))[0]
        if settings.vector_store.name == "faiss":
            in_memory_docstore = vectorstore.docstore._dict
            for filename in filenames:
                ids_list = [doc_id for doc_id, doc_data in in_memory_docstore.items() if extract_filename(doc_data.metadata) == filename]
                vectorstore.delete(ids_list)
                logger.info(f"Deleted documents with filenames {filename}")
        elif settings.vector_store.name == "pgvector":
            with vectorstore._make_session() as session:
                embedding_doc_store = session.query(vectorstore.EmbeddingStore.custom_id, vectorstore.EmbeddingStore.document, vectorstore.EmbeddingStore.cmetadata).all()
            for filename in filenames:
                ids_list = [doc_id for doc_id, doc_data, metadata in embedding_doc_store if extract_filename(metadata) == filename]
                vectorstore.delete(ids_list)
                logger.info(f"Deleted documents with filenames {filename}")
        elif settings.vector_store.name == "milvus":
            # Getting all the ID's > 0
            milvus_data = vectorstore.col.query(expr="pk >= 0", output_fields=["pk","source", "text"])
            for filename in filenames:
                ids_list = [metadata["pk"] for metadata in milvus_data if extract_filename(metadata) == filename]
                vectorstore.col.delete(f"pk in {ids_list}")
                logger.info(f"Deleted documents with filenames {filename}")
    except Exception as e:
        logger.error(f"Error occurred while deleting documents: {e}")
