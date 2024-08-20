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

from langchain_community.vectorstores import FAISS
import os
from langchain_community.document_loaders import UnstructuredHTMLLoader
from langchain.docstore.document import Document
import re
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
import shutil
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
EMBEDDING_PATH = '/tmp/embeddings'


class FAISSVS():
    def __init__(self,file_path):
        if not os.path.exists(EMBEDDING_PATH):
            os.makedirs(EMBEDDING_PATH)
        self.embedding_model_name = "None"
        self.embedding_model = None
        self.chunk_size = 1024 # default value
        self.overlap_size = 150 # default overlap_size
        self.dir_path = file_path
        self.retriever = None
        self.ids=[]
        return
    
    def generate_index(self,embedding_model_name,chunk_size,overlap_size):
        if embedding_model_name != self.embedding_model_name:
            logging.info(f"The embedding model changed from {self.embedding_model_name} to {embedding_model_name}")
            if os.path.exists(EMBEDDING_PATH) and os.listdir(EMBEDDING_PATH):
                logging.info("Remove the indexing of previous embedding model")
                shutil.rmtree(EMBEDDING_PATH)
                self.ids=[]
                self.retriever = None

        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.embedding_model_name = embedding_model_name
        self.embedding_model = NVIDIAEmbeddings(model=self.embedding_model_name, truncate="END")
        docs_list = self.get_page_docs_from_local()
        self.index_docs(docs_list)
        logging.info("Index created succesfully.")
        return True
        
    def get_embedding_model_name(self):
        return self.embedding_model_name
    
    def get_page_docs_from_local(self):
        docs_list=[]
        files_list = os.listdir(self.dir_path)
        existing_ids_source = [d["source"] for d in self.ids]
        for file in files_list:
            if file in existing_ids_source:
                logging.info(f"{file} is already indexed, skip it for next file processing")
                continue
            file_path = os.path.join(self.dir_path,file)
            if file.endswith(".pdf"):
                loader = PyPDFLoader(file_path)
                pages = loader.load_and_split()
                
            else:
                loader = UnstructuredHTMLLoader(file_path)
                pages = loader.load()

            for page in pages:
                page_content = page.page_content
                # not remove multiple \n which are useful for splitter.
                # page_content = re.sub("\n+", "\n",page_content)
                # remove the special charactors
                page_content = re.sub(r'[^\x00-\x7F]+', '', page_content)
                docs_list.append(
                    Document(page_content=page_content, 
                            metadata={"source": file}))
        return docs_list
    
    def splitter_text(self,source):
        """
        Args:
            source: raw content for splitter 
        Returns:
            None
        """
        text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.overlap_size,
                length_function=len,
            )
        source_chunks =[]
        for chunk in text_splitter.split_text(source.page_content):
            source_chunks.append(chunk)
        return source_chunks
    
    def index_docs(self,docs_list) -> None:
        """
        Args:
            docs_list: raw contents list for splitter and embedding
        Returns:
            None
        """
        for document in docs_list:
            chunks = self.splitter_text(document)
            # metadata to attach to document
            metadatas = [document.metadata] * len(chunks)

            # create embeddings and add to vector store
            if os.path.exists(EMBEDDING_PATH) and os.listdir(EMBEDDING_PATH):
                update = FAISS.load_local(folder_path=EMBEDDING_PATH, embeddings=self.embedding_model,allow_dangerous_deserialization=True)
                ids =update.add_texts(chunks, metadatas=metadatas)
                update.save_local(folder_path=EMBEDDING_PATH)
            else:
                docsearch = FAISS.from_texts(chunks, embedding=self.embedding_model, metadatas=metadatas)
                ids = list(docsearch.index_to_docstore_id.values())
                docsearch.save_local(folder_path=EMBEDDING_PATH)
            # Store the ids for each documents
            self.ids.append({"source":document.metadata["source"],"ids":ids})
        self.retriever = FAISS.load_local(folder_path=EMBEDDING_PATH, embeddings=self.embedding_model,allow_dangerous_deserialization=True)

    def get_reteriever_engine(self):
        # reteriever_engine = FAISS.load_local(folder_path=EMBEDDING_PATH, embeddings=self.self.embedding_model)
        # self.retriever
        return self.retriever
    
    def remove_index(self):
        if os.path.exists(EMBEDDING_PATH):
            shutil.rmtree(EMBEDDING_PATH)
            logging.info(f"FAISS index {EMBEDDING_PATH} removed")
        else:
            logging.info(f"FAISS index {EMBEDDING_PATH} not exist")
        self.retriever = None
        self.embedding_model_name = "None"
        self.embedding_model = None
        self.ids=[]

    def remove_source_ids(self,file_name):
        filtered_ids=[d.get("ids") for d in self.ids if d["source"] == file_name]
        if filtered_ids:
            for ids in filtered_ids:
                self.retriever.delete(ids)
            logging.info(f"Remove the vector related to {file_name}")
        self.ids = [d for d in self.ids if d["source"] != file_name]
        return


    def search(self,query,number_search):
        try:
            results = self.retriever.similarity_search(query, k=number_search)
            # logging.info(results)
            return results
        except:
            return ''
        
