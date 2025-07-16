#!/usr/bin/env python3
"""
Example script demonstrating how to apply vGPU configuration via SSH
"""

import asyncio
import json
import requests
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8081/v1"  # Adjust to your server URL
VM_CONFIG = {
    "vm_ip": "10.185.118.36",  # Replace with your VM IP
    "username": "userone",      # Replace with your username
    "password": "root@123",     # Replace with your password
    "ssh_port": 22,
    "timeout": 30
}

# Example vGPU configuration
VGPU_CONFIG = {
    "vGPU_profile": "L40S-24Q",
    "vCPU_count": 16,
    "system_RAM": 64,
    "gpu_memory_size": 24,
    "model_name": "Llama-3-8B",
    "storage_capacity": 500,
    "storage_type": "SSD"
}


def apply_vgpu_configuration(vm_config: Dict[str, Any], vgpu_config: Dict[str, Any]):
    """Apply vGPU configuration to a remote VM via SSH."""
    
    # Prepare the request payload
    payload = {
        **vm_config,
        "configuration": vgpu_config
    }
    
    print(f"Applying vGPU configuration to {vm_config['vm_ip']}...")
    print(f"Configuration: {json.dumps(vgpu_config, indent=2)}")
    print("-" * 60)
    
    try:
        # Send POST request to apply configuration
        response = requests.post(
            f"{API_BASE_URL}/apply-configuration",
            json=payload,
            stream=True,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code != 200:
            print(f"Error: Server returned status {response.status_code}")
            print(response.text)
            return
        
        # Process the streaming response
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        
                        # Display status updates
                        if data.get("status"):
                            print(f"\n[{data['status'].upper()}] {data.get('message', '')}")
                        
                        # Display command results
                        if data.get("command_results"):
                            for result in data["command_results"]:
                                if result.get("command"):
                                    print(f"\n$ {result['command']}")
                                    if result.get("output"):
                                        print(result["output"])
                                    if result.get("error") and not result.get("success"):
                                        print(f"ERROR: {result['error']}")
                        
                        # Check for completion
                        if data.get("status") == "completed":
                            print("\n✅ Configuration applied successfully!")
                        elif data.get("status") == "error":
                            print(f"\n❌ Configuration failed: {data.get('error', 'Unknown error')}")
                            
                    except json.JSONDecodeError as e:
                        print(f"Error parsing response: {e}")
                        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the server. Make sure the RAG server is running.")
    except Exception as e:
        print(f"Error: {str(e)}")


def test_ssh_connection(vm_config: Dict[str, Any]):
    """Test SSH connection without applying configuration."""
    import paramiko
    
    print(f"Testing SSH connection to {vm_config['vm_ip']}...")
    
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(
            hostname=vm_config['vm_ip'],
            username=vm_config['username'],
            password=vm_config['password'],
            port=vm_config.get('ssh_port', 22),
            timeout=vm_config.get('timeout', 30)
        )
        
        # Run a simple command
        stdin, stdout, stderr = ssh.exec_command('hostname')
        hostname = stdout.read().decode().strip()
        
        print(f"✅ Successfully connected to: {hostname}")
        
        # Check GPU availability
        stdin, stdout, stderr = ssh.exec_command('nvidia-smi --query-gpu=name --format=csv,noheader')
        gpu_info = stdout.read().decode().strip()
        
        if gpu_info:
            print(f"GPU detected: {gpu_info}")
        else:
            print("No GPU detected or nvidia-smi not available")
            
        ssh.close()
        return True
        
    except Exception as e:
        print(f"❌ SSH connection failed: {str(e)}")
        return False


if __name__ == "__main__":
    print("vGPU SSH Configuration Example")
    print("=" * 60)
    
    # Test mode selection
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Just test the SSH connection
        test_ssh_connection(VM_CONFIG)
    else:
        # Apply the full configuration
        apply_vgpu_configuration(VM_CONFIG, VGPU_CONFIG)
        
    print("\nDone!") 