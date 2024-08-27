import requests
import aiohttp
import asyncio

import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings, NVIDIARerank

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS



from dotenv import load_dotenv
load_dotenv()
chatnvidia_api_key = os.getenv("NGC_API_KEY")

embed_api_key = os.getenv("EMBED_KEY")
rerank_api_key = os.getenv("RERANK_KEY")


class RetrieverClient:
    def __init__(self):
        self.document_chunks = None
        self.vector_store = None #create a new "collection" for each time Retriever Client

        self.embedding_model = NVIDIAEmbeddings(
            model="NV-Embed-QA", 
            api_key=embed_api_key, 
            truncate="NONE", 
        )
        
        self.llm = ChatNVIDIA(
            model="meta/llama3-8b-instruct",
            api_key = chatnvidia_api_key
            )
    
    def add_files(self, document): #document parameter is content of input files
        
        #chunking (break down long piece of text)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", ";", ",", " ", ""],
        )
        
        self.document_chunks = text_splitter.split_documents(document)
        self.vector_store = FAISS.from_documents(self.document_chunks, embedding=self.embedding_model)
      
    
    def rag_query(self, user_query, raw_prompt):
        self.embedding_model.embed_query(user_query)[:10]
        # Optionally, we can also add a reranker here

        if self.document_chunks is None:
            print("You did not populate document chunks yet!")

        prompt = ChatPromptTemplate.from_messages([
            ("system", 
                f"{raw_prompt}"
                "{question}\n\nContext:{context}"
            ),
            ("user", "{question}")
        ])
        

        chain = (
            {
                "context": self.vector_store.as_retriever(),
                "question": RunnablePassthrough()
            }
            | prompt
            | self.llm
            | StrOutputParser()
        )

        return chain.invoke(user_query)
                
        
       
    #Can be used in Digital Fingerprinting user summary report generation step - reports are augmented with cyber context
    def search(self, user_query): #no embedding; our document space is small enough that we can just use a reranker to find most relevant context
        reranker = NVIDIARerank(model="nvidia/nv-rerankqa-mistral-4b-v3",
                                api_key = rerank_api_key)
        
        if self.document_chunks is None:
            print("You did not populate document chunks yet!") #self.document_chunks should be populated by add_files
        
        reranked_chunks = reranker.compress_documents(query=user_query,
                                                      documents=self.document_chunks) 
        
        page_contents = [doc.page_content for doc in reranked_chunks]
        return page_contents[0]
