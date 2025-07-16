#!/usr/bin/env python3
"""
Test script to verify that model tags flow correctly from frontend to backend.
"""

import json
import re
import sys
sys.path.insert(0, 'src')

from apply_configuration import ApplyConfigurationRequest

def test_model_tag_extraction():
    """Test extracting model tag from various sources."""
    
    print("=== Testing Model Tag Extraction ===\n")
    
    # Test 1: Model tag in configuration
    print("Test 1: Model tag directly in configuration")
    config = {
        "vGPU_profile": "L40S-24Q",
        "vCPU_count": 8,
        "gpu_memory_size": 24,
        "system_RAM": 96,
        "model_tag": "meta-llama/Meta-Llama-3-8B-Instruct"
    }
    
    model_tag = config.get("model_tag") or config.get("modelTag")
    print(f"  Configuration: {json.dumps(config, indent=2)}")
    print(f"  Extracted model tag: {model_tag}")
    print(f"  ✓ Success: {model_tag == 'meta-llama/Meta-Llama-3-8B-Instruct'}\n")
    
    # Test 2: Model tag in embedded VGPU_CONFIG
    print("Test 2: Model tag in embedded VGPU_CONFIG")
    description = """
    I need a vGPU configuration for LLM Inference with small (< 7B parameters) 
    using available GPU inventory: 1x NVIDIA L40S running Llama-3-8B with prompt 
    size of 1024 tokens, response size of 256 tokens with FP16 precision.
    <!--VGPU_CONFIG:{"workloadType":"inference","specificModel":"llama-3-8b","modelTag":"meta-llama/Meta-Llama-3-8B-Instruct","modelSize":"small","batchSize":"","promptSize":1024,"responseSize":256,"embeddingModel":null,"gpuInventory":{"l40s":1},"precision":"fp16","selectedGPU":"l40s","gpuCount":1}-->
    """
    
    vgpu_config_match = re.search(r'<!--VGPU_CONFIG:(.*?)-->', description)
    model_tag = None
    if vgpu_config_match:
        try:
            config_data = json.loads(vgpu_config_match.group(1))
            model_tag = config_data.get("modelTag")
        except:
            pass
    
    print(f"  Description: {description[:100]}...")
    print(f"  Extracted model tag: {model_tag}")
    print(f"  ✓ Success: {model_tag == 'meta-llama/Meta-Llama-3-8B-Instruct'}\n")
    
    # Test 3: Model tag flow through ApplyConfigurationRequest
    print("Test 3: Model tag flow through ApplyConfigurationRequest")
    
    # Simulate the request that would come from frontend
    request_data = {
        "vm_ip": "192.168.1.100",
        "username": "testuser",
        "password": "testpass",
        "configuration": {
            "vGPU_profile": "L40S-24Q",
            "vCPU_count": 8,
            "gpu_memory_size": 24,
            "system_RAM": 96,
            "model_tag": "meta-llama/Llama-3.1-8B-Instruct"
        },
        "hf_token": "hf_test_token",
        "description": description
    }
    
    # Create the request object
    request = ApplyConfigurationRequest(**request_data)
    
    # Extract model tag the same way apply_configuration.py does
    model_tag = request.configuration.get("model_tag") or request.configuration.get("modelTag")
    
    # If not in configuration, check description
    if not model_tag and request.description:
        vgpu_config_match = re.search(r'<!--VGPU_CONFIG:(.*?)-->', request.description)
        if vgpu_config_match:
            try:
                config_data = json.loads(vgpu_config_match.group(1))
                model_tag = config_data.get("modelTag")
            except:
                pass
    
    print(f"  Request configuration: {json.dumps(request.configuration, indent=2)}")
    print(f"  Extracted model tag: {model_tag}")
    print(f"  ✓ Success: {model_tag == 'meta-llama/Llama-3.1-8B-Instruct'}\n")
    
    # Test 4: Model tag mapping
    print("Test 4: Frontend model selection to tag mapping")
    
    # This is the mapping from WorkloadConfigWizard.tsx
    model_mappings = {
        "llama-3-8b": "meta-llama/Meta-Llama-3-8B-Instruct",
        "llama-3-70b": "meta-llama/Meta-Llama-3-70B-Instruct",
        "llama-3.1-8b": "meta-llama/Llama-3.1-8B-Instruct",
        "llama-3.1-70b": "meta-llama/Llama-3.3-70B-Instruct",
        "mistral-7b": "mistralai/Mistral-7B-Instruct-v0.3",
        "falcon-7b": "tiiuae/falcon-7b-instruct",
        "falcon-40b": "tiiuae/falcon-40b-instruct",
        "falcon-180b": "tiiuae/falcon-180B",
        "qwen-14b": "Qwen/Qwen3-14B",
    }
    
    for selection, expected_tag in model_mappings.items():
        print(f"  {selection} -> {expected_tag}")
    
    print("\n=== All Tests Completed ===")

if __name__ == "__main__":
    test_model_tag_extraction() 