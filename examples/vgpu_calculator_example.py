"""
Example usage of the vGPU Calculator
This script demonstrates various ways to use the modular vGPU calculator
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.calculator import VGPUCalculator, VGPURequest, VGPUResult, GPUSpec, ModelSpec
from src.vgpu_validation import VGPUValidator, CostEstimate
import json
from typing import List, Dict, Any


def basic_usage_example():
    """Basic example of using the vGPU calculator"""
    print("=== Basic Usage Example ===\n")
    
    # Create calculator instance
    calculator = VGPUCalculator()
    
    # Create a request
    request = VGPURequest(
        model_name="Llama-3-8B",
        vgpu_profile="A40-12Q",
        prompt_size=1024,
        response_size=256,
        n_concurrent_request=1,
        quantization="fp16"
    )
    
    # Calculate optimal configuration
    result = calculator.calculate(request)
    
    # Print results
    print(f"Model: {result.model}")
    print(f"Optimal GPU: {result.resultant_configuration.gpu_name} x{result.resultant_configuration.num_gpus}")
    print(f"Total Memory: {result.resultant_configuration.total_memory_gb} GB")
    print(f"Max KV Tokens: {result.resultant_configuration.max_kv_tokens:,}")
    print(f"TTFT: {result.performance_metrics.ttft_seconds:.3f}s")
    print(f"Throughput: {result.performance_metrics.throughput_tokens_per_second:.2f} tok/s")
    
    return result


def batch_processing_example():
    """Example of processing multiple configurations"""
    print("\n=== Batch Processing Example ===\n")
    
    calculator = VGPUCalculator()
    
    # Define multiple test cases
    test_cases = [
        {"model": "Llama-3-8B", "gpu": "A40-12Q", "concurrent": 1},
        {"model": "Llama-3-70B", "gpu": "A40-48Q", "concurrent": 2},
        {"model": "Mistral-7B", "gpu": "L40-24Q", "concurrent": 4},
    ]
    
    results = []
    for test in test_cases:
        request = VGPURequest(
            model_name=test["model"],
            vgpu_profile=test["gpu"],
            n_concurrent_request=test["concurrent"]
        )
        
        try:
            result = calculator.calculate(request)
            results.append({
                "test": test,
                "result": result.resultant_configuration.dict(),
                "performance": {
                    "throughput": result.performance_metrics.throughput_tokens_per_second,
                    "latency": result.performance_metrics.e2e_latency_seconds
                }
            })
            print(f"{test['model']} on {test['gpu']}: "
                  f"→ {result.resultant_configuration.gpu_name} x{result.resultant_configuration.num_gpus}")
        except Exception as e:
            print(f"{test['model']} on {test['gpu']}: Error - {e}")
    
    return results


def custom_model_example():
    """Example of adding custom models and GPUs"""
    print("\n=== Custom Model Example ===\n")
    
    calculator = VGPUCalculator()
    
    # Add a custom model
    custom_model = ModelSpec(
        name="CustomLLM-13B",
        params_billion=13,
        d_model=5120,
        n_layers=36
    )
    calculator.add_custom_model(custom_model)
    
    # Add a custom GPU
    custom_gpu = GPUSpec(
        name="H100-80Q",
        fp16_tflops=989,
        memory_gb=80,
        phy_memory_gb=80,
        bandwidth_gbps=3350
    )
    calculator.add_custom_gpu(custom_gpu)
    
    # Use the custom model and GPU
    request = VGPURequest(
        model_name="CustomLLM-13B",
        vgpu_profile="H100-80Q",
        prompt_size=2048,
        response_size=512
    )
    
    result = calculator.calculate(request)
    print(f"Custom Model: {result.model}")
    print(f"Custom GPU: {result.resultant_configuration.gpu_name}")
    print(f"Performance: {result.performance_metrics.throughput_tokens_per_second:.2f} tok/s")
    
    return result


def validation_example():
    """Example of using the validation module"""
    print("\n=== Validation Example ===\n")
    
    validator = VGPUValidator()
    
    # Create a challenging request
    request = VGPURequest(
        model_name="Llama-3-70B",
        vgpu_profile="A40-12Q",  # Too small for this model
        prompt_size=2048,
        response_size=512,
        n_concurrent_request=4
    )
    
    # Validate workload fit
    validation = validator.validate_workload_fit(request)
    print(f"Configuration Valid: {validation.is_valid}")
    print("Issues:")
    for issue in validation.issues:
        print(f"  - {issue}")
    print("Suggestions:")
    for suggestion in validation.suggestions:
        print(f"  - {suggestion}")
    
    return validation


def cost_optimization_example():
    """Example of finding the most cost-effective configuration"""
    print("\n=== Cost Optimization Example ===\n")
    
    validator = VGPUValidator()
    
    request = VGPURequest(
        model_name="Llama-3-8B",
        prompt_size=1024,
        response_size=256,
        n_concurrent_request=2
    )
    
    # Find cheapest configuration
    cheapest = validator.find_cheapest_configuration(request)
    
    if cheapest:
        print(f"Most Cost-Effective Configuration:")
        print(f"  GPU: {cheapest.configuration.gpu_name} x{cheapest.configuration.num_gpus}")
        print(f"  Hourly Cost: ${cheapest.hourly_cost:.2f}")
        print(f"  Monthly Cost: ${cheapest.monthly_cost:,.2f}")
        print(f"  Cost per Million Tokens: ${cheapest.cost_per_million_tokens:.2f}")
        print(f"  Max KV Tokens: {cheapest.configuration.max_kv_tokens:,}")
    
    return cheapest


def scaling_analysis_example():
    """Example of analyzing scaling options"""
    print("\n=== Scaling Analysis Example ===\n")
    
    validator = VGPUValidator()
    
    base_request = VGPURequest(
        model_name="Mistral-7B",
        vgpu_profile="L40-24Q",
        prompt_size=1024,
        response_size=256,
        n_concurrent_request=1
    )
    
    # Analyze scaling options
    scaling = validator.validate_scaling_options(base_request, scale_factors=[1, 2, 4, 8, 16])
    
    print("Scaling Options:")
    print(f"{'Scale':<8} {'GPU Config':<20} {'Throughput (tok/s)':<20} {'Monthly Cost':<15}")
    print("-" * 70)
    
    for option in scaling["scaling_options"]:
        if "error" not in option:
            gpu_config = f"{option['configuration']['gpu_name']} x{option['configuration']['num_gpus']}"
            throughput = option['performance']['throughput_tps']
            cost = option['cost_estimate']['monthly'] if option['cost_estimate'] else 0
            print(f"{option['scale_factor']}x{'':<6} {gpu_config:<20} "
                  f"{throughput:<20.2f} ${cost:<14,.2f}")
        else:
            print(f"{option['scale_factor']}x{'':<6} Error: {option['error']}")
    
    return scaling


def export_results_example(results: List[VGPUResult]):
    """Example of exporting results in various formats"""
    print("\n=== Export Results Example ===\n")
    
    # Export as JSON
    json_data = {
        "timestamp": "2024-01-01T12:00:00",
        "results": [result.dict() for result in results]
    }
    
    with open("vgpu_results.json", "w") as f:
        json.dump(json_data, f, indent=2)
    print("Results saved to vgpu_results.json")
    
    # Export as API response format
    api_responses = [result.to_api_response() for result in results]
    
    with open("vgpu_api_responses.json", "w") as f:
        json.dump(api_responses, f, indent=2)
    print("API responses saved to vgpu_api_responses.json")
    
    # Export as CSV (simplified)
    import csv
    with open("vgpu_results.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Model", "GPU", "Num GPUs", "Total Memory GB", 
                         "Max KV Tokens", "Throughput (tok/s)", "Latency (s)"])
        
        for result in results:
            writer.writerow([
                result.model,
                result.resultant_configuration.gpu_name,
                result.resultant_configuration.num_gpus,
                result.resultant_configuration.total_memory_gb,
                result.resultant_configuration.max_kv_tokens,
                result.performance_metrics.throughput_tokens_per_second
                if isinstance(result.performance_metrics.throughput_tokens_per_second, (int, float))
                else "N/A",
                result.performance_metrics.e2e_latency_seconds
                if isinstance(result.performance_metrics.e2e_latency_seconds, (int, float))
                else "N/A"
            ])
    print("Results saved to vgpu_results.csv")


def memory_analysis_example():
    """Example of memory footprint analysis"""
    print("\n=== Memory Analysis Example ===\n")
    
    calculator = VGPUCalculator()
    
    request = VGPURequest(
        prompt_size=2048,
        response_size=512,
        n_concurrent_request=4,
        quantization="fp16"
    )
    
    calculator.print_memory_analysis(request)
    
    # Also check OOM warnings
    print("\n")
    calculator.print_oom_warnings(request)


def main():
    """Run all examples"""
    print("vGPU Calculator Examples")
    print("=" * 50)
    
    # Collect results for export
    all_results = []
    
    # Run basic example
    result1 = basic_usage_example()
    all_results.append(result1)
    
    # Run batch processing
    batch_results = batch_processing_example()
    
    # Run custom model example
    result2 = custom_model_example()
    all_results.append(result2)
    
    # Run validation example
    validation_example()
    
    # Run cost optimization
    cost_optimization_example()
    
    # Run scaling analysis
    scaling_analysis_example()
    
    # Run memory analysis
    memory_analysis_example()
    
    # Export results
    export_results_example(all_results)
    
    print("\n" + "=" * 50)
    print("All examples completed!")


if __name__ == "__main__":
    main() 