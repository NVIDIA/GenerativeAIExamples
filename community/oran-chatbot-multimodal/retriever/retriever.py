# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from retriever.embedder import Embedder
from retriever.vector import VectorClient
import pickle
import os
from typing import List
from langchain.chains import LLMChain
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import NeMoEmbeddings
import yaml
import os

NVIDIA_API_KEY = yaml.safe_load(open("config.yaml"))['nvidia_api_key']
os.environ['NVIDIA_API_KEY'] = NVIDIA_API_KEY

def clean_source(full_path):
    return os.path.basename(full_path)

class Retriever(BaseModel):

    embedder : Embedder
    vector_client : VectorClient
    search_limit : int = 4

    def get_relevant_docs(self, DOCS_DIR, text, limit=None):
        if limit is None:
            limit = self.search_limit
        query_vector = self.embedder.embed_query(text)
        concatdocs, sources = self.vector_client.search([query_vector], limit)
        return concatdocs, sources

def get_relevant_docs(DOCS_DIR, text, limit=None):
        # with open(os.path.join(DOCS_DIR, "vectorstore_nv.pkl"), "rb") as f:
        #     vectorstore = pickle.load(f)

    if yaml.safe_load(open('config.yaml', 'r'))['NREM']:
        # Embeddings with NeMo Retriever Embeddings Microservice (NREM)
        print("Generating embeddings with NREM")
        nv_embedder = NVIDIAEmbeddings(base_url= yaml.safe_load(open('config.yaml', 'r'))['nrem_api_endpoint_url'],
                                       model=yaml.safe_load(open('config.yaml', 'r'))['nrem_model_name'],
                                       truncate = yaml.safe_load(open('config.yaml', 'r'))['nrem_truncate']
                                       )

    else:
        # Embeddings with NVIDIA AI Foundation Endpoints
        nv_embedder = NVIDIAEmbeddings(model=yaml.safe_load(open('config.yaml', 'r'))['embedding_model'])

    vectorstore = FAISS.load_local(os.path.join(DOCS_DIR, "vectorstore_nv"), nv_embedder, allow_dangerous_deserialization=True)
    retriever = vectorstore.as_retriever(search_type="similarity_score_threshold",
                             search_kwargs={"score_threshold": .3,
                                            "k": 10}) #search_type="similarity_score_threshold",
    print(retriever)
    concatdocs = ""
    sources = {}
    srcs = ""
    try:
        docs = retriever.get_relevant_documents(text)

    except UserWarning as e:
        print(f"A UserWarning was caught: {e}")
        pass

    if(len(docs)>0):
        for doc in docs:
            concatdocs += doc.page_content + "\n"
            srcs += clean_source(doc.metadata['source']) + "\n\n"
            sources[doc.metadata['source']] = {"doc_content": doc.page_content, "doc_metadata": doc.metadata['source']}
    return docs, concatdocs, sources

class LineList(BaseModel):
    # "lines" is the key (attribute name) of the parsed output
    lines: List[str] = Field(description="Lines of text")


class LineListOutputParser(PydanticOutputParser):
    def __init__(self) -> None:
        super().__init__(pydantic_object=LineList)

    def parse(self, text: str) -> LineList:
        lines = text.strip().split("\n")
        return LineList(lines=lines)


output_parser = LineListOutputParser()

QUERY_PROMPT = PromptTemplate(
    input_variables=["question"],
    template="""You are an ORAN standards assistant. Your task is to generate five
    different versions of the given user question relevant to ORAN from ORAN documents. By generating multiple perspectives on the user question, your goal is to help
    the user overcome some of the limitations of the distance-based similarity search.
    Provide these alternative questions separated by newlines.
    Original question: {question}""",
)

def get_relevant_docs_mq(DOCS_DIR, text):
    """Retrieves documents to be used as context for Nemo

    Args:
        text (str): Query from user

    Returns:
        str: relevant snippets from documents, separated by newline char
    """
    with open(os.path.join(DOCS_DIR, "vectorstore_nv.pkl"), "rb") as f:
        vectorstore = pickle.load(f)

    llm = ChatNVIDIA(model="playground_llama2_70b")
    llm_chain = LLMChain(llm=llm, prompt=QUERY_PROMPT, output_parser=output_parser)
    retriever_mq = MultiQueryRetriever(
    retriever=vectorstore.as_retriever(search_type="similarity_score_threshold",search_kwargs={"k": 10, "score_threshold": 0.3}), llm_chain=llm_chain, parser_key="lines")
    #retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    concatdocs = ""
    srcs = ""
    sources = {}
    try:
        docs = retriever_mq.get_relevant_documents(text)

    except UserWarning as e:
        print(f"A UserWarning was caught: {e}")
        pass

    if(len(docs)>0):
        for doc in docs:
            concatdocs += doc.page_content + "\n"
            srcs += clean_source(doc.metadata['source']) + "\n\n"
            sources[doc.metadata['source']] = {"doc_content": doc.page_content, "doc_metadata": doc.metadata['source']}
    return docs, concatdocs, sources
