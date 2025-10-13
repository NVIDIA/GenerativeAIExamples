import os
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores.faiss import FAISS
from dotenv import load_dotenv
load_dotenv()
api_key = os.getenv('API_KEY')
class HybridRetriever:
    def __init__(self, file_path, api_key):
        self.file_path = file_path
        os.environ["NVIDIA_API_KEY"] = api_key
        self.embeddings = self.initialize_nvidia_components()
        self.doc_splits = self.load_and_split_documents()
        self.bm25_retriever, self.faiss_retriever = self.create_retrievers()
        self.hybrid_retriever = self.create_hybrid_retriever()

    def initialize_nvidia_components(self):
        embeddings =NVIDIAEmbeddings(model="nvidia/llama-3.2-nv-embedqa-1b-v2", truncate="END")
        return  embeddings

    def load_and_split_documents(self):
        loader = TextLoader(self.file_path)
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=20000, chunk_overlap=10000)
        doc_splits = text_splitter.split_documents(docs)
        return doc_splits

    def create_retrievers(self):
        bm25_retriever = BM25Retriever.from_documents(self.doc_splits)
        faiss_vectorstore = FAISS.from_documents(self.doc_splits, self.embeddings)
        faiss_retriever = faiss_vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={'score_threshold': 0.8})
        return bm25_retriever, faiss_retriever

    def create_hybrid_retriever(self):
        hybrid_retriever = EnsembleRetriever(retrievers=[self.bm25_retriever, self.faiss_retriever], weights=[0.5, 0.5])
        return hybrid_retriever

    def get_retriever(self):
        return self.hybrid_retriever


