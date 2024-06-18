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

"""RAG example showcasing multi-turn conversation."""
import base64
import os
import logging
from pathlib import Path
from typing import Generator, List, Dict, Any

from langchain_community.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.prompts.prompt import PromptTemplate
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.runnables.passthrough import RunnableAssign

# pylint: disable=no-name-in-module, disable=import-error
from RetrievalAugmentedGeneration.common.utils import (
    get_config,
    get_llm,
    create_vectorstore_langchain,
    get_embedding_model,
    get_text_splitter,
    get_docs_vectorstore_langchain,
    del_docs_vectorstore_langchain,
    get_vectorstore
)
from RetrievalAugmentedGeneration.common.base import BaseExample
from RetrievalAugmentedGeneration.common.tracing import langchain_instrumentation_class_wrapper
from operator import itemgetter

document_embedder = get_embedding_model()
text_splitter = None
settings = get_config()
logger = logging.getLogger(__name__)

try:
    docstore = create_vectorstore_langchain(document_embedder=document_embedder)
except Exception as e:
    docstore = None
    logger.info(f"Unable to connect to vector store during initialization: {e}")


@langchain_instrumentation_class_wrapper
class MultiTurnChatbot(BaseExample):

    def save_memory_and_get_output(self, d, vstore):
        """Accepts 'input'/'output' dictionary and saves to convstore"""
        vstore.add_texts(
            [
                f"User previously responded with {d.get('input')}",
                f"Agent previously responded with {d.get('output')}",
            ]
        )
        return d.get("output")

    def ingest_docs(self, filepath: str, filename: str):
        """Ingest documents to the VectorDB."""
        if  not filename.endswith((".txt",".pdf",".md")):
            raise ValueError(f"{filename} is not a valid Text, PDF or Markdown file")
        try:
            # Load raw documents from the directory
            _path = filepath
            raw_documents = UnstructuredFileLoader(_path).load()

            if raw_documents:
                global text_splitter
                if not text_splitter:
                    text_splitter = get_text_splitter()

                documents = text_splitter.split_documents(raw_documents)
                ds = get_vectorstore(docstore, document_embedder)
                ds.add_documents(documents)
            else:
                logger.warning("No documents available to process!")
        except Exception as e:
            logger.error(f"Failed to ingest document due to exception {e}")
            raise ValueError(
                "Failed to upload document. Please upload an unstructured text document."
            )

    def llm_chain(
        self, query: str, chat_history: List["Message"], **kwargs
    ) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above."""

        logger.info("Using llm to generate response directly without knowledge base.")
        # WAR: Disable chat history (UI consistency).
        chat_history = []
        conversation_history = [(msg.role, msg.content) for msg in chat_history]
        system_message = [("system", settings.prompts.chat_template)]
        user_message = [("user", "{query_str}")]

        # TODO: Enable this block once conversation history is enabled for llm chain
        # Checking if conversation_history is not None and not empty
        # prompt_template = ChatPromptTemplate.from_messages(
        #     system_message + conversation_history + user_message
        # ) if conversation_history else ChatPromptTemplate.from_messages(
        #     system_message + user_message
        # )
        prompt_template = ChatPromptTemplate.from_messages(
            system_message + user_message
        )

        llm = get_llm(**kwargs)
        chain = prompt_template | llm | StrOutputParser()

        logger.info(f"Prompt used for response generation: {prompt_template.format(query_str=query)}")
        return chain.stream({"query_str": query}, config={"callbacks":[self.cb_handler]})

    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        logger.info("Using rag to generate response from document")

        # chat_prompt = ChatPromptTemplate.from_messages(
        #     [
        #         ("system", settings.prompts.multi_turn_rag_template),
        #         ("user", "{input}"),
        #     ]
        # )

        # This is a workaround Prompt Template
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("user", settings.prompts.multi_turn_rag_template + "User Query: {input}"),
            ]
        )

        llm = get_llm(**kwargs)
        stream_chain = chat_prompt | llm | StrOutputParser()

        convstore = create_vectorstore_langchain(
            document_embedder, collection_name="conv_store"
        )

        resp_str = ""
        # TODO Integrate chat_history
        try:
            ds = get_vectorstore(docstore, document_embedder)
            if ds:

                try:
                    logger.info(f"Getting retrieved top k values: {settings.retriever.top_k} with confidence threshold: {settings.retriever.score_threshold}")
                    retrieval_chain = (
                        RunnableAssign(
                            {"context": itemgetter("input") | ds.as_retriever(search_type="similarity_score_threshold",
                                                                                    search_kwargs={"score_threshold": settings.retriever.score_threshold, "k": settings.retriever.top_k})}
                        )
                        | RunnableAssign(
                            {"history": itemgetter("input") | convstore.as_retriever(search_type="similarity_score_threshold",
                                                                                    search_kwargs={"score_threshold": settings.retriever.score_threshold, "k": settings.retriever.top_k})}
                        )
                    )

                    # Handling Retrieval failure
                    docs = retrieval_chain.invoke({"input": query}, config={"callbacks":[self.cb_handler]})
                    if not docs:
                        logger.warning("Retrieval failed to get any relevant context")
                        return iter(["No response generated from LLM, make sure your query is relavent to the ingested document."])

                    logger.debug(f"Retrieved docs are: {docs}")

                    chain = retrieval_chain | stream_chain

                    for chunk in chain.stream({"input": query}, config={"callbacks":[self.cb_handler]}):
                        yield chunk
                        resp_str += chunk

                    self.save_memory_and_get_output(
                        {"input": query, "output": resp_str}, convstore
                    )

                    return chain.stream(query, config={"callbacks":[self.cb_handler]})

                except NotImplementedError:
                    # TODO: Optimize it, currently error is raised during stream
                    # check if there is better way to handle this similarity case
                    logger.info(f"Skipping similarity score as it's not supported by retriever")
                    # Some retriever like milvus don't have similarity score threshold implemented
                    retrieval_chain = (
                        RunnableAssign(
                            {"context": itemgetter("input") | ds.as_retriever()}
                        )
                        | RunnableAssign(
                            {"history": itemgetter("input") | convstore.as_retriever()}
                        )
                    )

                    # Handling Retrieval failure
                    docs = retrieval_chain.invoke({"input": query}, config={"callbacks":[self.cb_handler]})
                    if not docs:
                        logger.warning("Retrieval failed to get any relevant context")
                        return iter(["No response generated from LLM, make sure your query is relavent to the ingested document."])

                    logger.debug(f"Retrieved documents are: {docs}")
                    chain = retrieval_chain | stream_chain
                    for chunk in chain.stream({"input": query}, config={"callbacks":[self.cb_handler]}):
                        yield chunk
                        resp_str += chunk

                    self.save_memory_and_get_output(
                        {"input": query, "output": resp_str}, convstore
                    )

                    return chain.stream(query, config={"callbacks":[self.cb_handler]})

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
            ds = get_vectorstore(docstore, document_embedder)
            if ds != None:
                try:
                    retriever = ds.as_retriever(
                        search_type="similarity_score_threshold",
                        search_kwargs={"score_threshold": settings.retriever.score_threshold, "k": settings.retriever.top_k},
                    )
                    docs = retriever.invoke(content, config={"callbacks":[self.cb_handler]})
                except NotImplementedError:
                    # Some retriever like milvus don't have similarity score threshold implemented
                    retriever = ds.as_retriever()
                    docs = retriever.invoke(content, config={"callbacks":[self.cb_handler]})

                result = []
                for doc in docs:
                    result.append(
                        {
                            "source": os.path.basename(doc.metadata.get("source", "")),
                            "content": doc.page_content,
                        }
                    )
                return result
            return []
        except Exception as e:
            logger.error(f"Error from /documentSearch endpoint. Error details: {e}")
            return []

    def get_documents(self) -> List[str]:
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