"""
vGPU Calculator - A modular tool for optimizing GPU configurations for LLM deployments
"""

from typing import List, Optional, Dict, Any, Union, Tuple
from datetime import datetime
from pydantic import BaseModel, Field, validator
import json
import argparse


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


class VGPURequest(BaseModel):
    """Input request parameters"""
    num_gpu: int = Field(default=1, ge=1, description="Number of GPUs")
    prompt_size: int = Field(default=1024, ge=1, description="Prompt size in tokens")
    response_size: int = Field(default=250, ge=1, description="Response size in tokens")
    n_concurrent_request: int = Field(default=1, ge=1, description="Number of concurrent requests")
    quantization: str = Field(default="fp16", pattern="^(fp16|int8)$", description="Quantization precision")
    model_name: str = Field(default="Llama-3-8B", description="Model name")
    vgpu_profile: str = Field(default="A40-12Q", description="vGPU profile")


class VGPUResult(BaseModel):
    """Complete result of vGPU calculation"""
    model: str
    original_request: Dict[str, Any]
    resultant_configuration: Configuration
    alternative_configurations: List[AlternativeConfiguration]
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
            GPUSpec(name="A40-12Q", fp16_tflops=299, memory_gb=12, phy_memory_gb=48, bandwidth_gbps=696),
            GPUSpec(name="A40-24Q", fp16_tflops=299, memory_gb=24, phy_memory_gb=48, bandwidth_gbps=696),
            GPUSpec(name="A40-48Q", fp16_tflops=299, memory_gb=48, phy_memory_gb=48, bandwidth_gbps=696),
            GPUSpec(name="L40-12Q", fp16_tflops=362, memory_gb=12, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40-24Q", fp16_tflops=362, memory_gb=24, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40-48Q", fp16_tflops=362, memory_gb=48, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40S-12Q", fp16_tflops=366, memory_gb=12, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40S-24Q", fp16_tflops=366, memory_gb=24, phy_memory_gb=48, bandwidth_gbps=864),
            GPUSpec(name="L40S-48Q", fp16_tflops=366, memory_gb=48, phy_memory_gb=48, bandwidth_gbps=864),
        ]
    
    def _initialize_model_specs(self) -> List[ModelSpec]:
        """Initialize available model specifications"""
        return [
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
        """Find model specification by name"""
        for model in self.model_specs:
            if model.name == model_name:
                return model
        return None
    
    def _find_gpu(self, gpu_name: str) -> Optional[GPUSpec]:
        """Find GPU specification by name"""
        for gpu in self.gpu_specs:
            if gpu.name == gpu_name:
                return gpu
        return None
    
    def _calc_kv_cache_size_per_token(self, n_layers: int, d_model: int, quantization: str) -> float:
        """Calculate KV cache size per token in GB"""
        elem_size = 1 if quantization == "int8" else 2
        return 2 * elem_size * n_layers * d_model / self.BYTES_IN_GB
    
    def _calc_memory_footprint(self, model: ModelSpec, concurrent: int, context: int, 
                               bytes_per_param: int) -> float:
        """Calculate total memory footprint in GB"""
        kv_size = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, 
                                                      "fp16" if bytes_per_param == 2 else "int8")
        return kv_size * context * concurrent + model.params_billion * bytes_per_param
    
    def _calc_kv_cache_tokens(self, num_gpu: int, gpu_mem: int, params_billion: float, 
                              kv_size: float, bytes_per_param: int) -> float:
        """Calculate maximum KV cache tokens"""
        available = num_gpu * gpu_mem - params_billion * bytes_per_param
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
            for n_gpu in range(1, max_gpus + 1):
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
        # Find model and GPU
        model = self._find_model(request.model_name)
        if not model:
            raise ValueError(f"Model '{request.model_name}' not found. Available: {self.get_available_models()}")
        
        gpu = self._find_gpu(request.vgpu_profile)
        if not gpu:
            raise ValueError(f"GPU '{request.vgpu_profile}' not found. Available: {self.get_available_gpus()}")
        
        bytes_per_param = 2 if request.quantization == "fp16" else 1
        context_window = request.prompt_size + request.response_size
        
        # Calculate model memory footprint
        model_memory_footprint = self._calc_memory_footprint(
            model, request.n_concurrent_request, context_window, bytes_per_param
        )
        
        # Calculate initial metrics
        kv_size = self._calc_kv_cache_size_per_token(model.n_layers, model.d_model, request.quantization)
        max_kv = self._calc_kv_cache_tokens(request.num_gpu, gpu.memory_gb, model.params_billion, 
                                             kv_size, bytes_per_param)
        
        # Store configuration
        resultant_configuration = None
        alternative_configurations = []
        used_gpu = gpu
        used_num_gpu = request.num_gpu
        
        if max_kv == 0:
            # Find optimal configuration
            all_configs = self._find_all_viable_configurations(
                model, gpu, request.n_concurrent_request, context_window, request.quantization
            )
            
            if all_configs:
                optimal = all_configs[0]
                gpu_family, _ = self._get_gpu_family_and_size(gpu.name)
                
                resultant_configuration = Configuration(
                    gpu_name=optimal['gpu'].name,
                    num_gpus=optimal['num_gpu'],
                    total_memory_gb=int(model_memory_footprint),
                    gpu_memory_gb=optimal['total_memory'],
                    max_kv_tokens=int(optimal['max_kv']),
                    concurrent_requests=optimal['concurrent'],
                    context_window=optimal['context']
                )
                
                # Find cross-family alternatives
                cross_family_configs = self._find_cross_family_alternatives(
                    model, request.n_concurrent_request, context_window, 
                    request.quantization, exclude_family=gpu_family
                )
                
                alternative_configurations = [
                    AlternativeConfiguration(
                        gpu_name=config['gpu'].name,
                        num_gpus=config['num_gpu'],
                        gpu_family=config['family'],
                        total_memory_gb=int(model_memory_footprint),
                        gpu_memory_gb=config['total_memory'],
                        max_kv_tokens=int(config['max_kv'])
                    )
                    for config in cross_family_configs
                ]
                
                used_gpu = optimal['gpu']
                used_num_gpu = optimal['num_gpu']
                max_kv = optimal['max_kv']
            else:
                raise ValueError(f"No viable configuration found for {model.name}")
        else:
            # Original configuration is viable
            resultant_configuration = Configuration(
                gpu_name=gpu.name,
                num_gpus=request.num_gpu,
                total_memory_gb=int(model_memory_footprint),  # Model memory footprint
                gpu_memory_gb=gpu.memory_gb * request.num_gpu,  # Total GPU memory
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
    parser.add_argument("--vgpu_profile", type=str, default="A40-12Q", help="vGPU profile")
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
            print(f"  Model Memory Footprint: {result.resultant_configuration.total_memory_gb} GB")
            print(f"  Total GPU Memory: {result.resultant_configuration.gpu_memory_gb} GB")
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