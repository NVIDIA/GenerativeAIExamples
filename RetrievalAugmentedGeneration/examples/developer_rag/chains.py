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
import base64
import os
import logging
from pathlib import Path
from typing import Generator, List, Dict, Any

from llama_index import Prompt, download_loader
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.response.schema import StreamingResponse
from llama_index.node_parser import LangchainNodeParser

from RetrievalAugmentedGeneration.common.utils import (
    LimitRetrievedNodesLength,
    get_config,
    get_doc_retriever,
    get_llm,
    get_text_splitter,
    get_vector_index,
    is_base64_encoded,
    set_service_context,
    get_embedding_model,
)
from RetrievalAugmentedGeneration.common.base import BaseExample

# prestage the embedding model
_ = get_embedding_model()
set_service_context()


logger = logging.getLogger(__name__)

class QAChatbot(BaseExample):
    def ingest_docs(self, data_dir: str, filename: str):
        """Ingest documents to the VectorDB."""

        try:
            logger.info(f"Ingesting {filename} in vectorDB")
            _, ext = os.path.splitext(filename)

            if ext.lower() == ".pdf":
                PDFReader = download_loader("PDFReader")
                loader = PDFReader()
                documents = loader.load_data(file=Path(data_dir))

            else:
                unstruct_reader = download_loader("UnstructuredReader")
                loader = unstruct_reader()
                documents = loader.load_data(file=Path(data_dir), split_documents=False)

            encoded_filename = filename[:-4]
            if not is_base64_encoded(encoded_filename):
                encoded_filename = base64.b64encode(encoded_filename.encode("utf-8")).decode(
                    "utf-8"
                )

            for document in documents:
                document.metadata = {"filename": encoded_filename}

            index = get_vector_index()
            node_parser = LangchainNodeParser(get_text_splitter())
            nodes = node_parser.get_nodes_from_documents(documents)
            index.insert_nodes(nodes)
            logger.info(f"Document {filename} ingested successfully")
        except Exception as e:
            logger.error(f"Failed to ingest document due to exception {e}")
            raise ValueError("Failed to upload document. Please upload an unstructured text document.")

    def llm_chain(self, context: str, question: str, num_tokens: int) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above."""

        logger.info("Using llm to generate response directly without knowledge base.")
        set_service_context()
        prompt = get_config().prompts.chat_template.format(
            context_str=context, query_str=question
        )

        logger.info(f"Prompt used for response generation: {prompt}")
        response = get_llm().stream_complete(prompt, tokens=num_tokens)
        gen_response = (resp.delta for resp in response)
        return gen_response

    def rag_chain(self, prompt: str, num_tokens: int) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        logger.info("Using rag to generate response from document")

        set_service_context()
        if get_config().llm.model_engine == "triton-trt-llm":
            get_llm().llm.tokens = num_tokens  # type: ignore
        else:
            get_llm().llm.max_tokens = num_tokens
        retriever = get_doc_retriever(num_nodes=4)
        qa_template = Prompt(get_config().prompts.rag_template)

        logger.info(f"Prompt used for response generation: {qa_template}")
        query_engine = RetrieverQueryEngine.from_args(
            retriever,
            text_qa_template=qa_template,
            node_postprocessors=[LimitRetrievedNodesLength()],
            streaming=True,
        )
        response = query_engine.query(prompt)

        # Properly handle an empty response
        if isinstance(response, StreamingResponse):
            return response.response_gen

        logger.warning("No response generated from LLM, make sure you've ingested document.")
        return StreamingResponse(iter(["No response generated from LLM, make sure you have ingested document from the Knowledge Base Tab."])).response_gen  # type: ignore

    def document_search(self, content: str, num_docs: int) -> List[Dict[str, Any]]:
        """Search for the most relevant documents for the given search parameters."""

        try:
            retriever = get_doc_retriever(num_nodes=num_docs)
            nodes = retriever.retrieve(content)
            output = []
            for node in nodes:
                file_name = nodes[0].metadata["filename"]
                decoded_filename = base64.b64decode(file_name.encode("utf-8")).decode("utf-8")
                entry = {"score": node.score, "source": decoded_filename, "content": node.text}
                output.append(entry)

            return output

        except Exception as e:
            logger.error(f"Error from /documentSearch endpoint. Error details: {e}")
            return []
