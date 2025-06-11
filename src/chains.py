# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import logging
import os
import requests
import asyncio
from traceback import print_exc
from typing import Any, Iterable, Dict, Generator, List, Optional, Tuple
import json
import re

from langchain_nvidia_ai_endpoints.callbacks import get_usage_callback
from langchain_community.document_loaders import UnstructuredFileLoader
from langchain_core.output_parsers.string import StrOutputParser
from langchain_core.prompts import MessagesPlaceholder
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableAssign
from langchain_core.runnables import RunnablePassthrough
from langchain_core.documents import Document
from requests import ConnectTimeout
from pydantic import BaseModel, Field

from .base import BaseExample
from .utils import create_vectorstore_langchain
from .utils import get_config
from .utils import get_embedding_model
from .utils import get_llm
from .utils import get_prompts
from .utils import get_ranking_model
from .utils import get_text_splitter
from .utils import get_vectorstore
from .utils import format_document_with_source
from .utils import streaming_filter_think, get_streaming_filter_think_parser
from .reflection import ReflectionCounter, check_context_relevance, check_response_groundedness
from .utils import normalize_relevance_scores

# Import enhanced components
try:
    from .query_analyzer import QueryAnalyzer, get_collection_names_for_categories
    from .document_aggregator import DocumentAggregator
    from .vgpu_profile_validator import VGPUProfileValidator, DeploymentMode, ProfileMode
    from .rag_mode_config import get_rag_config
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Enhanced components not available. Using standard RAG only.")
    ENHANCED_COMPONENTS_AVAILABLE = False

# Structured Response Model for vGPU Configuration
class StructuredResponse(BaseModel):
    """Structured response model for vGPU configuration recommendations."""
    
    title: str = Field(
        default="generate_vgpu_config",
        description="Function title for vGPU configuration generation"
    )
    description: str = Field(
        description="Description of the recommended vGPU configuration based on workload requirements and hardware specs"
    )
    parameters: Dict[str, Any] = Field(
        description="vGPU configuration parameters"
    )

    def __init__(self, **data):
        # If parameters is not provided, create the default structure
        if 'parameters' not in data:
            data['parameters'] = {
                "type": "object",
                "properties": {
                    "vGPU_profile": {
                        "type": ["string", "null"],
                        "description": "Exact NVIDIA vGPU profile name found in context documentation (must match documented profiles exactly)",
                        "pattern": "^[A-Z0-9]+-[0-9]+[A-Z]?$"
                    },
                    "total_CPUs": {
                        "type": ["integer", "null"],
                        "description": "Total number of physical CPU cores allocated to the VM host",
                        "minimum": 1,
                        "maximum": 256
                    },
                    "vCPU_count": {
                        "type": ["integer", "null"],
                        "description": "Number of virtual CPUs allocated to the VM guest based on workload requirements",
                        "minimum": 1,
                        "maximum": 128
                    },
                    "gpu_memory_size": {
                        "type": ["integer", "null"],
                        "description": "GPU frame buffer memory in GB assigned to the vGPU profile (must match profile specifications)",
                        "minimum": 1,
                        "maximum": 128
                    },
                    "video_card_total_memory": {
                        "type": ["integer", "null"],
                        "description": "Total video card memory capacity in GB of the physical GPU hardware",
                        "minimum": 4,
                        "maximum": 200
                    },
                    "system_RAM": {
                        "type": ["integer", "null"],
                        "description": "System RAM allocated to the VM in GB based on workload analysis",
                        "minimum": 8,
                        "maximum": 2048
                    },
                    "storage_capacity": {
                        "type": ["integer", "null"],
                        "description": "Hard disk storage capacity in GB required for the workload including OS, model files, and data",
                        "minimum": 50,
                        "maximum": 10000
                    },
                    "storage_type": {
                        "type": ["string", "null"],
                        "description": "Recommended storage type based on performance requirements",
                        "enum": ["SSD", "NVMe", "HDD", "Network Storage"]
                    },
                    "driver_version": {
                        "type": ["string", "null"],
                        "description": "Compatible NVIDIA driver version determined from context documentation"
                    },
                    "AI_framework": {
                        "type": ["string", "null"],
                        "description": "Recommended AI framework or toolkit based on context analysis and workload requirements"
                    },
                    "performance_tier": {
                        "type": ["string", "null"],
                        "description": "Performance classification based on workload requirements",
                        "enum": ["Entry", "Standard", "High Performance", "Maximum Performance"]
                    },
                    "concurrent_users": {
                        "type": ["integer", "null"],
                        "description": "Number of concurrent users the configuration can support",
                        "minimum": 1,
                        "maximum": 1000
                    }
                },
                "required": []
            }
        
        # Set default title if not provided
        if 'title' not in data:
            data['title'] = "generate_vgpu_config"
            
        # Set default description if not provided
        if 'description' not in data:
            data['description'] = "Generate the recommended vGPU configuration based on workload requirements and hardware specs."
            
        super().__init__(**data)

logger = logging.getLogger(__name__)
VECTOR_STORE_PATH = "vectorstore.pkl"
TEXT_SPLITTER = None
settings = get_config()
document_embedder = get_embedding_model(model=settings.embeddings.model_name, url=settings.embeddings.server_url)
ranker = get_ranking_model(model=settings.ranking.model_name, url=settings.ranking.server_url, top_n=settings.retriever.top_k)
query_rewriter_llm_config = {"temperature": 0.7, "top_p": 0.2, "max_tokens": 1024}
logger.info("Query rewriter llm config: model name %s, url %s, config %s", settings.query_rewriter.model_name, settings.query_rewriter.server_url, query_rewriter_llm_config)
query_rewriter_llm = get_llm(model=settings.query_rewriter.model_name, llm_endpoint=settings.query_rewriter.server_url, **query_rewriter_llm_config)
prompts = get_prompts()
vdb_top_k = int(os.environ.get("VECTOR_DB_TOPK", 40))

try:
    VECTOR_STORE = create_vectorstore_langchain(document_embedder=document_embedder)
except Exception as ex:
    VECTOR_STORE = None
    logger.error("Unable to connect to vector store during initialization: %s", ex)

# Get a StreamingFilterThinkParser based on configuration
StreamingFilterThinkParser = get_streaming_filter_think_parser()

class APIError(Exception):
    """Custom exception class for API errors."""
    def __init__(self, message: str, code: int = 400):
        logger.error("APIError occurred: %s with HTTP status: %d", message, code)
        print_exc()
        self.message = message
        self.code = code
        super().__init__(message)

class UnstructuredRAG(BaseExample):
    
    def __init__(self):
        """Initialize UnstructuredRAG with enhanced components if available."""
        super().__init__()
        self.settings = get_config()
        
        # Initialize enhanced components if available
        if ENHANCED_COMPONENTS_AVAILABLE:
            self.query_analyzer = QueryAnalyzer()
            self.document_aggregator = DocumentAggregator(self.settings)
            self.profile_validator = VGPUProfileValidator()
            self.rag_config = get_rag_config()
        else:
            self.query_analyzer = None
            self.document_aggregator = None
            self.profile_validator = None
            self.rag_config = None

    def ingest_docs(self, data_dir: str, filename: str, collection_name: str = "", vdb_endpoint: str = "") -> None:
        """Ingests documents to the VectorDB.
        It's called when the POST endpoint of `/documents` API is invoked.

        Args:
            data_dir (str): The path to the document file.
            filename (str): The name of the document file.
            collection_name (str): The name of the collection to be created in the vectorstore.

        Raises:
            ValueError: If there's an error during document ingestion or the file format is not supported.
        """
        try:
            # Load raw documents from the directory
            _path = data_dir
            raw_documents = UnstructuredFileLoader(_path).load()

            if raw_documents:
                global TEXT_SPLITTER  # pylint: disable=W0603
                # Get text splitter instance, it is selected based on environment variable APP_TEXTSPLITTER_MODELNAME
                # tokenizer dimension of text splitter should be same as embedding model
                if not TEXT_SPLITTER:
                    TEXT_SPLITTER = get_text_splitter()

                # split documents based on configuration provided
                logger.info(f"Using text splitter instance: {TEXT_SPLITTER}")
                documents = TEXT_SPLITTER.split_documents(raw_documents)
                vs = get_vectorstore(document_embedder, collection_name, vdb_endpoint)
                # ingest documents into vectorstore
                vs.add_documents(documents)
            else:
                logger.warning("No documents available to process!")

        except ConnectTimeout as e:
            raise APIError(
                "Connection timed out while accessing the embedding model endpoint. Verify server availability.",
                code=504
            ) from e
        except Exception as e:
            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                raise APIError(
                    "Authentication or permission error: Verify NVIDIA API key validity and permissions.",
                    code=403
                ) from e
            if "[404] Not Found" in str(e):
                raise APIError(
                    "API endpoint or payload is invalid. Ensure the model name is valid.",
                    code=404
                ) from e
            raise APIError("Failed to upload document. " + str(e), code=500) from e

    def llm_chain(self, query: str, chat_history: List[Dict[str, Any]], **kwargs) -> Generator[str, None, None]:
        """Execute a simple LLM chain using the components defined above.
        It's called when the `/generate` API is invoked with `use_knowledge_base` set to `False`.

        Args:
            query (str): Query to be answered by llm.
            chat_history (List[Message]): Conversation history between user and chain.
            kwargs: ?
        """
        try:
            logger.info("Using llm to generate response directly without knowledge base.")
            system_message = []
            conversation_history = []
            user_message = []
            nemotron_message = []
            system_prompt = ""

            system_prompt += prompts.get("chat_template", "")

            if "llama-3.3-nemotron-super-49b" in str(kwargs.get("model")):
                if os.environ.get("ENABLE_NEMOTRON_THINKING", "false").lower() == "true":
                    logger.info("Setting system prompt as detailed thinking on")
                    system_prompt = "detailed thinking on"
                else:
                    logger.info("Setting system prompt as detailed thinking off")
                    system_prompt = "detailed thinking off"
                nemotron_message += [("user", prompts.get("chat_template", ""))]

            for message in chat_history:
                if message.role ==  "system":
                    system_prompt = system_prompt + " " + message.content
                else:
                    conversation_history.append((message.role, message.content))

            system_message = [("system", system_prompt)]

            logger.info("Query is: %s", query)
            if query is not None and query != "":
                user_message += [("user", "{question}")]

            # Prompt template with system message, conversation history and user query
            message = system_message + nemotron_message + conversation_history + user_message

            self.print_conversation_history(message, query)

            prompt_template = ChatPromptTemplate.from_messages(message)
            llm = get_llm(**kwargs)

            # Use structured output for consistent JSON responses
            structured_llm = llm.with_structured_output(StructuredResponse)
            chain = prompt_template | structured_llm
            
            # Stream the structured response as JSON
            def stream_structured_response():
                try:
                    structured_result = chain.invoke({"question": query}, config={'run_name':'llm-stream'})
                    # Convert to JSON and yield as a single chunk
                    json_response = json.dumps(structured_result.model_dump(), ensure_ascii=False, indent=2)
                    yield json_response
                except Exception as e:
                    logger.error("Error in structured response: %s", e)
                    error_response = StructuredResponse(
                        description=f"Error generating vGPU configuration: {str(e)}. Unable to provide recommendation."
                    )
                    yield json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)
            
            return stream_structured_response()
        except ConnectTimeout as e:
            logger.warning("Connection timed out while making a request to the LLM endpoint: %s", e)
            error_response = StructuredResponse(
                description="Connection timed out while making a request to the NIM endpoint. Verify if the NIM server is available. Unable to generate vGPU configuration."
            )
            return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])

        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                error_response = StructuredResponse(
                    description="Authentication or permission error: Verify the validity and permissions of your NVIDIA API key. Unable to generate vGPU configuration."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])
            elif "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                error_response = StructuredResponse(
                    description="Please verify the API endpoint and your payload. Ensure that the model name is valid. Unable to generate vGPU configuration."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])
            else:
                error_response = StructuredResponse(
                    description=f"Failed to generate RAG chain response. {str(e)}. Unable to generate vGPU configuration."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])

    def rag_chain(  # pylint: disable=arguments-differ
            self,
            query: str,
            chat_history: List[Dict[str, Any]],
            reranker_top_k: int,
            vdb_top_k: int,
            collection_name: str = "",
            **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above.
        It's called when the `/generate` API is invoked with `use_knowledge_base` set to `True`.

        Args:
            query (str): Query to be answered by llm.
            chat_history (List[Message]): Conversation history between user and chain.
            top_n (int): Fetch n document to generate.
            collection_name (str): Name of the collection to be searched from vectorstore.
            kwargs: ?
        """

        if os.environ.get("ENABLE_MULTITURN", "false").lower() == "true":
            return self.rag_chain_with_multiturn(query=query, chat_history=chat_history, reranker_top_k=reranker_top_k, vdb_top_k=vdb_top_k, collection_name=collection_name, **kwargs)
        
        # Determine if enhanced mode should be used
        use_enhanced = self._should_use_enhanced_mode(query)
        logger.info("Using %s RAG mode for query: %s", "enhanced" if use_enhanced else "standard", query)

        try:
            document_embedder = get_embedding_model(model=kwargs.get("embedding_model"), url=kwargs.get("embedding_endpoint"))
            vs = get_vectorstore(document_embedder, collection_name, kwargs.get("vdb_endpoint"))
            if vs is None:
                raise APIError("Vector store not initialized properly. Please check if the vector DB is up and running.", 500)

            llm = get_llm(**kwargs)
            ranker = get_ranking_model(model=kwargs.get("reranker_model"), url=kwargs.get("reranker_endpoint"), top_n=reranker_top_k)
            top_k = vdb_top_k if ranker and kwargs.get("enable_reranker") else reranker_top_k
            logger.info("Setting retriever top k as: %s.", top_k)
            retriever = vs.as_retriever(search_kwargs={"k": top_k})  # milvus does not support similarily threshold

            system_prompt = ""
            conversation_history = []
            system_prompt += prompts.get("rag_template", "")
            user_message = []

            if "llama-3.3-nemotron-super-49b" in str(kwargs.get("model")):
                if os.environ.get("ENABLE_NEMOTRON_THINKING", "false").lower() == "true":
                    logger.info("Setting system prompt as detailed thinking on")
                    system_prompt = "detailed thinking on"
                else:
                    logger.info("Setting system prompt as detailed thinking off")
                    system_prompt = "detailed thinking off"
                user_message += [("user", prompts.get("rag_template", ""))]

            for message in chat_history:
                if message.role ==  "system":
                    system_prompt = system_prompt + " " + message.content

            system_message = [("system", system_prompt)]
            user_message += [("user", "{question}")]

            # Prompt template with system message, conversation history and user query
            message = system_message + conversation_history + user_message
            self.print_conversation_history(message)
            prompt = ChatPromptTemplate.from_messages(message)
            # Retrieve documents based on mode
            if use_enhanced and self.document_aggregator:
                # Enhanced mode: retrieve from multiple collections
                context_to_show, retrieval_metadata = self._retrieve_enhanced_documents(
                    query, kwargs.get("vdb_endpoint"), vdb_top_k, kwargs
                )
                
                # Extract valid profiles and add validation context
                valid_profiles = self._extract_vgpu_profiles_from_context(context_to_show)
                enhanced_context = self._prepare_enhanced_context(query, context_to_show, valid_profiles)
                
                # Format documents
                docs = [format_document_with_source(d) for d in context_to_show]
                
                # Add enhanced context to system prompt
                if enhanced_context:
                    system_prompt += "\n\n" + enhanced_context
                    system_message = [("system", system_prompt)]
                    message = system_message + conversation_history + user_message
                    prompt = ChatPromptTemplate.from_messages(message)
                
            else:
                # Standard mode: use original retrieval logic
                # Get relevant documents with optional reflection
                if os.environ.get("ENABLE_REFLECTION", "false").lower() == "true":
                    max_loops = int(os.environ.get("MAX_REFLECTION_LOOP", 3))
                    reflection_counter = ReflectionCounter(max_loops)

                    context_to_show, is_relevant = check_context_relevance(
                        query,
                        retriever,
                        ranker,
                        reflection_counter
                    )

                    if not is_relevant:
                        logger.warning("Could not find sufficiently relevant context after maximum attempts")
                else:
                    if ranker and kwargs.get("enable_reranker"):
                        logger.info(
                            "Narrowing the collection from %s results and further narrowing it to "
                            "%s with the reranker for rag chain.",
                            top_k,
                            reranker_top_k)
                        logger.info("Setting ranker top n as: %s.", reranker_top_k)
                        context_reranker = RunnableAssign({
                            "context":
                                lambda input: ranker.compress_documents(query=input['question'], documents=input['context'])
                        })
                        # Create a chain with retriever and reranker
                        retriever = {"context": retriever} | RunnableAssign({"context": lambda input: input["context"]})
                        docs = retriever.invoke(query, config={'run_name':'retriever'})
                        docs = context_reranker.invoke({"context": docs.get("context", []), "question": query}, config={'run_name':'context_reranker'})
                        context_to_show = docs.get("context", [])
                        # Normalize scores to 0-1 range
                        context_to_show = normalize_relevance_scores(context_to_show)
                        # Remove metadata from context
                        logger.debug("Document Retrieved: %s", docs)
                    else:
                        context_to_show = retriever.invoke(query)
                docs = [format_document_with_source(d) for d in context_to_show]
            
            # Use structured output for consistent JSON responses
            structured_llm = llm.with_structured_output(StructuredResponse)
            chain = prompt | structured_llm

            # Check response groundedness if we still have reflection iterations available
            if os.environ.get("ENABLE_REFLECTION", "false").lower() == "true" and reflection_counter.remaining > 0:
                initial_response = chain.invoke({"question": query, "context": docs})
                final_response, is_grounded = check_response_groundedness(
                    initial_response.response if hasattr(initial_response, 'response') else str(initial_response),
                    docs,
                    reflection_counter
                )
                if not is_grounded:
                    logger.warning("Could not generate sufficiently grounded response after %d total reflection attempts",
                                    reflection_counter.current_count)
                structured_final = StructuredResponse(
                    description=f"vGPU configuration generated with reflection and grounding checks: {final_response}"
                )
                return iter([json.dumps(structured_final.model_dump(), ensure_ascii=False, indent=2)]), context_to_show
            else:
                def stream_structured_rag_response():
                    try:
                        structured_result = chain.invoke({"question": query, "context": docs}, config={'run_name':'llm-stream'})
                        json_response = json.dumps(structured_result.model_dump(), ensure_ascii=False, indent=2)
                        yield json_response
                    except Exception as e:
                        logger.error("Error in structured RAG response: %s", e)
                        error_response = StructuredResponse(
                            description=f"Error generating RAG vGPU configuration: {str(e)}. Unable to provide recommendation."
                        )
                        yield json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)
                
                return stream_structured_rag_response(), context_to_show
        except ConnectTimeout as e:
            logger.warning("Connection timed out while making a request to the LLM endpoint: %s", e)
            error_response = StructuredResponse(
                response="Connection timed out while making a request to the NIM endpoint. Verify if the NIM server is available.",
                sources_used=True
            )
            return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])

        except requests.exceptions.ConnectionError as e:
            if "HTTPConnectionPool" in str(e):
                logger.warning("Connection pool error while connecting to service: %s", e)
                error_response = StructuredResponse(
                    response="Connection error: Failed to connect to service. Please verify if all required services are running and accessible.",
                    sources_used=True
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])
        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                error_response = StructuredResponse(
                    response="Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.",
                    sources_used=True
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])
            elif "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                error_response = StructuredResponse(
                    response="Please verify the API endpoint and your payload. Ensure that the model name is valid.",
                    sources_used=True
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])
            else:
                error_response = StructuredResponse(
                    response=f"Failed to generate RAG chain response. {str(e)}",
                    sources_used=True
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])


    def rag_chain_with_multiturn(self,
                                 query: str,
                                 chat_history: List[Dict[str, Any]],
                                 reranker_top_k: int,
                                 vdb_top_k: int,
                                 collection_name: str,
                                 **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        # Determine if enhanced mode should be used
        use_enhanced = self._should_use_enhanced_mode(query)
        logger.info("Using %s multiturn RAG mode for query: %s", "enhanced" if use_enhanced else "standard", query)

        try:
            document_embedder = get_embedding_model(model=kwargs.get("embedding_model"), url=kwargs.get("embedding_endpoint"))
            vs = get_vectorstore(document_embedder, collection_name, kwargs.get("vdb_endpoint"))
            if vs is None:
                raise APIError("Vector store not initialized properly. Please check if the vector DB is up and running.", 500)

            llm = get_llm(**kwargs)
            logger.info("Ranker enabled: %s", kwargs.get("enable_reranker"))
            ranker = get_ranking_model(model=kwargs.get("reranker_model"), url=kwargs.get("reranker_endpoint"), top_n=reranker_top_k)
            top_k = vdb_top_k if ranker and kwargs.get("enable_reranker") else reranker_top_k
            logger.info("Setting retriever top k as: %s.", top_k)
            retriever = vs.as_retriever(search_kwargs={"k": top_k})  # milvus does not support similarily threshold

            # conversation is tuple so it should be multiple of two
            # -1 is to keep last k conversation
            history_count = int(os.environ.get("CONVERSATION_HISTORY", 15)) * 2 * -1
            chat_history = chat_history[history_count:]
            system_prompt = ""
            conversation_history = []
            system_prompt += prompts.get("rag_template", "")
            user_message = []

            if "llama-3.3-nemotron-super-49b" in str(kwargs.get("model")):
                if os.environ.get("ENABLE_NEMOTRON_THINKING", "false").lower() == "true":
                    logger.info("Setting system prompt as detailed thinking on")
                    system_prompt = "detailed thinking on"
                else:
                    logger.info("Setting system prompt as detailed thinking off")
                    system_prompt = "detailed thinking off"
                user_message += [("user", prompts.get("rag_template", ""))]

            for message in chat_history:
                if message.role ==  "system":
                    system_prompt = system_prompt + " " + message.content
                else:
                    conversation_history.append((message.role, message.content))

            system_message = [("system", system_prompt)]
            retriever_query = query
            if chat_history:
                if kwargs.get("enable_query_rewriting"):
                    # Based on conversation history recreate query for better document retrieval
                    contextualize_q_system_prompt = (
                        "Given a chat history and the latest user question "
                        "which might reference context in the chat history, "
                        "formulate a standalone question which can be understood "
                        "without the chat history. Do NOT answer the question, "
                        "just reformulate it if needed and otherwise return it as is."
                    )
                    query_rewriter_prompt = prompts.get("query_rewriter_prompt", contextualize_q_system_prompt)
                    contextualize_q_prompt = ChatPromptTemplate.from_messages(
                        [("system", query_rewriter_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}"),]
                    )
                    q_prompt = contextualize_q_prompt | query_rewriter_llm | StreamingFilterThinkParser | StrOutputParser()
                    # query to be used for document retrieval
                    logger.info("Query rewriter prompt: %s", contextualize_q_prompt)
                    retriever_query = q_prompt.invoke({"input": query, "chat_history": conversation_history}, config={'run_name':'query-rewriter'})
                    logger.info("Rewritten Query: %s %s", retriever_query, len(retriever_query))
                    if retriever_query.replace('"', "'") == "''" or len(retriever_query) == 0:
                        return iter([""])
                else:
                    # Use previous user queries and current query to form a single query for document retrieval
                    user_queries = [msg.content for msg in chat_history if msg.role == "user"]
                    # TODO: Find a better way to join this when queries already have punctuation
                    retriever_query = ". ".join([*user_queries, query])
                    logger.info("Combined retriever query: %s", retriever_query)

            # Prompt for response generation based on context
            user_message += [("user", "{question}")]
            message = system_message + conversation_history + user_message
            self.print_conversation_history(message)
            prompt = ChatPromptTemplate.from_messages(message)
            
            # Retrieve documents from our single vGPU knowledge base
            # Get relevant documents with optional reflection
            if os.environ.get("ENABLE_REFLECTION", "false").lower() == "true":
                max_loops = int(os.environ.get("MAX_REFLECTION_LOOP", 3))
                reflection_counter = ReflectionCounter(max_loops)

                context_to_show, is_relevant = check_context_relevance(
                    retriever_query,
                    retriever,
                    ranker,
                    reflection_counter
                )

                if not is_relevant:
                    logger.warning("Could not find sufficiently relevant context after %d attempts",
                                  reflection_counter.current_count)
            else:
                if ranker and kwargs.get("enable_reranker"):
                    logger.info(
                        "Narrowing the collection from %s results and further narrowing it to "
                        "%s with the reranker for rag chain.",
                        top_k,
                        settings.retriever.top_k)
                    logger.info("Setting ranker top n as: %s.", reranker_top_k)
                    context_reranker = RunnableAssign({
                        "context":
                            lambda input: ranker.compress_documents(query=input['question'], documents=input['context'])
                    })

                    retriever = {"context": retriever} | RunnableAssign({"context": lambda input: input["context"]})
                    docs = retriever.invoke(retriever_query, config={'run_name':'retriever'})
                    docs = context_reranker.invoke({"context": docs.get("context", []), "question": retriever_query}, config={'run_name':'context_reranker'})
                    context_to_show = docs.get("context", [])
                    # Normalize scores to 0-1 range
                    context_to_show = normalize_relevance_scores(context_to_show)
                else:
                    docs = retriever.invoke(retriever_query, config={'run_name':'retriever'})
                    context_to_show = docs

            # Extract valid profiles and enhance context
            valid_profiles = self._extract_vgpu_profiles_from_context(context_to_show)
            enhanced_context = self._prepare_enhanced_context(retriever_query, context_to_show, valid_profiles)
            
            # Format documents
            docs = [format_document_with_source(d) for d in context_to_show]
            
            # Add enhanced context to system prompt if available
            if enhanced_context:
                system_prompt += "\n\n" + enhanced_context
                system_message = [("system", system_prompt)]
                message = system_message + conversation_history + user_message
                prompt = ChatPromptTemplate.from_messages(message)
            
            # Use structured output for consistent JSON responses
            structured_llm = llm.with_structured_output(StructuredResponse)
            chain = prompt | structured_llm

            # Check response groundedness if we still have reflection iterations available
            if os.environ.get("ENABLE_REFLECTION", "false").lower() == "true" and reflection_counter.remaining > 0:
                initial_response = chain.invoke({"question": query, "context": docs})
                final_response, is_grounded = check_response_groundedness(
                    initial_response.response if hasattr(initial_response, 'response') else str(initial_response),
                    docs,
                    reflection_counter
                )
                if not is_grounded:
                    logger.warning("Could not generate sufficiently grounded response after %d total reflection attempts",
                                    reflection_counter.current_count)
                structured_final = StructuredResponse(
                    response=final_response,
                    sources_used=True,
                    reasoning="Response generated with multiturn RAG, reflection and grounding checks"
                )
                return iter([json.dumps(structured_final.model_dump(), ensure_ascii=False, indent=2)]), context_to_show
            else:
                def stream_structured_multiturn_response():
                    try:
                        structured_result = chain.invoke({"question": query, "context": docs}, config={'run_name':'llm-stream'})
                        # Ensure sources_used is marked as True for RAG responses
                        if hasattr(structured_result, 'sources_used') and structured_result.sources_used is None:
                            structured_result.sources_used = True
                        json_response = json.dumps(structured_result.model_dump(), ensure_ascii=False, indent=2)
                        yield json_response
                    except Exception as e:
                        logger.error("Error in structured multiturn RAG response: %s", e)
                        error_response = StructuredResponse(
                            response=f"Error generating multiturn RAG response: {str(e)}",
                            sources_used=True
                        )
                        yield json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)
                
                return stream_structured_multiturn_response(), context_to_show

        except ConnectTimeout as e:
            logger.warning("Connection timed out while making a request to the LLM endpoint: %s", e)
            error_response = StructuredResponse(
                response="Connection timed out while making a request to the NIM endpoint. Verify if the NIM server is available.",
                sources_used=True
            )
            return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])

        except requests.exceptions.ConnectionError as e:
            if "HTTPConnectionPool" in str(e):
                logger.error("Connection pool error while connecting to service: %s", e)
                error_response = StructuredResponse(
                    response="Connection error: Failed to connect to service. Please verify if all required NIMs are running and accessible.",
                    sources_used=True
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])

        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                error_response = StructuredResponse(
                    response="Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.",
                    sources_used=True
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])
            elif "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                error_response = StructuredResponse(
                    response="Please verify the API endpoint and your payload. Ensure that the model name is valid.",
                    sources_used=True
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])
            else:
                error_response = StructuredResponse(
                    response=f"Failed to generate RAG chain with multi-turn response. {str(e)}",
                    sources_used=True
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])


    def document_search(self, content: str, messages: List, reranker_top_k: int, vdb_top_k: int, collection_name: str = "", **kwargs) -> List[Dict[str, Any]]:
        """Search for the most relevant documents for the given search parameters.
        It's called when the `/search` API is invoked.

        Args:
            content (str): Query to be searched from vectorstore.
            num_docs (int): Number of similar docs to be retrieved from vectorstore.
            collection_name (str): Name of the collection to be searched from vectorstore.
        """

        logger.info("Searching relevant document for the query: %s", content)

        try:
            document_embedder = get_embedding_model(model=kwargs.get("embedding_model"), url=kwargs.get("embedding_endpoint"))
            vs = get_vectorstore(document_embedder, collection_name, kwargs.get("vdb_endpoint"))
            if vs is None:
                logger.error("Vector store not initialized properly. Please check if the vector db is up and running")
                raise ValueError()

            docs = []
            local_ranker = get_ranking_model(model=kwargs.get("reranker_model"), url=kwargs.get("reranker_endpoint"), top_n=reranker_top_k)
            top_k = vdb_top_k if local_ranker and kwargs.get("enable_reranker") else reranker_top_k
            logger.info("Setting top k as: %s.", top_k)
            retriever = vs.as_retriever(search_kwargs={"k": top_k})  # milvus does not support similarily threshold

            retriever_query = content
            if messages:
                if kwargs.get("enable_query_rewriting"):
                    # conversation is tuple so it should be multiple of two
                    # -1 is to keep last k conversation
                    history_count = int(os.environ.get("CONVERSATION_HISTORY", 15)) * 2 * -1
                    messages = messages[history_count:]
                    conversation_history = []

                    for message in messages:
                        if message.role !=  "system":
                            conversation_history.append((message.role, message.content))

                    # Based on conversation history recreate query for better document retrieval
                    contextualize_q_system_prompt = (
                        "Given a chat history and the latest user question "
                        "which might reference context in the chat history, "
                        "formulate a standalone question which can be understood "
                        "without the chat history. Do NOT answer the question, "
                        "just reformulate it if needed and otherwise return it as is."
                    )
                    query_rewriter_prompt = prompts.get("query_rewriter_prompt", contextualize_q_system_prompt)
                    contextualize_q_prompt = ChatPromptTemplate.from_messages(
                        [("system", query_rewriter_prompt), MessagesPlaceholder("chat_history"), ("human", "{input}"),]
                    )
                    q_prompt = contextualize_q_prompt | query_rewriter_llm | StreamingFilterThinkParser | StrOutputParser()
                    # query to be used for document retrieval
                    logger.info("Query rewriter prompt: %s", contextualize_q_prompt)
                    retriever_query = q_prompt.invoke({"input": content, "chat_history": conversation_history})
                    logger.info("Rewritten Query: %s %s", retriever_query, len(retriever_query))
                    if retriever_query.replace('"', "'") == "''" or len(retriever_query) == 0:
                        return []
                else:
                    # Use previous user queries and current query to form a single query for document retrieval
                    user_queries = [msg.content for msg in messages if msg.role == "user"]
                    retriever_query = ". ".join([*user_queries, content])
                    logger.info("Combined retriever query: %s", retriever_query)
            # Get relevant documents with optional reflection
            if os.environ.get("ENABLE_REFLECTION", "false").lower() == "true":
                max_loops = int(os.environ.get("MAX_REFLECTION_LOOP", 3))
                reflection_counter = ReflectionCounter(max_loops)
                docs, is_relevant = check_context_relevance(content, retriever, local_ranker, reflection_counter, kwargs.get("enable_reranker"))
                if not is_relevant:
                    logger.warning("Could not find sufficiently relevant context after maximum attempts")
                return docs
            else:
                if local_ranker and kwargs.get("enable_reranker"):
                    logger.info(
                        "Narrowing the collection from %s results and further narrowing it to %s with the reranker for rag"
                        " chain.",
                        top_k,
                        reranker_top_k)
                    logger.info("Setting ranker top n as: %s.", reranker_top_k)
                    # Update number of document to be retriever by ranker
                    local_ranker.top_n = reranker_top_k

                    context_reranker = RunnableAssign({
                        "context":
                            lambda input: local_ranker.compress_documents(query=input['question'],
                                                                        documents=input['context'])
                    })

                    retriever = {"context": retriever, "question": RunnablePassthrough()} | context_reranker
                    docs = retriever.invoke(retriever_query, config={'run_name':'retriever'})
                    # Normalize scores to 0-1 range"
                    docs = normalize_relevance_scores(docs.get("context", []))
                    return docs
            docs = retriever.invoke(retriever_query, config={'run_name':'retriever'})
            # TODO: Check how to get the relevance score from milvus
            return docs

        except Exception as e:
            raise APIError(f"Failed to search documents. {str(e)}") from e

    def print_conversation_history(self, conversation_history: List[str] = None, query: str | None = None):
        if conversation_history is not None:
            for role, content in conversation_history:
                logger.info("Role: %s", role)
                logger.info("Content: %s\n", content)
        if query is not None:
            logger.info("Query: %s\n", query)
    
    def _should_use_enhanced_mode(self, query: str) -> bool:
        """Determine if enhanced RAG mode should be used for this query."""
        if not ENHANCED_COMPONENTS_AVAILABLE or not self.rag_config:
            return False
        
        return self.rag_config.should_use_enhanced(query)
    
    def _retrieve_enhanced_documents(self, query: str, vdb_endpoint: str, 
                                   vdb_top_k: int, kwargs: Dict) -> Tuple[List[Document], Dict]:
        """Retrieve documents using enhanced multi-collection approach."""
        try:
            # Always include baseline collection
            baseline_collection = kwargs.get("collection_name", "multimodal_data")
            
            # Use async retrieval for multiple collections
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            documents, metadata = loop.run_until_complete(
                self.document_aggregator.retrieve_chained_documents(
                    query=query,
                    vdb_endpoint=vdb_endpoint or self.settings.vector_store.url,
                    top_k=max(1, vdb_top_k // 3),  # Distribute across collections
                    enable_reranker=kwargs.get("enable_reranker", True),
                    **kwargs
                )
            )
            
            # Also retrieve from baseline collection if not already included
            if baseline_collection not in metadata.get("collections_searched", []):
                baseline_docs = self._retrieve_from_single_collection(
                    query, baseline_collection, vdb_endpoint, vdb_top_k // 2, kwargs
                )
                documents.extend(baseline_docs)
                metadata["baseline_docs_added"] = len(baseline_docs)
            
            logger.info("Enhanced retrieval completed: %d documents from %d collections", 
                       len(documents), len(metadata.get("collections_searched", [])))
            
            return documents, metadata
            
        except Exception as e:
            logger.error("Error in enhanced document retrieval: %s", e)
            # Fallback to baseline collection only
            return self._retrieve_from_single_collection(
                query, kwargs.get("collection_name", "multimodal_data"), 
                vdb_endpoint, vdb_top_k, kwargs
            ), {"error": str(e), "fallback": True}
    
    def _retrieve_from_single_collection(self, query: str, collection_name: str,
                                       vdb_endpoint: str, top_k: int, 
                                       kwargs: Dict) -> List[Document]:
        """Retrieve documents from a single collection."""
        try:
            document_embedder = get_embedding_model(
                model=kwargs.get("embedding_model"), 
                url=kwargs.get("embedding_endpoint")
            )
            vs = get_vectorstore(document_embedder, collection_name, vdb_endpoint)
            
            if vs is None:
                logger.warning(f"Collection {collection_name} not found")
                return []
            
            retriever = vs.as_retriever(search_kwargs={"k": top_k})
            documents = retriever.invoke(query)
            
            # Add collection metadata
            for doc in documents:
                doc.metadata["collection"] = collection_name
                
            return documents
            
        except Exception as e:
            logger.error(f"Error retrieving from collection {collection_name}: {e}")
            return []
    
    def _extract_vgpu_profiles_from_context(self, documents: List[Document]) -> set:
        """Extract valid vGPU profile names from retrieved documents."""
        if not self.profile_validator:
            return set()
        
        profile_pattern = r'\b([A-Z0-9]+)-(\d+)([A-Z])\b'
        found_profiles = set()
        
        for doc in documents:
            matches = re.findall(profile_pattern, doc.page_content)
            for match in matches:
                profile_name = f"{match[0]}-{match[1]}{match[2]}"
                # Validate it looks like a real profile
                if match[0] in ["A100", "A40", "L40S", "L40", "L4", "RTX6000", "H100"]:
                    # Check if it's a valid profile
                    is_valid, _ = self.profile_validator.validate_profile(profile_name)
                    if is_valid:
                        found_profiles.add(profile_name)
        
        logger.info(f"Found valid vGPU profiles in context: {found_profiles}")
        return found_profiles
    
    def _extract_gpu_inventory_from_query(self, query: str) -> Dict[str, int]:
        """Extract GPU inventory from query text."""
        inventory = {}
        
        # Pattern to match "2x L40S", "4x L4", etc.
        pattern = r'(\d+)x?\s*(A100|A40|L40S?|L4|H100|RTX\d+)'
        matches = re.findall(pattern, query, re.IGNORECASE)
        
        for match in matches:
            count = int(match[0])
            gpu_model = match[1].upper()
            # Normalize GPU names
            if gpu_model == "L40":
                gpu_model = "L40"
            elif gpu_model == "L40S":
                gpu_model = "L40S"
            inventory[gpu_model] = count
        
        return inventory
    
    def _prepare_enhanced_context(self, query: str, documents: List[Document], 
                                valid_profiles: set) -> str:
        """Prepare enhanced context with validation constraints."""
        if not valid_profiles and not self.profile_validator:
            return ""
        
        context_parts = []
        
        # Add valid profiles constraint
        if valid_profiles:
            context_parts.append(f"VALID vGPU PROFILES found in context: {', '.join(sorted(valid_profiles))}")
            context_parts.append("You MUST ONLY use profiles from this list. Do NOT create or modify profile names.")
        
        # Extract GPU inventory from query
        gpu_inventory = self._extract_gpu_inventory_from_query(query)
        if gpu_inventory:
            inventory_str = ", ".join([f"{count}x {gpu}" for gpu, count in gpu_inventory.items()])
            context_parts.append(f"\nUSER'S GPU INVENTORY: {inventory_str}")
            context_parts.append("You MUST only recommend configurations compatible with this inventory.")
            
            # Get recommendations if profile validator is available
            if self.profile_validator:
                try:
                    workload_requirements = self._extract_workload_requirements_from_query(query)
                    recommendations = self.profile_validator.recommend_deployment_strategy(
                        gpu_inventory, workload_requirements
                    )
                    
                    if recommendations:
                        context_parts.append("\nPRE-VALIDATED CONFIGURATION OPTIONS:")
                        for i, rec in enumerate(recommendations[:3]):  # Top 3 recommendations
                            if rec.vgpu_profile:
                                context_parts.append(f"{i+1}. {rec.vgpu_profile}: {rec.max_vms} VMs, "
                                                    f"{rec.gpu_memory_gb}GB GPU memory, {rec.concurrent_users} users")
                            else:
                                context_parts.append(f"{i+1}. GPU Passthrough on {rec.gpu_count} GPUs: "
                                                    f"{rec.max_vms} VMs, {rec.gpu_memory_gb}GB GPU memory")
                except Exception as e:
                    logger.warning(f"Error generating recommendations: {e}")
        
        # Add calculation rules
        context_parts.append("\nVM CAPACITY CALCULATION RULES:")
        context_parts.append("- For vGPU: Use the max instances per GPU from the context")
        context_parts.append("- For passthrough: 1 VM per physical GPU")
        context_parts.append("- Calculate total VMs = (number of GPUs) × (VMs per GPU)")
        
        return "\n".join(context_parts)
    
    def _extract_workload_requirements_from_query(self, query: str) -> Dict[str, Any]:
        """Extract workload requirements from query."""
        requirements = {
            "concurrent_users": 1,
            "model_memory_gb": 0,
            "deployment_mode": "vgpu",
            "performance_level": "standard"
        }
        
        # Extract user counts
        user_patterns = [
            r'(\d+)[-–]\s*(\d+)\s*(?:concurrent\s*)?users?',
            r'(\d+)\s*(?:concurrent\s*)?users?',
            r'support\s*(\d+)'
        ]
        
        for pattern in user_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    counts = [int(x) for x in match if x.isdigit()]
                    if counts:
                        requirements["concurrent_users"] = max(counts)
                else:
                    requirements["concurrent_users"] = int(match)
        
        # Extract model size (rough estimate)
        model_patterns = [r'(\d+)[Bb]\+?\s*(?:parameter|param)?', r'(\d+)[Bb]\+?']
        for pattern in model_patterns:
            matches = re.findall(pattern, query)
            for match in matches:
                param_count = int(match)
                # Rough estimate: 2 bytes per parameter for FP16
                requirements["model_memory_gb"] = max(
                    requirements["model_memory_gb"],
                    param_count * 2
                )
        
        # Check deployment mode
        if "passthrough" in query.lower() or "pass-through" in query.lower():
            requirements["deployment_mode"] = "passthrough"
        
        # Extract performance level
        if "high performance" in query.lower():
            requirements["performance_level"] = "high"
        elif "maximum performance" in query.lower():
            requirements["performance_level"] = "maximum"
        elif "cost" in query.lower() or "efficient" in query.lower():
            requirements["performance_level"] = "standard"
        
        return requirements