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

import logging
import os
from functools import lru_cache
from typing import Generator, List, Dict, Any

from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores.faiss import FAISS
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from RetrievalAugmentedGeneration.common.base import BaseExample
from RetrievalAugmentedGeneration.common.utils import get_config, get_llm, get_embedding_model, get_vectorstore_langchain, get_docs_vectorstore_langchain, del_docs_vectorstore_langchain, get_text_splitter

logger = logging.getLogger(__name__)
DOCS_DIR = os.path.abspath("./uploaded_files")
vector_store_path = "vectorstore.pkl"
document_embedder = get_embedding_model()
vectorstore = None
text_splitter = None
settings = get_config()


class NvidiaAPICatalog(BaseExample):
    def ingest_docs(self, file_name: str, filename: str):
        """Ingest documents to the VectorDB."""
        try:
            # TODO: Load embedding created in older conversation, memory persistance
            # We initialize class in every call therefore it should be global
            global vectorstore
            # Load raw documents from the directory
            # Data is copied to `DOCS_DIR` in common.server:upload_document
            _path = os.path.join(DOCS_DIR, filename)
            raw_documents = UnstructuredFileLoader(_path).load()

            if raw_documents:
                global text_splitter
                if not text_splitter:
                    text_splitter = get_text_splitter()

                documents = text_splitter.split_documents(raw_documents)
                if vectorstore:
                    vectorstore.add_documents(documents)
                else:
                    vectorstore = get_vectorstore_langchain(documents, document_embedder)
            else:
                logger.warning("No documents available to process!")
        except Exception as e:
            logger.error(f"Failed to ingest document due to exception {e}")
            raise ValueError("Failed to upload document. Please upload an unstructured text document.")

    def llm_chain(
        self, query: str, chat_history: List["Message"], **kwargs
    ) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above."""

        logger.info("Using llm to generate response directly without knowledge base.")
        system_message = [("system", settings.prompts.chat_template)]
        conversation_history = [(msg.role, msg.content) for msg in chat_history]
        user_input = [("user", "{input}")]

        # Checking if conversation_history is not None and not empty
        prompt_template = ChatPromptTemplate.from_messages(
            system_message + conversation_history + user_input
        ) if conversation_history else ChatPromptTemplate.from_messages(
            system_message + user_input
        )

        llm = get_llm(**kwargs)

        chain = prompt_template | llm | StrOutputParser()
        augmented_user_input = (
            "\n\nQuestion: " + query + "\n"
        )
        return chain.stream({"input": augmented_user_input})

    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        logger.info("Using rag to generate response from document")
        system_message = [("system", settings.prompts.rag_template)]
        conversation_history = [(msg.role, msg.content) for msg in chat_history]
        user_input = [("user", "{input}")]

        # Checking if conversation_history is not None and not empty
        prompt_template = ChatPromptTemplate.from_messages(
            system_message + conversation_history + user_input
        ) if conversation_history else ChatPromptTemplate.from_messages(
            system_message + user_input
        )

        llm = get_llm(**kwargs)

        chain = prompt_template | llm | StrOutputParser()

        try:
            if vectorstore != None:
                try:
                    logger.info(f"Getting retrieved top k values: {settings.retriever.top_k} with confidence threshold: {settings.retriever.score_threshold}")
                    retriever = vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": settings.retriever.score_threshold, "k": settings.retriever.top_k})
                    docs = retriever.get_relevant_documents(query)
                except NotImplementedError:
                    # Some retriever like milvus don't have similarity score threshold implemented
                    retriever = vectorstore.as_retriever()
                    docs = retriever.get_relevant_documents(query)

                if not docs:
                    logger.warning("Retrieval failed to get any relevant context")
                    return iter(["No response generated from LLM, make sure your query is relavent to the ingested document."])

                context = ""
                for doc in docs:
                    context += doc.page_content + "\n\n"

                augmented_user_input = (
                    "Context: " + context + "\n\nQuestion: " + query + "\n"
                )

                return chain.stream({"input": augmented_user_input})
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
            if vectorstore != None:
                try:
                    retriever = vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": settings.retriever.score_threshold, "k": settings.retriever.top_k})
                    docs = retriever.get_relevant_documents(content)
                except NotImplementedError:
                    # Some retriever like milvus don't have similarity score threshold implemented
                    retriever = vectorstore.as_retriever()
                    docs = retriever.get_relevant_documents(content)

                result = []
                for doc in docs:
                    result.append(
                        {
                        "source": os.path.basename(doc.metadata.get('source', '')),
                        "content": doc.page_content
                        }
                    )
                return result
            return []
        except Exception as e:
            logger.error(f"Error from POST /search endpoint. Error details: {e}")

    def get_documents(self) -> List[str]:
        """Retrieves filenames stored in the vector store."""
        try:
            if vectorstore:
                return get_docs_vectorstore_langchain(vectorstore)
        except Exception as e:
            logger.error(f"Vectorstore not initialized. Error details: {e}")
        return []


    def delete_documents(self, filenames: List[str]):
        """Delete documents from the vector index."""
        try:
            if vectorstore:
                return del_docs_vectorstore_langchain(vectorstore, filenames)
        except Exception as e:
            logger.error(f"Vectorstore not initialized. Error details: {e}")