#!/usr/bin/env python3
"""Test calculator output for Llama-3-8B"""

from src.calculator import VGPUCalculator, VGPURequest

# Create calculator and request
calculator = VGPUCalculator()
request = VGPURequest(
    model_name="Llama-3-8B",
    vgpu_profile="L40S-24Q",
    num_gpu=1,
    prompt_size=1024,
    response_size=256,
    n_concurrent_request=1,
    quantization="fp16"
)

# Calculate
result = calculator.calculate(request)

# Print results
print(f"Model: {result.model}")
print(f"GPU Configuration: {result.resultant_configuration.gpu_name} x{result.resultant_configuration.num_gpus}")
print(f"Max KV Tokens: {result.resultant_configuration.max_kv_tokens:,}")
print(f"GPU Memory: {result.resultant_configuration.gpu_memory_gb} GB")
print(f"Required Memory: {result.resultant_configuration.required_gpu_memory_gb} GB")

# Check if it was optimized
if result.resultant_configuration.gpu_name != request.vgpu_profile:
    print(f"\nNote: Configuration was changed from {request.vgpu_profile} to {result.resultant_configuration.gpu_name}") 