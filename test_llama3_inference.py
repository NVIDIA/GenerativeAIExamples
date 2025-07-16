#!/usr/bin/env python3
"""Test script to demonstrate Llama-3-8B inference configurations with automatic GPU upgrades"""

import logging
from src.calculator import VGPUCalculator, VGPURequest

# Set up logging to see the upgrade messages
logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_llama3_8b_configurations():
    """Test various Llama-3-8B configurations to demonstrate memory calculations and GPU upgrades"""
    
    calculator = VGPUCalculator()
    
    print("=== Llama-3-8B Inference Configuration Tests ===\n")
    
    # Test 1: Standard configuration
    print("Test 1: Standard Configuration (1024 prompt, 256 response)")
    print("-" * 60)
    
    request1 = VGPURequest(
        model_name="Llama-3-8B",
        vgpu_profile="L40S-24Q",
        num_gpu=1,
        prompt_size=1024,
        response_size=256,
        n_concurrent_request=1,
        quantization="fp16"
    )
    
    result1 = calculator.calculate(request1)
    print_result(result1, request1)
    
    # Test 2: Larger context that might trigger upgrade
    print("\n\nTest 2: Larger Context (4096 prompt, 1024 response)")
    print("-" * 60)
    
    request2 = VGPURequest(
        model_name="Llama-3-8B",
        vgpu_profile="L40S-24Q",
        num_gpu=1,
        prompt_size=4096,
        response_size=1024,
        n_concurrent_request=1,
        quantization="fp16"
    )
    
    result2 = calculator.calculate(request2)
    print_result(result2, request2)
    
    # Test 3: Multiple concurrent requests
    print("\n\nTest 3: Multiple Concurrent Requests")
    print("-" * 60)
    
    request3 = VGPURequest(
        model_name="Llama-3-8B",
        vgpu_profile="L40S-24Q",
        num_gpu=1,
        prompt_size=2048,
        response_size=512,
        n_concurrent_request=4,
        quantization="fp16"
    )
    
    result3 = calculator.calculate(request3)
    print_result(result3, request3)
    
    # Test 4: INT8 quantization
    print("\n\nTest 4: INT8 Quantization (reduced memory)")
    print("-" * 60)
    
    request4 = VGPURequest(
        model_name="Llama-3-8B",
        vgpu_profile="L40S-12Q",
        num_gpu=1,
        prompt_size=2048,
        response_size=512,
        n_concurrent_request=1,
        quantization="int8"
    )
    
    result4 = calculator.calculate(request4)
    print_result(result4, request4)
    
    # Test 5: Edge case - exactly at memory limit
    print("\n\nTest 5: Edge Case - Near Memory Limit")
    print("-" * 60)
    
    request5 = VGPURequest(
        model_name="Llama-3-8B",
        vgpu_profile="L40S-24Q",
        num_gpu=1,
        prompt_size=3072,
        response_size=768,
        n_concurrent_request=1,
        quantization="fp16"
    )
    
    result5 = calculator.calculate(request5)
    print_result(result5, request5)
    
    # Memory breakdown example
    print("\n\n=== Memory Breakdown Example ===")
    print("-" * 60)
    
    model = calculator._find_model("Llama-3-8B")
    
    # Calculate components for request1
    bytes_per_param = 2  # fp16
    context_window = request1.prompt_size + request1.response_size
    
    model_memory = model.params_billion * bytes_per_param
    kv_per_token = calculator._calc_kv_cache_size_per_token(model.n_layers, model.d_model, "fp16")
    kv_cache_memory = kv_per_token * context_window * request1.n_concurrent_request
    
    print(f"Model: {model.name}")
    print(f"  Parameters: {model.params_billion}B")
    print(f"  Quantization: fp16 (2 bytes per param)")
    print(f"  Model Memory: {model_memory} GB")
    print()
    print(f"KV Cache:")
    print(f"  Context Window: {context_window} tokens")
    print(f"  KV Cache per Token: {kv_per_token:.6f} GB")
    print(f"  Total KV Cache: {kv_cache_memory:.2f} GB")
    print()
    print(f"Total Memory: {model_memory} + {kv_cache_memory:.2f} = {model_memory + kv_cache_memory:.2f} GB")


def print_result(result, request):
    """Print the configuration result"""
    config = result.resultant_configuration
    
    print(f"Requested: {request.vgpu_profile}")
    print(f"Selected: {config.gpu_name} x{config.num_gpus}")
    print(f"Total Memory Required: {config.total_memory_gb} GB")
    print(f"GPU Memory Available: {config.gpu_memory_gb} GB")
    print(f"Memory Margin: {config.gpu_memory_gb - config.total_memory_gb} GB")
    print(f"Max KV Tokens: {config.max_kv_tokens:,}")
    
    if config.gpu_name != request.vgpu_profile:
        print(f"✅ GPU upgraded from {request.vgpu_profile} to {config.gpu_name} for adequate memory margin")
    
    # Performance metrics
    if isinstance(result.performance_metrics.ttft_seconds, (int, float)):
        print(f"\nPerformance:")
        print(f"  TTFT: {result.performance_metrics.ttft_seconds:.3f}s")
        print(f"  E2E Latency: {result.performance_metrics.e2e_latency_seconds:.2f}s")
        print(f"  Throughput: {result.performance_metrics.throughput_tokens_per_second:.2f} tokens/s")


if __name__ == "__main__":
    test_llama3_8b_configurations() 