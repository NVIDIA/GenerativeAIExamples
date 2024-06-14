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

"""LLM Chains for executing Retrival Augmented Generation."""
import os
import logging
import nltk
from pathlib import Path
from typing import Generator, List, Dict, Any

from llama_index.core.prompts.base import Prompt
from llama_index.core.readers import download_loader
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.base.response.schema import StreamingResponse
from llama_index.core.node_parser import LangchainNodeParser
from llama_index.llms.langchain import LangChainLLM
from llama_index.embeddings.langchain import LangchainEmbedding
from RetrievalAugmentedGeneration.common.tracing import llama_index_cb_handler
from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager

from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate

from RetrievalAugmentedGeneration.common.utils import (
    LimitRetrievedNodesLength,
    get_config,
    get_doc_retriever,
    get_llm,
    get_text_splitter,
    get_vector_index,
    set_service_context,
    get_embedding_model,
    get_docs_vectorstore_llamaindex,
    del_docs_vectorstore_llamaindex,
)
from RetrievalAugmentedGeneration.common.base import BaseExample
from RetrievalAugmentedGeneration.common.tracing import (
    langchain_instrumentation_class_wrapper,
)

# nltk downloader
# nltk.download("averaged_perceptron_tagger")

# prestage the embedding model
_ = get_embedding_model()
set_service_context()


logger = logging.getLogger(__name__)
text_splitter = None


@langchain_instrumentation_class_wrapper
class QAChatbot(BaseExample):

    def ingest_docs(self, filepath: str, filename: str):
        """Ingest documents to the VectorDB."""
        try:
            Settings.callback_manager = CallbackManager([llama_index_cb_handler])
            logger.info(f"Ingesting {filename} in vectorDB")
            _, ext = os.path.splitext(filename)

            if ext.lower() == ".pdf":
                PDFReader = download_loader("PDFReader")
                loader = PDFReader()
                documents = loader.load_data(file=Path(filepath))

            else:
                unstruct_reader = download_loader("UnstructuredReader")
                loader = unstruct_reader()
                documents = loader.load_data(file=Path(filepath), split_documents=False)

            filename = filename[:-4]

            for document in documents:
                document.metadata = {"filename": filename, "common_field": "all"}
                document.excluded_embed_metadata_keys = ["filename", "page_label"]

            index = get_vector_index()

            global text_splitter
            if not text_splitter:
                text_splitter = get_text_splitter()
            node_parser = LangchainNodeParser(text_splitter)
            nodes = node_parser.get_nodes_from_documents(documents)
            index.insert_nodes(nodes)
            logger.info(f"Document {filename} ingested successfully")
        except Exception as e:
            logger.error(f"Failed to ingest document due to exception {e}")
            raise ValueError(
                "Failed to upload document. Please upload an unstructured text document."
            )

    def get_documents(self):
        """Retrieves filenames stored in the vector store."""
        return get_docs_vectorstore_llamaindex()

    def delete_documents(self, filenames: List[str]):
        """Delete documents from the vector index."""
        return del_docs_vectorstore_llamaindex(filenames)

    def llm_chain(
        self, query: str, chat_history: List["Message"], **kwargs
    ) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above."""

        logger.info("Using llm to generate response directly without knowledge base.")
        set_service_context(**kwargs)
        # TODO Include chat_history
        prompt = get_config().prompts.chat_template

        logger.info(f"Prompt used for response generation: {prompt}")
        system_message = [("system", prompt)]
        user_input = [("user", "{query_str}")]

        prompt_template = ChatPromptTemplate.from_messages(
            system_message + user_input
        )

        llm = get_llm(**kwargs)

        chain = prompt_template | llm | StrOutputParser()
        return chain.stream(
            {"query_str": query},
            config={"callbacks": [self.cb_handler]},
        )

    def rag_chain(
        self, query: str, chat_history: List["Message"], **kwargs
    ) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        logger.info("Using rag to generate response from document")

        set_service_context(**kwargs)

        retriever = get_doc_retriever(num_nodes=get_config().retriever.top_k)
        qa_template = Prompt(get_config().prompts.rag_template)

        logger.info(f"Prompt template used for response generation: {qa_template}")

        # Handling Retrieval failure
        nodes = retriever.retrieve(query)
        if not nodes:
            logger.warning("Retrieval failed to get any relevant context")
            return iter(
                [
                    "No response generated from LLM, make sure your query is relavent to the ingested document."
                ]
            )

        # TODO Include chat_history
        query_engine = RetrieverQueryEngine.from_args(
            retriever,
            text_qa_template=qa_template,
            node_postprocessors=[LimitRetrievedNodesLength()],
            streaming=True,
        )
        response = query_engine.query(query)

        # Properly handle an empty response
        if isinstance(response, StreamingResponse):
            return response.response_gen

        logger.warning(
            "No response generated from LLM, make sure you've ingested document."
        )
        return StreamingResponse(iter(["No response generated from LLM, make sure you have ingested document from the Knowledge Base Tab."])).response_gen  # type: ignore

    def document_search(self, content: str, num_docs: int) -> List[Dict[str, Any]]:
        """Search for the most relevant documents for the given search parameters."""

        try:
            retriever = get_doc_retriever(num_nodes=get_config().retriever.top_k)
            nodes = retriever.retrieve(content)
            output = []
            for node in nodes:
                file_name = nodes[0].metadata["filename"]
                entry = {"score": node.score, "source": file_name, "content": node.text}
                output.append(entry)

            return output

        except Exception as e:
            logger.error(f"Error from /documentSearch endpoint. Error details: {e}")
            return []
