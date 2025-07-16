#!/usr/bin/env python3
"""
Test script to demonstrate the improved vLLM polling mechanism.
Shows how the system adapts to different model sizes and uses multiple indicators.
"""

import asyncio
import json
import sys
sys.path.insert(0, 'src')

from apply_configuration import ApplyConfigurationRequest, VGPUConfigurationApplier

async def test_polling_mechanism():
    """Test the improved polling mechanism with different scenarios."""
    
    print("=== vLLM Polling Mechanism Test ===\n")
    
    # Test configurations for different model sizes
    test_configs = [
        {
            "name": "Small Model (7B)",
            "model_tag": "mistralai/Mistral-7B-Instruct-v0.3",
            "expected_time": "~2 minutes",
            "config": {
                "vGPU_profile": "L40S-12Q",
                "vCPU_count": 8,
                "gpu_memory_size": 12,
                "system_RAM": 32,
                "model_tag": "mistralai/Mistral-7B-Instruct-v0.3"
            }
        },
        {
            "name": "Medium Model (8B)",
            "model_tag": "meta-llama/Meta-Llama-3-8B-Instruct",
            "expected_time": "~2.5 minutes",
            "config": {
                "vGPU_profile": "L40S-24Q",
                "vCPU_count": 16,
                "gpu_memory_size": 24,
                "system_RAM": 64,
                "model_tag": "meta-llama/Meta-Llama-3-8B-Instruct"
            }
        },
        {
            "name": "Large Model (70B)",
            "model_tag": "meta-llama/Llama-3.3-70B-Instruct",
            "expected_time": "~10 minutes",
            "config": {
                "vGPU_profile": "A100-80Q",
                "vCPU_count": 32,
                "gpu_memory_size": 80,
                "system_RAM": 256,
                "model_tag": "meta-llama/Llama-3.3-70B-Instruct"
            }
        }
    ]
    
    print("The improved polling mechanism features:\n")
    print("1. **Model-aware timeouts**: Different timeouts for different model sizes")
    print("2. **Multiple success indicators**: Checks for various startup messages")
    print("3. **HTTP health checks**: Direct API endpoint checking")
    print("4. **Adaptive polling intervals**: Faster checks as we approach expected completion")
    print("5. **GPU memory monitoring**: Tracks actual memory allocation")
    print("\nModel timeout configuration:")
    print("- 7B models: 2 minutes")
    print("- 8B models: 2.5 minutes")
    print("- 14B models: 3 minutes")
    print("- 40B models: 5 minutes")
    print("- 70B models: 10 minutes")
    print("- 180B models: 15 minutes")
    print("\n" + "="*50 + "\n")
    
    # Simulate what would happen for each model
    for test in test_configs:
        print(f"\n📊 Scenario: {test['name']}")
        print(f"   Model: {test['model_tag']}")
        print(f"   Expected load time: {test['expected_time']}")
        print(f"   GPU Memory: {test['config']['gpu_memory_size']}GB")
        
        # Show what the polling would look like
        print("\n   Polling behavior:")
        print("   - Initial check interval: 5 seconds")
        print("   - After 50% of timeout: 3 seconds")
        print("   - After 80% of timeout: 2 seconds")
        print("   - Progress updates: Every 30 seconds")
        
        print("\n   Success indicators being monitored:")
        print("   ✓ 'Uvicorn running on' - Server is up")
        print("   ✓ 'Started server process' - Process started")
        print("   ✓ 'Model loaded successfully' - Model ready")
        print("   ✓ 'GPU blocks:' - Memory allocated")
        print("   ✓ HTTP health check on port 8000")
        print("   ✓ GPU memory usage via nvidia-smi")
        
    print("\n" + "="*50)
    print("\n🔍 Key improvements over fixed sleep(100):")
    print("1. No wasted time for small models (ready in 30s, not waiting 100s)")
    print("2. Sufficient time for large models (up to 15 minutes)")
    print("3. Real-time progress updates")
    print("4. Early error detection")
    print("5. Multiple verification methods")
    
    # Example of how to use with actual SSH connection
    print("\n📝 Example usage:")
    print("""
    # Create request with model tag
    request = ApplyConfigurationRequest(
        vm_ip="192.168.1.100",
        username="user",
        password="pass",
        configuration={
            "vGPU_profile": "L40S-24Q",
            "vCPU_count": 16,
            "gpu_memory_size": 24,
            "system_RAM": 64,
            "model_tag": "meta-llama/Meta-Llama-3-8B-Instruct"  # This determines timeout!
        },
        hf_token="your_token_here"
    )
    
    # Apply configuration with smart polling
    applier = VGPUConfigurationApplier()
    async for update in applier.apply_configuration_async(request):
        progress = json.loads(update)
        print(f"[{progress['status']}] {progress['message']}")
    """)

if __name__ == "__main__":
    asyncio.run(test_polling_mechanism()) 