from typing import Generator, List, Dict, Any
import logging

from llama_index.response.schema import StreamingResponse
from RetrievalAugmentedGeneration.common.base import BaseExample

# start-prestage-statements
from RetrievalAugmentedGeneration.common.utils import get_embedding_model, set_service_context

# prestage the embedding model
_ = get_embedding_model()
set_service_context()
# end-prestage-statements

# start-ingest-imports
from pathlib import Path
import base64

from llama_index import download_loader
from llama_index.node_parser import LangchainNodeParser
from RetrievalAugmentedGeneration.common.utils import get_vector_index, get_text_splitter, is_base64_encoded
# end-ingest-imports

logger = logging.getLogger(__name__)


class SimpleExample(BaseExample):
    # start-ingest-docs-method
    def ingest_docs(self, data_dir: str, filename: str):
        """Code to ingest documents"""
        try:
            logger.info(f"Ingesting {filename} in vectorDB")
            unstruct_reader = download_loader("UnstructuredReader")
            loader = unstruct_reader()
            documents = loader.load_data(file=Path(data_dir), split_documents=False)
            encoded_filename = filename[:-4]

            if not is_base64_encoded(encoded_filename):
                encoded_filename = base64.b64encode(encoded_filename.encode("utf-8")).decode("utf-8")

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
    # end-ingest-docs-method

    def llm_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Code to form an answer using LLM when context is already supplied"""
        logger.info(f"Forming response from provided context")
        return StreamingResponse(iter(["TODO: Implement LLM call"])).response_gen

    def rag_chain(self, query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Code to fetch context and form an answer using LLM"""
        logger.info(f"Forming response from document store")
        return StreamingResponse(iter(["TODO: Implement RAG chain call"])).response_gen

    def document_search(self, content: str, num_docs: int) -> List[Dict[str, Any]]:  ## Optional method
        """Search for the most relevant documents for the given search parameters"""

        logger.info("Searching for documents based on the query")
        return []
