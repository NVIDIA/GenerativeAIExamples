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
import logging
from shlex import quote
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
    from llama_index.core.postprocessor.types import BaseNodePostprocessor
    from llama_index.core.schema import MetadataMode
    from llama_index.core.utils import globals_helper, get_tokenizer
    from llama_index.vector_stores.milvus import MilvusVectorStore
    from llama_index.vector_stores.postgres import PGVectorStore
    from llama_index.core.indices import VectorStoreIndex
    from llama_index.core.service_context import ServiceContext, set_global_service_context
    from llama_index.llms.langchain import LangChainLLM
    from llama_index.embeddings.langchain import LangchainEmbedding
    if TYPE_CHECKING:
        from llama_index.core.indices.base_retriever import BaseRetriever
        from llama_index.core.indices.query.schema import QueryBundle
        from llama_index.core.schema import NodeWithScore
    from RetrievalAugmentedGeneration.common.tracing import llama_index_cb_handler
    from llama_index.core.callbacks import CallbackManager
except Exception as e:
    logger.error(f"Llamaindex import failed with error: {e}")

try:
    from langchain.text_splitter import SentenceTransformersTokenTextSplitter
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import FAISS
except Exception as e:
    logger.error(f"Langchain import failed with error: {e}")

try:
    from langchain_core.vectorstores import VectorStore
except Exception as e:
    logger.error(f"Langchain core import failed with error: {e}")

try:
    from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
except Exception as e:
    logger.error(f"Langchain nvidia ai endpoints import failed with error: {e}")

try:
    from langchain_community.vectorstores import PGVector
    from langchain_community.vectorstores import Milvus
    from langchain_community.docstore.in_memory import InMemoryDocstore
except Exception as e:
    logger.error(f"Langchain community import failed with error: {e}")

try:
    from faiss import IndexFlatL2
except Exception as e:
    logger.error(f"faiss import failed with error: {e}")

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import SimpleChatModel
from langchain.llms.base import LLM
from RetrievalAugmentedGeneration.common import configuration

if TYPE_CHECKING:
    from RetrievalAugmentedGeneration.common.configuration_wizard import ConfigWizard

DEFAULT_MAX_CONTEXT = 1500


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
        llm=llm, embed_model=embedding,
        callback_manager=CallbackManager([llama_index_cb_handler])
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
def get_vector_index(collection_name: str = "") -> "VectorStoreIndex":
    """Create the vector db index."""
    config = get_config()
    vector_store = None
    store_nodes_override = True

    logger.info(f"Using {config.vector_store.name} as vector store")

    if config.vector_store.name == "pgvector":
        db_name = quote(os.getenv('POSTGRES_DB', None))
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
        store_nodes_override = True
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
        store_nodes_override = False
    else:
        raise RuntimeError("Unable to find any supported Vector Store DB. Supported engines are milvus and pgvector.")
    vector_store_index = VectorStoreIndex.from_vector_store(vector_store=vector_store, store_nodes_override=store_nodes_override)
    return vector_store_index


def create_vectorstore_langchain(document_embedder, collection_name: str = "") -> VectorStore:
    """Create the vector db index for langchain."""

    config = get_config()

    if config.vector_store.name == "faiss":
        vectorstore = FAISS(document_embedder, IndexFlatL2(config.embeddings.dimensions), InMemoryDocstore(), {})
    elif config.vector_store.name == "pgvector":
        db_name = os.getenv('POSTGRES_DB', None)
        if not collection_name:
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")
        logger.info(f"Using PGVector collection: {collection_name}")
        connection_string = f"postgresql://{os.getenv('POSTGRES_USER', '')}:{os.getenv('POSTGRES_PASSWORD', '')}@{config.vector_store.url}/{db_name}"
        vectorstore = PGVector(
            collection_name=collection_name,
            connection_string=connection_string,
            embedding_function=document_embedder,
        )
    elif config.vector_store.name == "milvus":
        if not collection_name:
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")
        logger.info(f"Using milvus collection: {collection_name}")
        url = urlparse(config.vector_store.url)
        vectorstore = Milvus(
            document_embedder,
            connection_args={"host": url.hostname, "port": url.port},
            collection_name=collection_name,
            auto_id = True
        )
    else:
        raise ValueError(f"{config.vector_store.name} vector database is not supported")
    logger.info("Vector store created and saved.")
    return vectorstore


def get_vectorstore(vectorstore, document_embedder) -> VectorStore:
    """
    Send a vectorstore object.
    If a Vectorstore object already exists, the function returns that object.
    Otherwise, it creates a new Vectorstore object and returns it.
    """
    if vectorstore is None:
        return create_vectorstore_langchain(document_embedder)
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
    if settings.llm.model_engine == "nvidia-ai-endpoints":
        unused_params = [key for key in kwargs.keys() if key not in ['temperature', 'top_p', 'max_tokens']]
        if unused_params:
            logger.warning(f"The following parameters from kwargs are not supported: {unused_params} for {settings.llm.model_engine}")
        if settings.llm.server_url:
            logger.info(f"Using llm model {settings.llm.model_name} hosted at {settings.llm.server_url}")
            return ChatNVIDIA(base_url=f"http://{settings.llm.server_url}/v1",
                            model=settings.llm.model_name,
                            temperature = kwargs.get('temperature', None),
                            top_p = kwargs.get('top_p', None),
                            max_tokens = kwargs.get('max_tokens', None))
        else:
            logger.info(f"Using llm model {settings.llm.model_name} from api catalog")
            return ChatNVIDIA(model=settings.llm.model_name,
                            temperature = kwargs.get('temperature', None),
                            top_p = kwargs.get('top_p', None),
                            max_tokens = kwargs.get('max_tokens', None))
    else:
        raise RuntimeError("Unable to find any supported Large Language Model server. Supported engine name is nvidia-ai-endpoints.")


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
    elif settings.embeddings.model_engine == "nvidia-ai-endpoints":
        if settings.embeddings.server_url:
            logger.info(f"Using embedding model {settings.embeddings.model_name} hosted at {settings.embeddings.server_url}")
            return NVIDIAEmbeddings(base_url=f"http://{settings.embeddings.server_url}/v1", model=settings.embeddings.model_name, truncate="END")
        else:
            logger.info(f"Using embedding model {settings.embeddings.model_name} hosted at api catalog")
            return NVIDIAEmbeddings(model=settings.embeddings.model_name, truncate="END")
    else:
        raise RuntimeError("Unable to find any supported embedding model. Supported engine is huggingface and nvidia-ai-endpoints.")


def get_text_splitter() -> SentenceTransformersTokenTextSplitter:
    """Return the token text splitter instance from langchain."""

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
                filenames = set([extract_filename(metadata) for _, _, metadata in embedding_doc_store if metadata])
                return filenames
        elif settings.vector_store.name == "milvus":
            # Getting all the ID's > 0
            if vectorstore.col:
                milvus_data = vectorstore.col.query(expr="pk >= 0", output_fields=["pk","source", "text"])
                filenames = set([extract_filename(metadata) for metadata in milvus_data])
                return filenames
    except Exception as e:
        logger.error(f"Error occurred while retrieving documents: {e}")
    return []

def del_docs_vectorstore_langchain(vectorstore: VectorStore, filenames: List[str]) -> bool:
    """Delete documents from the vector index implemented in LangChain."""

    settings = get_config()
    try:
        # No other API availbe in LangChain for listing the docs, thus usig its private _dict
        extract_filename = lambda metadata : os.path.splitext(os.path.basename(metadata['source']))[0]
        if settings.vector_store.name == "faiss":
            in_memory_docstore = vectorstore.docstore._dict
            for filename in filenames:
                ids_list = [doc_id for doc_id, doc_data in in_memory_docstore.items() if extract_filename(doc_data.metadata) == filename]
                if not len(ids_list):
                    logger.info("File does not exist in the vectorstore")
                    return False
                vectorstore.delete(ids_list)
                logger.info(f"Deleted documents with filenames {filename}")
        elif settings.vector_store.name == "pgvector":
            with vectorstore._make_session() as session:
                collection = vectorstore.get_collection(session)
                filter_by = vectorstore.EmbeddingStore.collection_id == collection.uuid
                embedding_doc_store = session.query(vectorstore.EmbeddingStore.custom_id, vectorstore.EmbeddingStore.document, vectorstore.EmbeddingStore.cmetadata).filter(filter_by).all()
            for filename in filenames:
                ids_list = [doc_id for doc_id, doc_data, metadata in embedding_doc_store if extract_filename(metadata) == filename]
                if not len(ids_list):
                    logger.info("File does not exist in the vectorstore")
                    return False
                vectorstore.delete(ids_list)
                logger.info(f"Deleted documents with filenames {filename}")
        elif settings.vector_store.name == "milvus":
            # Getting all the ID's > 0
            milvus_data = vectorstore.col.query(expr="pk >= 0", output_fields=["pk","source", "text"])
            for filename in filenames:
                ids_list = [metadata["pk"] for metadata in milvus_data if extract_filename(metadata) == filename]
                if not len(ids_list):
                    logger.info("File does not exist in the vectorstore")
                    return False
                vectorstore.col.delete(f"pk in {ids_list}")
                logger.info(f"Deleted documents with filenames {filename}")
                return True
    except Exception as e:
        logger.error(f"Error occurred while deleting documents: {e}")
        return False


def get_docs_vectorstore_llamaindex() -> List[str]:
    """Retrieves filenames stored in the vector store implemented in LlamaIndex."""

    settings = get_config()
    index = get_vector_index()
    decoded_filenames = []
    try:
        if settings.vector_store.name == "pgvector":
            ref_doc_info = index.ref_doc_info
            for _ , ref_doc_value in ref_doc_info.items():
                metadata = ref_doc_value.metadata
                if 'filename' in metadata:
                    filename = metadata['filename']
                    decoded_filenames.append(filename)
            decoded_filenames = list(set(decoded_filenames))
        elif settings.vector_store.name == "milvus":
            client = index.vector_store.client
            collection_name = os.getenv('COLLECTION_NAME', "vector_db")
            query_res = client.query(collection_name=collection_name, filter="common_field == 'all'",
                                    output_fields=["filename"])
            if not query_res:
                return decoded_filenames

            filenames = [entry.get('filename') for entry in query_res]
            for filename in filenames:
                decoded_filenames.append(filename)
            decoded_filenames = list(set(decoded_filenames))
        return decoded_filenames
    except Exception as e:
        logger.error(f"Error occurred while retrieving documents: {e}")
        return []


def del_docs_vectorstore_llamaindex(filenames: List[str]) -> bool:
    """Delete documents from the vector index implemented in LlamaIndex."""

    settings = get_config()
    index = get_vector_index()
    try:
        if settings.vector_store.name == "pgvector":
            ref_doc_info = index.ref_doc_info
            for filename in filenames:
                for ref_doc_id, doc_info in ref_doc_info.items():
                    if 'filename' in doc_info.metadata and doc_info.metadata['filename'] == filename:
                        index.delete_ref_doc(ref_doc_id, delete_from_docstore=True)
                        logger.info(f"Deleted documents with filenames {filename}")
        elif settings.vector_store.name == "milvus":
            for filename in filenames:
                client = index.vector_store.client
                collection_name = os.getenv('COLLECTION_NAME', "vector_db")
                query_res = client.query(collection_name=collection_name, filter=f"filename == '{filename}'",
                                        output_fields=["id"])
                if not query_res:
                    logger.info("File does not exist in the vectorstore")
                    return False

                ids = [entry.get('id') for entry in query_res]
                res = client.delete(collection_name=collection_name, filter=f"id in {str(ids)}")
                logger.info(f"Deleted documents with filenames {filename}")
                return True
    except Exception as e:
        logger.error(f"Error occurred while deleting documents: {e}")
        return False
