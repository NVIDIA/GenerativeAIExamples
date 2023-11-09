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
from pathlib import Path
from typing import Generator

from llama_index import Prompt, download_loader
from llama_index.node_parser import SimpleNodeParser
from llama_index.query_engine import RetrieverQueryEngine
from llama_index.response.schema import StreamingResponse

from chain_server.utils import (
    LimitRetrievedNodesLength,
    get_config,
    get_doc_retriever,
    get_llm,
    get_text_splitter,
    get_vector_index,
    is_base64_encoded,
    set_service_context,
)


def llm_chain(
    context: str, question: str, num_tokens: int
) -> Generator[str, None, None]:
    """Execute a simple LLM chain using the components defined above."""
    set_service_context()
    prompt = get_config().prompts.chat_template.format(
        context_str=context, query_str=question
    )
    response = get_llm().stream_complete(prompt, tokens=num_tokens)
    gen_response = (resp.delta for resp in response)
    return gen_response


def rag_chain(prompt: str, num_tokens: int) -> Generator[str, None, None]:
    """Execute a Retrieval Augmented Generation chain using the components defined above."""
    set_service_context()
    get_llm().llm.tokens = num_tokens  # type: ignore
    retriever = get_doc_retriever(num_nodes=4)
    qa_template = Prompt(get_config().prompts.rag_template)
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
    return StreamingResponse(iter([])).response_gen  # type: ignore


def ingest_docs(data_dir: str, filename: str) -> None:
    """Ingest documents to the VectorDB."""
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
    text_splitter = get_text_splitter()
    node_parser = SimpleNodeParser.from_defaults(text_splitter=text_splitter)
    nodes = node_parser.get_nodes_from_documents(documents)
    index.insert_nodes(nodes)
