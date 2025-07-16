#!/usr/bin/env python3
"""Test script to verify the new GPU memory calculation logic"""

from src.calculator import VGPUCalculator, VGPURequest

def main():
    calculator = VGPUCalculator()
    
    # Test case: Llama-3-8B with L40S-24Q
    request = VGPURequest(
        model_name="Llama-3-8B",
        vgpu_profile="L40S-24Q",
        num_gpu=1,
        prompt_size=1024,
        response_size=256,
        n_concurrent_request=1,
        quantization="fp16"
    )
    
    print("Testing GPU memory calculation for Llama-3-8B on L40S-24Q")
    print("=" * 60)
    
    result = calculator.calculate(request)
    config = result.resultant_configuration
    
    print(f"Model: {result.model}")
    print(f"GPU: {config.gpu_name} x{config.num_gpus}")
    print(f"\nMemory Breakdown:")
    print(f"  Model Memory Footprint: {config.total_memory_gb} GB")
    print(f"  Available GPU Memory: {config.gpu_memory_gb} GB")
    print(f"  Required GPU Memory (Model + KV Cache): {config.required_gpu_memory_gb} GB")
    print(f"  Max KV Tokens: {config.max_kv_tokens:,}")
    
    # Calculate KV cache size
    model = calculator._find_model("Llama-3-8B")
    kv_size_per_token = calculator._calc_kv_cache_size_per_token(
        model.n_layers, model.d_model, request.quantization
    )
    kv_cache_total = kv_size_per_token * config.max_kv_tokens
    
    print(f"\nDetailed Calculation:")
    print(f"  Model weights: {model.params_billion * 2} GB (8B params * 2 bytes)")
    print(f"  KV cache per token: {kv_size_per_token:.6f} GB")
    print(f"  Total KV cache: {kv_cache_total:.2f} GB ({config.max_kv_tokens:,} tokens)")
    print(f"  Total: {model.params_billion * 2:.0f} + {kv_cache_total:.2f} = {config.required_gpu_memory_gb} GB")
    
    # Test with different models
    print("\n" + "=" * 60)
    print("Testing with other models:")
    
    for model_name in ["Mistral-7B", "Llama-3-70B"]:
        try:
            request.model_name = model_name
            result = calculator.calculate(request)
            config = result.resultant_configuration
            print(f"\n{model_name}:")
            print(f"  GPU: {config.gpu_name} x{config.num_gpus}")
            print(f"  Required Memory: {config.required_gpu_memory_gb} GB")
            print(f"  Max KV Tokens: {config.max_kv_tokens:,}")
        except Exception as e:
            print(f"\n{model_name}: {str(e)}")

if __name__ == "__main__":
    main() 