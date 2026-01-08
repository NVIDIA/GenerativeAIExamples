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

from .calculator import VGPUCalculator, VGPURequest, AdvancedCalculatorConfig
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
from .apply_configuration import model_extractor

# Import enhanced components
try:
    from .document_aggregator import DocumentAggregator
    ENHANCED_COMPONENTS_AVAILABLE = True
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("Enhanced components not available. Using standard RAG only.")
    ENHANCED_COMPONENTS_AVAILABLE = False

VALID_MODELS = [
    "Llama-3-8B", "Llama-3-70B", "Llama-3.1-8B", "Llama-3.1-70B",
    "Mistral-7B", "Falcon-7B", "Falcon-40B", "Falcon-180B", "Qwen-14B"
]
VALID_PRECISIONS = ["fp16", "fp8", "int8", "INT-8", "int-8", "FP16", "FP-16", "FP8", "FP-8", "fp4", "FP4"]

def extract_embedded_config(query: str) -> dict:
    """Extract structured config from HTML comment in query (from WorkloadConfigWizard)."""
    import json
    import re
    
    # Look for embedded config in format: <!--VGPU_CONFIG:{...}-->
    match = re.search(r'<!--VGPU_CONFIG:(.+?)-->', query, re.DOTALL)
    if match:
        try:
            config_json = match.group(1)
            return json.loads(config_json)
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse embedded config: {e}")
            return {}
    return {}


def parse_vgpu_query(query: str) -> dict:
    """Parse a natural language vGPU configuration query."""
    result = {
        "Workload": None,
        "Model": None,
        "Concurrent Users": None,
        "Precision": None,
        "Prompt Size": None,
        "Response Size": None,
    }
    
    # workload detection 
    for workload in ["RAG", "LLM Inference", "Inference"]:
        if re.search(rf"\b{re.escape(workload)}\b", query, re.IGNORECASE):
            result["Workload"] = workload
            break
    


    # 1) Explicit model mention
    # First, try to extract a HuggingFace model tag (format: org/model-name)
    hf_model_match = re.search(r'\b([a-zA-Z0-9_-]+/[a-zA-Z0-9._-]+(?:-[vV]?[\d.]+)?)\b', query)
    if hf_model_match:
        result["Model"] = hf_model_match.group(1)
    else:
        # Fallback: check against VALID_MODELS with flexible matching
        normalized_query = re.sub(r'[-\s]+', ' ', query.lower())
        
        for model in VALID_MODELS:
            # Normalize model name too (replace dashes/spaces with flexible pattern)
            normalized_model = re.sub(r'[-\s]+', ' ', model.lower())
            # Create a flexible pattern that matches the model name with optional version suffix
            pattern = rf"\b{re.escape(normalized_model)}(?:\s+v?[\d.]+)?\b"
            if re.search(pattern, normalized_query, re.IGNORECASE):
                result["Model"] = model
                break
    


    if not result["Model"]:
        # small: <7b parameters
        if re.search(r"<\s*7\s*[bB]", query) or re.search(r"\bsmall\b", query, re.IGNORECASE):
            result["Model"] = "Mistral-7B"
        # medium: >=7b and <=14b parameters or 'medium' keyword
        elif re.search(r"\bmedium\b", query, re.IGNORECASE) and result["Model"] is None:
            result["Model"] = "Qwen-14B"
        # large: >14b parameters or 'large' keyword
        elif re.search(r"\blarge\b", query, re.IGNORECASE) and result["Model"] is None:
            if re.search(r"\bextra\b", query, re.IGNORECASE):
                result["Model"] = "Llama-3.1-70B"
            else:
                result["Model"] = "Falcon-40B"
    
    # 3) Concurrent users
    user_match = re.search(r"(\d+)\s*(?:concurrent|simultaneous)?\s*users?", query, re.IGNORECASE)
    if user_match:
        result["Concurrent Users"] = int(user_match.group(1))
    
    # 4) Precision - support FP8, FP16, FP4, INT8
    prec_match = re.search(r"\b(fp16|fp8|fp4|int8|INT-8|FP-8)\b", query, re.IGNORECASE)
    if prec_match:
        precision = prec_match.group(1).lower().replace("-", "")
        if precision in ["fp8", "fp-8"]:
            result["Precision"] = "fp8"
        elif precision in ["fp16", "fp-16"]:
            result["Precision"] = "fp16"
        elif precision in ["fp4", "fp-4"]:
            result["Precision"] = "fp4"
        elif precision in ["int8", "int-8"]:
            result["Precision"] = "int8"
        else:
            result["Precision"] = None
    
    prompt_match = re.search(r"prompt.*?(\d+).*?tokens?", query, re.IGNORECASE)
    if prompt_match:
        try:
            result["Prompt Size"] = int(prompt_match.group(1))
        except ValueError:
            result["Prompt Size"] = None
    response_match = re.search(r"response.*?(\d+).*?tokens?", query, re.IGNORECASE)
    if response_match:
        try:
            result["Response Size"] = int(response_match.group(1))
        except ValueError:
            result["Response Size"] = None


    # 5) Default precision if not specified
    if not result["Precision"]:
        result["Precision"] = "fp8"  # Default to FP8 for modern inference
    if not result["Model"]:
        result["Model"] = "Llama-3-8B"
    if not result["Concurrent Users"]:
        result["Concurrent Users"] = 1
    if not result["Prompt Size"]:
        result["Prompt Size"] = 1024
    if not result["Response Size"]:
        result["Response Size"] = 256
    
    return result

# Structured Response Model for vGPU Configuration
class StructuredResponse(BaseModel):
    """Structured response model for vGPU configuration recommendations."""
    
    title: str = Field(
        default="generate_vgpu_config",
        description="Function title for vGPU configuration generation"
    )
    description: str = Field(
        description="Brief summary including: GPU family, vGPU profile, workload type (RAG/Inference), model name, AND precision (FP8/FP16/FP4). Example: 'BSE with vGPU profile BSE-48Q for RAG (Nemotron-30B) with FP8 precision'"
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
                    "vgpu_profile": {
                        "type": "string",
                        "description": "Exact NVIDIA vGPU profile name (must match one of the documented profiles) and must support at least gpu_memory_size GB of VRAM. ",
                        "enum": [
                            "L4-12Q, L4-24Q, L40S-24Q", "L40S-48Q", "L40-8Q", "L40-12Q", "L40-16Q",
                            "L40-24Q", "L40-48Q", "A40-8Q", "A40-12Q", "A40-16Q",
                            "A40-24Q", "A40-48Q", "L4-12Q", "L4-24Q", "DC-12Q",
                            "DC-24Q", "DC-48Q", "DC-96Q"
                        ]
                    },
                    "vcpu_count": {
                        "type": "integer",
                        "description": "Refer to the sizing guide if the workload is heavy, light, or moderate - take the cpu count here and multiply it by the concurrent users.",
                        "minimum": 1,
                        "maximum": 256
                    },
                    "gpu_memory_size": {
                        "type": "integer",
                        "description": "Total GPU VRAM needed in GB (calculate: model_params_billions × bytes_per_param × 1.2). FP16=2 bytes, INT8=1 byte.",
                        "minimum": 1,
                        "maximum": 256
                    },
                    "system_RAM": {
                        "type": "integer",  
                        "description": "System memory (in GB) allocated, including OS and framework overhead",
                        "minimum": 8,
                        "maximum": 2048
                    },
                    "max_kv_tokens": {
                        "type": ["integer", "null"],
                        "description": "Maximum KV cache tokens supported (leave null if not calculated)",
                        "minimum": 0,
                        "maximum": 1000000
                    },
                    "e2e_latency": {
                        "type": ["number", "null"],
                        "description": "End-to-end latency in seconds (leave null if not calculated)",
                        "minimum": 0
                    },
                    "time_to_first_token": {
                        "type": ["number", "null"],
                        "description": "Time to first token in seconds (leave null if not calculated)",
                        "minimum": 0
                    },
                    "throughput": {
                        "type": ["number", "null"],
                        "description": "Throughput in tokens per second (leave null if not calculated)",
                        "minimum": 0
                    }
                },
                "required": ["vgpu_profile", "vcpu_count", "gpu_memory_size", "system_RAM", "max_kv_tokens", "e2e_latency", "time_to_first_token", "throughput"],
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
            self.document_aggregator = DocumentAggregator(self.settings)
            self.profile_validator = None
            self.rag_config = None

        else:
            self.document_aggregator = None
            self.profile_validator = None
            self.rag_config = None
            self.vsphere = None

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
                    logger.info("Using nemotron thinking prompt")
                    system_prompt = "detailed thinking on"
                    # For chat mode, we don't have context, so use the chat template
                    nemotron_message += [("user", prompts.get("chat_template", ""))]
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
                    logger.info("Structured LLM response generated: %s", json_response)
                    
                    # Parse the response to extract values
                    json_data = json.loads(json_response)
                    params = json_data.get("parameters", {})
                    
                    # Build properly structured parameters with correct field names
                    corrected_params = {
                        "vgpu_profile": params.get("vgpu_profile"),
                        "vcpu_count": params.get("vcpu_count") or 8,
                        "gpu_memory_size": params.get("gpu_memory_size") or 24,
                        "system_RAM": params.get("system_RAM") or params.get("system_ram") or 96,
                        "max_kv_tokens": params.get("max_kv_tokens"),
                        "e2e_latency": params.get("e2e_latency"),
                        "time_to_first_token": params.get("time_to_first_token"),
                        "throughput": params.get("throughput"),
                        "model_tag": params.get("model_tag")
                    }
                    
                    # Enhance with calculator if model information is available
                    try:
                        # Extract embedded config if present (from WorkloadConfigWizard)
                        embedded_config = extract_embedded_config(query)
                        logger.info(f"[LLM_CHAIN DEBUG] Extracted embedded_config: {embedded_config}")
                        logger.info(f"[LLM_CHAIN DEBUG] modelTag from config: {embedded_config.get('modelTag') if embedded_config else 'NO CONFIG'}")
                        
                        # PRIORITY: Get model from embedded_config FIRST (wizard selection)
                        # This ensures we use Nemotron when user selects it, not the LLM's guess
                        model_name = None
                        if embedded_config:
                            model_name = embedded_config.get('modelTag') or embedded_config.get('specificModel')
                            if model_name:
                                logger.info(f"Using model from embedded config in llm_chain: {model_name}")
                        
                        # Only fall back to LLM params if embedded config didn't have it
                        if not model_name:
                            model_name = corrected_params.get("model_tag")
                        
                        # ALWAYS call calculator if we have a model name (regardless of vgpu_profile)
                        # The calculator will determine the correct profile/passthrough based on workload
                        if model_name:
                            logger.info(f"Enhancing LLM response with calculator for model: {model_name}")
                            
                            # Get configuration parameters
                            batch_size = int(embedded_config.get('batchSize', 1)) if embedded_config else 1
                            precision = (embedded_config.get('precision', 'fp8') if embedded_config else 'fp8').lower()
                            prompt_size = int(embedded_config.get('promptSize', 1024)) if embedded_config else 1024
                            response_size = int(embedded_config.get('responseSize', 256)) if embedded_config else 256
                            
                            # Extract GPU model from embedded config first, then vgpu_profile, then default
                            gpu_model = None
                            if embedded_config:
                                # Try selectedGPU field first
                                gpu_model = embedded_config.get('selectedGPU')
                                # If not found, try to get first key from gpuInventory
                                if not gpu_model and embedded_config.get('gpuInventory'):
                                    gpu_inventory = embedded_config.get('gpuInventory', {})
                                    if isinstance(gpu_inventory, dict) and gpu_inventory:
                                        gpu_model = list(gpu_inventory.keys())[0]
                            
                            # Fallback: try to extract from vgpu_profile if it exists and is valid
                            if not gpu_model and corrected_params.get("vgpu_profile") and corrected_params["vgpu_profile"] not in [None, "null", ""]:
                                gpu_model = corrected_params["vgpu_profile"].split('-')[0]
                            
                            # Final fallback (BSE is the wizard default)
                            if not gpu_model:
                                gpu_model = "BSE"
                            
                            logger.info(f"Using GPU model: {gpu_model} for calculator")
                            
                            # Create calculator request
                            from calculator import VGPUCalculator, VGPURequest, AdvancedCalculatorConfig
                            
                            vgpu_request = VGPURequest(
                                model_name=model_name,
                                quantization=precision,
                                n_concurrent_request=batch_size,
                                vgpu_profile=corrected_params["vgpu_profile"] or f"{gpu_model}-12Q",
                                prompt_size=prompt_size,
                                response_size=response_size,
                                framework="vllm"
                            )
                            
                            calculator = VGPUCalculator()
                            calculation = calculator.calculate(vgpu_request)
                            
                            if calculation and calculation.resultant_configuration:
                                import math
                                # Use vgpu_profile from calculator (not LLM) for accurate profile selection
                                corrected_params["vgpu_profile"] = calculation.resultant_configuration.vgpu_profile
                                corrected_params["max_kv_tokens"] = calculation.resultant_configuration.max_kv_tokens
                                corrected_params["gpu_memory_size"] = math.ceil(calculation.resultant_configuration.total_memory_gb)
                                # Add GPU model name (especially useful for passthrough configurations)
                                corrected_params["gpu_model"] = calculation.resultant_configuration.gpu_name
                                # Add GPU count (especially useful for passthrough configurations)
                                corrected_params["gpu_count"] = calculation.resultant_configuration.num_gpus
                                
                                if calculation.performance_metrics:
                                    corrected_params["e2e_latency"] = calculation.performance_metrics.e2e_latency_seconds if isinstance(calculation.performance_metrics.e2e_latency_seconds, (int, float)) else None
                                    if corrected_params["e2e_latency"] is not None:
                                        corrected_params["e2e_latency"] = str(round(corrected_params["e2e_latency"], 5)) + " (s)"
                                    corrected_params["time_to_first_token"] = calculation.performance_metrics.ttft_seconds if isinstance(calculation.performance_metrics.ttft_seconds, (int, float)) else None
                                    if corrected_params["time_to_first_token"] is not None:
                                        corrected_params["time_to_first_token"] = str(round(corrected_params["time_to_first_token"], 5)) + " (s)"
                                    corrected_params["throughput"] = calculation.performance_metrics.throughput_tokens_per_second if isinstance(calculation.performance_metrics.throughput_tokens_per_second, (int, float)) else None
                                    if corrected_params["throughput"] is not None:
                                        corrected_params["throughput"] = str(round(corrected_params["throughput"], 5)) + " (tokens/s)"
                                
                                # Add RAG breakdown from calculator
                                if hasattr(calculation, 'original_request') and calculation.original_request:
                                    rag_breakdown = calculation.original_request.get('rag_breakdown')
                                    if rag_breakdown:
                                        corrected_params["rag_breakdown"] = rag_breakdown
                                        logger.info("Added RAG breakdown to response: %s", rag_breakdown)
                                
                                logger.info("Enhanced LLM response with calculator results: %s", corrected_params)
                    except Exception as e:
                        import math
                        logger.warning("Calculator enhancement failed in llm_chain: %s", e)
                        # Fallback: Calculate profile based on gpu_memory_size
                        # Use vGPU only if single profile fits, otherwise passthrough
                        gpu_memory_size = corrected_params.get("gpu_memory_size", 24)
                        if not gpu_model:
                            gpu_model = "BSE"  # Default
                        available_profiles = {
                            'BSE': [8, 12, 24, 48, 96],
                            'L40S': [8, 12, 24, 48],
                            'L40': [8, 12, 24, 48],
                            'A40': [8, 12, 24, 48],
                            'L4': [4, 8, 12, 24]
                        }
                        profiles = available_profiles.get(gpu_model, [8, 12, 24, 48])
                        physical_memory = {'BSE': 96, 'L40S': 48, 'L40': 48, 'A40': 48, 'L4': 24}.get(gpu_model, 48)
                        
                        # Find smallest single profile that fits
                        selected_profile = None
                        for profile in sorted(profiles):
                            if profile * 0.95 >= gpu_memory_size:
                                selected_profile = profile
                                break
                        
                        if selected_profile:
                            corrected_params["vgpu_profile"] = f"{gpu_model}-{selected_profile}Q"
                            corrected_params["gpu_count"] = 1
                        else:
                            # No single profile fits - use passthrough
                            corrected_params["vgpu_profile"] = None
                            corrected_params["gpu_count"] = math.ceil(gpu_memory_size / (physical_memory * 0.95))
                            corrected_params["gpu_model"] = f"{gpu_model} (passthrough)"
                        logger.info(f"Fallback profile: {corrected_params['vgpu_profile']} x{corrected_params.get('gpu_count', 1)}")
                    
                    # Ensure embedded_config is available for final processing
                    if 'embedded_config' not in dir() or embedded_config is None:
                        embedded_config = extract_embedded_config(query)
                    
                    # Add rag_breakdown fallback for RAG workloads if not already present
                    workload_type = embedded_config.get('workloadType', 'inference') if embedded_config else 'inference'
                    if workload_type == 'rag' and "rag_breakdown" not in corrected_params and embedded_config:
                        rag_breakdown = {"workload_type": "rag"}
                        
                        embedding_model = embedded_config.get('embeddingModel')
                        vector_db_vectors = embedded_config.get('numberOfVectors')
                        vector_db_dimension = embedded_config.get('vectorDimension')
                        
                        if vector_db_vectors:
                            vector_db_vectors = int(vector_db_vectors) if isinstance(vector_db_vectors, str) else vector_db_vectors
                        if vector_db_dimension:
                            vector_db_dimension = int(vector_db_dimension) if isinstance(vector_db_dimension, str) else vector_db_dimension
                        
                        if embedding_model:
                            rag_breakdown["embedding_model"] = embedding_model
                            embedding_model_lower = embedding_model.lower()
                            if 'large' in embedding_model_lower or '1b' in embedding_model_lower:
                                embedding_mem = 2.0
                            elif 'base' in embedding_model_lower or '110m' in embedding_model_lower:
                                embedding_mem = 0.5
                            elif 'small' in embedding_model_lower:
                                embedding_mem = 0.25
                            else:
                                embedding_mem = 1.0
                            rag_breakdown["embedding_memory"] = f"{embedding_mem:.2f} GB"
                        
                        if vector_db_vectors and vector_db_dimension:
                            rag_breakdown["vector_db_vectors"] = vector_db_vectors
                            rag_breakdown["vector_db_dimension"] = vector_db_dimension
                            vector_mem_bytes = vector_db_vectors * vector_db_dimension * 4 * 1.5
                            vector_mem_gb = vector_mem_bytes / (1024**3)
                            if vector_mem_gb < 0.1:
                                rag_breakdown["vector_db_memory"] = f"{vector_mem_gb * 1024:.1f} MB"
                            else:
                                rag_breakdown["vector_db_memory"] = f"{vector_mem_gb:.2f} GB"
                        
                        corrected_params["rag_breakdown"] = rag_breakdown
                        logger.info("Added rag_breakdown fallback in llm_chain: %s", rag_breakdown)
                    
                    # CRITICAL: Use modelTag from embedded_config for the final response
                    final_model_tag = None
                    if embedded_config and embedded_config.get('modelTag'):
                        final_model_tag = embedded_config.get('modelTag')
                        logger.info(f"Using modelTag from embedded config for llm_chain final: {final_model_tag}")
                    if not final_model_tag:
                        # FALLBACK: Extract model from query text (e.g. "running nvidia/model-name")
                        import re
                        query_model_match = re.search(r'running\s+([\w\-/\.]+/[\w\-\.]+)', query, re.IGNORECASE)
                        if query_model_match:
                            final_model_tag = query_model_match.group(1)
                            logger.info(f"Extracted model from query text for llm_chain: {final_model_tag}")
                        else:
                            final_model_tag = corrected_params.get("model_tag") or "Unknown"
                    
                    # Update corrected_params to ensure JSON has the correct model_tag
                    corrected_params["model_tag"] = final_model_tag
                    
                    # Add precision from embedded config (default to FP8 - wizard default)
                    if embedded_config and embedded_config.get('precision'):
                        corrected_params["precision"] = embedded_config.get('precision').upper()
                    else:
                        corrected_params["precision"] = "FP8"  # Default if not specified (matches wizard default)
                    
                    # Get GPU model from embedded config or profile (default to BSE - wizard default)
                    final_gpu_model = "BSE"
                    if embedded_config and embedded_config.get('selectedGPU'):
                        final_gpu_model = embedded_config.get('selectedGPU')
                    elif corrected_params.get("vgpu_profile"):
                        final_gpu_model = corrected_params["vgpu_profile"].split('-')[0]
                    
                    # Reconstruct description with correct model name and precision
                    final_profile = corrected_params.get("vgpu_profile", "Unknown")
                    final_precision = corrected_params.get("precision", "FP8")
                    final_model_name = final_model_tag.split('/')[-1] if '/' in final_model_tag else final_model_tag
                    corrected_description = f"{final_gpu_model} with vGPU profile {final_profile} for inference of {final_model_name} ({final_precision})"
                    
                    # Build the final response with corrected field names
                    final_response = {
                        "title": json_data.get("title", "generate_vgpu_config"),
                        "description": corrected_description,
                        "parameters": corrected_params
                    }
                    
                    json_response = json.dumps(final_response, ensure_ascii=False, indent=2)
                    logger.info("Final corrected LLM response: %s", json_response)
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
                description="Connection timed out while making a request to the NIM endpoint. Verify if the NIM server is available."
            )
            return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])

        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                error_response = StructuredResponse(
                    description="Authentication or permission error: Verify the validity and permissions of your NVIDIA API key."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])
            elif "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid. Errror %s", e)
                error_response = StructuredResponse(
                    description="Please verify the API endpoint and your payload. Ensure that the model name is valid."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)])
            else:
                error_response = StructuredResponse(
                    description=f"Failed to generate LLM chain response. {str(e)}"
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
                    logger.info("Using nemotron thinking prompt for RAG")
                    system_prompt = "detailed thinking on"
                    # Use the nemotron_thinking_prompt instead of rag_template
                    user_message += [("user", prompts.get("nemotron_thinking_prompt", prompts.get("rag_template", "")))]
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
              pass    
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
                final_description, is_grounded = check_response_groundedness(
                    initial_response.description,
                    docs,
                    reflection_counter
                )
                
                if is_grounded:
                    # If the initial response was grounded, use it as-is
                    structured_final = initial_response
                else:
                    # If reflection improved the description, re-run the chain with enhanced prompt
                    logger.info("Re-running structured chain with grounded description from reflection")
                    
                    # Create an enhanced prompt that includes the grounded description
                    enhanced_query = f"""Original query: {query}

Based on the context documents, here is a grounded analysis:
{final_description}

Now provide a complete structured vGPU configuration based on this grounded analysis."""
                    
                    # Re-invoke the chain with the enhanced query
                    structured_final = chain.invoke({"question": enhanced_query, "context": docs})
                    
                    # Log for debugging
                    logger.info(f"Final structured response after reflection: {structured_final.description[:200]}...")
                
                # Enhance response with rag_breakdown for RAG workloads
                final_response = structured_final.model_dump()
                embedded_config = extract_embedded_config(query)
                workload_type = embedded_config.get('workloadType', 'inference') if embedded_config else 'inference'
                
                if workload_type == 'rag' and embedded_config:
                    params = final_response.get("parameters", {})
                    if "rag_breakdown" not in params:
                        rag_breakdown = {"workload_type": "rag"}
                        
                        # Extract RAG config from embedded config
                        embedding_model = embedded_config.get('embeddingModel')
                        vector_db_vectors = embedded_config.get('numberOfVectors')
                        vector_db_dimension = embedded_config.get('vectorDimension')
                        
                        if vector_db_vectors:
                            vector_db_vectors = int(vector_db_vectors) if isinstance(vector_db_vectors, str) else vector_db_vectors
                        if vector_db_dimension:
                            vector_db_dimension = int(vector_db_dimension) if isinstance(vector_db_dimension, str) else vector_db_dimension
                        
                        if embedding_model:
                            rag_breakdown["embedding_model"] = embedding_model
                            # Calculate embedding memory based on model size
                            embedding_model_lower = embedding_model.lower()
                            if 'large' in embedding_model_lower or '1b' in embedding_model_lower:
                                embedding_mem = 2.0
                            elif 'base' in embedding_model_lower or '110m' in embedding_model_lower:
                                embedding_mem = 0.5
                            elif 'small' in embedding_model_lower:
                                embedding_mem = 0.25
                            else:
                                embedding_mem = 1.0
                            rag_breakdown["embedding_memory"] = f"{embedding_mem:.2f} GB"
                        
                        if vector_db_vectors and vector_db_dimension:
                            rag_breakdown["vector_db_vectors"] = vector_db_vectors
                            rag_breakdown["vector_db_dimension"] = vector_db_dimension
                            vector_mem_bytes = vector_db_vectors * vector_db_dimension * 4 * 1.5
                            vector_mem_gb = vector_mem_bytes / (1024**3)
                            if vector_mem_gb < 0.1:
                                rag_breakdown["vector_db_memory"] = f"{vector_mem_gb * 1024:.1f} MB"
                            else:
                                rag_breakdown["vector_db_memory"] = f"{vector_mem_gb:.2f} GB"
                        
                        params["rag_breakdown"] = rag_breakdown
                        final_response["parameters"] = params
                        logger.info("Added rag_breakdown to reflection response: %s", rag_breakdown)
                
                return iter([json.dumps(final_response, ensure_ascii=False, indent=2)]), context_to_show
            else:
                def stream_structured_rag_response():
                    try:
                        logger.info("Here is the query: %s", query)


                        structured_result = chain.invoke({"question": query, "context": docs}, config={'run_name':'llm-stream'})
                        json_response = json.dumps(structured_result.model_dump(), ensure_ascii=False, indent=2)
                        logger.info("Structured RAG response generated successfully: %s", json_response)
                        
                        # Parse the response to extract values
                        json_data = json.loads(json_response)
                        params = json_data.get("parameters", {})
                        
                        # Extract GPU info and model info from wherever the LLM put it
                        vgpu_profile = params.get("vgpu_profile") or ""
                        
                        # Extract embedded config to get the actual GPU model and LLM model selected by user
                        embedded_config = extract_embedded_config(query)
                        logger.info(f"[RAG DEBUG] Extracted embedded_config: {embedded_config}")
                        logger.info(f"[RAG DEBUG] modelTag from config: {embedded_config.get('modelTag') if embedded_config else 'NO CONFIG'}")
                        
                        # PRIORITY: Get model from embedded config (wizard selection) FIRST
                        # This ensures we use Nemotron when user selects it, not fallback to LLM's guess
                        model_name = None
                        if embedded_config:
                            model_name = embedded_config.get('modelTag') or embedded_config.get('specificModel')
                            if model_name:
                                logger.info(f"Using model from embedded config: {model_name}")
                        
                        # Fallback to LLM params only if embedded config didn't have it
                        if not model_name:
                            model_name = params.get("model_name") or params.get("model")
                        
                        # Extract GPU model from embedded config first (most reliable)
                        gpu_model = None
                        if embedded_config:
                            # Try selectedGPU field first
                            gpu_model = embedded_config.get('selectedGPU')
                            # If not found, try to get first key from gpuInventory
                            if not gpu_model and embedded_config.get('gpuInventory'):
                                gpu_inventory = embedded_config.get('gpuInventory', {})
                                if isinstance(gpu_inventory, dict) and gpu_inventory:
                                    gpu_model = list(gpu_inventory.keys())[0]
                        
                        # Fallback: try params.gpu_model or extract from vgpu_profile if it exists and is valid
                        if not gpu_model:
                            gpu_model = params.get("gpu_model")
                        if not gpu_model and vgpu_profile and vgpu_profile not in [None, "null", ""]:
                            gpu_model = vgpu_profile.split('-')[0]
                        
                        # Final fallback (BSE is the wizard default)
                        if not gpu_model:
                            gpu_model = "BSE"
                        
                        logger.info(f"Using GPU model: {gpu_model} for RAG chain")
                        
                        # Initialize workload with default value
                        workload = "RAG"  # Default to RAG for RAG chain queries
                        prompt_size = None
                        response_size = None
        
                        # Try to extract from description if not in parameters
                        if not model_name:
                            payload = parse_vgpu_query(query)
                            model_name = model_name or payload.get("Model")
                            precision = payload.get("Precision", "fp8").lower()
                            workload = payload.get("Workload") or payload.get("workload") or "RAG"
                            prompt_size = payload.get("Prompt Size")
                            response_size = payload.get("Response Size")
                            logger.info("Extracted model name: %s, precision: %s, workload: %s, prompt size: %s, response size: %s", model_name, precision, workload, prompt_size, response_size)
                        else:
                            # Even if model_name exists, try to extract workload from query
                            payload = parse_vgpu_query(query)
                            workload = payload.get("Workload") or payload.get("workload") or "RAG"
                            prompt_size = payload.get("Prompt Size")
                            response_size = payload.get("Response Size")
                        # Build properly structured parameters with correct field names
                        # PRIORITY: Use the modelTag from embedded_config directly if available
                        # This is the AUTHORITATIVE source - user selected this in the wizard
                        model_tag = None
                        if embedded_config and embedded_config.get('modelTag'):
                            # Embedded config has the full HuggingFace model tag from wizard - USE THIS
                            model_tag = embedded_config.get('modelTag')
                            logger.info(f"Using modelTag from embedded config (authoritative): {model_tag}")
                        else:
                            # FALLBACK: Extract model from query text (e.g. "running nvidia/model-name")
                            # This handles cases where embedded config isn't sent
                            import re
                            query_model_match = re.search(r'running\s+([\w\-/\.]+/[\w\-\.]+)', query, re.IGNORECASE)
                            if query_model_match:
                                model_tag = query_model_match.group(1)
                                logger.info(f"Extracted model from query text: {model_tag}")
                            elif model_name:
                                # Fallback to model_name extraction only if no embedded config
                                if "/" in model_name:
                                    model_tag = model_name
                                    logger.info(f"Using HuggingFace model tag directly: {model_tag}")
                                else:
                                    model_tag = model_extractor.extract(model_name)
                                    if not model_tag:
                                        # No fallback to hardcoded model - use what was provided
                                        logger.warning(f"No match for model '{model_name}', keeping as-is")
                                        model_tag = model_name  # Use the provided name, don't substitute
                        
                        # CRITICAL: ALWAYS update model_name with extracted model_tag for VGPURequest
                        # The model_tag from query/embedded_config is authoritative over params defaults
                        if model_tag:
                            model_name = model_tag
                            logger.info(f"Using model_tag for calculator: {model_name}")

                        # Get precision from embedded config (default to fp8 which is the wizard default)
                        precision_from_config = (embedded_config.get('precision', 'fp8') if embedded_config else precision or 'fp8').lower()
                        
                        # Get prompt/response sizes from embedded config first
                        prompt_size_from_config = int(embedded_config.get('promptSize', 1024)) if embedded_config else (prompt_size or 1024)
                        response_size_from_config = int(embedded_config.get('responseSize', 256)) if embedded_config else (response_size or 256)
                        
                        corrected_params = {
                            "vgpu_profile": params.get("vgpu_profile"),
                            "vcpu_count": ((params.get("system_RAM") or 96) // 4),
                            "gpu_memory_size": params.get("gpu_memory_size") or 24,
                            "system_RAM": params.get("system_RAM") or params.get("system_ram") or 96,
                            "max_kv_tokens": None,
                            "e2e_latency": None,
                            "time_to_first_token": None,
                            "throughput": None,
                            "model_tag": model_tag,
                            # Add precision and prompt/response sizes
                            "precision": precision_from_config.upper(),
                            "prompt_size": prompt_size_from_config,
                            "response_size": response_size_from_config,
                        }
                        

                        corrected_params["vgpu_profile"] = f"{gpu_model}-12Q"
                        
                        extra_gpu_memory = None

                        try:
                            vector_dim_pattern = r"(\d+)[dD]\s+vectors?"

                            # Pattern 2: Extract total number of vectors (e.g., "100 total vectors")
                            vector_count_pattern = r"(\d+)\s+(?:total\s+)?vectors?"

                                # Apply regex
                            vector_dim_match = re.search(vector_dim_pattern, query)
                            vector_count_match = re.search(vector_count_pattern, query)

                                # Extracted values
                            vector_dim = vector_dim_match.group(1) if vector_dim_match else None
                            vector_count = vector_count_match.group(1) if vector_count_match else None

                            if vector_dim and vector_count:
                                logger.info("Extracted vector dimension: %s, vector count: %s", vector_dim, vector_count)
                                extra_gpu_memory = (int(vector_dim) * int(vector_count) * 2) / (1024 ** 3)
                        except:
                            pass
                        # If we have model info and it's a workload we can calculate, enhance with calculator
                        if model_name and workload in ["RAG", "LLM Inference", "Inference"]:
                            try:
                                # embedded_config already extracted above
                                # Get batch size from embedded config, or default to 1
                                batch_size = int(embedded_config.get('batchSize', 1)) if embedded_config else 1
                                logger.info(f"Using batch size (concurrent requests): {batch_size}")
                                
                                # Extract RAG-specific parameters if workload type is RAG
                                # First try embedded config, then detect from query text, then fall back to LLM response
                                workload_type = embedded_config.get('workloadType', 'inference') if embedded_config else 'inference'
                                
                                # ROBUST RAG DETECTION: Check query text directly for RAG indicators
                                is_rag_query = ('RAG' in query or 'Retrieval-Augmented' in query or 
                                               'embedding model' in query.lower() or 'vector' in query.lower())
                                if is_rag_query:
                                    workload_type = 'rag'
                                    logger.info(f"Workload type set to 'rag' based on query text analysis")
                                # If embedded config says inference but LLM extracted "RAG", use that instead
                                elif workload_type.lower() == 'inference' and workload and 'rag' in workload.lower():
                                    workload_type = 'rag'
                                    logger.info(f"Workload type set to 'rag' based on LLM extraction: {workload}")
                                else:
                                    workload_type = 'rag' if workload_type.lower() == 'rag' else 'inference'
                                
                                embedding_model = None
                                vector_db_vectors = None
                                vector_db_dimension = None
                                if workload_type == 'rag':
                                    # Try to get from embedded config first
                                    if embedded_config:
                                        embedding_model = embedded_config.get('embeddingModel')
                                        # Convert to integers if present (they come as strings from JSON)
                                        num_vectors = embedded_config.get('numberOfVectors')
                                        vec_dim = embedded_config.get('vectorDimension')
                                        if num_vectors:
                                            vector_db_vectors = int(num_vectors) if isinstance(num_vectors, str) else num_vectors
                                        if vec_dim:
                                            vector_db_dimension = int(vec_dim) if isinstance(vec_dim, str) else vec_dim
                                    
                                    # If not in embedded config, try to extract from query text
                                    if not embedding_model:
                                        # Extract embedding model from query (e.g., "using embedding model nvidia/nvolveqa-embed-large-1B")
                                        embedding_match = re.search(r'embedding\s+model\s+([^\s,]+)', query, re.IGNORECASE)
                                        if embedding_match:
                                            embedding_model = embedding_match.group(1)
                                            logger.info(f"Extracted embedding model from query: {embedding_model}")
                                    
                                    # If vector DB params not in embedded config, try to extract from query
                                    if not vector_db_vectors or not vector_db_dimension:
                                        # Extract vector dimension (e.g., "1024d vectors" or "1024D")
                                        vector_dim_match = re.search(r'(\d+)[dD]\s+vectors?', query, re.IGNORECASE)
                                        if vector_dim_match:
                                            vector_db_dimension = int(vector_dim_match.group(1))
                                        
                                        # Extract vector count (e.g., "10000 total vectors" or "10000 vectors")
                                        vector_count_match = re.search(r'(\d+)\s+(?:total\s+)?vectors?', query, re.IGNORECASE)
                                        if vector_count_match:
                                            vector_db_vectors = int(vector_count_match.group(1))
                                        
                                        if vector_db_dimension or vector_db_vectors:
                                            logger.info(f"Extracted vector DB params from query - Dimension: {vector_db_dimension}, Vectors: {vector_db_vectors}")
                                    
                                    if embedding_model:
                                        logger.info(f"RAG workload detected - Embedding: {embedding_model}, Vectors: {vector_db_vectors}, Dimension: {vector_db_dimension}")
                                
                                advanced_config = None
                                if 'advanced_config' in kwargs and kwargs['advanced_config']:
                                    adv_cfg_dict = kwargs['advanced_config']
                                    advanced_config = AdvancedCalculatorConfig(
                                        model_memory_overhead=adv_cfg_dict.get('model_memory_overhead', 1.3),
                                        hypervisor_reserve_gb=adv_cfg_dict.get('hypervisor_reserve_gb', 3.0),
                                        cuda_memory_overhead=adv_cfg_dict.get('cuda_memory_overhead', 1.2),
                                        vcpu_per_gpu=adv_cfg_dict.get('vcpu_per_gpu', 8),
                                        ram_gb_per_vcpu=adv_cfg_dict.get('ram_gb_per_vcpu', 8),
                                    )
                                elif embedded_config and 'advancedConfig' in embedded_config:
                                    # Use advanced config from embedded config if available
                                    adv_cfg = embedded_config['advancedConfig']
                                    advanced_config = AdvancedCalculatorConfig(
                                        model_memory_overhead=adv_cfg.get('modelMemoryOverhead', 1.3),
                                        hypervisor_reserve_gb=adv_cfg.get('hypervisorReserveGb', 3.0),
                                        cuda_memory_overhead=adv_cfg.get('cudaMemoryOverhead', 1.2),
                                        vcpu_per_gpu=adv_cfg.get('vcpuPerGpu', 8),
                                        ram_gb_per_vcpu=adv_cfg.get('ramGbPerVcpu', 8),
                                    )
                                
                                vgpu_request = VGPURequest(
                                    model_name=model_name,
                                    quantization=precision,
                                    n_concurrent_request=batch_size,  # Use batch size from embedded config
                                    vgpu_profile=corrected_params["vgpu_profile"] or f"{gpu_model}-{corrected_params['gpu_memory_size']}Q",
                                    prompt_size=prompt_size,
                                    response_size=response_size,
                                    advanced_config=advanced_config,
                                    # RAG-specific parameters
                                    workload_type=workload_type,
                                    embedding_model=embedding_model,
                                    vector_db_vectors=vector_db_vectors,
                                    vector_db_dimension=vector_db_dimension,
                                    framework="vllm"  # Default framework
                                )
                                
                                calculator = VGPUCalculator()
                                calculation = calculator.calculate(vgpu_request)
                                
                                if calculation and calculation.resultant_configuration:
                                    import math 
                                    # Use the recommended vgpu_profile from calculator (not LLM)
                                    # This ensures correct profile selection (e.g., 15GB -> L40S-24Q, not L40S-48Q)
                                    corrected_params["vgpu_profile"] = calculation.resultant_configuration.vgpu_profile
                                    corrected_params["max_kv_tokens"] = calculation.resultant_configuration.max_kv_tokens
                                    # Use calculator's total_memory_gb directly - it already includes all RAG components
                                    # Do NOT add extra_gpu_memory as that would double-count vector DB memory
                                    corrected_params["gpu_memory_size"] = calculation.resultant_configuration.total_memory_gb
                                    # Add GPU model name (especially useful for passthrough configurations)
                                    corrected_params["gpu_model"] = calculation.resultant_configuration.gpu_name
                                    # Add GPU count (especially useful for passthrough configurations)
                                    corrected_params["gpu_count"] = calculation.resultant_configuration.num_gpus
                                    if calculation.performance_metrics:
                                        corrected_params["e2e_latency"] = calculation.performance_metrics.e2e_latency_seconds if isinstance(calculation.performance_metrics.e2e_latency_seconds, (int, float)) else None
                                        if corrected_params["e2e_latency"] is not None:
                                            corrected_params["e2e_latency"] = str(round(corrected_params["e2e_latency"], 5)) + " (s)"
                                        corrected_params["time_to_first_token"] = calculation.performance_metrics.ttft_seconds if isinstance(calculation.performance_metrics.ttft_seconds, (int, float)) else None
                                        if corrected_params["time_to_first_token"] is not None:
                                            corrected_params["time_to_first_token"] = str(round(corrected_params["time_to_first_token"], 5)) + " (s)"
                                        corrected_params["throughput"] = calculation.performance_metrics.throughput_tokens_per_second if isinstance(calculation.performance_metrics.throughput_tokens_per_second, (int, float)) else None
                                        if corrected_params["throughput"] is not None:
                                            corrected_params["throughput"] = str(round(corrected_params["throughput"], 5)) + " (tokens/s)"
                                    
                                    # Use advanced config values for vCPU and RAM calculation
                                    adv_config = vgpu_request.advanced_config if vgpu_request.advanced_config else AdvancedCalculatorConfig()
                                    
                                    num_gpu = calculation.resultant_configuration.num_gpus
                                    vCPU_count = adv_config.vcpu_per_gpu * num_gpu
                                    system_RAM = adv_config.ram_gb_per_vcpu * vCPU_count
                                    corrected_params["vcpu_count"] = vCPU_count
                                    corrected_params["system_RAM"] = system_RAM
                                    
                                    # Add RAG breakdown from calculator
                                    if hasattr(calculation, 'original_request') and calculation.original_request:
                                        rag_breakdown = calculation.original_request.get('rag_breakdown')
                                        if rag_breakdown:
                                            corrected_params["rag_breakdown"] = rag_breakdown
                                            logger.info("Added RAG breakdown to response: %s", rag_breakdown)

                                        
                                logger.info("Enhanced with calculator results: %s", corrected_params)
                            except Exception as e:
                                import traceback
                                logger.warning("Calculator enhancement failed: %s", e)
                                logger.warning("Traceback: %s", traceback.format_exc())
                                # Fallback: Calculate profile based on gpu_memory_size even if calculator fails
                                gpu_memory_size = corrected_params.get("gpu_memory_size", 24)
                                # Profile selection: Pick smallest profile where profile × 0.95 >= workload
                                # If no single profile fits, use passthrough
                                available_profiles = {
                                    'BSE': [8, 12, 24, 48, 96],
                                    'L40S': [8, 12, 24, 48],
                                    'L40': [8, 12, 24, 48],
                                    'A40': [8, 12, 24, 48],
                                    'L4': [4, 8, 12, 24]
                                }
                                profiles = available_profiles.get(gpu_model, [8, 12, 24, 48])
                                physical_memory = {'BSE': 96, 'L40S': 48, 'L40': 48, 'A40': 48, 'L4': 24}.get(gpu_model, 48)
                                
                                # Find smallest single profile where profile × 0.95 >= workload
                                selected_profile = None
                                for profile in sorted(profiles):
                                    if profile * 0.95 >= gpu_memory_size:
                                        selected_profile = profile
                                        break
                                
                                if selected_profile:
                                    # Single vGPU profile fits
                                    corrected_params["vgpu_profile"] = f"{gpu_model}-{selected_profile}Q"
                                    corrected_params["gpu_count"] = 1
                                    logger.info(f"Fallback: Using {corrected_params['vgpu_profile']}")
                                else:
                                    # No single profile fits - use passthrough
                                    corrected_params["vgpu_profile"] = None
                                    corrected_params["gpu_count"] = math.ceil(gpu_memory_size / (physical_memory * 0.95))
                                    corrected_params["gpu_model"] = f"{gpu_model} (passthrough)"
                                    logger.info(f"Fallback: Using passthrough with {corrected_params['gpu_count']}x {gpu_model}")
                        
                        # Add RAG-specific fields to the response if this is a RAG workload
                        if workload_type == 'rag':
                            # Add top-level RAG fields
                            if embedding_model:
                                corrected_params["embedding_model"] = embedding_model
                            if vector_db_vectors:
                                corrected_params["vector_db_vectors"] = vector_db_vectors
                            if vector_db_dimension:
                                corrected_params["vector_db_dimension"] = vector_db_dimension
                            
                            # Build rag_breakdown if not already present (from calculator)
                            if "rag_breakdown" not in corrected_params:
                                rag_breakdown = {"workload_type": "rag"}
                                if embedding_model:
                                    rag_breakdown["embedding_model"] = embedding_model
                                    # Calculate embedding memory based on model size (approximate)
                                    # Common embedding models and their approximate sizes:
                                    embedding_model_lower = embedding_model.lower()
                                    if 'large' in embedding_model_lower or '1b' in embedding_model_lower:
                                        embedding_mem = 2.0  # ~1B params at FP16
                                    elif 'base' in embedding_model_lower or '110m' in embedding_model_lower:
                                        embedding_mem = 0.5  # ~110M params at FP16
                                    elif 'small' in embedding_model_lower:
                                        embedding_mem = 0.25  # ~33M params at FP16
                                    else:
                                        embedding_mem = 1.0  # Default estimate
                                    rag_breakdown["embedding_memory"] = f"{embedding_mem:.2f} GB"
                                
                                if vector_db_vectors and vector_db_dimension:
                                    rag_breakdown["vector_db_vectors"] = vector_db_vectors
                                    rag_breakdown["vector_db_dimension"] = vector_db_dimension
                                    # Calculate vector DB memory: vectors * dimension * 4 bytes (float32) + 50% overhead for index
                                    vector_mem_bytes = vector_db_vectors * vector_db_dimension * 4 * 1.5
                                    vector_mem_gb = vector_mem_bytes / (1024**3)
                                    if vector_mem_gb < 0.1:
                                        rag_breakdown["vector_db_memory"] = f"{vector_mem_gb * 1024:.1f} MB"
                                    else:
                                        rag_breakdown["vector_db_memory"] = f"{vector_mem_gb:.2f} GB"
                                elif vector_db_vectors:
                                    rag_breakdown["vector_db_vectors"] = vector_db_vectors
                                elif vector_db_dimension:
                                    rag_breakdown["vector_db_dimension"] = vector_db_dimension
                                
                                # Add prompt/response size info
                                rag_breakdown["prompt_size"] = prompt_size_from_config
                                rag_breakdown["response_size"] = response_size_from_config
                                corrected_params["rag_breakdown"] = rag_breakdown
                                logger.info("Built RAG breakdown manually: %s", rag_breakdown)
                            else:
                                logger.info("Using rag_breakdown from calculator: %s", corrected_params["rag_breakdown"])
                        
                        # Reconstruct description with correct format: GPU family, profile, workload, model, precision
                        final_profile = corrected_params.get("vgpu_profile", f"{gpu_model}-12Q")
                        final_precision = corrected_params.get("precision", precision_from_config.upper())
                        
                        # CRITICAL: Get model_tag from embedded_config first (most reliable source)
                        # This ensures the JSON model_tag matches what the user selected in the wizard
                        final_model_tag = None
                        if embedded_config and embedded_config.get('modelTag'):
                            final_model_tag = embedded_config.get('modelTag')
                            logger.info(f"Using modelTag from embedded config for final response: {final_model_tag}")
                        if not final_model_tag:
                            final_model_tag = corrected_params.get("model_tag") or model_tag or "Unknown"
                        
                        # Update corrected_params to ensure JSON has the correct model_tag
                        corrected_params["model_tag"] = final_model_tag
                        
                        if workload_type == 'rag':
                            # Format: "L40S with vGPU profile L40S-48Q for RAG (model-name) with embedding-model (FP8)"
                            emb_model_name = embedding_model.split('/')[-1] if embedding_model else "embedding"
                            final_model_name = final_model_tag.split('/')[-1] if '/' in final_model_tag else final_model_tag
                            corrected_description = f"{gpu_model} with vGPU profile {final_profile} for RAG ({final_model_name}) with {emb_model_name} ({final_precision})"
                            
                            # Add rag_config sub-object with RAG-specific configuration
                            rag_config = {
                                "workload_type": "rag",
                                "embedding_model": embedding_model,
                                "vector_dimension": vector_db_dimension,
                                "total_vectors": vector_db_vectors,
                            }
                            # Remove None values
                            rag_config = {k: v for k, v in rag_config.items() if v is not None}
                            if rag_config:
                                corrected_params["rag_config"] = rag_config
                                logger.info(f"Added rag_config to response: {rag_config}")
                        else:
                            # Format: "L40S with vGPU profile L40S-48Q for inference of model-name (FP8)"
                            final_model_name = final_model_tag.split('/')[-1] if '/' in final_model_tag else final_model_tag
                            corrected_description = f"{gpu_model} with vGPU profile {final_profile} for inference of {final_model_name} ({final_precision})"
                        
                        # Build the final response with corrected field names
                        final_response = {
                            "title": json_data.get("title", "generate_vgpu_config"),
                            "description": corrected_description,
                            "parameters": corrected_params
                        }
                        
                        json_response = json.dumps(final_response, ensure_ascii=False, indent=2)
                        logger.info("Final corrected response: %s", json_response)
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
                description="Connection timed out while making a request to the NIM endpoint. Verify if the NIM server is available."
            )
            return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []

        except requests.exceptions.ConnectionError as e:
            if "HTTPConnectionPool" in str(e):
                logger.warning("Connection pool error while connecting to service: %s", e)
                error_response = StructuredResponse(
                    description="Connection error: Failed to connect to service. Please verify if all required services are running and accessible."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []
        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                error_response = StructuredResponse(
                    description="Authentication or permission error: Verify the validity and permissions of your NVIDIA API key."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []
            elif "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                error_response = StructuredResponse(
                    description="Please verify the API endpoint and your payload. Ensure that the model name is valid."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []
            else:
                error_response = StructuredResponse(
                    description=f"Failed to generate RAG chain response. {str(e)}"
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []


    def rag_chain_with_multiturn(self,
                                 query: str,
                                 chat_history: List[Dict[str, Any]],
                                 reranker_top_k: int,
                                 vdb_top_k: int,
                                 collection_name: str,
                                 **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""

        # Check for conversational mode - return plain text instead of structured JSON
        conversational_mode = kwargs.get("conversational_mode", False)
        if conversational_mode:
            logger.info("Using CONVERSATIONAL mode for chat query: %s", query[:100])
            return self._conversational_chain(query, chat_history, reranker_top_k, vdb_top_k, collection_name, **kwargs)

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
                    logger.info("Using nemotron thinking prompt for multiturn RAG")
                    system_prompt = "detailed thinking on"
                    # Use the nemotron_thinking_prompt instead of rag_template
                    user_message += [("user", prompts.get("nemotron_thinking_prompt", prompts.get("rag_template", "")))]
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
                        return iter([""]), []
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
                final_description, is_grounded = check_response_groundedness(
                    initial_response.description,
                    docs,
                    reflection_counter
                )
                
                if is_grounded:
                    # If the initial response was grounded, use it as-is
                    structured_final = initial_response
                else:
                    # If reflection improved the description, re-run the chain with enhanced prompt
                    logger.info("Re-running structured chain with grounded description from reflection")
                    
                    # Create an enhanced prompt that includes the grounded description
                    enhanced_query = f"""Original query: {query}

Based on the context documents, here is a grounded analysis:
{final_description}

Now provide a complete structured vGPU configuration based on this grounded analysis."""
                    
                    # Re-invoke the chain with the enhanced query
                    structured_final = chain.invoke({"question": enhanced_query, "context": docs})
                    
                    # Log for debugging
                    logger.info(f"Final structured response after reflection: {structured_final.description[:200]}...")
                
                return iter([json.dumps(structured_final.model_dump(), ensure_ascii=False, indent=2)]), context_to_show
            else:
                def stream_structured_multiturn_response():
                    try:
                        structured_result = chain.invoke({"question": query, "context": docs}, config={'run_name':'llm-stream'})
                        json_response = json.dumps(structured_result.model_dump(), ensure_ascii=False, indent=2)
                        logger.info("Structured multiturn RAG response generated: %s", json_response)
                        
                        # Parse the response to extract values
                        json_data = json.loads(json_response)
                        params = json_data.get("parameters", {})
                        
                        # Extract GPU info and model info from wherever the LLM put it
                        vgpu_profile = params.get("vgpu_profile") or ""
                        model_name = params.get("model_name") or params.get("model")
                        precision = params.get("precision", "fp8").lower() if params.get("precision") else "fp8"
                        
                        # Extract embedded config to get the actual GPU model selected by user
                        embedded_config = extract_embedded_config(query)
                        logger.info(f"[MULTITURN DEBUG] Extracted embedded_config: {embedded_config}")
                        logger.info(f"[MULTITURN DEBUG] modelTag from config: {embedded_config.get('modelTag') if embedded_config else 'NO CONFIG'}")
                        
                        # Extract GPU model from embedded config first (most reliable)
                        gpu_model = None
                        if embedded_config:
                            # Try selectedGPU field first
                            gpu_model = embedded_config.get('selectedGPU')
                            # If not found, try to get first key from gpuInventory
                            if not gpu_model and embedded_config.get('gpuInventory'):
                                gpu_inventory = embedded_config.get('gpuInventory', {})
                                if isinstance(gpu_inventory, dict) and gpu_inventory:
                                    gpu_model = list(gpu_inventory.keys())[0]
                        
                        # Fallback: try params.gpu_model or extract from vgpu_profile if it exists and is valid
                        if not gpu_model:
                            gpu_model = params.get("gpu_model")
                        if not gpu_model and vgpu_profile and vgpu_profile not in [None, "null", ""]:
                            gpu_model = vgpu_profile.split('-')[0]
                        
                        # Final fallback (BSE is the wizard default)
                        if not gpu_model:
                            gpu_model = "BSE"
                        
                        logger.info(f"Using GPU model: {gpu_model} for multiturn RAG chain")
                        
                        # Initialize workload with default value
                        workload = "RAG"  # Default to RAG for multiturn queries
                        
                        # Try to extract from description if not in parameters
                        if not model_name:
                            payload = parse_vgpu_query(json_data.get("description", ""))
                            model_name = model_name or payload.get("Model")
                            precision = precision or payload.get("Precision", "fp8").lower()
                            workload = payload.get("Workload", "RAG")
                        else:
                            # Even if model_name exists, try to extract workload from description
                            payload = parse_vgpu_query(json_data.get("description", ""))
                            workload = payload.get("Workload", "RAG")
                        
                        # PRIORITY: Use modelTag from embedded_config directly if available
                        # This is the AUTHORITATIVE source - user selected this in the wizard
                        model_tag = None
                        if embedded_config and embedded_config.get('modelTag'):
                            model_tag = embedded_config.get('modelTag')
                            logger.info(f"Using modelTag from embedded config for multiturn (authoritative): {model_tag}")
                        else:
                            # FALLBACK: Extract model from query text (e.g. "running nvidia/model-name")
                            # This handles cases where embedded config isn't sent
                            import re
                            query_model_match = re.search(r'running\s+([\w\-/\.]+/[\w\-\.]+)', query, re.IGNORECASE)
                            if query_model_match:
                                model_tag = query_model_match.group(1)
                                logger.info(f"Extracted model from query text: {model_tag}")
                            elif model_name:
                                # Fallback to model_name extraction only if no embedded config
                                if "/" in model_name:
                                    model_tag = model_name
                                    logger.info(f"Using HuggingFace model tag directly: {model_tag}")
                                else:
                                    model_tag = model_extractor.extract(model_name)
                                    if not model_tag:
                                        # No fallback to hardcoded model - use what was provided
                                        logger.warning(f"No match for model '{model_name}', keeping as-is")
                                        model_tag = model_name  # Use the provided name, don't substitute
                        
                        # CRITICAL: ALWAYS update model_name with extracted model_tag for VGPURequest
                        # The model_tag from query/embedded_config is authoritative over params defaults
                        if model_tag:
                            model_name = model_tag
                            logger.info(f"Using model_tag for calculator: {model_name}")
                        
                        # Get precision from embedded config (default to fp8 - wizard default)
                        precision_from_config = (embedded_config.get('precision', 'fp8') if embedded_config else precision or 'fp8').lower()
                        
                        # Build properly structured parameters with correct field names
                        corrected_params = {
                            "vgpu_profile": params.get("vgpu_profile"),
                            "vcpu_count": params.get("vcpu_count") or 8,
                            "gpu_memory_size": params.get("gpu_memory_size") or 24,
                            "system_RAM": params.get("system_RAM") or params.get("system_ram") or 96,
                            "max_kv_tokens": None,
                            "e2e_latency": None,
                            "time_to_first_token": None,
                            "throughput": None,
                            "model_tag": model_tag,
                            "precision": precision_from_config.upper()
                        }
                        
                        # If we have model info and it's a workload we can calculate, enhance with calculator
                        if model_name and workload in ["RAG", "LLM Inference", "Inference"]:
                            try:
                                vgpu_request = VGPURequest(
                                    model_name=model_name,
                                    quantization=precision,
                                    n_concurrent_request=1,  # Default to 1 if not specified
                                    vgpu_profile=corrected_params["vgpu_profile"] or f"{gpu_model}-12Q"
                                )
                                
                                calculator = VGPUCalculator()
                                calculation = calculator.calculate(vgpu_request)
                                
                                if calculation and calculation.resultant_configuration:
                                    # Update with calculated values
                                    # Use vgpu_profile from calculator (not LLM) for accurate profile selection
                                    corrected_params["vgpu_profile"] = calculation.resultant_configuration.vgpu_profile
                                    corrected_params["max_kv_tokens"] = calculation.resultant_configuration.max_kv_tokens
                                    # Use calculator's total_memory_gb directly - it already includes all components
                                    # This replaces the LLM's estimate with the actual calculated value
                                    corrected_params["gpu_memory_size"] = calculation.resultant_configuration.total_memory_gb
                                    # Add GPU model name (especially useful for passthrough configurations)
                                    corrected_params["gpu_model"] = calculation.resultant_configuration.gpu_name
                                    # Add GPU count (especially useful for passthrough configurations)
                                    corrected_params["gpu_count"] = calculation.resultant_configuration.num_gpus
                                    
                                    if calculation.performance_metrics:
                                        corrected_params["e2e_latency"] = calculation.performance_metrics.e2e_latency_seconds if isinstance(calculation.performance_metrics.e2e_latency_seconds, (int, float)) else None
                                        corrected_params["time_to_first_token"] = calculation.performance_metrics.ttft_seconds if isinstance(calculation.performance_metrics.ttft_seconds, (int, float)) else None
                                        corrected_params["throughput"] = calculation.performance_metrics.throughput_tokens_per_second if isinstance(calculation.performance_metrics.throughput_tokens_per_second, (int, float)) else None
                                
                                logger.info("Enhanced multiturn with calculator results: %s", corrected_params)
                            except Exception as e:
                                import math
                                logger.warning("Calculator enhancement failed in multiturn: %s", e)
                                # Fallback: Calculate profile based on gpu_memory_size
                                # Use vGPU only if single profile fits, otherwise passthrough
                                gpu_memory_size = corrected_params.get("gpu_memory_size", 24)
                                available_profiles = {
                                    'BSE': [8, 12, 24, 48, 96],
                                    'L40S': [8, 12, 24, 48],
                                    'L40': [8, 12, 24, 48],
                                    'A40': [8, 12, 24, 48],
                                    'L4': [4, 8, 12, 24]
                                }
                                profiles = available_profiles.get(gpu_model, [8, 12, 24, 48])
                                physical_memory = {'BSE': 96, 'L40S': 48, 'L40': 48, 'A40': 48, 'L4': 24}.get(gpu_model, 48)
                                
                                # Find smallest single profile that fits
                                selected_profile = None
                                for profile in sorted(profiles):
                                    if profile * 0.95 >= gpu_memory_size:
                                        selected_profile = profile
                                        break
                                
                                if selected_profile:
                                    corrected_params["vgpu_profile"] = f"{gpu_model}-{selected_profile}Q"
                                    corrected_params["gpu_count"] = 1
                                else:
                                    # No single profile fits - use passthrough
                                    corrected_params["vgpu_profile"] = None
                                    corrected_params["gpu_count"] = math.ceil(gpu_memory_size / (physical_memory * 0.95))
                                    corrected_params["gpu_model"] = f"{gpu_model} (passthrough)"
                                logger.info(f"Fallback profile: {corrected_params['vgpu_profile']} x{corrected_params.get('gpu_count', 1)}")
                        
                        # ========== Extract RAG Configuration from Query ==========
                        # Detect if this is a RAG workload from query text
                        is_rag_workload = 'RAG' in query or 'Retrieval-Augmented' in query or 'embedding model' in query.lower()
                        
                        if is_rag_workload:
                            import re
                            rag_config = {}
                            rag_breakdown = {"workload_type": "rag"}
                            
                            # Extract embedding model (e.g., "using embedding model nvidia/nvolveqa-embed-large-1B")
                            embedding_match = re.search(r'embedding model\s+([\w\-/\.]+)', query, re.IGNORECASE)
                            if embedding_match:
                                embedding_model = embedding_match.group(1)
                                rag_config["embedding_model"] = embedding_model
                                rag_breakdown["embedding_model"] = embedding_model
                                # Estimate embedding memory based on model name
                                embedding_model_lower = embedding_model.lower()
                                if 'large' in embedding_model_lower or '1b' in embedding_model_lower:
                                    embedding_mem = 2.0
                                elif 'base' in embedding_model_lower or '400m' in embedding_model_lower:
                                    embedding_mem = 0.8
                                elif 'small' in embedding_model_lower or '200m' in embedding_model_lower:
                                    embedding_mem = 0.4
                                else:
                                    embedding_mem = 1.0
                                rag_breakdown["embedding_memory"] = f"{embedding_mem:.2f} GB"
                            
                            # Extract vector dimension (e.g., "1024d vectors")
                            dimension_match = re.search(r'(\d+)d\s*vectors', query, re.IGNORECASE)
                            if dimension_match:
                                vector_dimension = int(dimension_match.group(1))
                                rag_config["vector_dimension"] = vector_dimension
                                rag_breakdown["vector_db_dimension"] = vector_dimension
                            
                            # Extract total vectors (e.g., "10000 total vectors")
                            vectors_match = re.search(r'(\d+)\s*total\s*vectors', query, re.IGNORECASE)
                            if vectors_match:
                                total_vectors = int(vectors_match.group(1))
                                rag_config["total_vectors"] = total_vectors
                                rag_breakdown["vector_db_vectors"] = total_vectors
                            
                            # Calculate vector DB memory if we have both dimension and count
                            if rag_breakdown.get("vector_db_vectors") and rag_breakdown.get("vector_db_dimension"):
                                vector_mem_bytes = rag_breakdown["vector_db_vectors"] * rag_breakdown["vector_db_dimension"] * 4 * 1.5
                                vector_mem_gb = vector_mem_bytes / (1024**3)
                                if vector_mem_gb < 0.1:
                                    rag_breakdown["vector_db_memory"] = f"{vector_mem_gb * 1024:.1f} MB"
                                else:
                                    rag_breakdown["vector_db_memory"] = f"{vector_mem_gb:.2f} GB"
                            
                            # Add RAG config and breakdown to params
                            if rag_config:
                                corrected_params["rag_config"] = rag_config
                            if any(k != "workload_type" for k in rag_breakdown.keys()):
                                corrected_params["rag_breakdown"] = rag_breakdown
                                logger.info(f"Added RAG breakdown to multiturn response: {rag_breakdown}")
                        
                        # Reconstruct description with correct model name and precision
                        final_profile = corrected_params.get("vgpu_profile", "Unknown")
                        final_precision = corrected_params.get("precision", "FP8")
                        final_model_name = model_tag.split('/')[-1] if model_tag and '/' in model_tag else (model_tag or "Unknown")
                        
                        # Use different description format for RAG vs Inference
                        if is_rag_workload and corrected_params.get("rag_config", {}).get("embedding_model"):
                            embedding_short = corrected_params["rag_config"]["embedding_model"].split('/')[-1]
                            corrected_description = f"{gpu_model} with vGPU profile {final_profile} for RAG (Retrieval-Augmented Generation) with {final_model_name} and {embedding_short}"
                        else:
                            corrected_description = f"{gpu_model} with vGPU profile {final_profile} for inference of {final_model_name} ({final_precision})"
                        
                        # Build the final response with corrected field names
                        final_response = {
                            "title": json_data.get("title", "generate_vgpu_config"),
                            "description": corrected_description,
                            "parameters": corrected_params
                        }
                        
                        json_response = json.dumps(final_response, ensure_ascii=False, indent=2)
                        logger.info("Final corrected multiturn response: %s", json_response)
                        yield json_response
                    except Exception as e:
                        logger.error("Error in structured multiturn RAG response: %s", e)
                        error_response = StructuredResponse(
                            description=f"Error generating multiturn RAG response: {str(e)}"
                        )
                        yield json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)
                
                return stream_structured_multiturn_response(), context_to_show

        except ConnectTimeout as e:
            logger.warning("Connection timed out while making a request to the LLM endpoint: %s", e)
            error_response = StructuredResponse(
                description="Connection timed out while making a request to the NIM endpoint. Verify if the NIM server is available."
            )
            return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []

        except requests.exceptions.ConnectionError as e:
            if "HTTPConnectionPool" in str(e):
                logger.error("Connection pool error while connecting to service: %s", e)
                error_response = StructuredResponse(
                    description="Connection error: Failed to connect to service. Please verify if all required NIMs are running and accessible."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []

        except Exception as e:
            logger.warning("Failed to generate response due to exception %s", e)
            print_exc()

            if "[403] Forbidden" in str(e) and "Invalid UAM response" in str(e):
                logger.warning("Authentication or permission error: Verify the validity and permissions of your NVIDIA API key.")
                error_response = StructuredResponse(
                    description="Authentication or permission error: Verify the validity and permissions of your NVIDIA API key."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []
            elif "[404] Not Found" in str(e):
                logger.warning("Please verify the API endpoint and your payload. Ensure that the model name is valid.")
                error_response = StructuredResponse(
                    description="Please verify the API endpoint and your payload. Ensure that the model name is valid."
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []
            else:
                error_response = StructuredResponse(
                    description=f"Failed to generate RAG chain with multi-turn response. {str(e)}"
                )
                return iter([json.dumps(error_response.model_dump(), ensure_ascii=False, indent=2)]), []


    def _conversational_chain(self,
                              query: str,
                              chat_history: List[Dict[str, Any]],
                              reranker_top_k: int,
                              vdb_top_k: int,
                              collection_name: str,
                              **kwargs) -> tuple:
        """
        Execute a conversational RAG chain that returns plain text responses.
        Used for the chat panel where users ask follow-up questions about their config.
        """
        try:
            document_embedder = get_embedding_model(model=kwargs.get("embedding_model"), url=kwargs.get("embedding_endpoint"))
            vs = get_vectorstore(document_embedder, collection_name, kwargs.get("vdb_endpoint"))
            if vs is None:
                raise APIError("Vector store not initialized properly.", 500)

            llm = get_llm(**kwargs)
            ranker = get_ranking_model(model=kwargs.get("reranker_model"), url=kwargs.get("reranker_endpoint"), top_n=reranker_top_k)
            top_k = vdb_top_k if ranker and kwargs.get("enable_reranker") else reranker_top_k
            retriever = vs.as_retriever(search_kwargs={"k": top_k})

            # Build conversation history for the prompt
            conversation_history = []
            user_provided_context = ""
            history_count = int(os.environ.get("CONVERSATION_HISTORY", 15)) * 2 * -1
            chat_history = chat_history[history_count:]
            
            for message in chat_history:
                if message.role == "system":
                    # Capture the system message context from frontend (contains vGPU config details)
                    user_provided_context = message.content
                    logger.info(f"[CONVERSATIONAL] Found system context: {user_provided_context[:200]}...")
                else:
                    conversation_history.append((message.role, message.content))

            # Build system prompt - include user's configuration context if provided
            base_prompt = """You are a helpful AI assistant with expertise in NVIDIA GPUs, vGPU technology, LLMs, and AI infrastructure.

Answer the user's question directly and conversationally. Use the retrieved documents AND the configuration context to support your answers.

Guidelines:
- Be concise but thorough
- Use plain text only, no JSON or structured output
- If asked about model parameters, GPU profiles, or vGPU configurations, explain clearly
- For technical questions, provide specific details when available
- Reference the user's specific configuration when answering
- If you don't know something, say so honestly"""

            # Add user's configuration context if provided
            if user_provided_context:
                system_prompt = f"""{base_prompt}

=== USER'S CURRENT VGPU CONFIGURATION ===
{user_provided_context}

=== ADDITIONAL CONTEXT FROM KNOWLEDGE BASE ===
{{context}}"""
            else:
                system_prompt = f"""{base_prompt}

Context from knowledge base:
{{context}}"""
            
            logger.info(f"[CONVERSATIONAL] System prompt length: {len(system_prompt)}")

            # Retrieve relevant documents
            retriever_query = query
            if kwargs.get("enable_query_rewriting") and conversation_history:
                contextualize_q_system_prompt = (
                    "Given a chat history and the latest user question "
                    "which might reference context in the chat history, "
                    "formulate a standalone question which can be understood "
                    "without the chat history. Do NOT answer the question, "
                    "just reformulate it if needed and otherwise return it as is."
                )
                q_prompt = ChatPromptTemplate.from_messages([
                    ("system", contextualize_q_system_prompt),
                    MessagesPlaceholder("chat_history"),
                    ("human", "{input}"),
                ])
                query_rewriter_llm = get_llm(
                    model=settings.query_rewriter.model_name,
                    llm_endpoint=settings.query_rewriter.server_url,
                    **query_rewriter_llm_config
                )
                # Create chain: prompt -> LLM -> string output
                query_rewriter_chain = q_prompt | query_rewriter_llm | StrOutputParser()
                retriever_query = query_rewriter_chain.invoke(
                    {"input": query, "chat_history": conversation_history},
                    config={'run_name': 'query-rewriter'}
                )
                logger.info(f"Conversational query rewritten to: {retriever_query}")

            # Get documents
            docs_raw = retriever.invoke(retriever_query)
            if ranker and kwargs.get("enable_reranker"):
                docs_raw = ranker.invoke({"query": retriever_query, "documents": docs_raw})
            
            docs = [format_document_with_source(d) for d in docs_raw[:reranker_top_k]]
            context_str = "\n\n".join(docs) if docs else "No relevant documents found."

            # Build the prompt
            messages = [("system", system_prompt)]
            messages.extend(conversation_history)
            messages.append(("user", query))
            
            prompt = ChatPromptTemplate.from_messages(messages)
            chain = prompt | llm | StrOutputParser()

            def stream_conversational_response():
                """Yield plain text chunks - server.py handles SSE formatting."""
                try:
                    for chunk in chain.stream({"context": context_str}):
                        # Just yield the raw text - server.py will format as SSE
                        yield chunk
                except Exception as e:
                    logger.error(f"Error in conversational stream: {e}")
                    yield f"I apologize, but I encountered an error: {str(e)}"

            # Return generator and context for citations
            context_to_show = docs_raw[:reranker_top_k] if docs_raw else []
            return stream_conversational_response(), context_to_show

        except Exception as e:
            logger.error(f"Error in conversational chain: {e}")
            def error_stream():
                yield "I'm sorry, I encountered an error processing your question. Please try again."
            return error_stream(), []


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
        # Since we removed rag_config, always return False to use standard mode
        return False
    
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
        # Since we removed the profile validator, we'll just extract profile patterns
        # and rely on the context to provide valid profiles
        profile_pattern = r'\b([A-Z0-9]+)-(\d+)([Q])\b'  
        found_profiles = set()
        
        for doc in documents:
            matches = re.findall(profile_pattern, doc.page_content)
            for match in matches:
                profile_name = f"{match[0]}-{match[1]}{match[2]}"
                # Basic validation - check if it looks like a real GPU profile
                if match[0] in ["A40", "L40S", "L40", "L4", "RTX6000"]:
                    found_profiles.add(profile_name)
        
        logger.info(f"Found vGPU profiles in context: {found_profiles}")
        return found_profiles
    
    def _extract_gpu_inventory_from_query(self, query: str) -> Dict[str, int]:
        """Extract GPU inventory from query text."""
        inventory = {}
        
        # Pattern to match "2x L40S", "4x L4", etc.
        pattern = r'(\d+)x?\s*(A40|L40S?|L4|RTX\d+)'
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
        """Prepare enhanced context with vGPU profile validation and recommendations."""
        context_parts = []
        
        # Extract GPU inventory from query
        gpu_inventory = self._extract_gpu_inventory_from_query(query)
        
        # Extract workload requirements
        workload_requirements = self._extract_workload_requirements_from_query(query)
        
        if gpu_inventory and workload_requirements:
            # Since we don't have the profile validator, we'll add basic guidance
            context_parts.append("\n## vGPU Configuration Guidelines\n")
            
            # Add GPU inventory information
            context_parts.append(f"\n### Available GPU Inventory")
            for gpu_model, count in gpu_inventory.items():
                context_parts.append(f"- {count}x {gpu_model}")
            
            # Add workload requirements
            context_parts.append(f"\n### Workload Requirements")
            context_parts.append(f"- Concurrent Users: {workload_requirements.get('concurrent_users', 1)}")
            context_parts.append(f"- Model Memory: {workload_requirements.get('model_memory_gb', 0)}GB")
            context_parts.append(f"- Performance Level: {workload_requirements.get('performance_level', 'standard')}")
            
            # Add profile validation rules
            context_parts.append(f"\n### CRITICAL: vGPU Profile Validation Rules")
            context_parts.append("- NVIDIA vGPU profiles ALWAYS end with specific suffixes:")
            context_parts.append("  - 'Q' for time-sliced vGPU (e.g., L40S-8Q, L4-4Q)")
            context_parts.append("- NEVER create profiles with 'A' suffix - this is NOT a valid vGPU profile suffix")
            context_parts.append("- Only use profiles that are explicitly mentioned in the documentation")
        
        # Add valid profiles from context
        if valid_profiles:
            context_parts.append(f"\n### Valid vGPU Profiles Found in Documentation")
            for profile in sorted(valid_profiles):
                context_parts.append(f"- {profile}")
            
            # Add warning about invalid profiles
            context_parts.append(f"\n### WARNING")
            context_parts.append("- Only use the exact profile names listed above")
            context_parts.append("- Do NOT modify profile names or create new ones")
            context_parts.append("- If you see 'L40S-8A' or similar with 'A' suffix, it's INVALID")
        
        return "\n".join(context_parts)
    
    def _extract_workload_requirements_from_query(self, query: str) -> Dict[str, Any]:
        """Extract workload requirements from query."""
        requirements = {
            "concurrent_users": 1,
            "model_memory_gb": 0,

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
        
        
        # Extract performance level
        if "high performance" in query.lower():
            requirements["performance_level"] = "high"
        elif "maximum performance" in query.lower():
            requirements["performance_level"] = "maximum"
        elif "cost" in query.lower() or "efficient" in query.lower():
            requirements["performance_level"] = "standard"
        
        return requirements