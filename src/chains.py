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

import logging
import os
from traceback import print_exc
from typing import Any
from typing import Dict
from typing import Generator
from typing import List

from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableAssign
from langchain_core.runnables import RunnablePassthrough
from requests import ConnectTimeout

from .base import BaseExample
from .server import Message
from .utils import create_vectorstore_langchain
from .utils import del_docs_vectorstore_langchain
from .utils import get_config
from .utils import get_docs_vectorstore_langchain
from .utils import get_embedding_model
from .utils import get_llm
from .utils import get_prompts
from .utils import get_ranking_model
from .utils import get_text_splitter
from .utils import get_vectorstore

logger = logging.getLogger(__name__)
VECTOR_STORE_PATH = "vectorstore.pkl"
document_embedder = get_embedding_model()
ranker = get_ranking_model()
TEXT_SPLITTER = None
settings = get_config()
prompts = get_prompts()
vector_db_top_k = int(os.environ.get("VECTOR_DB_TOPK", 40))

try:
    VECTOR_STORE = create_vectorstore_langchain(document_embedder=document_embedder)
except Exception as ex:
    VECTOR_STORE = None
    logger.info("Unable to connect to vector store during initialization: %s", ex)


class UnstructuredRAG(BaseExample):

    def ingest_docs(self, data_dir: str, filename: str, collection_name: str = "") -> None:
        """Ingests documents to the VectorDB.
        It's called when the POST endpoint of `/documents` API is invoked.

        Args:
            data_dir (str): The path to the document file.
            filename (str): The name of the document file.
            collection_name (str): The name of the collection to be created in the vectorstore.

        Raises:
            ValueError: If there's an error during document ingestion or the file format is not supported.
        """
        try:
            # Load raw documents from the directory
            _path = data_dir
            raw_documents = UnstructuredFileLoader(_path).load()

            if raw_documents:
                global TEXT_SPLITTER  # pylint: disable=W0603
                # Get text splitter instance, it is selected based on environment variable APP_TEXTSPLITTER_MODELNAME
                # tokenizer dimension of text splitter should be same as embedding model
                if not TEXT_SPLITTER:
                    TEXT_SPLITTER = get_text_splitter()

                # split documents based on configuration provided
                logger.info(f"Using text splitter instance: {TEXT_SPLITTER}")
                documents = TEXT_SPLITTER.split_documents(raw_documents)
                vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
                # ingest documents into vectorstore
                vs.add_documents(documents)
            else:
                logger.warning("No documents available to process!")

        except ConnectTimeout as e:
            logger.warning("Connection timed out while making a request to the NIM model endpoint: %s", e)
            raise ValueError(
                    "Connection timed out while making a request to the embedding model endpoint. Verify if the server is available.") from e

        except Exception as e:
            print_exc()
            logger.error("Failed to ingest document due to exception %s", e)

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                raise ValueError(
                    "Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.") from e

            if "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                raise ValueError(
                    "Please verify the API endpoint and your payload. Ensure that the embedding model name is valid.") from e


            raise ValueError(f"Failed to upload document. {str(e)}") from e

    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above.
        It's called when the `/generate` API is invoked with `use_knowledge_base` set to `False`.

        Args:
            query (str): Query to be answered by llm.
            chat_history (List[Message]): Conversation history between user and chain.
            kwargs: ?
        """

        logger.info("Using llm to generate response directly without knowledge base.")
        system_message = []
        conversation_history = []
        user_message = []
        system_prompt = ""

        system_prompt += prompts.get("chat_template", "")

        for message in chat_history:
            if message.role ==  "system":
                system_prompt = system_prompt + " " + message.content
            else:
                conversation_history.append((message.role, message.content))

        system_message = [("system", system_prompt)]

        logger.info("Query is: %s", query)
        if query is not None and query != "":
            user_message = [("user", "{question}")]

        # Prompt template with system message, conversation history and user query
        message = system_message + conversation_history + user_message

        self.print_conversation_history(message, query)

        prompt_template = ChatPromptTemplate.from_messages(message)

        llm = get_llm(**kwargs)

        # Simple langchain chain to generate response based on user's query
        chain = prompt_template | llm | StrOutputParser()
        return chain.stream({"question": f"{query}"})

    def rag_chain(  # pylint: disable=arguments-differ
            self,
            query: str,
            chat_history: List["Message"],
            top_n: int,
            collection_name: str = "",
            **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above.
        It's called when the `/generate` API is invoked with `use_knowledge_base` set to `True`.

        Args:
            query (str): Query to be answered by llm.
            chat_history (List[Message]): Conversation history between user and chain.
            top_n (int): Fetch n document to generate.
            collection_name (str): Name of the collection to be searched from vectorstore.
            kwargs: ?
        """

        if os.environ.get("ENABLE_MULTITURN", "false").lower() == "true":
            return self.rag_chain_with_multiturn(query, chat_history, top_n, collection_name, **kwargs)
        logger.info("Using rag to generate response from document for the query: %s", query)

        try:
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs is None:
                logger.error("Vector store not initialized properly. Please check if the vector db is up and running")
                raise ValueError()

            llm = get_llm(**kwargs)
            top_k = vector_db_top_k if ranker else top_n
            logger.info("Setting retriever top k as: %s.", top_k)
            retriever = vs.as_retriever(search_kwargs={"k": top_k})  # milvus does not support similarily threshold

            system_prompt = ""
            conversation_history = []
            system_prompt += prompts.get("rag_template", "")

            for message in chat_history:
                if message.role ==  "system":
                    system_prompt = system_prompt + " " + message.content

            system_message = [("system", system_prompt)]
            user_message = [("user", "{question}")]

            # Prompt template with system message, conversation history and user query
            message = system_message + conversation_history + user_message
            self.print_conversation_history(message)
            prompt = ChatPromptTemplate.from_messages(message)

            if ranker:
                logger.info(
                    "Narrowing the collection from %s results and further narrowing it to "
                    "%s with the reranker for rag chain.",
                    top_k,
                    top_n)
                logger.info("Setting ranker top n as: %s.", top_n)
                ranker.top_n = top_n
                reranker = RunnableAssign({
                    "context":
                        lambda input: ranker.compress_documents(query=input['question'], documents=input['context'])
                })

                # Create a chain with retriever and reranker
                retriever = {"context": retriever, "question": RunnablePassthrough()} | reranker
                docs = retriever.invoke(query)

                # Remove metadata from context
                docs = [d.page_content for d in docs.get("context", [])]

                logger.debug("Document Retrieved: %s", docs)
                chain = prompt | llm | StrOutputParser()
            else:
                docs = retriever.invoke(query)
                docs = [d.page_content for d in docs]
                chain = prompt | llm | StrOutputParser()
            return chain.stream({"question": query, "context": docs})
        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()
        logger.warning("No response generated from LLM, make sure you've ingested document.")
        return iter(
            ["No response generated from LLM, make sure you have ingested document from the Knowledge Base Tab."])

    def rag_chain_with_multiturn(self,
                                 query: str,
                                 chat_history: List["Message"],
                                 top_n: int,
                                 collection_name: str,
                                 **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        logger.info("Using multiturn rag to generate response from document for the query: %s", query)

        try:
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs is None:
                logger.error("Vector store not initialized properly. Please check if the vector db is up and running")
                raise ValueError()

            llm = get_llm(**kwargs)
            top_k = vector_db_top_k if ranker else top_n
            logger.info("Setting retriever top k as: %s.", top_k)
            retriever = vs.as_retriever(search_kwargs={"k": top_k})  # milvus does not support similarily threshold

            # conversation is tuple so it should be multiple of two
            # -1 is to keep last k conversation
            history_count = int(os.environ.get("CONVERSATION_HISTORY", 15)) * 2 * -1
            chat_history = chat_history[history_count:]
            system_prompt = ""
            conversation_history = []
            system_prompt += prompts.get("rag_template", "")

            for message in chat_history:
                if message.role ==  "system":
                    system_prompt = system_prompt + " " + message.content
                else:
                    conversation_history.append((message.role, message.content))

            system_message = [("system", system_prompt)]
            retriever_query = query
            if os.environ.get("ENABLE_QUERYREWRITER", "false").lower() == "true":
                # Based on conversation history recreate query for better document retrieval
                contextualize_q_system_prompt = (
                    "Given a chat history and the latest user question "
                    "which might reference context in the chat history, "
                    "formulate a standalone question which can be understood "
                    "without the chat history. Do NOT answer the question, "
                    "just reformulate it if needed and otherwise return it as is."
                )
                query_rewriter_prompt = prompts.get("query_rewriter_prompt", contextualize_q_system_prompt)
                contextualize_q_prompt = ChatPromptTemplate.from_messages(
                    [("system", query_rewriter_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}"),]
                )
                q_prompt = contextualize_q_prompt | llm | StrOutputParser()
                # query to be used for document retrieval
                logger.info("Query rewriter prompt: %s", contextualize_q_prompt)
                retriever_query = q_prompt.invoke({"input": query, "chat_history": conversation_history})
                logger.info("Rewritten Query: %s %s", retriever_query, len(retriever_query))
                if retriever_query.replace('"', "'") == "''" or len(retriever_query) == 0:
                    return iter([""])

            # Prompt for response generation based on context
            user_message = [("user", "{question}")]

            # Prompt template with system message, conversation history and user query
            message = system_message + conversation_history + user_message
            self.print_conversation_history(message)
            prompt = ChatPromptTemplate.from_messages(message)

            if ranker:
                logger.info(
                    "Narrowing the collection from %s results and further narrowing it to "
                    "%s with the reranker for rag chain.",
                    top_k,
                    settings.retriever.top_k)
                logger.info("Setting ranker top n as: %s.", top_n)
                ranker.top_n = top_n
                context_reranker = RunnableAssign({
                    "context":
                        lambda input: ranker.compress_documents(query=input['question'], documents=input['context'])
                })

                retriever = {"context": retriever, "question": RunnablePassthrough()} | context_reranker
                docs = retriever.invoke(retriever_query)
                docs = [d.page_content for d in docs.get("context", [])]
                chain = prompt | llm | StrOutputParser()
            else:
                docs = retriever.invoke(retriever_query)
                docs = [d.page_content for d in docs]
                chain = prompt | llm | StrOutputParser()
            return chain.stream({"question": f"{query}", "context": docs})

        except ConnectTimeout as e:
            logger.warning("Connection timed out while making a request to the LLM endpoint: %s", e)
            return iter(
                    ["Connection timed out while making a request to the NIM endpoint. Verify if the NIM server is available."])

        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                return iter(
                    ["Authentication or permission error: Verify the validity and permissions of your NVIDIA API key."])
            if "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                return iter(
                    ["Please verify the API endpoint and your payload. Ensure that the model name is valid."])

        # Fallback response
        logger.warning("No response generated from LLM, make sure you've ingested document.")
        return iter(
            ["No response generated from LLM, make sure you have ingested document from the Knowledge Base Tab."])

    def document_search(self, content: str, num_docs: int, collection_name: str = "") -> List[Dict[str, Any]]:
        """Search for the most relevant documents for the given search parameters.
        It's called when the `/search` API is invoked.

        Args:
            content (str): Query to be searched from vectorstore.
            num_docs (int): Number of similar docs to be retrieved from vectorstore.
            collection_name (str): Name of the collection to be searched from vectorstore.
        """

        logger.info("Searching relevant document for the query: %s", content)

        try:
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs is None:
                logger.error("Vector store not initialized properly. Please check if the vector db is up and running")
                raise ValueError()

            docs = []
            local_ranker = get_ranking_model()
            top_k = vector_db_top_k if local_ranker else num_docs
            logger.info("Setting top k as: %s.", top_k)
            retriever = vs.as_retriever(search_kwargs={"k": top_k})  # milvus does not support similarily threshold

            if local_ranker:
                logger.info(
                    "Narrowing the collection from %s results and further narrowing it to %s with the reranker for rag"
                    " chain.",
                    top_k,
                    num_docs)
                logger.info("Setting ranker top n as: %s.", num_docs)
                # Update number of document to be retriever by ranker
                local_ranker.top_n = num_docs

                context_reranker = RunnableAssign({
                    "context":
                        lambda input: local_ranker.compress_documents(query=input['question'],
                                                                      documents=input['context'])
                })

                retriever = {"context": retriever, "question": RunnablePassthrough()} | context_reranker
                docs = retriever.invoke(content)
                resp = []
                for doc in docs.get("context"):
                    resp.append({
                        "source": os.path.basename(doc.metadata.get("source", "")),
                        "content": doc.page_content,
                        "score": doc.metadata.get("relevance_score", 0)
                    })
                return resp

            docs = retriever.invoke(content)
            resp = []
            for doc in docs:
                resp.append({
                    "source": os.path.basename(doc.metadata.get("source", "")),
                    "content": doc.page_content,
                    "score": doc.metadata.get("relevance_score", 0)
                })
            return resp

        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

        return []

    def get_documents(self, collection_name: str = "") -> List[str]:
        """Retrieves filenames stored in the vector store.
        It's called when the GET endpoint of `/documents` API is invoked.

        Returns:
            List[str]: List of filenames ingested in vectorstore.
        """
        try:
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs:
                return get_docs_vectorstore_langchain(vs)
        except Exception as e:
            logger.error("Vectorstore not initialized. Error details: %s", e)

        return []

    def delete_documents(self, filenames: List[str], collection_name: str = "") -> bool:
        """Delete documents from the vector index.
        It's called when the DELETE endpoint of `/documents` API is invoked.

        Args:
            filenames (List[str]): List of filenames to be deleted from vectorstore.
            collection_name (str): Name of the collection to be deleted from vectorstore.
        """
        try:
            # Get vectorstore instance
            vs = get_vectorstore(VECTOR_STORE, document_embedder, collection_name)
            if vs:
                return del_docs_vectorstore_langchain(vs, filenames)
        except Exception as e:
            logger.error("Vectorstore not initialized. Error details: %s", e)
        return False

    def print_conversation_history(self, conversation_history: List[str] = None, query: str | None = None):
        if conversation_history is not None:
            for role, content in conversation_history:
                logger.info("Role: %s", role)
                logger.info("Content: %s\n", content)
        if query is not None:
            logger.info("Query: %s\n", query)
