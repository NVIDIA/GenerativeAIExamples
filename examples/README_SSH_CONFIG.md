# vGPU SSH Configuration

This feature allows you to apply vGPU configurations to remote VMs via SSH directly from the UI or programmatically.

## How it Works

1. **Frontend Form**: Users input VM credentials and the system generates a vGPU configuration
2. **Backend SSH Connection**: The backend connects to the VM using Paramiko (SSH library)
3. **Command Execution**: Configuration commands are executed on the remote host
4. **Real-time Feedback**: Progress and results are streamed back to the UI

## Usage

### From the UI

1. Generate a vGPU configuration using the chat interface
2. Click "Apply Configuration" in the configuration drawer
3. Fill in the form:
   - **VM IP Address**: The IP address of your target VM
   - **Username**: SSH username for the VM
   - **Password**: SSH password
   - **Hugging Face Token**: (Optional) For model downloads

### Programmatically

Use the example script:

```bash
# Test SSH connection only
python examples/vgpu_ssh_example.py test

# Apply full configuration
python examples/vgpu_ssh_example.py
```

### Via API

```python
import requests

payload = {
    "vm_ip": "10.185.118.36",
    "username": "your_username",
    "password": "your_password",
    "configuration": {
        "vGPU_profile": "L40S-24Q",
        "vCPU_count": 16,
        "system_RAM": 64,
        "gpu_memory_size": 24,
        "model_name": "Llama-3-8B"
    }
}

response = requests.post(
    "http://localhost:8081/v1/apply-configuration",
    json=payload,
    stream=True
)

# Process streaming response
for line in response.iter_lines():
    if line and line.startswith(b"data: "):
        data = json.loads(line[6:])
        print(data)
```

## Commands Executed

The system executes several types of commands:

1. **System Information**:
   - `hostname`
   - `uname -a`
   - `nvidia-smi`
   - `free -h`
   - `df -h`

2. **GPU Configuration**:
   - `nvidia-smi vgpu -q`
   - GPU profile verification

3. **Environment Checks**:
   - Docker installation
   - NVIDIA Docker runtime
   - Python/ML package availability

## Security Considerations

- **Credentials**: SSH credentials are transmitted over HTTPS (ensure SSL is enabled)
- **No Persistence**: Passwords are not stored; they're used only for the connection
- **Command Safety**: Only diagnostic and configuration commands are executed
- **Network Security**: Ensure VMs are accessible only from trusted networks

## Troubleshooting

### Connection Issues

1. **Authentication Failed**: 
   - Verify username and password
   - Check if SSH is enabled on the VM
   - Verify SSH port (default: 22)

2. **Timeout**:
   - Check network connectivity
   - Verify firewall rules
   - Increase timeout in configuration

3. **Command Failures**:
   - Ensure user has necessary permissions
   - Check if required tools (nvidia-smi, docker) are installed

### Example Error Messages

```
❌ Authentication failed: Invalid username or password
❌ Failed to connect to host: [Errno 113] No route to host
❌ SSH connection failed: timed out
```

## Requirements

### Backend
- Python 3.8+
- paramiko==3.4.0 (included in requirements.txt)

### Target VM
- SSH server enabled
- NVIDIA drivers installed (for GPU commands)
- User with appropriate permissions

## Future Enhancements

- [ ] SSH key authentication support
- [ ] Batch configuration for multiple VMs
- [ ] Configuration templates
- [ ] Rollback functionality
- [ ] Configuration validation before applying 