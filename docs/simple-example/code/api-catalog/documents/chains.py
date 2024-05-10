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

DOCS_DIR = os.path.abspath("./uploaded_files")
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
            # Files are copied to DOCS_DIR in the common.server:upload_document method.
            _path = os.path.join(DOCS_DIR, filename)

            raw_documents = UnstructuredFileLoader(_path).load()
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

    # start-get-documents-method
    def get_documents(self) -> List[str]:
        """Retrieve file names from the vector store."""
        extract_filename = lambda metadata : os.path.basename(metadata['source'])
        try:
            global vector_store

            in_memory_docstore = vector_store.docstore._dict
            filenames = [extract_filename(doc.metadata) for doc in in_memory_docstore.values()]
            filenames = list(set(filenames))
            return filenames
        except Exception as e:
            logger.error(f"Vector store not initialized. Error details: {e}")
        return []
    # end-get-documents-method


    # start-delete-documents-method
    def delete_documents(self, filenames: List[str]):
        """Delete documents from the vector index."""
        extract_filename = lambda metadata : os.path.basename(metadata['source'])
        try:
            global vector_store

            in_memory_docstore = vector_store.docstore._dict
            for filename in filenames:
                ids_list = [doc_id for doc_id, doc_data in in_memory_docstore.items() if extract_filename(doc_data.metadata) == filename]
                if vector_store.delete(ids_list):
                    logger.info(f"Deleted document with file name: {filename}")
                else:
                    logger.error(f"Failed to delete document: {filename}")

        except Exception as e:
            logger.error(f"Vector store not initialized. Error details: {e}")
            raise
    # end-delete-documents-method

    # start-document-search-method
    def document_search(self, content: str, num_docs: int) -> List[Dict[str, Any]]:
        """Search for the most relevant documents for the given search parameters."""

        try:
            retriever = vector_store.as_retriever(search_type="similarity_score_threshold", search_kwargs={"score_threshold": settings.retriever.score_threshold, "k": settings.retriever.top_k})
            docs = retriever.invoke(content)

            result = []
            for doc in docs:
                result.append(
                    {
                        "source": os.path.basename(doc.metadata.get('source', '')),
                        "content": doc.page_content
                    }
                )
                return result
            return []
        except Exception as e:
            logger.error(f"Error from POST /search endpoint. Error details: {e}")
            raise
    # end-document-search-method
