"""
vGPU Calculator - A modular tool for optimizing GPU configurations for LLM deployments

Total Memory = Model Weights + KV Cache Memory
KV Cache Memory ≈ (Prompt Size + Response Size) × kv_cache_bytes_per_token × num_concurrent_requests
"""

import logging
import math
from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json
import argparse
import requests
from functools import lru_cache
import re


# ============= Helper Functions =============

@lru_cache(maxsize=100)
def fetch_model_config_from_hf(model_id: str, hf_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Fetch model configuration from HuggingFace Hub.
    
    Args:
        model_id: HuggingFace model ID (e.g., "meta-llama/Llama-3.1-8B-Instruct")
        hf_token: Optional HuggingFace token for authenticated requests
    
    Returns:
        Dictionary with model configuration or None if fetch fails
    """
    try:
        headers = {}
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"
        
        # Try to fetch config.json from HuggingFace
        config_url = f"https://huggingface.co/{model_id}/resolve/main/config.json"
        response = requests.get(config_url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        else:
            logging.warning(f"Failed to fetch config for {model_id}: HTTP {response.status_code}")
            return None
    except Exception as e:
        logging.warning(f"Error fetching model config for {model_id}: {e}")
        return None


def extract_model_params_from_name(model_name: str) -> Optional[float]:
    """
    Extract parameter count from model name (e.g., "Llama-3-8B" -> 8.0).
    
    Args:
        model_name: Model name containing parameter count
    
    Returns:
        Parameter count in billions or None if not found
    """
    # Look for patterns like "8B", "70B", "7B", "180B", etc.
    match = re.search(r'(\d+(?:\.\d+)?)[Bb](?:-|$|\s)', model_name)
    if match:
        return float(match.group(1))
    return None


def estimate_model_spec_from_params(params_billion: float, model_name: str = "") -> Dict[str, Any]:
    """
    Estimate d_model and n_layers based on parameter count using scaling laws.
    
    Args:
        params_billion: Model parameters in billions
        model_name: Optional model name for better heuristics
    
    Returns:
        Dictionary with estimated d_model and n_layers
    """
    # Heuristic based on common LLM architectures
    # Small models (< 10B): typically 32 layers
    # Medium models (10-40B): typically 40-60 layers
    # Large models (> 40B): typically 60-80 layers
    
    if params_billion < 3:
        n_layers = 22
        d_model = int((params_billion * 1e9 / (12 * n_layers)) ** 0.5)
    elif params_billion < 10:
        n_layers = 32
        d_model = int((params_billion * 1e9 / (12 * n_layers)) ** 0.5)
    elif params_billion < 20:
        n_layers = 40
        d_model = int((params_billion * 1e9 / (12 * n_layers)) ** 0.5)
    elif params_billion < 40:
        n_layers = 60
        d_model = int((params_billion * 1e9 / (12 * n_layers)) ** 0.5)
    else:
        n_layers = 80
        d_model = int((params_billion * 1e9 / (12 * n_layers)) ** 0.5)
    
    return {"d_model": d_model, "n_layers": n_layers}


def create_model_spec_from_hf(model_id: str, hf_token: Optional[str] = None) -> Optional['ModelSpec']:
    """
    Create ModelSpec by fetching config from HuggingFace or using estimation.
    
    Args:
        model_id: HuggingFace model ID
        hf_token: Optional HuggingFace token
    
    Returns:
        ModelSpec object or None if creation fails
    """
    # First, try to fetch from HuggingFace
    config = fetch_model_config_from_hf(model_id, hf_token)
    
    # Extract simple name from full ID
    simple_name = model_id.split('/')[-1] if '/' in model_id else model_id
    
    params_billion = None
    d_model = None
    n_layers = None
    
    # Try to get from config
    if config:
        # Try to extract parameter count from config
        if 'num_parameters' in config:
            params_billion = config['num_parameters'] / 1e9
        
        # Try to extract d_model (can be named differently in different models)
        d_model = config.get('hidden_size') or config.get('d_model') or config.get('n_embd')
        
        # Try to extract n_layers (can be named differently)
        n_layers = config.get('num_hidden_layers') or config.get('n_layers') or config.get('num_layers')
    
    # If we don't have params_billion yet, try to extract from name
    if params_billion is None:
        params_billion = extract_model_params_from_name(model_id)
    
    # If we still don't have params, we can't create the spec
    if params_billion is None:
        logging.warning(f"Could not determine parameter count for {model_id}")
        return None
    
    # If we're missing d_model or n_layers, estimate them
    if d_model is None or n_layers is None:
        estimated = estimate_model_spec_from_params(params_billion, model_id)
        d_model = d_model or estimated['d_model']
        n_layers = n_layers or estimated['n_layers']
    
    logging.info(f"Created ModelSpec for {model_id}: {params_billion}B params, d_model={d_model}, n_layers={n_layers}")
    
    return ModelSpec(
        name=simple_name,
        params_billion=params_billion,
        d_model=d_model,
        n_layers=n_layers
    )


# ============= Pydantic Models =============

class GPUSpec(BaseModel):
    """Specification for a vGPU profile"""
    name: str
    fp16_tflops: float
    memory_gb: int
    phy_memory_gb: int
    bandwidth_gbps: float
    
    class Config:
        frozen = True  # Make immutable


class ModelSpec(BaseModel):
    """Specification for an LLM model"""
    name: str
    params_billion: float
    d_model: int
    n_layers: int
    
    class Config:
        frozen = True  # Make immutable


class Configuration(BaseModel):
    """GPU configuration details"""
    gpu_name: str
    num_gpus: int
    total_memory_gb: int
    gpu_memory_gb: int
    max_kv_tokens: int
    concurrent_requests: int
    context_window: int
    vgpu_profile: Optional[str] = None  # Recommended vGPU profile (e.g., "L40S-24Q") or None for passthrough


class AlternativeConfiguration(BaseModel):
    """Alternative GPU configuration from other families"""
    gpu_name: str
    num_gpus: int
    gpu_family: str
    total_memory_gb: int
    gpu_memory_gb: int
    max_kv_tokens: int


class PerformanceMetrics(BaseModel):
    """Performance metrics for a configuration"""
    max_kv_tokens: int
    ttft_seconds: Union[float, str]
    e2e_latency_seconds: Union[float, str]
    throughput_tokens_per_second: Union[float, str]


class AdvancedCalculatorConfig(BaseModel):
    """Advanced configuration options for calculator accuracy tuning.
    
    These are optional parameters that allow fine-tuning of memory calculations
    for different deployment scenarios. Default values are industry best practices.
    """
    model_memory_overhead: float = Field(
        default=1.3,
        ge=1.0,
        le=2.0,
        description="Model memory overhead multiplier (default 1.3 = 30% overhead for framework + hypervisor)"
    )
    hypervisor_reserve_gb: float = Field(
        default=3.0,
        ge=0.0,
        le=10.0,
        description="GPU memory reserved for hypervisor layer in GB (default 3GB)"
    )
    cuda_memory_overhead: float = Field(
        default=1.2,
        ge=1.0,
        le=1.5,
        description="CUDA memory overhead multiplier (default 1.2 = 20% overhead)"
    )
    vcpu_per_gpu: int = Field(
        default=8,
        ge=1,
        le=32,
        description="Number of vCPUs to allocate per GPU (default 8)"
    )
    ram_gb_per_vcpu: int = Field(
        default=8,
        ge=2,
        le=32,
        description="GB of system RAM to allocate per vCPU (default 8GB)"
    )
    
    class Config:
        frozen = False  # Allow modification if needed


class VGPURequest(BaseModel):
    """Input request parameters"""
    num_gpu: int = Field(default=1, ge=1, description="Number of GPUs")
    prompt_size: int = Field(default=1024, ge=1, description="Prompt size in tokens")
    response_size: int = Field(default=250, ge=1, description="Response size in tokens")
    n_concurrent_request: int = Field(default=1, ge=1, description="Number of concurrent requests")
    quantization: str = Field(default="fp16", pattern="^(fp16|fp8|fp4|int8)$", description="Quantization precision (fp16, fp8, fp4, or int8)")
    model_name: str = Field(default="Llama-3-8B", description="Model name")
    vgpu_profile: str = Field(default="A40-12Q", description="vGPU profile")
    advanced_config: Optional[AdvancedCalculatorConfig] = Field(
        default=None,
        description="Advanced configuration options for fine-tuning calculations"
    )
    
    # RAG-specific fields
    workload_type: str = Field(default="inference", pattern="^(inference|rag)$", description="Workload type: inference or rag")
    embedding_model: Optional[str] = Field(default=None, description="Embedding model name for RAG workloads (e.g., nvidia/nvolveqa-embed-large-1B)")
    vector_db_vectors: Optional[int] = Field(default=None, ge=0, description="Number of vectors in vector database")
    vector_db_dimension: Optional[int] = Field(default=None, ge=1, description="Dimension of vectors in vector database")
    reranker_model: Optional[str] = Field(default=None, description="Optional reranker model name")
    
    # Framework selection
    framework: str = Field(default="vllm", description="Inference framework (vllm, trt-llm, tgi, transformers)")


class VGPUResult(BaseModel):
    """Complete result of vGPU calculation"""
    model: str
    original_request: Dict[str, Any]
    resultant_configuration: Configuration
    alternative_configurations: Optional[List[AlternativeConfiguration]] = None
    performance_metrics: PerformanceMetrics
    
    def to_api_response(self) -> Dict[str, Any]:
        """Convert to API response format"""
        return {
            "status": "success",
            "data": {
                "configuration": self.resultant_configuration.dict(),
                "alternatives": [alt.dict() for alt in self.alternative_configurations],
                "performance": {
                    "max_kv_tokens": self.performance_metrics.max_kv_tokens,
                    "ttft": f"{self.performance_metrics.ttft_seconds:.3f}s" 
                            if isinstance(self.performance_metrics.ttft_seconds, (int, float)) 
                            else self.performance_metrics.ttft_seconds,
                    "e2e_latency": f"{self.performance_metrics.e2e_latency_seconds:.2f}s" 
                                   if isinstance(self.performance_metrics.e2e_latency_seconds, (int, float)) 
                                   else self.performance_metrics.e2e_latency_seconds,
                    "throughput": f"{self.performance_metrics.throughput_tokens_per_second:.2f} tok/s" 
                                  if isinstance(self.performance_metrics.throughput_tokens_per_second, (int, float)) 
                                  else self.performance_metrics.throughput_tokens_per_second
                }
            },
            "metadata": {
                "model": self.model,
                "quantization": self.original_request["quantization"],
                "timestamp": datetime.now().isoformat()
            }
        }


# ============= Calculator Class =============

class VGPUCalculator:
    """Modular vGPU Calculator for LLM deployments"""
    
    def __init__(self):
        self.gpu_specs = self._initialize_gpu_specs()
        self.model_specs = self._initialize_model_specs()
        self.embedding_specs = self._initialize_embedding_specs()
        self.reranker_specs = self._initialize_reranker_specs()
        self.BYTES_IN_GB = 1_073_741_824
    
    def _initialize_gpu_specs(self) -> List[GPUSpec]:
        """Initialize available GPU specifications from configuration file"""
        import os
        
        # Try to load from gpu_specs.json
        config_path = os.path.join(os.path.dirname(__file__), 'gpu_specs.json')
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            gpu_specs = []
            physical_gpus = config.get('physical_gpus', {})
            
            # Build GPUSpec objects from configuration
            for profile in config.get('vgpu_profiles', []):
                physical_gpu_family = profile.get('physical_gpu')
                physical_gpu_info = physical_gpus.get(physical_gpu_family, {})
                
                gpu_spec = GPUSpec(
                    name=profile['name'],
                    fp16_tflops=profile['fp16_tflops'],
                    memory_gb=profile['memory_gb'],
                    phy_memory_gb=physical_gpu_info.get('memory_gb', profile['memory_gb']),
                    bandwidth_gbps=profile['bandwidth_gbps']
                )
                gpu_specs.append(gpu_spec)
            
            logging.info(f"Loaded {len(gpu_specs)} GPU profiles from {config_path}")
            return gpu_specs
            
        except Exception as e:
            logging.error(f"CRITICAL: Could not load GPU specs from {config_path}: {e}")
            logging.error("GPU specs configuration file is required for the calculator to function.")
            raise RuntimeError(f"Failed to load GPU specs from {config_path}: {e}")
    
    def _initialize_model_specs(self) -> List[ModelSpec]:
        """Initialize available model specifications from HuggingFace and defaults"""
        # Start with hardcoded fallback specs for common models
        default_specs = [
            ModelSpec(name="Llama-3-8B", params_billion=8, d_model=4096, n_layers=32),
            ModelSpec(name="Llama-3-70B", params_billion=70, d_model=8192, n_layers=80),
            ModelSpec(name="Llama-3.1-8B", params_billion=8, d_model=4096, n_layers=32),
            ModelSpec(name="Llama-3.1-70B", params_billion=70, d_model=8192, n_layers=80),
            ModelSpec(name="Mistral-7B", params_billion=7, d_model=4096, n_layers=32),
            ModelSpec(name="Falcon-7B", params_billion=7, d_model=4544, n_layers=32),
            ModelSpec(name="Falcon-40B", params_billion=40, d_model=8192, n_layers=60),
            ModelSpec(name="Falcon-180B", params_billion=180, d_model=14848, n_layers=80),
            ModelSpec(name="Qwen-14B", params_billion=14, d_model=5120, n_layers=40),
            # NVIDIA Nemotron model - 30B parameters
            ModelSpec(name="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8", params_billion=30, d_model=8192, n_layers=48),
        ]
        
        # Try to dynamically fetch popular models from HuggingFace
        try:
            # Import here to avoid circular dependency
            from .apply_configuration import fetch_huggingface_models
            
            hf_models = fetch_huggingface_models()
            logging.info(f"Fetched {len(hf_models)} models from HuggingFace")
            
            # Create specs for fetched models (if not already in defaults)
            default_names = {spec.name for spec in default_specs}
            
            for model_id in hf_models[:15]:  # Limit to top 15 models
                simple_name = model_id.split('/')[-1]
                if simple_name not in default_names:
                    spec = create_model_spec_from_hf(model_id)
                    if spec:
                        default_specs.append(spec)
                        default_names.add(simple_name)
            
            logging.info(f"Initialized {len(default_specs)} model specifications")
        except Exception as e:
            logging.warning(f"Could not fetch dynamic models: {e}, using defaults only")
        
        return default_specs
    
    def _initialize_embedding_specs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize embedding model specifications"""
        return {
            "nvidia/nvolveqa-embed-large-1B": {
                "params_billion": 1.0,
                "dimension": 1024,
                "description": "NVIDIA NV-Embed-QA Large 1B"
            },
            "nvidia/NV-Embed-v2": {
                "params_billion": 7.9,
                "dimension": 4096,
                "description": "NVIDIA NV-Embed-v2 (7.9B)"
            },
            "BAAI/bge-large-en-v1.5": {
                "params_billion": 0.335,
                "dimension": 1024,
                "description": "BGE Large English v1.5"
            },
            "sentence-transformers/all-MiniLM-L6-v2": {
                "params_billion": 0.022,
                "dimension": 384,
                "description": "All-MiniLM-L6-v2 (small, fast)"
            },
            "intfloat/e5-large-v2": {
                "params_billion": 0.335,
                "dimension": 1024,
                "description": "E5 Large v2"
            },
            "thenlper/gte-large": {
                "params_billion": 0.335,
                "dimension": 1024,
                "description": "GTE Large"
            },
            "intfloat/e5-mistral-7b-instruct": {
                "params_billion": 7.1,
                "dimension": 4096,
                "description": "E5 Mistral 7B Instruct"
            }
        }
    
    def _initialize_reranker_specs(self) -> Dict[str, Dict[str, Any]]:
        """Initialize reranker model specifications"""
        return {
            "BAAI/bge-reranker-large": {
                "params_billion": 0.335,
                "description": "BGE Reranker Large"
            },
            "BAAI/bge-reranker-base": {
                "params_billion": 0.278,
                "description": "BGE Reranker Base"
            },
            "cross-encoder/ms-marco-MiniLM-L-12-v2": {
                "params_billion": 0.033,
                "description": "MS MARCO MiniLM L-12 v2"
            },
            "BAAI/bge-reranker-v2-m3": {
                "params_billion": 0.568,
                "description": "BGE Reranker v2-m3"
            }
        }
    
    def _get_framework_overhead(self, framework: str) -> float:
        """Get framework-specific overhead multiplier from configuration"""
        config = self._load_gpu_config()
        framework_overheads = config.get('framework_overheads', {})
        
        framework_lower = framework.lower()
        if framework_lower in framework_overheads:
            return framework_overheads[framework_lower].get('multiplier', 1.3)
        
        # If framework not found in config, use default 1.3x
        logging.warning(f"Framework '{framework}' not found in configuration, using default overhead of 1.3x")
        return 1.3
    
    def _calc_embedding_memory(self, embedding_model: str, quantization: str) -> float:
        """Calculate memory for embedding model"""
        if not embedding_model:
            return 0.0
        
        # Map quantization to bytes per param
        bytes_per_param_map = {
            "fp16": 2.0,
            "fp8": 1.0,
            "fp4": 0.5,
            "int8": 1.0
        }
        bytes_per_param = bytes_per_param_map.get(quantization.lower(), 2.0)
        
        # Find embedding model specs
        if embedding_model in self.embedding_specs:
            params_billion = self.embedding_specs[embedding_model]["params_billion"]
            memory_gb = params_billion * bytes_per_param
            logging.info(f"Embedding model '{embedding_model}': {params_billion}B params = {memory_gb:.2f} GB")
            return memory_gb
        else:
            # Try to extract parameter count from model name
            params = extract_model_params_from_name(embedding_model)
            if params:
                memory_gb = params * bytes_per_param
                logging.warning(f"Embedding model '{embedding_model}' not in database, estimated {params}B params = {memory_gb:.2f} GB")
                return memory_gb
            else:
                # Default to 1B parameters if unknown
                logging.warning(f"Unknown embedding model '{embedding_model}', assuming 1B params")
                return 1.0 * bytes_per_param
    
    def _calc_reranker_memory(self, reranker_model: str, quantization: str) -> float:
        """Calculate memory for reranker model"""
        if not reranker_model:
            return 0.0
        
        bytes_per_param_map = {
            "fp16": 2.0,
            "fp8": 1.0,
            "fp4": 0.5,
            "int8": 1.0
        }
        bytes_per_param = bytes_per_param_map.get(quantization.lower(), 2.0)
        
        if reranker_model in self.reranker_specs:
            params_billion = self.reranker_specs[reranker_model]["params_billion"]
            memory_gb = params_billion * bytes_per_param
            logging.info(f"Reranker model '{reranker_model}': {params_billion}B params = {memory_gb:.2f} GB")
            return memory_gb
        else:
            logging.warning(f"Unknown reranker model '{reranker_model}', assuming 0.3B params")
            return 0.3 * bytes_per_param
    
    def _calc_vector_db_memory(self, num_vectors: int, dimension: int, use_index: bool = True) -> float:
        """Calculate memory for vector database index"""
        if not num_vectors or not dimension:
            return 0.0
        
        # Vector storage: num_vectors × dimension × 4 bytes (fp32)
        base_memory_gb = (num_vectors * dimension * 4) / self.BYTES_IN_GB
        
        # Add index overhead (HNSW typically adds ~25% overhead)
        index_overhead = 1.25 if use_index else 1.0
        total_memory_gb = base_memory_gb * index_overhead
        
        logging.info(f"Vector DB: {num_vectors:,} vectors × {dimension} dims = {total_memory_gb:.3f} GB (with {'HNSW' if use_index else 'flat'} index)")
        return total_memory_gb
    
    def add_custom_gpu(self, gpu_spec: GPUSpec) -> None:
        """Add a custom GPU specification"""
        self.gpu_specs.append(gpu_spec)
    
    def add_custom_model(self, model_spec: ModelSpec) -> None:
        """Add a custom model specification"""
        self.model_specs.append(model_spec)
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names"""
        return [model.name for model in self.model_specs]
    
    def get_available_gpus(self) -> List[str]:
        """Get list of available GPU profiles"""
        return [gpu.name for gpu in self.gpu_specs]
    
    def _find_model(self, model_name: str) -> Optional[ModelSpec]:
        """Find model specification by name, fetching from HuggingFace if not found"""
        # First, try exact match in existing specs
        for model in self.model_specs:
            if model.name == model_name or model.name.lower() == model_name.lower():
                return model
        
        # Try partial match for common patterns
        lower_name = model_name.lower()
        for model in self.model_specs:
            lower_model_name = model.name.lower()
            # Check if model name appears in query OR query appears in model name
            # e.g., "nemotron-30b-fp8" in "nvidia/nvidia-nemotron-3-nano-30b-a3b-fp8" OR vice versa
            if lower_model_name in lower_name or lower_name in lower_model_name:
                logging.info(f"Partial match found: '{model.name}' matches '{model_name}'")
                return model
            # Check for Nemotron patterns specifically (handles "nemotron-30b-fp8" -> "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-FP8")
            if 'nemotron' in lower_name and 'nemotron' in lower_model_name:
                logging.info(f"Nemotron match found: '{model.name}' for '{model_name}'")
                return model
        
        # If not found, try to create it dynamically from HuggingFace
        logging.info(f"Model '{model_name}' not in cache, attempting to fetch from HuggingFace")
        
        # Try with the name as-is
        spec = create_model_spec_from_hf(model_name)
        if spec:
            self.model_specs.append(spec)
            logging.info(f"Successfully added model '{model_name}' from HuggingFace")
            return spec
        
        # Try to find in HuggingFace models list
        try:
            from .apply_configuration import MODEL_TAGS, model_extractor
            extracted_model = model_extractor.extract(model_name)
            if extracted_model and extracted_model != model_name:
                spec = create_model_spec_from_hf(extracted_model)
                if spec:
                    self.model_specs.append(spec)
                    logging.info(f"Successfully added model '{extracted_model}' (matched from '{model_name}')")
                    return spec
        except Exception as e:
            logging.warning(f"Could not extract model from '{model_name}': {e}")
        
        # Final fallback: Try to create a model spec from the name using parameter extraction
        # This handles cases like "Llama-3-70B-Custom" where we can extract "70B"
        params_billion = extract_model_params_from_name(model_name)
        if params_billion:
            logging.info(f"Creating dynamic model spec for '{model_name}' with {params_billion}B params")
            estimated = estimate_model_spec_from_params(params_billion, model_name)
            fallback_spec = ModelSpec(
                name=model_name,
                params_billion=params_billion,
                n_layers=estimated.get('n_layers', 32),
                d_model=estimated.get('d_model', 4096),
                max_context_length=32768
            )
            self.model_specs.append(fallback_spec)
            return fallback_spec
        
        # Absolute last resort: Use a default 8B model spec
        logging.warning(f"Could not determine model specs for '{model_name}', using default 8B model")
        default_spec = ModelSpec(
            name=model_name,
            params_billion=8.0,
            n_layers=32,
            d_model=4096,
            max_context_length=32768
        )
        return default_spec
    
    def _find_gpu(self, gpu_name: str) -> Optional[GPUSpec]:
        """Find GPU specification by name"""
        for gpu in self.gpu_specs:
            if gpu.name == gpu_name:
                return gpu
        return None
    
    def _load_gpu_config(self) -> Dict[str, Any]:
        """Load GPU configuration from JSON file (cached)"""
        if not hasattr(self, '_gpu_config_cache'):
            import os
            config_path = os.path.join(os.path.dirname(__file__), 'gpu_specs.json')
            try:
                with open(config_path, 'r') as f:
                    self._gpu_config_cache = json.load(f)
            except Exception as e:
                logging.warning(f"Could not load GPU config: {e}")
                self._gpu_config_cache = {}
        return self._gpu_config_cache
    
    def _get_physical_gpu_memory(self, gpu_family: str) -> int:
        """Get physical GPU memory for a GPU family from configuration"""
        config = self._load_gpu_config()
        physical_gpus = config.get('physical_gpus', {})
        
        if gpu_family in physical_gpus:
            return physical_gpus[gpu_family].get('memory_gb', 48)
        
        # GPU family not found in configuration
        logging.error(f"GPU family '{gpu_family}' not found in configuration!")
        logging.error(f"Available GPU families: {list(physical_gpus.keys())}")
        raise ValueError(f"GPU family '{gpu_family}' is not configured. Please add it to gpu_specs.json")
    
    def _get_available_profiles(self, gpu_family: str) -> List[int]:
        """Get available vGPU profile sizes for a GPU family from configuration"""
        config = self._load_gpu_config()
        physical_gpus = config.get('physical_gpus', {})
        
        if gpu_family in physical_gpus:
            profiles = physical_gpus[gpu_family].get('profiles', [])
            if not profiles:
                logging.error(f"No profiles configured for GPU family '{gpu_family}'")
                raise ValueError(f"GPU family '{gpu_family}' has no profiles configured in gpu_specs.json")
            return profiles
        
        # GPU family not found in configuration
        logging.error(f"GPU family '{gpu_family}' not found in configuration!")
        logging.error(f"Available GPU families: {list(physical_gpus.keys())}")
        raise ValueError(f"GPU family '{gpu_family}' is not configured. Please add it to gpu_specs.json")
    
    def _recommend_vgpu_profile(self, total_memory_needed: float, gpu_family: str, 
                                safety_buffer_gb: float = 0.0) -> Dict[str, Any]:
        """
        Recommend vGPU profile based on total memory needed with 5% headroom reserve.
        
        CRITICAL RULE: Use vGPU profiles ONLY when workload fits in a SINGLE profile.
        If workload exceeds max single profile capacity, use GPU passthrough.
        
        Logic:
        1. If workload fits in single profile (workload ≤ profile × 0.95): use smallest fitting profile
        2. If workload > max_profile × 0.95: recommend passthrough with N GPUs
        """
        import math
        physical_memory = self._get_physical_gpu_memory(gpu_family)
        available_profiles = self._get_available_profiles(gpu_family)
        
        # Get max profile for this GPU family
        max_profile = max(available_profiles) if available_profiles else physical_memory
        max_profile_usable = max_profile * 0.95  # 95% usable capacity (5% reserved)
        usable_physical = physical_memory * 0.95  # 95% usable physical GPU memory
        
        # Try to find smallest single profile that fits
        recommended_profile = None
        for profile_size in sorted(available_profiles):
            usable_capacity = profile_size * 0.95  # 5% headroom reserved
            if usable_capacity >= total_memory_needed:
                recommended_profile = profile_size
                break
        
        # If single profile found, use it
        if recommended_profile is not None:
            usable_capacity = recommended_profile * 0.95
            return {
                "type": "vgpu",
                "profile": f"{gpu_family}-{recommended_profile}Q",
                "gpu_count": 1,
                "profile_memory_gb": recommended_profile,
                "total_memory_available": recommended_profile,
                "recommendation": f"1x {gpu_family}-{recommended_profile}Q vGPU profile",
                "reason": f"Workload needs {total_memory_needed:.1f}GB, selected profile: {recommended_profile}GB (usable: {usable_capacity:.1f}GB with 5% reserved for system overhead)",
                "warning": None
            }
        
        # No single profile fits - use GPU passthrough
        # Calculate GPUs needed based on physical GPU memory
        num_gpus_needed = math.ceil(total_memory_needed / usable_physical)
        return {
            "type": "passthrough",
            "profile": None,
            "gpu_count": num_gpus_needed,
            "profile_memory_gb": physical_memory,
            "total_memory_available": physical_memory * num_gpus_needed,
            "recommendation": f"{num_gpus_needed}x {gpu_family} GPU passthrough",
            "reason": f"Workload requires {total_memory_needed:.1f}GB which exceeds max vGPU profile capacity ({max_profile_usable:.1f}GB usable from {max_profile}GB profile). GPU passthrough with {num_gpus_needed} GPUs provides {physical_memory * num_gpus_needed}GB total capacity."
        }


    def _calc_kv_cache_size_per_token(self, n_layers: int, d_model: int, quantization: str) -> float:
        """Calculate KV cache size per token in GB"""
        if n_layers is None or d_model is None:
            # Return a reasonable default if model architecture details are missing
            logging.warning(f"Missing model architecture details (n_layers={n_layers}, d_model={d_model}), using defaults")
            n_layers = n_layers or 32
            d_model = d_model or 4096
        
        # Map quantization to element size in bytes
        elem_size_map = {
            "fp16": 2.0,
            "fp8": 1.0,
            "fp4": 0.5,
            "int8": 1.0
        }
        elem_size = elem_size_map.get(quantization.lower(), 2.0)
        
        # Formula: 2 (for K and V) × elem_size × n_layers × d_model / bytes_in_GB
        return 2 * elem_size * n_layers * d_model / self.BYTES_IN_GB
    
    def _calc_memory_footprint(self, model: ModelSpec, concurrent: int, context: int, 
                               bytes_per_param: int, memory_overhead: float = 1.3) -> float:
        """Calculate total memory footprint in GB
        
        Args:
            model: Model specification
            concurrent: Number of concurrent requests
            context: Context window size
            bytes_per_param: Bytes per parameter (2 for FP16, 1 for INT8)
            memory_overhead: Overhead multiplier (default 1.3 = 30% overhead)
        """
        return math.ceil(model.params_billion * bytes_per_param * memory_overhead) 
    
    def _calc_total_memory_with_kv_cache(self, model_memory: float, model: ModelSpec, context_window: int,
                                         concurrent_requests: int, bytes_per_param: int,
                                         quantization: str) -> float:
        """Calculate total memory including model weights and KV cache"""
        # Model weights memory        
        # KV cache memory for the context window
        kv_size_per_token = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, quantization)
        kv_cache_memory = kv_size_per_token * context_window * concurrent_requests

        return math.ceil(model_memory + kv_cache_memory) # accounting for the 40% overhead from 20% and 20% HV layer
    
    def _calc_kv_cache_tokens(self, num_gpu: int, gpu_mem: int, params_billion: float, 
                              kv_size: float, bytes_per_param: int, 
                              hypervisor_reserve_gb: float = 3.0,
                              cuda_overhead: float = 1.2) -> float:
        """Calculate maximum KV cache tokens
        
        Args:
            num_gpu: Number of GPUs
            gpu_mem: GPU memory in GB
            params_billion: Model parameters in billions
            kv_size: KV cache size per token in GB
            bytes_per_param: Bytes per parameter
            hypervisor_reserve_gb: GPU memory reserved for hypervisor (default 3GB)
            cuda_overhead: CUDA memory overhead multiplier (default 1.2 = 20%)
        """
        if num_gpu * gpu_mem < hypervisor_reserve_gb:
            raise Exception("Not enough memory to run the model")
        if kv_size is None or kv_size <= 0:
            logging.warning(f"Invalid kv_size: {kv_size}, returning 0 tokens")
            return 0
        available = ((num_gpu * gpu_mem) - hypervisor_reserve_gb) - math.ceil((params_billion * bytes_per_param) * cuda_overhead)
        return max(available / kv_size, 0)
    
    def _effective_flops(self, gpu: GPUSpec) -> float:
        """Calculate effective FLOPS based on memory fraction"""
        return gpu.fp16_tflops * (gpu.memory_gb / gpu.phy_memory_gb)
    
    def _effective_bandwidth(self, gpu: GPUSpec) -> float:
        """Calculate effective bandwidth based on memory fraction"""
        return gpu.bandwidth_gbps * (gpu.memory_gb / gpu.phy_memory_gb)
    
    def _calc_prefill_time(self, params_billion: float, gpu: GPUSpec, 
                           bytes_per_param: int, num_gpu: int) -> float:
        """Calculate prefill time in seconds"""
        flops_eff = self._effective_flops(gpu)
        return (params_billion * bytes_per_param) / flops_eff / num_gpu
    
    def _calc_tpot(self, params_billion: float, gpu: GPUSpec, 
                   bytes_per_param: int, num_gpu: int) -> float:
        """Calculate time per output token in milliseconds"""
        bw_eff = self._effective_bandwidth(gpu)
        return (params_billion * bytes_per_param) / bw_eff / num_gpu * 1000
    
    def _calc_e2e(self, prefill: float, tpot: float, in_size: int, out_size: int) -> float:
        """Calculate end-to-end latency in seconds"""
        return (in_size * prefill + out_size * tpot) / 1000
    
    def _get_gpu_family_and_size(self, gpu_name: str) -> Tuple[str, int]:
        """Extract GPU family and size from name"""
        parts = gpu_name.split('-')
        return parts[0], int(parts[1].replace('Q', ''))
    
    def _find_all_viable_configurations(self, model: ModelSpec, initial_gpu: GPUSpec, 
                                        concurrent: int, context: int, quantization: str,
                                        max_alternatives: int = 3) -> List[Dict[str, Any]]:
        """Find all viable configurations within the same GPU family"""
        gpu_family, _ = self._get_gpu_family_and_size(initial_gpu.name)
        family_gpus = [g for g in self.gpu_specs if g.name.startswith(gpu_family)]
        
        max_gpus = 8
        bytes_per_param = 2 if quantization == "fp16" else 1
        
        kv_size = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, quantization)
        required_kv_tokens = context * concurrent
        
        viable_configs = []
        
        for gpu in family_gpus:
            for n_gpu in range(1, math.ceil((initial_gpu.memory_gb * 1.2)/gpu.memory_gb) + 1):
                max_kv = self._calc_kv_cache_tokens(n_gpu, gpu.memory_gb, model.params_billion, 
                                                     kv_size, bytes_per_param)
                if max_kv >= required_kv_tokens:
                    config = {
                        "gpu": gpu,
                        "num_gpu": n_gpu,
                        "concurrent": concurrent,
                        "context": context,
                        "max_kv": max_kv,
                        "total_memory": gpu.memory_gb * n_gpu,
                        "cost_score": gpu.memory_gb * n_gpu + n_gpu * 10
                    }
                    viable_configs.append(config)
        
        viable_configs.sort(key=lambda x: x["cost_score"])
        return viable_configs[:max_alternatives + 1]
    
    def _find_cross_family_alternatives(self, model: ModelSpec, concurrent: int, context: int, 
                                        quantization: str, exclude_family: str = None, 
                                        max_alternatives: int = 3) -> List[Dict[str, Any]]:
        """Find viable configurations across all GPU families"""
        max_gpus = 8
        bytes_per_param = 2 if quantization == "fp16" else 1
        
        kv_size = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, quantization)
        required_kv_tokens = context * concurrent
        
        viable_configs = []
        
        for gpu in self.gpu_specs:
            if exclude_family and gpu.name.startswith(exclude_family):
                continue
                
            for n_gpu in range(1, max_gpus + 1):
                max_kv = self._calc_kv_cache_tokens(n_gpu, gpu.memory_gb, model.params_billion, 
                                                     kv_size, bytes_per_param)
                if max_kv >= required_kv_tokens:
                    gpu_family = gpu.name.split('-')[0]
                    config = {
                        "gpu": gpu,
                        "num_gpu": n_gpu,
                        "family": gpu_family,
                        "concurrent": concurrent,
                        "context": context,
                        "max_kv": max_kv,
                        "total_memory": gpu.memory_gb * n_gpu,
                        "cost_score": gpu.memory_gb * n_gpu + n_gpu * 10
                    }
                    viable_configs.append(config)
        
        viable_configs.sort(key=lambda x: x["cost_score"])
        return viable_configs[:max_alternatives]
    
    def calculate(self, request: VGPURequest) -> VGPUResult:
        """
        Main calculation method - SIMPLIFIED LOGIC
        
        Steps:
        1. Calculate model memory (base)
        2. Calculate KV cache memory (base)
        3. Sum and apply overhead ONCE
        4. Add hypervisor reserve
        5. Recommend vGPU profile or passthrough
        """
        # Get advanced config or use defaults
        config = request.advanced_config if request.advanced_config else AdvancedCalculatorConfig()
        
        # Find model
        logging.info(f"Looking up model: '{request.model_name}'")
        model = self._find_model(request.model_name)
        if not model:
            raise ValueError(f"Model '{request.model_name}' not found. Available: {self.get_available_models()}")
        logging.info(f"Found model: '{model.name}' with {model.params_billion}B params")
        
        # Get GPU family from vgpu_profile
        gpu = self._find_gpu(request.vgpu_profile)
        if not gpu:
            raise ValueError(f"GPU '{request.vgpu_profile}' not found. Available: {self.get_available_gpus()}")
        
        gpu_family, _ = self._get_gpu_family_and_size(gpu.name)
        
        # Determine bytes per parameter based on precision
        bytes_per_param_map = {
            "fp16": 2.0,
            "fp8": 1.0,
            "fp4": 0.5,
            "int8": 1.0
        }
        bytes_per_param = bytes_per_param_map.get(request.quantization.lower(), 2.0)
        
        context_window = request.prompt_size + request.response_size
        
        logging.info("="*60)
        logging.info(f"{'RAG' if request.workload_type == 'rag' else 'INFERENCE'} VGPU CALCULATION ({request.framework.upper()})")
        logging.info("="*60)
        
        # ========== STEP 1: Calculate Main Model Memory (BASE) ==========
        model_memory_base = model.params_billion * bytes_per_param
        logging.info(f"Step 1 - Main Model Memory (base): {model.params_billion}B × {bytes_per_param} bytes/param = {model_memory_base:.2f} GB")
        
        # ========== STEP 2: Calculate Main KV Cache Memory (BASE) ==========
        kv_size_per_token = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, request.quantization)
        kv_cache_memory_base = kv_size_per_token * context_window * request.n_concurrent_request
        
        logging.info(f"Step 2 - Main KV Cache Memory (base):")
        logging.info(f"  - KV size per token: {kv_size_per_token:.6f} GB/token")
        logging.info(f"  - Context window: {context_window} tokens")
        logging.info(f"  - Concurrent requests: {request.n_concurrent_request}")
        logging.info(f"  - Total KV cache: {kv_size_per_token:.6f} × {context_window} × {request.n_concurrent_request} = {kv_cache_memory_base:.2f} GB")
        
        # ========== STEP 3: Calculate RAG Components (if applicable) ==========
        rag_memory_total = 0.0
        embedding_memory = 0.0
        vector_db_memory = 0.0
        reranker_memory = 0.0
        
        if request.workload_type == "rag":
            logging.info(f"Step 3 - RAG Components:")
            
            # Embedding model
            embedding_memory = self._calc_embedding_memory(request.embedding_model, request.quantization) if request.embedding_model else 0.0
            if embedding_memory > 0:
                logging.info(f"  - Embedding model: {embedding_memory:.2f} GB")
            
            # Vector database
            vector_db_memory = self._calc_vector_db_memory(
                request.vector_db_vectors, 
                request.vector_db_dimension
            ) if request.vector_db_vectors and request.vector_db_dimension else 0.0
            if vector_db_memory > 0:
                logging.info(f"  - Vector DB index: {vector_db_memory:.3f} GB")
            
            # Reranker model (optional)
            reranker_memory = self._calc_reranker_memory(request.reranker_model, request.quantization) if request.reranker_model else 0.0
            if reranker_memory > 0:
                logging.info(f"  - Reranker model: {reranker_memory:.2f} GB")
            
            rag_memory_total = embedding_memory + vector_db_memory + reranker_memory
            logging.info(f"  - RAG Total: {rag_memory_total:.2f} GB")
        else:
            logging.info(f"Step 3 - RAG Components: None (inference-only workload)")
        
        # ========== STEP 4: Apply Workload-Specific Overhead ==========
        total_base_memory = model_memory_base + kv_cache_memory_base + rag_memory_total
        
        # Get overhead values from configuration
        gpu_config = self._load_gpu_config()
        workload_overheads = gpu_config.get('workload_overheads', {})
        
        # Dynamic overhead based on actual workload type and components
        if request.workload_type == "rag":
            # Get RAG overhead settings from config
            rag_config = workload_overheads.get('rag', {})
            base_overhead = rag_config.get('base_overhead', 0.05)
            embedding_overhead = rag_config.get('embedding_overhead', 0.03)
            vector_db_overhead = rag_config.get('vector_db_overhead', 0.05)
            reranker_overhead = rag_config.get('reranker_overhead', 0.02)
            
            # Start with base RAG overhead (e.g., 1.05 = 5%)
            workload_overhead = 1.0 + base_overhead
            
            # Add overhead for each component present
            overhead_components = []
            if embedding_memory > 0:
                workload_overhead += embedding_overhead
                overhead_components.append(f"embedding (+{embedding_overhead*100:.0f}%)")
            if vector_db_memory > 0:
                workload_overhead += vector_db_overhead
                overhead_components.append(f"vector DB (+{vector_db_overhead*100:.0f}%)")
            if reranker_memory > 0:
                workload_overhead += reranker_overhead
                overhead_components.append(f"reranker (+{reranker_overhead*100:.0f}%)")
            
            logging.info(f"  - RAG components active: {', '.join(overhead_components) if overhead_components else 'none'}")
        else:
            # Pure inference workloads - get from config
            inference_config = workload_overheads.get('inference', {})
            workload_overhead = inference_config.get('multiplier', 1.10)
        
        framework_overhead = self._get_framework_overhead(request.framework)
        total_overhead = workload_overhead * framework_overhead
        total_memory_with_overhead = total_base_memory * total_overhead
        
        logging.info(f"Step 4 - Apply Overhead ({request.workload_type.upper()} + {request.framework}):")
        logging.info(f"  - Base memory: {total_base_memory:.2f} GB")
        logging.info(f"  - Workload overhead: {workload_overhead:.3f}x ({'RAG' if request.workload_type == 'rag' else 'Inference'})")
        logging.info(f"  - Framework overhead: {framework_overhead}x ({request.framework})")
        logging.info(f"  - Combined overhead: {total_overhead:.3f}x")
        logging.info(f"  - Memory with overhead: {total_memory_with_overhead:.2f} GB")
        
        # ========== STEP 5: Determine Memory for Profile Selection ==========
        # For profile selection, use BASE memory without overhead multipliers
        # The 5% headroom in profile selection already accounts for framework/system overhead
        # This prevents over-provisioning (e.g., 18GB base shouldn't need 48Q profile)
        # IMPORTANT: Round UP to match what users see in gpu_memory_size
        memory_for_profile_selection = math.ceil(total_base_memory)
        
        # Keep full calculation for reporting purposes (production vGPU estimate)
        total_memory_needed = total_memory_with_overhead + config.hypervisor_reserve_gb
        
        logging.info(f"Step 5 - Memory Calculation:")
        logging.info(f"  - Base memory (model + KV + RAG): {total_base_memory:.2f} GB")
        logging.info(f"  - Rounded for profile selection: {memory_for_profile_selection} GB (5% headroom applied in profile)")
        logging.info(f"  - With overhead multipliers: {total_memory_with_overhead:.2f} GB (reference)")
        logging.info(f"  - Total with hypervisor: {total_memory_needed:.2f} GB (production vGPU estimate)")
        
        # ========== STEP 6: Recommend vGPU Profile ==========
        recommendation = self._recommend_vgpu_profile(memory_for_profile_selection, gpu_family)
        
        logging.info(f"Step 6 - Recommendation:")
        logging.info(f"  - Type: {recommendation['type']}")
        logging.info(f"  - Recommendation: {recommendation['recommendation']}")
        logging.info(f"  - Reason: {recommendation['reason']}")
        if recommendation.get('warning'):
            logging.warning(f"  - Warning: {recommendation['warning']}")
        
        # ========== Calculate Max KV Tokens ==========
        # Available memory = Profile memory - hypervisor reserve - model memory (with overhead)
        if recommendation['type'] == 'passthrough':
            available_memory = (recommendation['total_memory_available'] - 
                              config.hypervisor_reserve_gb - 
                              model_memory_base * config.model_memory_overhead)
            num_gpus = recommendation['gpu_count']
        else:
            available_memory = (recommendation['profile_memory_gb'] - 
                              config.hypervisor_reserve_gb - 
                              model_memory_base * config.model_memory_overhead)
            num_gpus = recommendation['gpu_count']
        
        # Max KV tokens = available memory / (kv_size_per_token * overhead)
        kv_size_with_overhead = kv_size_per_token * config.model_memory_overhead
        max_kv_tokens = max(0, available_memory / kv_size_with_overhead) if kv_size_with_overhead > 0 else 0
        
        logging.info(f"Max KV Tokens Calculation:")
        logging.info(f"  - Available memory: {available_memory:.2f} GB")
        logging.info(f"  - KV size with overhead: {kv_size_with_overhead:.6f} GB/token")
        logging.info(f"  - Max KV tokens: {int(max_kv_tokens):,}")
        logging.info("="*60)
        
        # ========== Create Configuration ==========
        # IMPORTANT: total_memory_gb = calculated memory REQUIREMENT (not profile size)
        # gpu_memory_gb = profile memory AVAILABLE
        resultant_configuration = Configuration(
            gpu_name=recommendation['profile'] if recommendation['type'] == 'vgpu' else f"{gpu_family} (passthrough)",
            num_gpus=num_gpus,
            total_memory_gb=int(math.ceil(total_base_memory)),  # ACTUAL model + KV + RAG memory (base, no overhead)
            gpu_memory_gb=recommendation['total_memory_available'],  # Profile memory size
            max_kv_tokens=int(max_kv_tokens),
            concurrent_requests=request.n_concurrent_request,
            context_window=context_window,
            vgpu_profile=recommendation['profile']  # "L40S-24Q" for vGPU, None for passthrough
        )
        
        logging.info(f"Configuration Created:")
        logging.info(f"  - Calculated memory requirement (base): {math.ceil(total_base_memory)} GB")
        logging.info(f"  - Total memory needed (with overhead + hypervisor): {math.ceil(total_memory_needed)} GB")
        logging.info(f"  - Recommended profile memory: {recommendation['total_memory_available']} GB")
        
        # ========== Calculate Performance Metrics ==========
        # Use the recommended GPU for performance calculations
        if recommendation['type'] == 'vgpu':
            perf_gpu = self._find_gpu(recommendation['profile'])
        else:
            # For passthrough, use the base GPU from the family
            perf_gpu = gpu
        
        pre = self._calc_prefill_time(model.params_billion, perf_gpu, bytes_per_param, num_gpus)
        tpot = self._calc_tpot(model.params_billion, perf_gpu, bytes_per_param, num_gpus)
        
        if any(isinstance(x, str) for x in (pre, tpot)):
            ttft = e2e = throughput = "OOM"
        else:
            ttft = pre + tpot / 1000
            e2e = self._calc_e2e(pre, tpot, request.prompt_size, request.response_size)
            throughput = request.response_size / e2e if e2e > 0 else "OOM"
        
        performance_metrics = PerformanceMetrics(
            max_kv_tokens=int(max_kv_tokens),
            ttft_seconds=ttft if isinstance(ttft, (int, float)) else ttft,
            e2e_latency_seconds=e2e if isinstance(e2e, (int, float)) else e2e,
            throughput_tokens_per_second=throughput if isinstance(throughput, (int, float)) else throughput
        )
        
        # ========== Create RAG Breakdown (only for RAG workloads) ==========
        rag_breakdown = None
        if request.workload_type == "rag":
            rag_breakdown = {
                "workload_type": "rag",
            }
            
            # Embedding model details
            if embedding_memory > 0 and request.embedding_model:
                rag_breakdown["embedding_model"] = request.embedding_model
                rag_breakdown["embedding_memory"] = f"{embedding_memory:.2f} GB"
            
            # Vector DB details - always include if vectors are specified
            if request.vector_db_vectors and request.vector_db_dimension:
                rag_breakdown["vector_db_vectors"] = request.vector_db_vectors
                rag_breakdown["vector_db_dimension"] = request.vector_db_dimension
                # Calculate and show memory even if very small
                if vector_db_memory > 0:
                    # Format appropriately based on size
                    if vector_db_memory < 0.1:
                        rag_breakdown["vector_db_memory"] = f"{vector_db_memory * 1024:.1f} MB"
                    else:
                        rag_breakdown["vector_db_memory"] = f"{vector_db_memory:.2f} GB"
                else:
                    rag_breakdown["vector_db_memory"] = "< 1 MB"
            
            # Reranker details
            if reranker_memory > 0 and request.reranker_model:
                rag_breakdown["reranker_model"] = request.reranker_model
                rag_breakdown["reranker_memory"] = f"{reranker_memory:.2f} GB"
        
        # ========== Create Result ==========
        original_request = {
            "gpu": request.vgpu_profile,
            "num_gpus": request.num_gpu,
            "prompt_size": request.prompt_size,
            "response_size": request.response_size,
            "concurrent_requests": request.n_concurrent_request,
            "quantization": request.quantization,
            "recommended_profile": recommendation['recommendation'],
        }
        
        # Only add rag_breakdown if it's a RAG workload
        if rag_breakdown is not None:
            original_request["rag_breakdown"] = rag_breakdown
        
        return VGPUResult(
            model=model.name,
            original_request=original_request,
            resultant_configuration=resultant_configuration,
            alternative_configurations=[],  # Can add alternatives later if needed
            performance_metrics=performance_metrics
        )
    
    def print_memory_analysis(self, request: VGPURequest) -> None:
        """Print memory footprint analysis for all models"""
        bytes_per_param = 2 if request.quantization == "fp16" else 1
        context_window = request.prompt_size + request.response_size
        
        print(f"\n=== Memory Footprint Analysis ===")
        print(f"Quantization: {request.quantization}")
        print(f"Context: {context_window} tokens, Concurrent Requests: {request.n_concurrent_request}")
        
        mem_tbl = []
        for model in self.model_specs:
            mf = self._calc_memory_footprint(model, request.n_concurrent_request, 
                                             context_window, bytes_per_param)
            kv = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, 
                                                     request.quantization)
            mem_tbl.append({
                "Model": model.name,
                "Memory Footprint (GB)": f"{mf:.2f}",
                "KV Size/token (GiB)": f"{kv:.6f}"
            })
        
        # Print table header
        print("\n{:<30} {:<20} {:<20}".format("Model", "Memory Footprint (GB)", "KV Size/token (GiB)"))
        print("-" * 70)
        
        # Print table rows
        for row in mem_tbl:
            print("{:<30} {:<20} {:<20}".format(
                row["Model"], 
                row["Memory Footprint (GB)"], 
                row["KV Size/token (GiB)"]
            ))
    
    def print_oom_warnings(self, request: VGPURequest) -> None:
        """Print OOM warnings for all model-GPU combinations"""
        bytes_per_param = 2 if request.quantization == "fp16" else 1
        context_window = request.prompt_size + request.response_size
        
        print("\n=== OOM Warnings ===")
        warnings = []
        
        for model in self.model_specs:
            for gpu in self.gpu_specs:
                mf = self._calc_memory_footprint(model, request.n_concurrent_request, 
                                                 context_window, bytes_per_param)
                available = request.num_gpu * gpu.memory_gb
                if mf > available:
                    kv_size = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, 
                                                                  request.quantization)
                    max_req = int(self._calc_kv_cache_tokens(
                        request.num_gpu, gpu.memory_gb, model.params_billion, 
                        kv_size, bytes_per_param) // context_window)
                    warnings.append({
                        "model": model.name,
                        "gpu": gpu.name,
                        "max_concurrent": max_req
                    })
        
        for w in warnings:
            print(f"⚠️  {w['model']} with {w['gpu']}: Max concurrent requests = {w['max_concurrent']}")
    
    def validate_configuration(self, model_name: str, gpu_name: str, num_gpus: int = 1,
                               prompt_size: int = 1024, response_size: int = 250,
                               concurrent_requests: int = 1, quantization: str = "fp16") -> bool:
        """Validate if a specific configuration is viable"""
        model = self._find_model(model_name)
        gpu = self._find_gpu(gpu_name)
        
        if not model or not gpu:
            return False
        
        bytes_per_param = 2 if quantization == "fp16" else 1
        context_window = prompt_size + response_size
        
        kv_size = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, quantization)
        max_kv = self._calc_kv_cache_tokens(num_gpus, gpu.memory_gb, model.params_billion, 
                                             kv_size, bytes_per_param)
        required_kv = context_window * concurrent_requests
        
        return max_kv >= required_kv


# ============= Utility Functions =============

def create_example_requests() -> List[VGPURequest]:
    """Create example requests for testing"""
    return [
        VGPURequest(model_name="Llama-3-8B", vgpu_profile="A40-12Q"),
        VGPURequest(model_name="Llama-3-70B", vgpu_profile="A40-48Q", num_gpu=2),
        VGPURequest(model_name="Mistral-7B", vgpu_profile="L40-24Q", quantization="int8"),
    ]


def save_results_to_file(results: List[VGPUResult], filename: str = "vgpu_results.json") -> None:
    """Save multiple results to a JSON file"""
    data = {
        "timestamp": datetime.now().isoformat(),
        "results": [result.dict() for result in results]
    }
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Results saved to {filename}")


# ============= CLI Interface =============

def main():
    parser = argparse.ArgumentParser(description="vGPU Calculator for LLM Deployments")
    parser.add_argument("--num_gpu", type=int, default=1, help="Number of GPUs")
    parser.add_argument("--prompt_size", type=int, default=1024, help="Prompt size in tokens")
    parser.add_argument("--response_size", type=int, default=250, help="Response size in tokens")
    parser.add_argument("--n_concurrent_request", type=int, default=1, help="Concurrent requests")
    parser.add_argument("--quantization", choices=["fp16", "int8"], default="fp16", help="Quantization")
    parser.add_argument("--model", type=str, default="Llama-3-8B", help="Model name")
    parser.add_argument("--vgpu_profile", type=str, default="L40S-12Q", help="vGPU profile")
    parser.add_argument("--show_memory_analysis", action="store_true", help="Show memory analysis")
    parser.add_argument("--show_oom_warnings", action="store_true", help="Show OOM warnings")
    parser.add_argument("--output_json", action="store_true", help="Output results as JSON")
    parser.add_argument("--api_format", action="store_true", help="Output in API response format")
    parser.add_argument("--save_to_file", type=str, help="Save results to file")
    
    args = parser.parse_args()
    
    # Create calculator instance
    calculator = VGPUCalculator()
    
    # Create request
    request = VGPURequest(
        num_gpu=args.num_gpu,
        prompt_size=args.prompt_size,
        response_size=args.response_size,
        n_concurrent_request=args.n_concurrent_request,
        quantization=args.quantization,
        model_name=args.model,
        vgpu_profile=args.vgpu_profile
    )
    
    try:
        # Calculate results
        result = calculator.calculate(request)
        
        if args.output_json:
            print(result.json(indent=2))
        elif args.api_format:
            print(json.dumps(result.to_api_response(), indent=2))
        else:
            # Print human-readable output
            print(f"\n=== vGPU Configuration Results ===")
            print(f"Model: {result.model}")
            print(f"Original Request: {args.vgpu_profile} x{args.num_gpu}")
            print(f"\nOptimal Configuration:")
            print(f"  GPU: {result.resultant_configuration.gpu_name} x{result.resultant_configuration.num_gpus}")
            print(f"  Total Memory Required (Model + KV Cache): {result.resultant_configuration.total_memory_gb} GB")
            print(f"  GPU Memory Available: {result.resultant_configuration.gpu_memory_gb} GB")
            print(f"  Memory Margin: {result.resultant_configuration.gpu_memory_gb - result.resultant_configuration.total_memory_gb} GB")
            print(f"  Max KV Tokens: {result.resultant_configuration.max_kv_tokens:,}")
            
            if result.alternative_configurations:
                print(f"\nAlternative Configurations:")
                for i, alt in enumerate(result.alternative_configurations, 1):
                    print(f"  {i}. {alt.gpu_family}: {alt.gpu_name} x{alt.num_gpus} "
                          f"(Model: {alt.total_memory_gb}GB, GPU: {alt.gpu_memory_gb}GB, {alt.max_kv_tokens:,} tokens)")
            
            print(f"\nPerformance Metrics:")
            print(f"  TTFT: {result.performance_metrics.ttft_seconds:.3f}s" 
                  if isinstance(result.performance_metrics.ttft_seconds, (int, float)) 
                  else f"  TTFT: {result.performance_metrics.ttft_seconds}")
            print(f"  E2E Latency: {result.performance_metrics.e2e_latency_seconds:.2f}s"
                  if isinstance(result.performance_metrics.e2e_latency_seconds, (int, float))
                  else f"  E2E Latency: {result.performance_metrics.e2e_latency_seconds}")
            print(f"  Throughput: {result.performance_metrics.throughput_tokens_per_second:.2f} tok/s"
                  if isinstance(result.performance_metrics.throughput_tokens_per_second, (int, float))
                  else f"  Throughput: {result.performance_metrics.throughput_tokens_per_second}")
        
        # Save to file if requested
        if args.save_to_file:
            save_results_to_file([result], args.save_to_file)
        
        # Show additional analysis if requested
        if args.show_memory_analysis:
            calculator.print_memory_analysis(request)
        
        if args.show_oom_warnings:
            calculator.print_oom_warnings(request)
            
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())