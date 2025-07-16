#!/usr/bin/env python3
"""Test script to verify the corrected memory calculations"""

from src.calculator import VGPUCalculator, VGPURequest

def test_memory_calculations():
    """Test the corrected memory calculation logic"""
    
    calculator = VGPUCalculator()
    
    print("=== Testing Corrected Memory Calculations ===\n")
    
    # Test configuration
    request = VGPURequest(
        model_name="Llama-3-8B",
        vgpu_profile="L40S-24Q",
        num_gpu=1,
        prompt_size=1024,
        response_size=256,
        n_concurrent_request=1,
        quantization="fp16"
    )
    
    # Get model and GPU specs
    model = calculator._find_model(request.model_name)
    gpu = calculator._find_gpu(request.vgpu_profile)
    
    # Calculate components
    bytes_per_param = 2  # fp16
    context_window = request.prompt_size + request.response_size
    
    # Model weights
    model_weights_gb = model.params_billion * bytes_per_param
    print(f"Model: {model.name}")
    print(f"  Parameters: {model.params_billion}B")
    print(f"  Model Weights: {model_weights_gb} GB")
    print()
    
    # KV cache per token
    kv_per_token = calculator._calc_kv_cache_size_per_token(model.n_layers, model.d_model, "fp16")
    print(f"KV Cache:")
    print(f"  KV Cache per Token: {kv_per_token:.6f} GB")
    print()
    
    # Calculate max KV tokens that can fit
    kv_size = calculator._calc_kv_cache_size_per_token(model.n_layers, model.d_model, request.quantization)
    max_kv = calculator._calc_kv_cache_tokens(request.num_gpu, gpu.memory_gb, model.params_billion, 
                                               kv_size, bytes_per_param)
    
    print(f"GPU: {gpu.name}")
    print(f"  Available Memory: {gpu.memory_gb} GB")
    print(f"  Max KV Tokens: {int(max_kv):,}")
    print()
    
    # Old calculation (incorrect)
    old_memory = calculator._calc_memory_footprint(
        model, request.n_concurrent_request, context_window, bytes_per_param
    )
    print(f"Old Calculation (context-based):")
    print(f"  Context Window: {context_window} tokens")
    print(f"  Total Memory: {old_memory:.2f} GB")
    print(f"  Formula: {model_weights_gb} + ({context_window} × {kv_per_token:.6f}) = {old_memory:.2f} GB")
    print()
    
    # New calculation (correct)
    new_memory = calculator._calc_actual_memory_usage(
        model, int(max_kv), bytes_per_param, request.quantization
    )
    kv_cache_total = kv_per_token * max_kv
    print(f"New Calculation (max_kv-based):")
    print(f"  Max KV Tokens: {int(max_kv):,}")
    print(f"  KV Cache Total: {kv_cache_total:.2f} GB")
    print(f"  Total Memory: {new_memory:.2f} GB")
    print(f"  Formula: {model_weights_gb} + ({int(max_kv):,} × {kv_per_token:.6f}) = {new_memory:.2f} GB")
    print()
    
    # Run full calculation
    result = calculator.calculate(request)
    config = result.resultant_configuration
    
    print(f"Full Calculation Result:")
    print(f"  GPU Configuration: {config.gpu_name} x{config.num_gpus}")
    print(f"  Total Memory (from config): {config.total_memory_gb} GB")
    print(f"  GPU Memory Available: {config.gpu_memory_gb} GB")
    print(f"  Memory Margin: {config.gpu_memory_gb - config.total_memory_gb} GB")
    print(f"  Max KV Tokens: {config.max_kv_tokens:,}")
    
    # Verify the calculation matches
    if abs(config.total_memory_gb - int(new_memory)) <= 1:  # Allow for rounding
        print(f"\n✅ Memory calculation is correct!")
    else:
        print(f"\n❌ Memory calculation mismatch!")


if __name__ == "__main__":
    test_memory_calculations() 