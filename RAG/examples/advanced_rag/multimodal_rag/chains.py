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
from functools import lru_cache
from traceback import print_exc
from typing import Any, Dict, Generator, List

from langchain_community.document_loaders import UnstructuredFileLoader

from RAG.src.chain_server.utils import utils_cache

logger = logging.getLogger(__name__)

from RAG.examples.advanced_rag.multimodal_rag.llm.llm_client import LLMClient
from RAG.examples.advanced_rag.multimodal_rag.vectorstore.vectorstore_updater import update_vectorstore
from RAG.src.chain_server.base import BaseExample
from RAG.src.chain_server.tracing import langchain_instrumentation_class_wrapper
from RAG.src.chain_server.utils import (
    create_vectorstore_langchain,
    del_docs_vectorstore_langchain,
    get_config,
    get_docs_vectorstore_langchain,
    get_embedding_model,
    get_prompts,
    get_text_splitter,
    get_vectorstore,
)

document_embedder = get_embedding_model()
text_splitter = None
settings = get_config()
prompts = get_prompts()
sources = []
RESPONSE_PARAPHRASING_MODEL = settings.llm.model_name

try:
    docstore = create_vectorstore_langchain(document_embedder=document_embedder)
except Exception as e:
    docstore = None
    logger.info(f"Unable to connect to vector store during initialization: {e}")


@utils_cache
@lru_cache()
def get_llm(model_name, cb_handler, is_response_generator=False, **kwargs):
    return LLMClient(
        model_name=model_name, is_response_generator=is_response_generator, cb_handler=cb_handler, **kwargs
    )


@langchain_instrumentation_class_wrapper
class MultimodalRAG(BaseExample):
    def ingest_docs(self, filepath: str, filename: str):
        """Ingest documents to the VectorDB."""

        if not filename.endswith((".pdf", ".pptx", ".png")):
            raise ValueError(
                f"{filename} is not a valid PDF/PPTX/PNG file. Only PDF/PPTX/PNG files are supported for multimodal rag. The PDF/PPTX/PNG files can contain multimodal data."
            )

        try:
            _path = filepath
            ds = get_vectorstore(docstore, document_embedder)
            update_vectorstore(_path, ds, document_embedder, os.getenv('COLLECTION_NAME', "vector_db"))
        except Exception as e:
            logger.error(f"Failed to ingest document due to exception {e}")
            raise ValueError("Failed to upload document. Please upload an unstructured text document.")

    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above."""
        # TODO integrate chat_history
        logger.info("Using llm to generate response directly without knowledge base.")
        response = get_llm(
            model_name=RESPONSE_PARAPHRASING_MODEL, cb_handler=self.cb_handler, is_response_generator=True, **kwargs
        ).chat_with_prompt(prompts.get("chat_template", ""), query)
        return response

    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        logger.info("Using rag to generate response from document")
        # TODO integrate chat_history
        try:
            ds = get_vectorstore(docstore, document_embedder)
            if ds:
                try:
                    logger.info(
                        f"Getting retrieved top k values: {settings.retriever.top_k} with confidence threshold: {settings.retriever.score_threshold}"
                    )
                    retriever = ds.as_retriever(
                        search_type="similarity_score_threshold",
                        search_kwargs={
                            "score_threshold": settings.retriever.score_threshold,
                            "k": settings.retriever.top_k,
                        },
                    )
                    docs = retriever.invoke(input=query, config={"callbacks": [self.cb_handler]})
                    if not docs:
                        logger.warning("Retrieval failed to get any relevant context")
                        return iter(
                            [
                                "No response generated from LLM, make sure your query is relavent to the ingested document."
                            ]
                        )

                    augmented_prompt = "Relevant documents:" + docs + "\n\n[[QUESTION]]\n\n" + query
                    system_prompt = prompts.get("rag_template", "")
                    logger.info(f"Formulated prompt for RAG chain: {system_prompt}\n{augmented_prompt}")
                    response = get_llm(
                        model_name=RESPONSE_PARAPHRASING_MODEL,
                        cb_handler=self.cb_handler,
                        is_response_generator=True,
                        **kwargs,
                    ).chat_with_prompt(prompts.get("rag_template", ""), augmented_prompt)
                    return response
                except Exception as e:
                    logger.info(f"Skipping similarity score as it's not supported by retriever")
                    retriever = ds.as_retriever()
                    docs = retriever.invoke(input=query, config={"callbacks": [self.cb_handler]})
                    if not docs:
                        logger.warning("Retrieval failed to get any relevant context")
                        return iter(
                            [
                                "No response generated from LLM, make sure your query is relavent to the ingested document."
                            ]
                        )
                    docs = [doc.page_content for doc in docs]
                    docs = " ".join(docs)
                    augmented_prompt = "Relevant documents:" + docs + "\n\n[[QUESTION]]\n\n" + query
                    system_prompt = prompts.get("rag_template", "")
                    logger.info(f"Formulated prompt for RAG chain: {system_prompt}\n{augmented_prompt}")
                    response = get_llm(
                        model_name=RESPONSE_PARAPHRASING_MODEL,
                        cb_handler=self.cb_handler,
                        is_response_generator=True,
                        **kwargs,
                    ).chat_with_prompt(prompts.get("rag_template", ""), augmented_prompt)
                    return response
        except Exception as e:
            logger.warning(f"Failed to generate response due to exception {e}")
        logger.warning("No response generated from LLM, make sure you've ingested document.")
        return iter(
            ["No response generated from LLM, make sure you have ingested document from the Knowledge Base Tab."]
        )

    def document_search(self, content: str, num_docs: int) -> List[Dict[str, Any]]:
        """Search for the most relevant documents for the given search parameters."""

        try:
            ds = get_vectorstore(docstore, document_embedder)
            retriever = ds.as_retriever()
            sources = retriever.invoke(input=content, limit=num_docs, config={"callbacks": [self.cb_handler]})
            output = []
            for every_chunk in sources:
                entry = {"source": every_chunk.metadata['filename'], "content": every_chunk.page_content}
                output.append(entry)
            return output
        except Exception as e:
            logger.error(f"Error from POST /search endpoint. Error details: {e}")
        return []

    def get_documents(self):
        """Retrieves filenames stored in the vector store."""
        try:
            ds = get_vectorstore(docstore, document_embedder)
            if ds:
                return get_docs_vectorstore_langchain(ds)
        except Exception as e:
            logger.error(f"Vectorstore not initialized. Error details: {e}")
        return []

    def delete_documents(self, filenames: List[str]):
        """Delete documents from the vector index."""
        try:
            ds = get_vectorstore(docstore, document_embedder)
            if ds:
                return del_docs_vectorstore_langchain(ds, filenames)
        except Exception as e:
            logger.error(f"Vectorstore not initialized. Error details: {e}")
