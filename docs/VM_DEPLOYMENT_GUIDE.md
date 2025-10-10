# VM Deployment Testing Guide

Complete guide for deploying and testing vLLM configurations on target VMs.

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Detailed Workflow](#detailed-workflow)
5. [Troubleshooting](#troubleshooting)

---

## Overview

The AI vWS Sizing Tool can automatically deploy vLLM servers to target VMs based on recommended configurations. This guide covers the complete deployment and testing process.

### What Gets Deployed

When you apply a configuration to a VM, the system:
1. ✅ Creates a Python virtual environment (`~/hf_env`)
2. ✅ Authenticates with HuggingFace (for model downloads)
3. ✅ Installs vLLM framework (if not already installed)
4. ✅ Starts vLLM server with optimized settings
5. ✅ Verifies GPU memory allocation
6. ✅ Tests API endpoint availability

---

## Prerequisites

### Target VM Requirements
- **OS**: Ubuntu 22.04 or 24.04
- **GPU**: NVIDIA L40S, L40, or similar (with vGPU profile configured)
- **GPU Driver**: 530.30.02 or later
- **CUDA**: 12.6 or later
- **Network**: SSH access (port 22)
- **Python**: 3.10 or later
- **Free GPU Memory**: Sufficient for your model (check with `nvidia-smi`)

### Access Requirements
- SSH credentials (username/password)
- HuggingFace API token (for gated models)
- Sudo access (for package installation)

---

## Quick Start

### Option 1: Pre-Install vLLM (Recommended)

**Save 10-15 minutes** by pre-installing vLLM on your target VM:

```bash
cd /home/nvadmin/Desktop/ai-vws-sizing-tool

# Pre-install vLLM on target VM
python3 scripts/pre_install_vllm.py <VM_IP> <username> <password>

# Example:
python3 scripts/pre_install_vllm.py 10.185.118.78 jaival MyPassword123
```

This script will:
- Create the Python virtual environment
- Install vLLM and all dependencies
- Verify the installation

**Then use the UI** for deployment (will be much faster).

### Option 2: UI Deployment (All-in-One)

1. Open UI: http://localhost:8090
2. Generate a configuration
3. Click "Apply Configuration"
4. Enter VM details:
   - **VM IP**: 10.185.118.78
   - **Username**: jaival
   - **Password**: ●●●●●●●●
   - **HuggingFace Token**: hf_xxxxx (optional)
5. Click "Deploy"
6. Wait 10-20 minutes for completion

---

## Detailed Workflow

### Step 1: Check Target VM

Before deployment, verify the VM is ready:

```bash
# SSH into your VM
ssh username@10.185.118.78

# Check GPU
nvidia-smi

# Check Python
python3 --version  # Should be 3.10+

# Check free memory
free -h

# Check disk space
df -h
```

**Expected GPU Output:**
```
+-----------------------------------------------------------------------------------------+
| NVIDIA-SMI 580.65.06              Driver Version: 580.65.06      CUDA Version: 13.0     |
+-----------------------------------------+------------------------+----------------------+
| GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
| Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
|=========================================+========================+======================|
|   0  NVIDIA L40S                    Off |   00000000:03:00.0 Off |                    0 |
| N/A   38C    P0             82W /  350W |     1472MiB /  46068MiB |      0%      Default |
+-----------------------------------------+------------------------+----------------------+
```

**Good**: <2GB GPU memory used, 40GB+ free
**Bad**: >30GB already used (orphaned processes)

### Step 2: Clean Up Orphaned Processes (If Needed)

If GPU memory is mostly used:

```bash
# Kill any orphaned vLLM processes
pkill -9 -f 'vllm'
pkill -9 -f 'VLLM::EngineCore'

# Wait for GPU memory to be released
sleep 5

# Verify cleanup
nvidia-smi
```

### Step 3: Pre-Install vLLM (Optional but Recommended)

From your local machine:

```bash
cd /home/nvadmin/Desktop/ai-vws-sizing-tool
python3 scripts/pre_install_vllm.py 10.185.118.78 jaival YourPassword
```

**Expected Output:**
```
============================================================
🚀 vLLM Pre-Installation Tool
============================================================
Target VM: 10.185.118.78
Username: jaival
============================================================

🔗 Connecting to 10.185.118.78...
✅ Connected successfully

📦 Step 1: Creating Python virtual environment...
🐍 Python version: 3.10
✅ Virtual environment already exists

📦 Step 2: Checking vLLM installation status...
❌ vLLM not installed

📦 Step 3: Installing vLLM (this will take 10-15 minutes)...
   ⏳ Please wait, this is a one-time setup...
   📥 Downloading and installing packages...
   Downloading vllm-0.6.4-cp310-cp310-linux_x86_64.whl (205.3 MB)
   ...
   Successfully installed vllm-0.6.4

✅ vLLM installed successfully in 847s (14m 7s)
   Version: 0.6.4

🔌 Connection closed

============================================================
✅ Pre-installation completed successfully!
============================================================
```

### Step 4: Deploy via UI

1. **Access UI**: http://localhost:8090

2. **Generate Configuration**:
   - Workload: LLM Inference / RAG / Training
   - GPU Inventory: 1x NVIDIA L40S
   - Model: Llama 3.1 8B
   - Precision: FP16
   - Prompt/Response sizes

3. **Apply Configuration**:
   - Click "Apply Configuration" button
   - Fill in VM details
   - Add HuggingFace token (for Llama access)
   - Click "Deploy"

4. **Monitor Progress**:
   ```
   ✅ SSH connection established
   ✅ System identified: VMware on Linux
   ✅ GPU verified: NVIDIA L40S
   ✅ HuggingFace authentication successful
   ✅ vLLM already installed (or installing...)
   ⏳ Starting vLLM server...
   ⏳ Optimizing GPU memory allocation...
   ✅ vLLM server started successfully!
   ```

### Step 5: Verify Deployment

After successful deployment, verify on the target VM:

```bash
# Check vLLM is running
ps aux | grep vllm

# Check GPU memory usage
nvidia-smi

# Test vLLM API
curl http://localhost:8000/health

# Test inference
curl -X POST http://localhost:8000/v1/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "prompt": "Hello, how are you?",
    "max_tokens": 50
  }'
```

**Expected Health Check Response:**
```json
{
  "status": "healthy",
  "model_name": "meta-llama/Llama-3.1-8B-Instruct"
}
```

---

## Troubleshooting

### Issue 1: Network Error / Timeout

**Symptoms:**
```
❌ Error: network error
Debug Output: Installing vLLM (this may take several minutes)...
```

**Root Cause:** vLLM installation takes too long (10-15 min) and connection times out.

**Solution:**
1. Pre-install vLLM using the script (Option 1 in Quick Start)
2. Or wait for the new async installation (now implemented)
3. Check backend logs: `docker logs rag-server --tail 50`

### Issue 2: GPU Memory Full

**Symptoms:**
```
ValueError: Free memory on device (4.34/44.39 GiB) is less than required (37.73 GiB)
```

**Root Cause:** Orphaned vLLM process from previous attempt consuming GPU memory.

**Solution:**
```bash
# SSH into VM
ssh username@vm_ip

# Kill all vLLM processes
pkill -9 -f 'vllm'
pkill -9 -f 'VLLM::EngineCore'
pkill -9 -f 'python.*vllm'

# Wait and verify
sleep 5
nvidia-smi
```

### Issue 3: HuggingFace Authentication Failed

**Symptoms:**
```
❌ Error: Failed to authenticate with HuggingFace
```

**Solution:**
1. Get a valid HuggingFace token: https://huggingface.co/settings/tokens
2. Ensure token has permissions:
   - ✅ Read access to public gated repos
   - ✅ Read access to repos under your namespace
3. Accept Llama model license: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct

### Issue 4: SSH Connection Failed

**Symptoms:**
```
❌ Error: SSH connection failed
```

**Solution:**
1. Verify SSH access: `ssh username@vm_ip`
2. Check firewall rules (port 22)
3. Verify credentials
4. Check SSH service: `sudo systemctl status ssh`

### Issue 5: vLLM Crashes During Startup

**Symptoms:**
```
RuntimeError: Engine core initialization failed
```

**Solutions:**

**A) Insufficient GPU Memory:**
- Reduce model size
- Use quantized model (e.g., AWQ, GPTQ)
- Decrease `max_model_len`
- Lower `gpu_memory_utilization`

**B) CUDA/Driver Issues:**
```bash
# Check CUDA
nvidia-smi

# Reinstall GPU driver if needed
sudo apt update
sudo apt install --reinstall nvidia-driver-530
sudo reboot
```

**C) Model Not Found:**
```bash
# Check HuggingFace authentication
cd ~/hf_env
source bin/activate
huggingface-cli whoami

# Re-authenticate if needed
huggingface-cli login --token YOUR_TOKEN
```

### Issue 6: Slow Performance

**Symptoms:** vLLM starts but inference is slow.

**Optimizations:**

1. **Increase GPU Utilization**:
   - System tries 0.75, 0.80, 0.85, 0.90
   - Higher = more memory for KV cache = faster

2. **Enable Flash Attention**:
   ```bash
   vllm serve model --enable-chunked-prefill
   ```

3. **Optimize Batch Size**:
   - Default: `--max-num-seqs 1`
   - Increase for throughput: `--max-num-seqs 256`

4. **Check CPU**:
   ```bash
   htop  # CPU usage should be <50%
   ```

---

## Advanced: Manual Deployment

If UI deployment fails, you can manually deploy:

```bash
# 1. SSH into VM
ssh username@vm_ip

# 2. Create venv
python3 -m venv ~/hf_env
source ~/hf_env/bin/activate

# 3. Install vLLM
pip install vllm

# 4. Authenticate HuggingFace
pip install huggingface-hub
huggingface-cli login --token YOUR_TOKEN

# 5. Start vLLM
vllm serve meta-llama/Llama-3.1-8B-Instruct \
  --host 0.0.0.0 \
  --port 8000 \
  --max-model-len 2048 \
  --gpu-memory-utilization 0.85 \
  --dtype float16

# 6. Test
curl http://localhost:8000/health
```

---

## Performance Benchmarks

| Model | GPU | Memory | TTFT | Throughput |
|-------|-----|--------|------|------------|
| Llama 3.1 8B | L40S-24Q | 22GB | 0.12s | 26.7 tok/s |
| Mistral 7B | L40S-20Q | 18GB | 0.10s | 31.2 tok/s |
| Llama 3.3 70B | L40S-48Q x2 | 140GB | 0.45s | 12.4 tok/s |

---

## Next Steps

After successful deployment:

1. **Test Inference**: Use the vLLM API for inference
2. **Monitor Performance**: Track GPU usage, latency, throughput
3. **Scale Up**: Deploy to additional VMs as needed
4. **Integrate**: Connect to your application via OpenAI-compatible API

For questions or issues, check:
- Backend logs: `docker logs rag-server --tail 100`
- Frontend logs: Check browser console
- VM logs: `/tmp/vllm_8000.log` on target VM

---

## Summary

**Fastest Path to Success:**
1. Run `pre_install_vllm.py` on your target VM (one-time, 15 min)
2. Use UI to deploy configurations (< 2 min after pre-install)
3. Verify with `nvidia-smi` and API health check
4. Start inference testing

**Key Points:**
- ✅ Pre-installation saves 10-15 minutes per deployment
- ✅ Clean up orphaned processes before new deployments  
- ✅ Ensure 40GB+ free GPU memory before starting
- ✅ Use HuggingFace token for gated models (Llama, etc.)
- ✅ Monitor `/tmp/vllm_install.log` for installation progress

Good luck with your deployments! 🚀

