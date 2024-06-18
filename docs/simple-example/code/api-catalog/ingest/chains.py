from typing import Generator, List, Dict, Any
import logging

from llama_index.core.base.response.schema import StreamingResponse
from RetrievalAugmentedGeneration.common.base import BaseExample

# start-ingest-imports
from langchain.document_loaders import UnstructuredFileLoader
from langchain.text_splitter import CharacterTextSplitter
from RetrievalAugmentedGeneration.common.utils import get_config, get_llm, get_embedding_model

document_embedder = get_embedding_model()
settings = get_config()
# end-ingest-imports

# start-ingest-faiss
import os
from langchain.vectorstores import FAISS

vector_store_path = "vectorstore.pkl"
vector_store = None
# end-ingest-faiss

logger = logging.getLogger(__name__)


class SimpleExample(BaseExample):
    # start-ingest-docs-method
    def ingest_docs(self, data_dir: str, filename: str):
        """Code to ingest documents"""
        try:
            global vector_store

            raw_documents = UnstructuredFileLoader(data_dir).load()
            if raw_documents:
                text_splitter = CharacterTextSplitter(chunk_size=settings.text_splitter.chunk_size,
                                                      chunk_overlap=settings.text_splitter.chunk_overlap)
                documents = text_splitter.split_documents(raw_documents)
                if vector_store:
                    vector_store.add_documents(documents)
                else:
                    vector_store = FAISS.from_documents(documents, document_embedder)
                    logger.info("Vector store created and saved.")
            else:
                logger.warning(f"No documents in '{DOCS_DIR}' to process.")
        except Exception as e:
            logger.error(f"Failed to ingest document: {e}")
            raise ValueError("Failed to upload document. Upload an unstructured text or PDF file.")
    # end-ingest-docs-method

    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Code to form an answer using LLM when context is already supplied"""
        logger.info(f"Forming response from provided context")
        return StreamingResponse(iter(["TODO: Implement LLM call"])).response_gen

    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Code to fetch context and form an answer using LLM"""
        logger.info(f"Forming response from document store")
        return StreamingResponse(iter(["TODO: Implement RAG chain call"])).response_gen

    def get_documents(self) -> List[str]:
        """Retrieve file names from the vector store."""
        logger.info("Getting document file names from the vector store")
        return []

    def delete_documents(self, filenames: List[str]) -> None:
        """Delete documents from the vector index."""
        logger.info("Deleting documents from the vector index")

    def document_search(self, content: str, num_docs: int) -> List[Dict[str, Any]]:  ## Optional method
        """Search for the most relevant documents for the given search parameters."""
        logger.info("Searching for documents based on the query")
        return []
