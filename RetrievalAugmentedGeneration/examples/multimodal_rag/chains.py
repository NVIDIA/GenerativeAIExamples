# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import logging
import os
from typing import Generator, List, Dict, Any
from functools import lru_cache
from traceback import print_exc

from RetrievalAugmentedGeneration.common.utils import utils_cache

logger = logging.getLogger(__name__)

from RetrievalAugmentedGeneration.common.base import BaseExample
from RetrievalAugmentedGeneration.example.llm.llm_client import LLMClient
from RetrievalAugmentedGeneration.example.retriever.embedder import NVIDIAEmbedders
from RetrievalAugmentedGeneration.example.retriever.vector import MilvusVectorClient
from RetrievalAugmentedGeneration.example.retriever.retriever import Retriever
from RetrievalAugmentedGeneration.example.vectorstore.vectorstore_updater import update_vectorstore
from RetrievalAugmentedGeneration.common.utils import get_config
from RetrievalAugmentedGeneration.common.tracing import langchain_instrumentation_class_wrapper 

settings = get_config()
sources = []
RESPONSE_PARAPHRASING_MODEL = settings.llm.model_name

@lru_cache
def get_vector_index(embed_dim: int = 1024) -> MilvusVectorClient:
    return MilvusVectorClient(hostname="milvus", port="19530", collection_name=os.getenv('COLLECTION_NAME', "vector_db"), embedding_size=embed_dim)

@lru_cache
def get_embedder(type: str = "query") -> NVIDIAEmbedders:
    if type == "query":
        embedder = NVIDIAEmbedders(name=settings.embeddings.model_name, type="query")
    else:
        embedder = NVIDIAEmbedders(name=settings.embeddings.model_name, type="passage")
    return embedder

@lru_cache
def get_doc_retriever(type: str = "query") -> Retriever:
    embedder = get_embedder(type)
    embedding_size = embedder.get_embedding_size()
    return Retriever(embedder=get_embedder(type) , vector_client=get_vector_index(embedding_size))

@utils_cache
@lru_cache()
def get_llm(model_name, cb_handler, is_response_generator=False, **kwargs):
    return LLMClient(model_name=model_name, is_response_generator=is_response_generator, cb_handler=cb_handler, **kwargs)


@langchain_instrumentation_class_wrapper
class MultimodalRAG(BaseExample):

    def ingest_docs(self, filepath: str, filename: str):
        """Ingest documents to the VectorDB."""

        if not filename.endswith(".pdf"):
            raise ValueError(f"{filename} is not a valid PDF file. Only PDF files are supported for multimodal rag. The PDF files can contain multimodal data.")

        try:
            embedder = get_embedder(type="passage")
            embedding_size = embedder.get_embedding_size()
            update_vectorstore(os.path.abspath(filepath), get_vector_index(embedding_size), embedder, os.getenv('COLLECTION_NAME', "vector_db"))
        except Exception as e:
            logger.error(f"Failed to ingest document due to exception {e}")
            print_exc()
            raise ValueError("Failed to upload document. Please check chain server logs for details.")


    def llm_chain(
        self, query: str, chat_history: List["Message"], **kwargs
    ) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above."""
        # TODO integrate chat_history
        logger.info("Using llm to generate response directly without knowledge base.")
        response = get_llm(model_name=RESPONSE_PARAPHRASING_MODEL, cb_handler=self.cb_handler, is_response_generator=True, **kwargs).chat_with_prompt(settings.prompts.chat_template, query)
        return response


    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        logger.info("Using rag to generate response from document")
        # TODO integrate chat_history
        try:
            retriever = get_doc_retriever(type="query")
            context, sources = retriever.get_relevant_docs(query, limit=settings.retriever.top_k)
            if not context:
                logger.warning("Retrieval failed to get any relevant context")
                return iter(["No response generated from LLM, make sure your query is relavent to the ingested document."])

            augmented_prompt = "Relevant documents:" + context + "\n\n[[QUESTION]]\n\n" + query
            system_prompt = settings.prompts.rag_template
            logger.info(f"Formulated prompt for RAG chain: {system_prompt}\n{augmented_prompt}")
            response = get_llm(model_name=RESPONSE_PARAPHRASING_MODEL, cb_handler=self.cb_handler, is_response_generator=True, **kwargs).chat_with_prompt(settings.prompts.rag_template, augmented_prompt)
            return response

        except Exception as e:
            logger.warning(f"Failed to generate response due to exception {e}")
        logger.warning(
            "No response generated from LLM, make sure you've ingested document."
        )
        return iter(
            [
                "No response generated from LLM, make sure you have ingested document from the Knowledge Base Tab."
            ]
        )

    def document_search(self, content: str, num_docs: int) -> List[Dict[str, Any]]:
        """Search for the most relevant documents for the given search parameters."""

        try:
            retriever = get_doc_retriever(type="query")
            context, sources = retriever.get_relevant_docs(content, limit=settings.retriever.top_k)
            output = []
            for every_chunk in sources.values():
                entry = {"source": every_chunk['doc_metadata']['filename'], "content": every_chunk['doc_content']}
                output.append(entry)
            return output
        except Exception as e:
            logger.error(f"Error from POST /search endpoint. Error details: {e}")
        return []

    def get_documents(self):
        """Retrieves filenames stored in the vector store."""
        embedding_size = get_embedder(type="passage").get_embedding_size()
        vector_db = get_vector_index(embedding_size)
        decoded_filenames = vector_db.list_filenames()
        return decoded_filenames

    def delete_documents(self, filenames: List[str]):
        """Delete documents from the vector index."""
        embedding_size = get_embedder(type="passage").get_embedding_size()
        vector_db = get_vector_index(embedding_size)
        for each_file in filenames:
            vector_db.delete_by_filename(each_file)