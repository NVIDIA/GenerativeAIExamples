from typing import Generator, List, Dict, Any
import logging

from llama_index.core.base.response.schema import StreamingResponse
from RetrievalAugmentedGeneration.common.base import BaseExample

logger = logging.getLogger(__name__)

class SimpleExample(BaseExample):
    def ingest_docs(self, file_name: str, filename: str):
        """Code to ingest documents."""
        logger.info(f"Ingesting the documents")

    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Code to form an answer using LLM when context is already supplied."""
        logger.info(f"Forming response from provided context")
        return StreamingResponse(iter(["TODO: Implement LLM call"])).response_gen

    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Code to fetch context and form an answer using LLM."""
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

