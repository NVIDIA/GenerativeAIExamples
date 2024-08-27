import requests
import aiohttp
import asyncio

import os
from langchain_nvidia_ai_endpoints import NVIDIARerank
# from langchain_community.document_loaders import TextLoader

# from langchain_core.prompts import ChatPromptTemplate
# from langchain_core.output_parsers import StrOutputParser

from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain_community.vectorstores import FAISS
# from langchain.retrievers import ContextualCompressionRetriever
# from langchain.chains import RetrievalQA
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("NGC_API_KEY")
os.environ["NVIDIA_API_KEY"] = api_key


class RetrieverClient:
    def __init__(self):
        self.document_chunks = None
    
    def add_files(self, document): #document parameter is content of input files

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", ";", ",", " ", ""],
        )
        
        self.document_chunks = text_splitter.split_documents(document)
        print("Number of chunks from the document:", len(self.document_chunks))
        return self.document_chunks
        
    
    def search(self, user_query, top_k=3):
        reranker = NVIDIARerank(model="nvidia/nv-rerankqa-mistral-4b-v3")
        if self.document_chunks is None:
            print("You did not populate document chunks yet!")
            #self.document_chunks should be populated by add_files
        
        reranked_chunks = reranker.compress_documents(query=user_query,
                                                      documents=self.document_chunks) 
        
        page_contents = [doc.page_content for doc in reranked_chunks]
        return page_contents