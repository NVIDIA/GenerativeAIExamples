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
    quantization: str = Field(default="fp16", pattern="^(fp16|int8)$", description="Quantization precision")
    model_name: str = Field(default="Llama-3-8B", description="Model name")
    vgpu_profile: str = Field(default="A40-12Q", description="vGPU profile")
    advanced_config: Optional[AdvancedCalculatorConfig] = Field(
        default=None,
        description="Advanced configuration options for fine-tuning calculations"
    )


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
        self.BYTES_IN_GB = 1_073_741_824
    
    def _initialize_gpu_specs(self) -> List[GPUSpec]:
        """Initialize available GPU specifications"""
        return [
            GPUSpec(name="L4-12Q", fp16_tflops=242, memory_gb=12, phy_memory_gb=24, bandwidth_gbps=300),
            GPUSpec(name="L4-24Q", fp16_tflops=242, memory_gb=24, phy_memory_gb=24, bandwidth_gbps=300),
            GPUSpec(name="A40-12Q", fp16_tflops=299, memory_gb=12, phy_memory_gb=48, bandwidth_gbps=696),
            GPUSpec(name="A40-24Q", fp16_tflops=299, memory_gb=24, phy_memory_gb=48, bandwidth_gbps=696),
            GPUSpec(name="A40-48Q", fp16_tflops=299, memory_gb=48, phy_memory_gb=48, bandwidth_gbps=696),
            GPUSpec(name="L40-12Q", fp16_tflops=362, memory_gb=12, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40-24Q", fp16_tflops=362, memory_gb=24, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40-48Q", fp16_tflops=362, memory_gb=48, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40S-12Q", fp16_tflops=366, memory_gb=12, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40S-24Q", fp16_tflops=366, memory_gb=24, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40S-48Q", fp16_tflops=366, memory_gb=48, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="DC-12Q", fp16_tflops=500, memory_gb=12, phy_memory_gb=96, bandwidth_gbps=1600),
            GPUSpec(name="DC-24Q", fp16_tflops=500, memory_gb=24, phy_memory_gb=96, bandwidth_gbps=1600),
            GPUSpec(name="DC-32Q", fp16_tflops=500, memory_gb=32, phy_memory_gb=96, bandwidth_gbps=1600),
            GPUSpec(name="DC-48Q", fp16_tflops=500, memory_gb=48, phy_memory_gb=96, bandwidth_gbps=1600),
            GPUSpec(name="DC-96Q", fp16_tflops=500, memory_gb=96, phy_memory_gb=96, bandwidth_gbps=1600),
        ]
    
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
        # First, try to find in existing specs
        for model in self.model_specs:
            if model.name == model_name or model.name.lower() == model_name.lower():
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
        
        return None
    
    def _find_gpu(self, gpu_name: str) -> Optional[GPUSpec]:
        """Find GPU specification by name"""
        for gpu in self.gpu_specs:
            if gpu.name == gpu_name:
                return gpu
        return None
    
    def _find_optimal_vgpu_profile(self, model_memory_footprint: float, gpu: GPUSpec) -> GPUSpec:
        """Find optimal vGPU profile based on the model memory footprint (accounting for the hypervisor layer)"""

        gpu_family, _ = self._get_gpu_family_and_size(gpu.name)
        family_gpus = [g for g in self.gpu_specs if g.name.startswith(gpu_family)]
        family_gpus.sort(key=lambda g: self._get_gpu_family_and_size(g.name)[1])

        for g in family_gpus:
            if model_memory_footprint <= (g.memory_gb - 2): 
                return g
        # If none of the profiles have enough memory, return the highest memory profile
        if family_gpus:
            return family_gpus[-1]
        else:
            return None


    def _calc_kv_cache_size_per_token(self, n_layers: int, d_model: int, quantization: str) -> float:
        """Calculate KV cache size per token in GB"""
        elem_size = 1 if quantization == "int8" else 2
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
        """Main calculation method"""
        # Get advanced config or use defaults
        config = request.advanced_config if request.advanced_config else AdvancedCalculatorConfig()
        
        # Find model and GPU
        model = self._find_model(request.model_name)
        if not model:
            raise ValueError(f"Model '{request.model_name}' not found. Available: {self.get_available_models()}")
        
        gpu = self._find_gpu(request.vgpu_profile)
        if not gpu:
            raise ValueError(f"GPU '{request.vgpu_profile}' not found. Available: {self.get_available_gpus()}")
        
        bytes_per_param = 2 if request.quantization == "fp16" else 1
        context_window = request.prompt_size + request.response_size
        
        # Calculate model memory footprint using configurable overhead
        model_memory_footprint = self._calc_memory_footprint(
            model, request.n_concurrent_request, context_window, bytes_per_param, 
            memory_overhead=config.model_memory_overhead
        ) 
        logging.info(f"hello: {model_memory_footprint:.2f} GB")
        print(f"hello: {model_memory_footprint:.2f} GB")
        
        # if the model memory is greater than or equal to the (gpu_memory that we have - the Hypervisor layer)
        optimal_gpu = self._find_optimal_vgpu_profile(model_memory_footprint, gpu)
        if optimal_gpu:
            gpu = optimal_gpu

        logging.info(f"optimal_gpu: {optimal_gpu.name}")
        # the default num_gpu here is 1, so we first have to see if based on the model memory footprint, we have to adjust for the num_gpu (round down if ratio its less than 0.5)
        num_gpu_ratio = model_memory_footprint / gpu.memory_gb
        if num_gpu_ratio < 0.5:
            request.num_gpu = 1
        else:
            request.num_gpu = math.ceil(num_gpu_ratio)

        logging.info(f"num_gpu: {request.num_gpu}")
        kv_size = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, request.quantization)
        logging.info(f"heres the kv_size: {kv_size}")
        max_kv = self._calc_kv_cache_tokens(
            request.num_gpu, gpu.memory_gb, model.params_billion, 
            kv_size, bytes_per_param,
            hypervisor_reserve_gb=config.hypervisor_reserve_gb,
            cuda_overhead=config.cuda_memory_overhead
        )
        

        # Store configuration
        total_memory_required = self._calc_total_memory_with_kv_cache(model_memory_footprint, model, context_window, request.n_concurrent_request, bytes_per_param, request.quantization)
        resultant_configuration = None
        alternative_configurations = []
        used_gpu = gpu
        used_num_gpu = request.num_gpu

        # recalc the gpu we need to use based on the total_memory_required
        optimal_gpu = self._find_optimal_vgpu_profile(total_memory_required, gpu)
        if optimal_gpu:
            gpu = optimal_gpu
            used_gpu = optimal_gpu
            used_num_gpu = request.num_gpu
            max_kv = self._calc_kv_cache_tokens(
                request.num_gpu, gpu.memory_gb, model.params_billion, 
                kv_size, bytes_per_param,
                hypervisor_reserve_gb=config.hypervisor_reserve_gb,
                cuda_overhead=config.cuda_memory_overhead
            )

        
        if max_kv == 0:
            # increase the num_gpu by 1 and recalculate the max_kv and total_memory_required
            request.num_gpu += 1
            max_kv = self._calc_kv_cache_tokens(
                request.num_gpu, gpu.memory_gb, model.params_billion, 
                kv_size, bytes_per_param,
                hypervisor_reserve_gb=config.hypervisor_reserve_gb,
                cuda_overhead=config.cuda_memory_overhead
            )
            used_num_gpu = request.num_gpu
        else:
            resultant_configuration = Configuration(
                gpu_name=gpu.name,
                num_gpus=request.num_gpu,
                total_memory_gb=total_memory_required,
                gpu_memory_gb=gpu.memory_gb * request.num_gpu,
                max_kv_tokens=int(max_kv),
                concurrent_requests=request.n_concurrent_request,
                context_window=context_window
            )
                    
        
        # Calculate performance metrics
        pre = self._calc_prefill_time(model.params_billion, used_gpu, bytes_per_param, used_num_gpu)
        tpot = self._calc_tpot(model.params_billion, used_gpu, bytes_per_param, used_num_gpu)
        
        if any(isinstance(x, str) for x in (pre, tpot)):
            ttft = e2e = throughput = "OOM"
        else:
            ttft = pre + tpot / 1000
            e2e = self._calc_e2e(pre, tpot, request.prompt_size, request.response_size)
            throughput = request.response_size / e2e if e2e > 0 else "OOM"
        
        performance_metrics = PerformanceMetrics(
            max_kv_tokens=int(max_kv),
            ttft_seconds=ttft if isinstance(ttft, (int, float)) else ttft,
            e2e_latency_seconds=e2e if isinstance(e2e, (int, float)) else e2e,
            throughput_tokens_per_second=throughput if isinstance(throughput, (int, float)) else throughput
        )
        logging.info("the max kv is: " + str(max_kv))
        # Create result
        return VGPUResult(
            model=model.name,
            original_request={
                "gpu": gpu.name,
                "num_gpus": request.num_gpu,
                "prompt_size": request.prompt_size,
                "response_size": request.response_size,
                "concurrent_requests": request.n_concurrent_request,
                "quantization": request.quantization
            },
            resultant_configuration=resultant_configuration,
            alternative_configurations=alternative_configurations,
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