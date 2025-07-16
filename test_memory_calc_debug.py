#!/usr/bin/env python3
"""Debug script to check memory calculations"""

from src.calculator import VGPUCalculator, VGPURequest

def debug_memory_calculation():
    calculator = VGPUCalculator()
    
    # Simple test case
    request = VGPURequest(
        model_name="Llama-3-8B",
        vgpu_profile="L40S-24Q",
        num_gpu=1,
        prompt_size=1024,
        response_size=256,
        n_concurrent_request=1,
        quantization="fp16"
    )
    
    # Get model and GPU
    model = calculator._find_model(request.model_name)
    gpu = calculator._find_gpu(request.vgpu_profile)
    
    print(f"Model: {model.name}")
    print(f"  Parameters: {model.params_billion}B")
    print(f"  d_model: {model.d_model}")
    print(f"  n_layers: {model.n_layers}")
    print()
    
    print(f"GPU: {gpu.name}")
    print(f"  Memory: {gpu.memory_gb} GB")
    print()
    
    # Calculate components
    bytes_per_param = 2  # fp16
    context_window = request.prompt_size + request.response_size
    
    # Model weights
    model_weights_gb = model.params_billion * bytes_per_param
    print(f"Model weights: {model_weights_gb} GB")
    
    # KV cache per token
    kv_per_token = calculator._calc_kv_cache_size_per_token(model.n_layers, model.d_model, "fp16")
    print(f"KV cache per token: {kv_per_token:.6f} GB")
    
    # Max KV tokens
    kv_size = calculator._calc_kv_cache_size_per_token(model.n_layers, model.d_model, request.quantization)
    max_kv = calculator._calc_kv_cache_tokens(request.num_gpu, gpu.memory_gb, model.params_billion, 
                                               kv_size, bytes_per_param)
    print(f"Max KV tokens: {int(max_kv):,}")
    
    # Total required memory
    required_memory = calculator._calc_total_gpu_memory_required(
        model, int(max_kv), bytes_per_param, request.quantization
    )
    print(f"Required memory: {required_memory:.2f} GB")
    
    # KV cache memory
    kv_cache_memory = kv_per_token * max_kv
    print(f"KV cache memory: {kv_cache_memory:.2f} GB")
    
    print(f"\nTotal: {model_weights_gb} + {kv_cache_memory:.2f} = {required_memory:.2f} GB")

if __name__ == "__main__":
    debug_memory_calculation() 