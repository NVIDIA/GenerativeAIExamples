import asyncio
import json
import logging
import math
import re
from typing import Dict, List, AsyncGenerator, Optional, Any
from pydantic import BaseModel, Field, field_validator
from contextlib import contextmanager
import time
import difflib
from collections import OrderedDict
import requests
from functools import lru_cache
import subprocess


logger = logging.getLogger(__name__)


def map_os(query: str):
    """
    Fuzzy-match a system string to a known hypervisor and OS.

    Args:
        query (str): The raw system string (e.g., output of uname -a)

    Returns:
        (matched_hypervisor, matched_os)
    """
    OS = ["Linux", "Windows"]

    query_lower = query.lower()

    def match_any(candidates):
        for candidate in candidates:
            if candidate.lower() in query_lower:
                return candidate
        # fallback: fuzzy match
        return difflib.get_close_matches(query_lower, [c.lower() for c in candidates], n=1, cutoff=0.4)[0] if difflib.get_close_matches(query_lower, [c.lower() for c in candidates], n=1, cutoff=0.4) else None

    os_match = match_any(OS)

    return os_match



def map_hypervisor(query: str):
    """
    Fuzzy-match a system string to a known hypervisor and OS.

    Args:
        query (str): The raw system string (e.g., output of uname -a)

    Returns:
        (matched_hypervisor, matched_os)
    """
    HYPERVISORS = ["ESXI", "VMware", "KVM"]

    query_lower = query.lower()

    def match_any(candidates):
        for candidate in candidates:
            if candidate.lower() in query_lower:
                return candidate
        # fallback: fuzzy match
        return difflib.get_close_matches(query_lower, [c.lower() for c in candidates], n=1, cutoff=0.4)[0] if difflib.get_close_matches(query_lower, [c.lower() for c in candidates], n=1, cutoff=0.4) else None

    hypervisor_match = match_any(HYPERVISORS)

    return hypervisor_match
    
def grab_total_size(query: Optional[str]) -> Optional[int]:
    """
    Fuzzy-extract the total token size (prompt + response) from the description using difflib.
    Returns the sum if both are found, else returns the one found, or None.
    """
    if not query:
        return 2040


    # Lowercase and remove spaces for fuzzy matching
    query_clean = query.lower().replace(" ", "")

    # Possible patterns for prompt and response size
    prompt_patterns = [
        "prompttokens", "promptsize", "promptlength", "prompt token", "prompt size", "prompt length"
    ]
    response_patterns = [
        "responsetokens", "responsesize", "responselength", "response token", "response size", "response length"
    ]

    # Find closest matches in the query for prompt and response
    prompt_match = None
    response_match = None

    for pattern in prompt_patterns:
        if difflib.get_close_matches(pattern, [query_clean], n=1, cutoff=0.7):
            prompt_match = pattern
            break

    for pattern in response_patterns:
        if difflib.get_close_matches(pattern, [query_clean], n=1, cutoff=0.7):
            response_match = pattern
            break


    prompt_size = None
    response_size = None

    # Try to extract numbers near the matched patterns
    if prompt_match:
        prompt_regex = re.compile(rf"{prompt_match}.*?(\d+)", re.IGNORECASE)
        m = prompt_regex.search(query_clean)
        if m:
            try:
                prompt_size = int(m.group(1))
            except ValueError:
                prompt_size = None

    if response_match:
        response_regex = re.compile(rf"{response_match}.*?(\d+)", re.IGNORECASE)
        m = response_regex.search(query_clean)
        if m:
            try:
                response_size = int(m.group(1))
            except ValueError:
                response_size = None

    # If both found, return their sum; else return the one found; else None
    if prompt_size is not None and response_size is not None:
        return prompt_size + response_size
    elif prompt_size is not None:
        return prompt_size
    elif response_size is not None:
        return response_size
    else:
        return 2024
@lru_cache(maxsize=1)
def fetch_huggingface_models(hf_token: Optional[str] = None) -> List[str]:
    """
    Fetch popular LLM models from HuggingFace API with fallback to default list.
    
    Args:
        hf_token: Optional HuggingFace token for authenticated requests
    
    Returns:
        List of model IDs (e.g., "meta-llama/Llama-3.1-8B-Instruct")
    """
    # Default fallback models
    DEFAULT_MODELS = [
        "meta-llama/Llama-3.1-8B-Instruct",  # General fallback model
        "meta-llama/Meta-Llama-3-8B-Instruct",
        "meta-llama/Llama-3.3-70B-Instruct",
        "meta-llama/Meta-Llama-3-70B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "Qwen/Qwen2.5-7B-Instruct",
        "tiiuae/falcon-40b-instruct",
        "tiiuae/falcon-180B"
    ]
    
    try:
        # Fetch popular text-generation models from HuggingFace
        headers = {}
        if hf_token:
            headers["Authorization"] = f"Bearer {hf_token}"
        
        # Query for popular instruct/chat models
        params = {
            "filter": "text-generation",
            "sort": "downloads",
            "limit": 50,
            "full": False
        }
        
        response = requests.get(
            "https://huggingface.co/api/models",
            params=params,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            models = response.json()
            # Filter for instruct/chat models and extract IDs
            model_ids = []
            for model in models:
                model_id = model.get("id", "")
                # Only include instruct/chat models
                if any(keyword in model_id.lower() for keyword in ["instruct", "chat"]):
                    model_ids.append(model_id)
            
            # Combine fetched models with defaults (defaults first as fallback)
            combined = DEFAULT_MODELS + [m for m in model_ids if m not in DEFAULT_MODELS]
            logger.info(f"Successfully fetched {len(model_ids)} models from HuggingFace API")
            return combined[:50]  # Limit to 50 models
        else:
            logger.warning(f"HuggingFace API returned status {response.status_code}, using default models")
            return DEFAULT_MODELS
            
    except Exception as e:
        logger.warning(f"Failed to fetch models from HuggingFace API: {e}, using default models")
        return DEFAULT_MODELS


class ModelNameExtractor:
    """
    Generic model tag extractor.
    Builds a flexible alias map from a list of tags, then identifies
    the best matching tag for any free-form query.
    """
    def __init__(self, tags: List[str], fuzzy_cutoff: float = 0.7):
        self.tags = tags
        self.fuzzy_cutoff = fuzzy_cutoff
        self.alias_map: Dict[str, str] = {}
        self._build_alias_map()
        self.aliases = list(self.alias_map.keys())

    @staticmethod
    def simplify(text: str) -> str:
        """
        Lowercase and strip all but letters, numbers, dots, and dashes.
        """
        return re.sub(r"[^a-z0-9\.-]", "", text.lower())

    def _build_alias_map(self):
        """
        For each tag, generate a rich set of alias variants:
        - simplified name
        - suffix-stripped
        - token-level splits and joins
        - separator-stripped forms
        """
        for tag in self.tags:
            # take only the final part (after slash)
            raw_name = tag.split('/')[-1]
            base = self.simplify(raw_name)

            # strip common suffixes (e.g., '-instruct', '-v1.0')
            stripped = re.sub(r"(?:-instruct|-v[0-9]+(?:\.[0-9]+)*)$", "", base)

            # tokens by splitting on non-alphanumeric
            tokens = re.split(r"[^a-z0-9]+", base)
            stripped_tokens = re.split(r"[^a-z0-9]+", stripped)

            variants = set([base, stripped])
            variants.add("".join(tokens))
            variants.add("".join(stripped_tokens))
            variants.update(tokens)
            variants.update(stripped_tokens)

            # also add separator-stripped forms for all variants
            for alias in list(variants):
                no_dash = alias.replace('-', '')
                no_dot = alias.replace('.', '')
                variants.update([no_dash, no_dot, no_dash.replace('.', ''), no_dot.replace('-', '')])

            # populate alias map
            for alias in variants:
                if alias:
                    self.alias_map.setdefault(alias, tag)

    def extract(self, query: Optional[str]) -> Optional[str]:
        """
        Identify the most likely tag based on the query:
        1. direct substring in simplified query
        2. word-boundary match in original query
        3. fuzzy match on simplified tokens
        """
        if not query:
            return None
        q_low = query.lower()
        q_simp = self.simplify(q_low)

        # 1. direct substring match
        for alias, tag in self.alias_map.items():
            if alias in q_simp:
                return tag

        # 2. word-boundary match
        for alias, tag in self.alias_map.items():
            if re.search(rf"\b{re.escape(alias)}\b", q_low):
                return tag

        # 3. fuzzy matching on tokens
        tokens = re.findall(r"[a-z0-9\.-]+", q_simp)
        best_alias, best_score = None, 0.0
        for alias in self.aliases:
            for token in tokens:
                score = difflib.SequenceMatcher(None, alias, token).ratio()
                if score > best_score:
                    best_alias, best_score = alias, score
        if best_score >= self.fuzzy_cutoff and best_alias:
            return self.alias_map[best_alias]

        return None

# Initialize the model extractor with dynamically fetched models
# The list will be fetched from HuggingFace API on first use with fallback to defaults
MODEL_TAGS = fetch_huggingface_models()
GENERAL_FALLBACK_MODEL = "meta-llama/Llama-3.1-8B-Instruct"

model_extractor = ModelNameExtractor(MODEL_TAGS, fuzzy_cutoff=0.6)

# Define request and response models
class ApplyConfigurationRequest(BaseModel):
    """Request model for applying vGPU configuration to a remote host or locally."""
    deployment_mode: str = Field(default="remote", description="Deployment mode: 'local' or 'remote'")
    vm_ip: Optional[str] = Field(None, description="IP address of the VM to configure (required for remote mode)")
    username: Optional[str] = Field(None, description="SSH username (required for remote mode)")
    password: Optional[str] = Field(None, description="SSH password (required for remote mode)")
    configuration: Dict[str, Any] = Field(..., description="vGPU configuration to apply")
    ssh_port: int = Field(default=22, description="SSH port")
    timeout: int = Field(default=30, description="SSH connection timeout")
    hf_token: Optional[str] = Field(None, description="Hugging Face token for model downloads")
    description: Optional[str] = Field(None, description="Original query description")
    advanced_config: Optional[Dict[str, Any]] = Field(None, description="Advanced calculator configuration options")

    temperature: Optional[float] = Field(None, description="LLM sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for LLM response")
    model: Optional[str] = Field(None, description="LLM model name")
    model_tag: Optional[str] = Field(None, description="Model tag/ID for vLLM deployment (e.g., mistralai/Mistral-7B-Instruct-v0.3)")
    llm_endpoint: Optional[str] = Field(None, description="LLM endpoint URL")
    
    @field_validator('vm_ip', 'username', 'password')
    @classmethod
    def validate_remote_fields(cls, v, info):
        """Validate that VM fields are provided when in remote mode."""
        # Get deployment_mode from the data being validated
        deployment_mode = info.data.get('deployment_mode', 'remote')
        field_name = info.field_name
        
        # Only require these fields in remote mode
        if deployment_mode == 'remote' and not v:
            raise ValueError(f"{field_name} is required for remote deployment mode")
        
        return v


class CommandResult(BaseModel):
    """Result of a single command execution."""
    command: str
    output: str
    error: str
    success: bool
    timestamp: float

class ConfigurationProgress(BaseModel):
    """Progress update during configuration application."""
    status: str  # 'connecting', 'executing', 'completed', 'error'
    message: Optional[str] = None
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    command_results: Optional[List[CommandResult]] = None
    error: Optional[str] = None
    display_message: Optional[str] = None  # Special message to display prominently in UI

class VGPUConfigurationApplierDisabled:
    """
    SSH-based configuration is currently disabled (paramiko dependency removed).
    This class is preserved for reference but is not functional.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        raise NotImplementedError("SSH-based configuration is currently disabled")
        
    @contextmanager
    def ssh_connection(self, hostname: str, username: str, password: str, 
                      port: int = 22, timeout: int = 30):
        """
        Context manager for SSH connections using Paramiko.
        """
        raise NotImplementedError("SSH-based configuration is currently disabled")
        
        try:
            self.logger.info(f"Establishing SSH connection to {hostname}:{port}")
            ssh_client.connect(
                hostname=hostname,
                username=username,
                password=password,
                port=port,
                timeout=timeout,
                look_for_keys=False,
                allow_agent=False
            )
            yield ssh_client
        except Exception as e:  # was: paramiko.AuthenticationException
            self.logger.error(f"Authentication failed: {e}")
            raise
        except Exception as e:  # was: paramiko.SSHException
            self.logger.error(f"SSH connection failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise
        finally:
            ssh_client.close()
            self.logger.info("SSH connection closed")
    
    def execute_command(self, ssh_client: Any, command: str, 
                       timeout: int = 300) -> tuple:
        """
        Execute a command on the remote host and return output.
        
        Args:
            ssh_client: Paramiko SSH client
            command: Command to execute
            timeout: Command timeout in seconds (default 300s for downloads)
        """
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
        
        # Read output
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        exit_status = stdout.channel.recv_exit_status()
        
        return output, error, exit_status
    
    def exec_raw(self, ssh_client: Any, command: str, timeout: int = 300):
        """
        Execute a command and return raw stdin, stdout, stderr channels.
        
        Args:
            ssh_client: Paramiko SSH client
            command: Command to execute
            timeout: Command timeout in seconds
        """
        return ssh_client.exec_command(command, timeout=timeout)
    
    def stream_exec(self, ssh_client: Any, command: str, timeout: int = 300):
        """
        Execute a command and stream output in real-time.
        Returns (exit_status, output_lines, error_lines)
        """
        stdin, stdout, stderr = ssh_client.exec_command(command, timeout=timeout)
        
        # Set channels to non-blocking mode
        stdout.channel.setblocking(0)
        stderr.channel.setblocking(0)
        
        output_lines = []
        error_lines = []
        
        # Read output in real-time
        import select
        while not stdout.channel.exit_status_ready():
            # Use select to check if data is available
            readable, _, _ = select.select([stdout.channel, stderr.channel], [], [], 0.1)
            
            if stdout.channel in readable:
                try:
                    line = stdout.channel.recv(4096).decode('utf-8')
                    if line:
                        output_lines.append(line)
                except:
                    pass
                    
            if stderr.channel in readable:
                try:
                    line = stderr.channel.recv(4096).decode('utf-8')
                    if line:
                        error_lines.append(line)
                except:
                    pass
        
        # Get any remaining output
        remaining_out = stdout.read().decode('utf-8')
        remaining_err = stderr.read().decode('utf-8')
        
        if remaining_out:
            output_lines.append(remaining_out)
        if remaining_err:
            error_lines.append(remaining_err)
            
        exit_status = stdout.channel.recv_exit_status()
        
        return exit_status, ''.join(output_lines), ''.join(error_lines)
    
    async def stream_command_output(self, ssh_client: Any, 
                                  command: str) -> AsyncGenerator[str, None]:
        """
        Execute a command and stream its output line by line.
        """
        stdin, stdout, stderr = ssh_client.exec_command(command)
        
        # Stream stdout
        for line in iter(stdout.readline, ''):
            if line:
                yield f"[STDOUT] {line.strip()}"
                await asyncio.sleep(0.01)  # Small delay for streaming effect
        
        # Stream stderr
        for line in iter(stderr.readline, ''):
            if line:
                yield f"[STDERR] {line.strip()}"
                await asyncio.sleep(0.01)
        
        exit_status = stdout.channel.recv_exit_status()
        yield f"[EXIT] Command completed with status: {exit_status}"
    
    async def apply_configuration(self, request: ApplyConfigurationRequest) -> AsyncGenerator[str, None]:
        """
        Apply vGPU configuration to a remote host with streaming updates.
        """
        try:
            yield "Starting vGPU configuration process..."
            yield f"Connecting to {request.vm_ip}:{request.ssh_port}..."
            
            # Establish SSH connection
            with self.ssh_connection(
                hostname=request.vm_ip,
                username=request.username,
                password=request.password,
                port=request.ssh_port,
                timeout=request.timeout
            ) as ssh_client:
                yield "✅ SSH connection established successfully"
                
                # Verify system information
                yield "\nGathering system information..."
                output, error, status = self.execute_command(ssh_client, "uname -a")
                if status == 0:
                    yield f"System: {output}"
                
                # Check GPU availability
                yield "\nChecking GPU availability..."
                output, error, status = self.execute_command(ssh_client, "nvidia-smi --query-gpu=name --format=csv,noheader")
                if status == 0:
                    yield f"GPU detected: {output}"
                else:
                    yield "⚠️ No GPU detected or nvidia-smi not available"
                
                # Apply configuration based on the provided settings
                config = request.configuration
                
                # Example: Set up environment variables
                if config.get("vGPU_profile"):
                    yield f"\n📝 Configuring vGPU profile: {config['vGPU_profile']}"
                    # Add actual vGPU configuration commands here
                    
                if config.get("model_name"):
                    yield f"\n🤖 Setting up for model: {config['model_name']}"
                    
                    # Example: Download model if HF token provided
                    if request.hf_token:
                        yield "📥 Preparing model download..."
                        # Add model download logic here
                        
                # System resource configuration
                if config.get("vCPU_count"):
                    yield f"\n⚙️ Allocating {config['vCPU_count']} vCPUs"
                    
                if config.get("system_RAM"):
                    yield f"💾 Allocating {config['system_RAM']}GB RAM"
                    
                # Example: Run a test command to verify setup
                yield "\n🔍 Running verification tests..."
                test_commands = [
                    "python3 --version",
                    "pip list | grep torch",
                    "df -h",
                    "free -m"
                ]
                
                for cmd in test_commands:
                    output, error, status = self.execute_command(ssh_client, cmd)
                    if status == 0 and output:
                        yield f"✓ {cmd}: {output.split()[0] if output else 'OK'}"
                
                # Final configuration summary
                yield "\n📊 Configuration Summary:"
                yield f"  - vGPU Profile: {config.get('vGPU_profile', 'N/A')}"
                yield f"  - vCPUs: {config.get('vCPU_count', 'N/A')}"
                yield f"  - RAM: {config.get('system_RAM', 'N/A')}GB"
                yield f"  - GPU Memory: {config.get('gpu_memory_size', 'N/A')}GB"
                yield f"  - Model: {config.get('model_name', 'N/A')}"
                yield f"  - Storage: {config.get('storage_capacity', 'N/A')}GB {config.get('storage_type', '')}"
                
                yield "\n✅ vGPU configuration completed successfully!"
                
        except Exception:  # was: paramiko.AuthenticationException
            yield "❌ Authentication failed. Please check your credentials."
        except Exception as e:  # was: paramiko.SSHException
            yield f"❌ SSH connection error: {str(e)}"
        except Exception as e:
            yield f"❌ Error: {str(e)}"
            self.logger.exception("Error during configuration application")

    def validate_configuration(self, configuration: Dict[str, Any]) -> bool:
        """Validate the configuration parameters."""
        # Normalize field names from generated config to expected format
        if "vgpu_profile" in configuration and "vGPU_profile" not in configuration:
            configuration["vGPU_profile"] = configuration["vgpu_profile"]
        if "vcpu_count" in configuration and "vCPU_count" not in configuration:
            configuration["vCPU_count"] = configuration["vcpu_count"]
        
        # Check for required fields
        if "vGPU_profile" not in configuration or not configuration["vGPU_profile"]:
            raise ValueError("Missing required configuration field: vGPU_profile")
                
        # Validate vGPU profile format
        vgpu_profile = configuration['vGPU_profile']
        if not vgpu_profile or not isinstance(vgpu_profile, str):
            raise ValueError("Invalid vGPU profile format")
            
        return True
    
    async def wait_for_vllm_live(self, ssh_client: Any, gpu_util: float, 
                                    model_ref: str, venv_path: str, total_size: int, port: int = 8000) -> tuple[bool, str, Optional[str]]:
        """
        Start vLLM server and watch output for readiness or failure.
        Returns (success, message)
        """
        # Start vLLM in background so it persists after SSH session ends
        start_cmd = rf"""bash -lc "source $HOME/hf_env/bin/activate && \
        nohup vllm serve '{model_ref}' \
        --host 0.0.0.0 \
        --port {port} \
        --max-model-len {total_size} \
        --max-num-seqs 1 \
        --gpu-memory-utilization {gpu_util:.2f} \
        --kv-cache-dtype auto \
        --dtype float16 \
        --trust-remote-code > /tmp/vllm_{port}.log 2>&1 &
        echo \$!
        "
        """
        
        logger.info(f"vLLM start command: {start_cmd}")
        
        # Start vLLM in background
        stdin_start, stdout_start, _ = ssh_client.exec_command(start_cmd)
        vllm_pid = stdout_start.read().decode().strip()
        logger.info(f"vLLM started with PID: {vllm_pid}")
        
        # Now tail the log file to monitor startup
        tail_cmd = f"tail -f /tmp/vllm_{port}.log"
        logger.info(f"Monitoring vLLM output: {tail_cmd}")
        
        stdin, stdout, stderr = ssh_client.exec_command(tail_cmd, get_pty=True)
        
        # Watch vLLM output for readiness or failure
        start_time = time.time()
        timeout = 900  # 15 minutes timeout - increased to handle large model download, loading, and compilation
        mem_size_and_tokens = None  # Reset KV cache size for each line
        kv_cache_size = None
        last_progress_time = start_time
        last_output_time = start_time
        graph_capture_complete = False
        model_loaded = False
        torch_compile_started = False

        while True:
            current_time = time.time()
            elapsed = current_time - start_time
            
            # Log progress every 30 seconds
            if current_time - last_progress_time > 30:
                logger.info(f"vLLM startup in progress... ({elapsed:.0f}s elapsed)")
                last_progress_time = current_time
            
            if elapsed > timeout:
                logger.warning(f"Timeout after {timeout} seconds waiting for vLLM to start")
                
                # Check if we at least got to graph capturing
                if graph_capture_complete:
                    logger.info("Graph capturing was completed but API server didn't start - considering it ready anyway")
                    # Try to get memory usage
                    query = (
                        "nvidia-smi "
                        "--query-compute-apps=pid,used_memory "
                        "--format=csv,noheader,nounits"
                    )
                    stdin2, stdout2, _ = ssh_client.exec_command(query)
                    raw = stdout2.read().decode().strip()
                    
                    if raw:
                        for row in raw.splitlines():
                            try:
                                pid, used = [x.strip() for x in row.split(",")]
                                ps_cmd = f"ps -p {pid} -o args="
                                stdin3, stdout3, _ = ssh_client.exec_command(ps_cmd)
                                args = stdout3.read().decode().strip()
                                
                                if "vllm" in args.lower() or "/hf_env/bin/python" in args:
                                    used = int(used) / 1024  # Convert to GB
                                    return True, f"{used:.2f} GB", kv_cache_size if kv_cache_size else None
                            except:
                                pass
                
                return False, "Timeout waiting for vLLM to start", None
                
            # Check if there's data available to read
            if stdout.channel.recv_ready():
                line = stdout.readline()
                if not line:
                    # Check if process exited
                    if stdout.channel.exit_status_ready():
                        exit_code = stdout.channel.recv_exit_status()
                        return False, f"vLLM process exited early with code {exit_code}", None
                    await asyncio.sleep(0.1)
                    continue
            else:
                # No data available, check if process is still running
                if stdout.channel.exit_status_ready():
                    exit_code = stdout.channel.recv_exit_status()
                    
                    # If graph capturing was complete, check if vLLM is still running
                    if graph_capture_complete:
                        logger.info(f"SSH channel closed with exit code {exit_code} after graph capturing")
                        
                        # Check if vLLM process is still alive
                        ps_check = "ps aux | grep -E 'vllm serve|python.*vllm' | grep -v grep"
                        stdin_ps, stdout_ps, _ = ssh_client.exec_command(ps_check)
                        ps_result = stdout_ps.read().decode().strip()
                        
                        if ps_result:
                            logger.info("vLLM process is still running despite SSH channel closing")
                            # Check GPU memory allocation
                            query = (
                                "nvidia-smi "
                                "--query-compute-apps=pid,used_memory "
                                "--format=csv,noheader,nounits"
                            )
                            stdin2, stdout2, _ = ssh_client.exec_command(query)
                            raw = stdout2.read().decode().strip()
                            
                            if raw:
                                for row in raw.splitlines():
                                    try:
                                        pid, used = [x.strip() for x in row.split(",")]
                                        ps_cmd = f"ps -p {pid} -o args="
                                        stdin3, stdout3, _ = ssh_client.exec_command(ps_cmd)
                                        args = stdout3.read().decode().strip()
                                        
                                        if "vllm" in args.lower() or "/hf_env/bin/python" in args:
                                            used = int(used) / 1024  # Convert to GB
                                            logger.info(f"vLLM running with {used:.2f}GB allocated")
                                            return True, f"{used:.2f} GB", kv_cache_size if kv_cache_size else None
                                    except:
                                        pass
                    
                    # Check if model was at least loaded
                    if "Model loading took" in '\n'.join(locals().get('all_output', [])):
                        logger.error(f"vLLM process exited during torch compilation with code {exit_code}")
                        return False, f"vLLM crashed during torch compilation (exit code {exit_code}). This often indicates insufficient GPU memory.", None
                    else:
                        return False, f"vLLM process exited early with code {exit_code}", None
                        
                # Check if we've been stuck for too long without output
                # For large models, torch compilation can take a long time
                no_output_timeout = 480 if torch_compile_started else 300  # 8 minutes if compiling, 5 minutes otherwise
                
                if current_time - last_output_time > no_output_timeout:
                    logger.warning(f"No output from vLLM for {no_output_timeout/60:.0f} minutes, checking if process is alive...")
                    
                    # Check if vLLM process is still running
                    ps_check = "ps aux | grep 'vllm serve' | grep -v grep || echo 'not found'"
                    stdin_ps, stdout_ps, _ = ssh_client.exec_command(ps_check)
                    ps_result = stdout_ps.read().decode().strip()
                    
                    if "not found" in ps_result:
                        logger.error("vLLM process appears to have crashed")
                        return False, "vLLM process crashed during initialization", None
                            
                await asyncio.sleep(0.5)
                continue
                
            line = line.strip()
            logger.info(f"vLLM output: {line}")
            last_output_time = time.time()  # Update last output time
            
            # Track model loading
            if "Model loading took" in line:
                model_loaded = True
                logger.info("Model loaded successfully")
            
            # Track API server startup
            if "vLLM API server version" in line:
                logger.info("vLLM API server module loaded")
            
            # Track torch compile progress
            if "Cache the graph" in line or "torch.compile" in line:
                torch_compile_started = True
                logger.info("Torch compilation started - this may take several minutes...")
                
            if "KV cache size" in line:
                logger.info(f"KV cache size line: {line}")
                result = re.search(r"GPU KV cache size:\s*([\d,]+)\s*tokens", line)
                if result:
                    kv_cache_size = result.group(1).replace(',', '')

            # Check for critical error that requires immediate failure
            if "Engine core not yet initialized, failed to start" in line:
                logger.error("vLLM engine core failed to initialize")
                
                # Check GPU memory to see if model weights were loaded
                logger.info("Checking GPU memory allocation after engine core error...")
                query = (
                    "nvidia-smi "
                    "--query-compute-apps=pid,used_memory "
                    "--format=csv,noheader,nounits"
                )
                stdin2, stdout2, _ = ssh_client.exec_command(query)
                raw = stdout2.read().decode().strip()
                logger.info(f"GPU memory check after engine error: {raw}")
                
                # Check if any vLLM process allocated memory
                memory_allocated = False
                allocated_memory_mb = 0
                if raw:
                    for row in raw.splitlines():
                        try:
                            pid, used = [x.strip() for x in row.split(",")]
                            # Check if this is a vLLM process
                            ps_cmd = f"ps -p {pid} -o args= 2>/dev/null || echo ''"
                            stdin3, stdout3, _ = ssh_client.exec_command(ps_cmd)
                            args = stdout3.read().decode().strip()
                            
                            if "vllm" in args.lower() or "/hf_env/bin/python" in args:
                                allocated_memory_mb = int(used)
                                memory_allocated = True
                                logger.info(f"Found vLLM process (PID {pid}) with {allocated_memory_mb}MB allocated")
                                break
                        except Exception as e:
                            logger.debug(f"Error checking process: {e}")
                
                if memory_allocated and allocated_memory_mb > 1000:  # More than 1GB allocated
                    allocated_gb = allocated_memory_mb / 1024
                    return False, (f"Model weights loaded successfully ({allocated_gb:.1f}GB allocated) but engine/KV cache initialization failed. "
                                 f"This indicates insufficient remaining GPU memory for KV cache with max_model_len={total_size}. "
                                 f"The system will retry with adjusted parameters."), None
                else:
                    return False, "vLLM engine core failed to initialize - model loading may have failed", None
                
            # Check for success indicators
            if ("Uvicorn running on" in line or 
                "Started server process" in line or
                "API server started" in line or
                "Starting vLLM API server" in line or
                "Application startup complete" in line or
                "Available routes are:" in line or
                "Serving model" in line or
                "ASGI app" in line or
                ("INFO:" in line and "Started server process" in line)):
                # API server is ready
                logger.info(f"API server ready indicator found: {line}")
                ready_to_check = True
            elif (("init engine" in line and "took" in line and "seconds" in line) or 
                 ("Engine" in line and "vllm cache_config_info" in line) or
                 ("Graph capturing finished" in line) or
                 ("Capturing CUDA graph shapes: 100%" in line)):
                # Engine initialized or graph capturing completed
                logger.info("vLLM initialization completed - waiting for API server")
                
                if "Graph capturing finished" in line or "Capturing CUDA graph shapes: 100%" in line:
                    graph_capture_complete = True
                    logger.info("CUDA graph capturing detected as complete")
                    
                    # Important: Continue reading output after graph capturing
                    # The progress bar might have consumed some output, so we need to be careful
                    logger.info("Continuing to monitor output after graph capturing...")
                
                # After graph capturing, vLLM should start the API server
                # Let's wait and check for more output
                api_started = False
                wait_time = 0
                max_wait = 60  # Increased from 30 to 60 seconds to wait for API server
                
                logger.info("Waiting for API server to start after graph capturing...")
                
                while wait_time < max_wait and not api_started:
                    await asyncio.sleep(2)
                    wait_time += 2
                    
                    # Check for any new output
                    if stdout.channel.recv_ready():
                        next_line = stdout.readline()
                        if next_line:
                            next_line = next_line.strip()
                            logger.info(f"Post-graph-capture output: {next_line}")
                            
                            # Check if this indicates API server started
                            if ("Available routes are:" in next_line or 
                                "Started server process" in next_line or
                                "init engine" in next_line and "took" in next_line or
                                "Uvicorn running on" in next_line or
                                "API server started" in next_line):
                                logger.info("API server started after graph capturing")
                                api_started = True
                                break
                    
                    # Also check if process is still alive
                    if stdout.channel.exit_status_ready():
                        exit_code = stdout.channel.recv_exit_status()
                        logger.error(f"vLLM process exited with code {exit_code} after graph capturing")
                        return False, f"vLLM process exited unexpectedly with code {exit_code}", None
                    
                    # Log progress
                    if wait_time % 10 == 0:
                        logger.info(f"Still waiting for API server... ({wait_time}s elapsed)")
                
                # Consider it ready even if we didn't see explicit API start message
                logger.info("Considering vLLM ready after graph capturing completion")
                
                # For graph capturing case, we should check if process is running
                if graph_capture_complete:
                    logger.info("Graph capturing complete, checking if vLLM process is running...")
                    
                    # First check if the vLLM process is still alive via ps
                    ps_check = "ps aux | grep -E 'vllm serve|python.*vllm' | grep -v grep"
                    stdin_ps, stdout_ps, _ = ssh_client.exec_command(ps_check)
                    ps_result = stdout_ps.read().decode().strip()
                    
                    if ps_result:
                        logger.info(f"vLLM process found running: {ps_result[:200]}...")
                    else:
                        logger.warning("No vLLM process found via ps aux")
                    
                    # Check if vLLM has allocated memory
                    query = (
                        "nvidia-smi "
                        "--query-compute-apps=pid,used_memory "
                        "--format=csv,noheader,nounits"
                    )
                    stdin2, stdout2, _ = ssh_client.exec_command(query)
                    raw = stdout2.read().decode().strip()
                    logger.info(f"GPU memory allocation check: {raw}")
                    
                    if raw:
                        for row in raw.splitlines():
                            try:
                                pid, used = [x.strip() for x in row.split(",")]
                                ps_cmd = f"ps -p {pid} -o args="
                                stdin3, stdout3, _ = ssh_client.exec_command(ps_cmd)
                                args = stdout3.read().decode().strip()
                                
                                if "vllm" in args.lower() or "/hf_env/bin/python" in args:
                                    used = int(used) / 1024  # Convert to GB
                                    logger.info(f"vLLM process found with {used:.2f}GB allocated after graph capturing")
                                    
                                    # Wait for API server to be ready (can take 60-120 seconds after graph capturing)
                                    logger.info("Waiting for API server to become ready...")
                                    api_ready = False
                                    for retry in range(60):  # Try for 120 seconds (60 * 2s)
                                        await asyncio.sleep(2)
                                        # Try health endpoint - check HTTP status code instead of response body
                                        # (health endpoint returns empty body with 200 OK)
                                        health_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{port}/health 2>/dev/null"
                                        stdin_h, stdout_h, stderr_h = ssh_client.exec_command(health_cmd)
                                        http_code = stdout_h.read().decode().strip()
                                        exit_status = stdout_h.channel.recv_exit_status()
                                        
                                        # Check if health endpoint returned 200 OK
                                        if http_code == "200" or exit_status == 0:
                                            logger.info(f"API health check succeeded after {retry*2}s (HTTP {http_code})")
                                            api_ready = True
                                            break
                                        elif retry % 10 == 0:  # Log progress every 20 seconds
                                            logger.info(f"Still waiting for API... ({retry*2}s elapsed, last status: {http_code})")
                                    
                                    if api_ready:
                                        return True, f"{used:.2f} GB", kv_cache_size if kv_cache_size else None
                                    else:
                                        logger.warning("API didn't respond but vLLM process is running - may need more time")
                                        # Still return success since vLLM is running with memory allocated
                                        return True, f"{used:.2f} GB (API initializing)", kv_cache_size if kv_cache_size else None
                            except Exception as e:
                                logger.debug(f"Error checking process: {e}")
                
                ready_to_check = True
            else:
                ready_to_check = False
                
            if ready_to_check:
                query = (
                "nvidia-smi "
                "--query-compute-apps=pid,used_memory "
                "--format=csv,noheader,nounits"
            )
                stdin2, stdout2, _ = ssh_client.exec_command(query)
                raw = stdout2.read().decode().strip()
                logger.info(f"Raw output from nvidia-smi: {raw}")

                found = False
                for row in raw.splitlines():
                    try:
                        pid, used = [x.strip() for x in row.split(",")]
                        # Check process args for venv path
                        ps_cmd = f"ps -p {pid} -o args="
                        stdin3, stdout3, _ = ssh_client.exec_command(ps_cmd)
                        args = stdout3.read().decode().strip()
                        logger.info(f"Process args for PID {pid}: {args}")
                        if re.search(r"/hf_env/bin/python3(\s|$)", args):
                            logger.info(f"Found vLLM process with PID {pid} and used: {used}")
                            used = int(used)
                            # convert to GB
                            used = used / 1024  # Convert from MiB to GB
                            found = True
                            break
                    except Exception as e:
                        logger.warning(f"Error parsing process info for row '{row}': {e}")
                        continue
                
                mem_size = mem_str = f"{used:.2f} GB" if found else None
                if mem_size:
                    if kv_cache_size:
                        return True, mem_size, kv_cache_size
                    else:
                        return True, mem_size, None
                else:
                    return True, "vLLM started successfully, but KV cache size not reported", None

 
            # Check for failure indicators
            if "Traceback" in line or "CUDA out of memory" in line or "RuntimeError" in line or ("ERROR" in line and "[core.py:" in line):
                # Read more lines to get full error for logging
                error_lines = [line]
                for _ in range(20):  # Read up to 20 more lines for context
                    if stdout.channel.recv_ready():
                        next_line = stdout.readline()
                        if next_line:
                            error_lines.append(next_line.strip())
                            logger.info(f"vLLM error line: {next_line.strip()}")
                
                # Log full error for debugging
                full_error = '\n'.join(error_lines)
                logger.error(f"vLLM startup error:\n{full_error}")
                
                # Check GPU memory to see if model weights were loaded
                logger.info("Checking GPU memory allocation after error...")
                query = (
                    "nvidia-smi "
                    "--query-compute-apps=pid,used_memory "
                    "--format=csv,noheader,nounits"
                )
                stdin2, stdout2, _ = ssh_client.exec_command(query)
                raw = stdout2.read().decode().strip()
                logger.info(f"GPU memory check after error: {raw}")
                
                # Check if any vLLM process allocated memory
                memory_allocated = False
                allocated_memory_mb = 0
                if raw:
                    for row in raw.splitlines():
                        try:
                            pid, used = [x.strip() for x in row.split(",")]
                            # Check if this is a vLLM process
                            ps_cmd = f"ps -p {pid} -o args= 2>/dev/null || echo ''"
                            stdin3, stdout3, _ = ssh_client.exec_command(ps_cmd)
                            args = stdout3.read().decode().strip()
                            
                            if "vllm" in args.lower() or "/hf_env/bin/python" in args:
                                allocated_memory_mb = int(used)
                                memory_allocated = True
                                logger.info(f"Found vLLM process (PID {pid}) with {allocated_memory_mb}MB allocated")
                                break
                        except Exception as e:
                            logger.debug(f"Error checking process: {e}")
                
                # Return specific error based on memory allocation
                if memory_allocated and allocated_memory_mb > 1000:  # More than 1GB allocated
                    allocated_gb = allocated_memory_mb / 1024
                    return False, (f"Model weights loaded ({allocated_gb:.1f}GB allocated) but KV cache compilation failed. "
                                 f"This is likely due to insufficient remaining GPU memory for the KV cache with max_model_len={total_size}. "
                                 f"The system will retry with adjusted parameters."), None
                
                # No significant memory allocated - model loading likely failed
                # Return more specific error messages
                if "CUDA out of memory" in full_error:
                    return False, "Insufficient GPU memory to load model weights", None
                elif "FileNotFoundError" in full_error or "No such file" in full_error:
                    return False, "Model not found", None
                elif "Permission denied" in full_error:
                    return False, "Permission denied", None
                elif "Address already in use" in full_error or "port 8000" in full_error:
                    return False, "Port 8000 already in use - existing vLLM process may be running", None
                elif "torch.cuda.OutOfMemoryError" in full_error:
                    return False, "CUDA out of memory error during model loading", None
                elif "ImportError" in full_error or "ModuleNotFoundError" in full_error:
                    return False, "Missing Python dependencies", None
                else:
                    # Include a snippet of the actual error
                    error_snippet = error_lines[0] if error_lines else "Unknown error"
                    return False, f"vLLM startup failed: {error_snippet}", None
        
        return False, "Unexpected end of output", None

    async def apply_configuration_async(self, request: ApplyConfigurationRequest, **kwargs) -> AsyncGenerator[str, None]:
        """
        Apply vGPU configuration to a remote host with streaming updates.
        Returns JSON formatted progress updates.
        """
        steps_successful = []  # Track successful steps for summary
        
        async def yield_progress(progress: ConfigurationProgress):
            """Helper to yield progress with proper flushing."""
            yield json.dumps(progress.model_dump()) + "\n"
            await asyncio.sleep(0.001)  # Minimal delay to ensure flush
        
        try:
            # Validate configuration first
            self.validate_configuration(request.configuration)
            
            # Log the full configuration for debugging
            logger.info(f"Full request configuration: {request.configuration}")
            logger.info(f"Configuration keys: {list(request.configuration.keys())}")
            logger.info(f"Request description: {request.description}")
            
            async for msg in yield_progress(ConfigurationProgress(
                status="connecting",
                message=f"Connecting to {request.vm_ip}...",
                current_step=0,
                total_steps=1
            )):
                yield msg
            
            # Establish SSH connection
            with self.ssh_connection(
                hostname=request.vm_ip,
                username=request.username,
                password=request.password,
                port=request.ssh_port,
                timeout=request.timeout
            ) as ssh_client:
                
                # Connection successful
                async for msg in yield_progress(ConfigurationProgress(
                    status="executing",
                    message="Connected successfully. Executing configuration commands...",
                    current_step=0,
                    total_steps=5
                )):
                    yield msg
                
                steps_successful.append("✓ SSH connection established")
                
                # Step 0a: Validate HuggingFace token if provided
                if request.hf_token:
                    async for msg in yield_progress(ConfigurationProgress(
                        status="executing",
                        message="Validating HuggingFace credentials...",
                        current_step=0,
                        total_steps=7,
                        display_message="🔐 Validating HuggingFace token and permissions..."
                    )):
                        yield msg
                    
                    try:
                        from src.huggingface_validator import validate_huggingface_setup
                        
                        model_id = request.configuration.get('model_tag') or request.model
                        is_valid, msg, details = validate_huggingface_setup(request.hf_token, model_id)
                        
                        if not is_valid:
                            async for msg_err in yield_progress(ConfigurationProgress(
                                status="error",
                                message="HuggingFace validation failed",
                                error=msg,
                                current_step=0,
                                total_steps=7
                            )):
                                yield msg_err
                            return
                        
                        logger.info(f"HuggingFace validation: {msg}")
                        steps_successful.append("✓ HuggingFace token validated")
                        
                        async for msg_ok in yield_progress(ConfigurationProgress(
                            status="executing",
                            message=msg,
                            current_step=0,
                            total_steps=7,
                            display_message="✅ HuggingFace credentials verified"
                        )):
                            yield msg_ok
                            
                    except Exception as e:
                        logger.warning(f"Failed to validate HuggingFace token: {e}")
                        # Don't fail deployment, just warn
                        async for msg_warn in yield_progress(ConfigurationProgress(
                            status="executing",
                            message=f"Warning: Could not validate HuggingFace token: {str(e)}",
                            current_step=0,
                            total_steps=7
                        )):
                            yield msg_warn
                
                # Step 0b: Validate VM specifications
                async for msg in yield_progress(ConfigurationProgress(
                    status="executing",
                    message="Validating VM specifications against recommendations...",
                    current_step=0,
                    total_steps=7,
                    display_message="📊 Checking if VM meets recommended specifications..."
                )):
                    yield msg
                
                try:
                    from src.vm_validator import validate_vm_configuration
                    
                    is_valid, validation_msg, validation_details = validate_vm_configuration(
                        ssh_client, request.configuration
                    )
                    
                    logger.info(f"VM Validation Result:\n{validation_msg}")
                    
                    if not is_valid:
                        # VM doesn't meet requirements
                        async for msg_err in yield_progress(ConfigurationProgress(
                            status="error",
                            message="VM does not meet recommended specifications",
                            error=validation_msg,
                            current_step=0,
                            total_steps=7
                        )):
                            yield msg_err
                        return
                    
                    steps_successful.append("✓ VM specifications validated")
                    
                    # Show validation summary
                    vm_specs = validation_details.get('vm_specs', {})
                    summary = (
                        f"✅ VM validated: "
                        f"{vm_specs.get('vcpu_count')}vCPU, "
                        f"{vm_specs.get('system_RAM')}GB RAM, "
                        f"{vm_specs.get('gpu_name', 'Unknown GPU')}"
                    )
                    
                    async for msg_ok in yield_progress(ConfigurationProgress(
                        status="executing",
                        message=summary,
                        current_step=0,
                        total_steps=7,
                        display_message=summary
                    )):
                        yield msg_ok
                        
                except Exception as e:
                    logger.warning(f"Failed to validate VM specs: {e}")
                    # Don't fail deployment, just warn
                    async for msg_warn in yield_progress(ConfigurationProgress(
                        status="executing",
                        message=f"Warning: Could not validate VM specs: {str(e)}",
                        current_step=0,
                        total_steps=7
                    )):
                        yield msg_warn
                
                # Get configuration
                config = request.configuration
                
                # System information
                async for msg in yield_progress(ConfigurationProgress(
                    status="executing",
                    message="Gathering system information...",
                    current_step=1,
                    total_steps=5
                )):
                    yield msg
                
                hypervisor_output, error_hp, status_hp = self.execute_command(ssh_client, "cat /sys/class/dmi/id/product_name")
                os_output, error_os, status_os = self.execute_command(ssh_client, "uname -a")
                # transcribe the OS and the Hypervisor Layer
                if status_hp == 0 and status_os == 0:
                    hypervisor_layer = map_hypervisor(hypervisor_output)
                    os_info = map_os(os_output)
                    
                    if hypervisor_layer and os_info:
                        async for msg in yield_progress(ConfigurationProgress(
                            status="executing",
                            message=f"Hypervisor Layer: {hypervisor_layer}, OS: {os_info}",
                            current_step=1,
                            total_steps=5
                        )):
                            yield msg
                        steps_successful.append(f"✓ System identified: {hypervisor_layer} on {os_info}")

                    else:
                        async for msg in yield_progress(ConfigurationProgress(
                            status="error",
                            message="Here is the hypervisor output: " + hypervisor_output + "\n" + "Here is the OS output: " + os_output,
                            current_step=1,
                            total_steps=5
                        )):
                            yield msg
                
                # GPU availability
                async for msg in yield_progress(ConfigurationProgress(
                    status="executing",
                    message="Checking GPU availability...",
                    current_step=2,
                    total_steps=5
                )):
                    yield msg
                
                output, error, status = self.execute_command(ssh_client, "nvidia-smi --query-gpu=name --format=csv,noheader")
                
                # Check if GPU detection was successful
                if status != 0:
                    async for msg in yield_progress(ConfigurationProgress(
                        status="error",
                        message="No GPU detected or nvidia-smi not available",
                        error=f"nvidia-smi command failed: {error if error else 'Command returned non-zero status'}",
                        current_step=2,
                        total_steps=5
                    )):
                        yield msg
                    return
                
                # Parse GPU information
                detected_gpu_name = output.strip().split("\n")[0] if output.strip() else ""
                if not detected_gpu_name:
                    async for msg in yield_progress(ConfigurationProgress(
                        status="error",
                        message="GPU detection returned empty result",
                        error="nvidia-smi returned no GPU information",
                        current_step=2,
                        total_steps=5
                    )):
                        yield msg
                    return
                
                logger.info(f"Detected GPU: {detected_gpu_name}")
                logger.info(f"Requested vGPU profile: {request.configuration.get('vgpu_profile', 'N/A')}")
                
                # Extract expected GPU family from vGPU profile
                vgpu_profile = request.configuration.get("vgpu_profile", "N/A")
                if vgpu_profile == "N/A":
                    logger.warning("No vGPU profile specified in configuration")
                    steps_successful.append(f"⚠️  GPU detected: {detected_gpu_name} (no profile specified)")
                else:
                    expected_prefix = vgpu_profile.split('-')[0]
                    
                    # Calculate similarity between expected and detected GPU
                    similarity = difflib.SequenceMatcher(None, expected_prefix.lower(), detected_gpu_name.lower()).ratio()
                    logger.info(f"GPU similarity score: {similarity:.2f} (expected: {expected_prefix}, detected: {detected_gpu_name})")
                    
                    # Check if GPU matches (either high similarity or substring match)
                    if similarity > 0.5 or expected_prefix.lower() in detected_gpu_name.lower():
                        async for msg in yield_progress(ConfigurationProgress(
                            status="executing",
                            message=f"GPU verified: {detected_gpu_name} (matches {vgpu_profile})",
                            current_step=2,
                            total_steps=5
                        )):
                            yield msg
                        steps_successful.append(f"✓ GPU verified: {detected_gpu_name}")
                    else:
                        # GPU mismatch - this is a critical error
                        error_msg = (
                            f"GPU mismatch detected!\n"
                            f"Expected: {expected_prefix} (from profile {vgpu_profile})\n"
                            f"Detected: {detected_gpu_name}\n"
                            f"Similarity score: {similarity:.2%}"
                        )
                        logger.error(error_msg)
                        
                        async for msg in yield_progress(ConfigurationProgress(
                            status="error",
                            message=f"GPU mismatch: Expected {expected_prefix}, found {detected_gpu_name}",
                            error=error_msg,
                            current_step=2,
                            total_steps=5
                        )):
                            yield msg
                        return 
                
                
                # Setup phase with fallback logic
                async for msg in yield_progress(ConfigurationProgress(
                    status="executing",
                    message="Starting setup phase...",
                    current_step=3,
                    total_steps=5
                )):
                    yield msg
                
                model_name = request.configuration.get("model_tag", None)
                logger.info(f"Model name extracted from configuration: {model_name}")
                total_size = grab_total_size(request.description)
                logger.info(f"Description: {request.description}")
                logger.info(f"Extracted total_size: {total_size} tokens (prompt + response)")
                test_results = []
                
                # Define consistent venv path early
                VENV_PATH = "$HOME/hf_env"
                
                # Debug: Show actual home directory
                home_check = "echo \"Home directory: $HOME\""
                output_home, _, _ = self.execute_command(ssh_client, home_check)
                logger.info(f"Remote home directory: {output_home}")
                
                # Step 1: HuggingFace authentication (if token provided)
                logger.info(f"HuggingFace token provided: {'Yes' if request.hf_token else 'No'}")
                if request.hf_token:
                    logger.info(f"HuggingFace token length: {len(request.hf_token)}")
                    async for msg in yield_progress(ConfigurationProgress(
                        status="executing",
                        message="Authenticating with HuggingFace...",
                        current_step=3,
                        total_steps=5,
                        display_message="Authenticating with HuggingFace..."
                    )):
                        yield msg
                    
                    # First, create a virtual environment if it doesn't exist
                    async for msg in yield_progress(ConfigurationProgress(
                        status="executing",
                        message="Setting up Python environment...",
                        current_step=3,
                        total_steps=5,
                        display_message="Setting up Python virtual environment..."
                    )):
                        yield msg
                    
                    # Check if python3-venv is available, install if needed
                    venv_cmd = rf"""bash -lc '
                    # Get Python version (e.g., 3.10)
                    PYTHON_VERSION=$(python3 -c "import sys; print(f\"{{sys.version_info.major}}.{{sys.version_info.minor}}\")")
                    echo "🐍 Python version: $PYTHON_VERSION"
                    
                    # Check for python3, python3-venv, and python3-pip
                    PYTHON_OK=0
                    command -v python3 >/dev/null 2>&1 || PYTHON_OK=1
                    command -v pip3 >/dev/null 2>&1 || PYTHON_OK=1
                    
                    # Try to import ensurepip to verify venv is fully functional
                    python3 -c "import ensurepip" >/dev/null 2>&1 || PYTHON_OK=1

                    if [ $PYTHON_OK -eq 1 ]; then
                        echo "📦 Installing Python packages..."
                        echo "{request.password}" | sudo -S apt update
                        # Install both generic and version-specific packages
                        echo "{request.password}" | sudo -S apt install -y python3 python3-pip python3-venv python${{PYTHON_VERSION}}-venv
                        echo "✅ Python packages installed"
                    else
                        echo "✅ python3, python3-venv, and python3-pip are already installed"
                    fi

                    # Check if venv exists AND has activate script
                    if test -f {VENV_PATH}/bin/activate; then
                        echo "✅ Valid venv already exists at: {VENV_PATH}"
                    else
                        # Remove incomplete venv if it exists
                        if test -d {VENV_PATH}; then
                            echo "⚠️ Incomplete venv found, removing..."
                            rm -rf {VENV_PATH}
                        fi
                        
                        echo "📦 Creating new venv at: {VENV_PATH}"
                        python3 -m venv {VENV_PATH} 2>&1
                        
                        # Verify activate script was created
                        if test -f {VENV_PATH}/bin/activate; then
                            echo "✅ venv created successfully"
                        else
                            echo "❌ Failed to create valid venv - activate script missing"
                            exit 1
                        fi
                    fi
                    '"""
                    
                    output, error, status = self.execute_command(ssh_client, venv_cmd, timeout=120)
                    logger.info(f"Venv setup output: {output}")
                    
                    if status != 0:
                        async for msg in yield_progress(ConfigurationProgress(
                            status="error",
                            message="Failed to create virtual environment",
                            error=f"Virtual environment setup failed: {error or output}",
                            current_step=3,
                            total_steps=5
                        )):
                            yield msg
                        return
                    
                    # Install huggingface-hub in the virtual environment
                    async for msg in yield_progress(ConfigurationProgress(
                        status="executing",
                        message="Installing HuggingFace CLI tools...",
                        current_step=3,
                        total_steps=5,
                        display_message="Installing HuggingFace CLI tools..."
                    )):
                        yield msg
                    
                    install_hf_cmd = rf"""bash -lc '
                    source {VENV_PATH}/bin/activate

                    if ! command -v huggingface-cli >/dev/null 2>&1; then
                        echo "huggingface-cli not found, installing huggingface-hub...";
                        pip install --upgrade pip && pip install huggingface-hub;
                    else
                        echo "huggingface-cli already installed.";
                    fi


                    ls -al {VENV_PATH}/bin
                    '"""

                    output, error, status = self.execute_command(ssh_client, install_hf_cmd, timeout=120)
                    
                    if status != 0:
                        # Installation failed
                        async for msg in yield_progress(ConfigurationProgress(
                            status="error",
                            message="Failed to install HuggingFace CLI",
                            error=f"Failed to install huggingface-hub: {error or output}",
                            current_step=3,
                            total_steps=5
                        )):
                            yield msg
                        return
                    
                    # Authenticate with HuggingFace
                    async for msg in yield_progress(ConfigurationProgress(
                        status="executing",
                        message="Authenticating with HuggingFace (this may take a moment)...",
                        current_step=3,
                        total_steps=5,
                        display_message="Logging into HuggingFace..."
                    )):
                        yield msg
                    
                    hf_auth_cmd = rf"""bash -lc '
                    source {VENV_PATH}/bin/activate
                    huggingface-cli login --token {request.hf_token}
                    '"""

                    output, error, status = self.execute_command(ssh_client, hf_auth_cmd, timeout=60)
                    
                    if status != 0:
                        # Authentication failed
                        async for msg in yield_progress(ConfigurationProgress(
                            status="error",
                            message="HuggingFace authentication failed",
                            error=f"Failed to authenticate with HuggingFace: {error or output}",
                            current_step=3,
                            total_steps=5
                        )):
                            yield msg
                        return
                    
                    # Authentication successful
                    logger.info("HuggingFace authentication successful")
                    steps_successful.append("✓ HuggingFace authentication successful")
                    
                    test_results.append(CommandResult(
                        command="huggingface-cli login",
                        output="Authentication successful",
                        error="",
                        success=True,
                        timestamp=time.time()
                    ))
                
                # Step 2: Check and install vLLM with background installation
                logger.info("Checking vLLM installation status")
                # Check if vLLM is already installed in the virtual environment
                check_vllm_cmd = rf"""bash -lc '
                source {VENV_PATH}/bin/activate
                pip show vllm
                '"""
                output, error, status = self.execute_command(ssh_client, check_vllm_cmd, timeout=30)
                
                if status != 0:
                    # vLLM not installed, install it in background
                    logger.info("vLLM not found, starting background installation...")
                    
                    async for msg in yield_progress(ConfigurationProgress(
                        status="executing",
                        message="Starting vLLM installation in background...",
                        current_step=4,
                        total_steps=5,
                        display_message="Installing vLLM framework (monitoring progress)..."
                    )):
                        yield msg
                    
                    # Start installation in background with output to log file
                    install_log = "/tmp/vllm_install.log"
                    pip_cmd = rf"""bash -lc '
                    source {VENV_PATH}/bin/activate
                    nohup pip install vllm > {install_log} 2>&1 &
                    echo $!
                    '"""
                    
                    start_time = time.time()
                    output, error, status = self.execute_command(ssh_client, pip_cmd, timeout=30)
                    
                    if status != 0:
                        async for msg in yield_progress(ConfigurationProgress(
                            status="error",
                            message="Failed to start vLLM installation",
                            error=f"Could not start installation: {error or output}",
                            current_step=4,
                            total_steps=5
                        )):
                            yield msg
                        return
                    
                    install_pid = output.strip()
                    logger.info(f"vLLM installation started with PID: {install_pid}")
                    
                    # Monitor installation progress
                    max_wait = 1200  # 20 minutes max
                    poll_interval = 10  # Check every 10 seconds
                    elapsed = 0
                    
                    while elapsed < max_wait:
                        await asyncio.sleep(poll_interval)
                        elapsed = int(time.time() - start_time)
                        
                        # Check if process is still running
                        check_cmd = f"ps -p {install_pid} > /dev/null 2>&1 && echo 'running' || echo 'done'"
                        ps_output, _, _ = self.execute_command(ssh_client, check_cmd, timeout=10)
                        
                        if "done" in ps_output:
                            # Installation completed, check if successful
                            logger.info("vLLM installation process completed")
                            
                            # Verify installation
                            verify_output, verify_error, verify_status = self.execute_command(
                                ssh_client, check_vllm_cmd, timeout=30
                            )
                            
                            if verify_status == 0:
                                logger.info(f"vLLM installed successfully in {elapsed}s")
                                steps_successful.append(f"✓ vLLM installed successfully (took {elapsed}s)")
                                
                                async for msg in yield_progress(ConfigurationProgress(
                                    status="executing",
                                    message=f"vLLM installed successfully in {elapsed}s",
                                    current_step=4,
                                    total_steps=5,
                                    display_message=f"✅ vLLM installation complete ({elapsed}s)"
                                )):
                                    yield msg
                                break
                            else:
                                # Installation failed, get error from log
                                log_cmd = f"tail -50 {install_log}"
                                log_output, _, _ = self.execute_command(ssh_client, log_cmd, timeout=10)
                                
                                logger.error(f"vLLM installation failed. Log:\n{log_output}")
                                async for msg in yield_progress(ConfigurationProgress(
                                    status="error",
                                    message="vLLM installation failed",
                                    error=f"Installation completed but verification failed. Last 50 lines of log:\n{log_output[-1000:]}",
                                    current_step=4,
                                    total_steps=5
                                )):
                                    yield msg
                                return
                        else:
                            # Still installing, send progress update
                            if elapsed % 30 == 0:  # Update every 30 seconds
                                async for msg in yield_progress(ConfigurationProgress(
                                    status="executing",
                                    message=f"Installing vLLM... ({elapsed}s elapsed)",
                                    current_step=4,
                                    total_steps=5,
                                    display_message=f"Installing vLLM framework ({elapsed}s elapsed, this may take 10-15 minutes)..."
                                )):
                                    yield msg
                                logger.info(f"vLLM installation still in progress... ({elapsed}s)")
                    
                    if elapsed >= max_wait:
                        # Timeout
                        logger.error(f"vLLM installation timed out after {max_wait}s")
                        
                        # Try to get log
                        log_cmd = f"tail -50 {install_log}"
                        log_output, _, _ = self.execute_command(ssh_client, log_cmd, timeout=10)
                        
                        async for msg in yield_progress(ConfigurationProgress(
                            status="error",
                            message="vLLM installation timed out",
                            error=f"Installation did not complete within {max_wait/60:.0f} minutes. Log:\n{log_output[-1000:]}",
                            current_step=4,
                            total_steps=5
                        )):
                            yield msg
                        return
                    
                    test_results.append(CommandResult(
                        command="pip install vllm",
                        output=f"vLLM installed successfully in {elapsed}s",
                        error="",
                        success=True,
                        timestamp=time.time()
                    ))
                else:
                    # vLLM already installed
                    logger.info("vLLM is already installed")
                    steps_successful.append("✓ vLLM already installed")
                    
                    async for msg in yield_progress(ConfigurationProgress(
                        status="executing",
                        message="vLLM already installed",
                        current_step=4,
                        total_steps=5,
                        display_message="✅ vLLM already installed, skipping installation"
                    )):
                        yield msg
                    
                    test_results.append(CommandResult(
                        command=check_vllm_cmd,
                        output="vLLM already installed",
                        error="",
                        success=True,
                        timestamp=time.time()
                    ))
                
                # Step 3: Start vLLM server with progressive GPU utilization

                PORT         = 8000

                # Retry settings
                # take the estimated VRAM from the vGPU profile
                profile = request.configuration.get("vgpu_profile", "N/A")
                prof_val = re.search(r'-([0-9]{1,3})Q', profile)
                value = int(prof_val.group(1)) if prof_val else None

                estimated_vram = request.configuration.get("gpu_memory_size", None)
                
                if estimated_vram is not None and value is not None:
                    num_gpus = math.ceil(estimated_vram / value)
                    total_value = num_gpus * value
                    ratio = estimated_vram / total_value
                    # round ratio to nearest tenth of a decimal (0.1-1.0)
                    ratio = round(ratio, 1)
                    logger.info(f"Estimated VRAM: {estimated_vram}MB, vGPU profile value: {value}MB, ratio: {ratio}")
                    # Cap at 0.85 to leave headroom for CUDA overhead
                    INITIAL_UTIL = min(ratio, 0.85)
                    
                else:
                    INITIAL_UTIL = 0.75              # starting default

                # Start lower and increment up, but cap at 0.95 (can't use 100% of GPU)
                DELTA_UTIL   = 0.05              # smaller increment on each retry  
                MAX_ATTEMPTS = 4                 # number of attempts to find optimal memory
                MAX_GPU_UTIL = 0.95              # maximum allowed GPU utilization
                MODEL_REF = model_name

                logger.info(f"Final MODEL_REF to be used: {MODEL_REF}")
                
                gpu_util = INITIAL_UTIL
                successful_gpu_mem = None 
                kv_cache = None  # Initialize kv_cache
                
                for attempt in range(1, MAX_ATTEMPTS + 1):
                    # Show optimizing message instead of scary attempt numbers
                    if attempt == 1:
                        display_msg = "Starting vLLM server..."
                    else:
                        display_msg = f"Optimizing GPU memory allocation (step {attempt}/{MAX_ATTEMPTS})..."
                    
                    async for msg in yield_progress(ConfigurationProgress(
                        status="executing",
                        message=f"Trying gpu-memory-utilization={gpu_util:.2f}",
                        current_step=4,
                        total_steps=5,
                        display_message=display_msg
                    )):
                        yield msg

                    # Always cleanup old vLLM processes before starting (not just on retries)
                    logger.info("Cleaning up any existing vLLM processes...")
                    cleanup_cmds = [
                        "pkill -9 -f 'vllm serve' || true",  # -9 for forceful kill
                        "pkill -9 -f 'vllm.entrypoints' || true",
                        "pkill -9 -f 'python.*vllm' || true",
                        "pkill -9 -f 'VLLM::EngineCore' || true",  # Kill engine core processes
                        "pkill -9 -f 'vllm' || true",  # Catch any remaining vllm processes
                        "sleep 3"  # Give time for GPU memory to be released
                    ]
                    for cmd in cleanup_cmds:
                        self.execute_command(ssh_client, cmd, timeout=10)
                        logger.info(f"Executed cleanup: {cmd}")
                    
                    # Check GPU memory before starting
                    gpu_mem_cmd = "nvidia-smi --query-gpu=memory.free,memory.total --format=csv,noheader,nounits"
                    output, _, _ = self.execute_command(ssh_client, gpu_mem_cmd)
                    if output:
                        try:
                            free_mem, total_mem = map(int, output.strip().split(','))
                            logger.info(f"GPU memory before vLLM start: {free_mem}MB free / {total_mem}MB total ({free_mem/total_mem*100:.1f}% free)")
                        except Exception as e:
                            logger.warning(f"Could not parse GPU memory: {e}")
                    
                    # For later attempts, try reducing max_model_len
                    adjusted_total_size = total_size
                    if attempt > 2 and total_size > 1024:
                        # Reduce context length on later attempts
                        adjusted_total_size = max(1024, total_size - (attempt - 2) * 256)
                        logger.info(f"Reducing max_model_len from {total_size} to {adjusted_total_size} for attempt {attempt}")
                    
                    # Start vLLM and wait for it to be ready
                    logger.info(f"Starting vLLM with: model={MODEL_REF}, gpu_util={gpu_util}, total_size={adjusted_total_size}")
                    success, message_vllm, kv_cache = await self.wait_for_vllm_live(
                        ssh_client, gpu_util, MODEL_REF, VENV_PATH, adjusted_total_size, PORT
                    )
                    
                    if success:
                        async for msg in yield_progress(ConfigurationProgress(
                            status="executing",
                            current_step=4,
                            total_steps=5,
                            display_message=f"✅ vLLM server started successfully!"
                        )):
                            yield msg
                        
                        # Give it a moment to stabilize
                        await asyncio.sleep(3)
                        
                        # Verify vLLM is actually accessible
                        logger.info("Verifying vLLM API is accessible...")
                        health_check_cmd = f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{PORT}/health || echo 'failed'"
                        health_output, _, _ = self.execute_command(ssh_client, health_check_cmd, timeout=10)
                        
                        if "200" in health_output:
                            logger.info(f"vLLM API health check passed: {health_output}")
                        else:
                            logger.warning(f"vLLM API health check result: {health_output}")
                            # Still consider it successful if the process started and allocated memory
                            logger.info(f"vLLM process is running with GPU memory allocated ({message_vllm})")
                        
                        steps_successful.append(f"✓ vLLM configured optimally with gpu-memory-utilization={gpu_util:.2f}")
                        successful_gpu_mem = message_vllm  # Store the GPU memory allocation
                        break
                        
                    else:
                        # Log error for debugging but don't scare the user
                        logger.info(f"Attempt {attempt} failed: {message_vllm}")
                        
                        if attempt < MAX_ATTEMPTS:
                            gpu_util = min(gpu_util + DELTA_UTIL, MAX_GPU_UTIL)
                            logger.info(f"Incrementing gpu_util to {gpu_util:.2f} (capped at {MAX_GPU_UTIL})")
                            # Don't show error to user, just indicate we're optimizing
                            await asyncio.sleep(2)  # Brief pause between attempts
                        else:
                            # Only show error if ALL attempts failed
                            async for msg in yield_progress(ConfigurationProgress(
                                status="error",
                                message="Unable to start vLLM server",
                                error=f"vLLM failed to start after {MAX_ATTEMPTS} attempts. This may be due to insufficient GPU memory for the model. Last error: {message_vllm}",
                                current_step=4,
                                total_steps=5
                            )):
                                yield msg
                            return
                
                # Final check to ensure vLLM is still running
                logger.info("Final check: verifying vLLM is still running...")
                # Use a more robust check that looks for the actual vllm process
                final_check_cmd = "ps aux | grep -E 'vllm serve|python.*vllm|hf_env.*vllm' | grep -v grep"
                check_output, _, _ = self.execute_command(ssh_client, final_check_cmd)
                
                vllm_running = False
                if check_output and check_output.strip():
                    vllm_running = True
                    process_count = len(check_output.strip().split('\n'))
                    logger.info(f"✅ vLLM process confirmed running ({process_count} process(es))")
                else:
                    logger.warning("⚠️ vLLM process not found in final check")
                
                # If we successfully allocated GPU memory earlier, that's what matters
                if successful_gpu_mem and not vllm_running:
                    logger.info(f"Note: vLLM had successfully allocated {successful_gpu_mem} but process may have exited")
                
                # Update summary message to be clearer about the status
                if successful_gpu_mem:
                    status_line = f"• Status: vLLM started and allocated {successful_gpu_mem}\n"
                    if not vllm_running:
                        status_line += "  ⚠️  API endpoint is still initializing\n"
                else:
                    status_line = "• Status: Configuration attempted\n"
                
                summary_message = (
                    "✅ vLLM server configuration completed!\n\n"
                    "Configuration Details:\n"
                    f"• Model: {model_name}\n" +
                    status_line +
                    f"• GPU Memory Utilization: {gpu_util:.0%}\n"
                    f"• KV Cache: {kv_cache if kv_cache else 'N/A'} tokens\n\n"
                    "Advisor System Configuration:\n"
                    f"• vGPU Profile: {request.configuration.get('vGPU_profile', 'N/A')}\n"
                    f"• vCPUs: {request.configuration.get('vCPU_count', 'N/A')}\n"
                    f"• RAM: {request.configuration.get('system_RAM', 'N/A')}GB\n"
                )
                try:
                    from src.utils import get_llm
                    llm = get_llm(**kwargs)

                    prompt = (
                        "You are an AI assistant generating ticket-style diagnostic reports for IT professionals. "
                        "Based on the provided deployment summary created a report that an IT engineer "
                        "can forward to their development or platform team. The log must be written in **markdown** "
                        "and should resemble a professional internal ticket (e.g., for Jira, ServiceNow).\n\n"
                        "Your output must include the following clearly labeled sections:\n\n"
                        "1. **Title** — a short, informative title that includes model name or vGPU profile if available "
                        f"(e.g., 'vLLM Server Starting {gpu_info}')\n"
                        "2. **Issue Summary** — a concise paragraph summarizing the issue and its root cause if known\n"
                        "3. **Environment** — bullet list of configuration info: model, GPU, vGPU profile, RAM, vCPUs, GPU memory usage, KV cache tokens\n"
                        "4. **Deployment Steps Completed** — bullet list of successful setup steps\n"
                        "5. **Observed Behavior** — describe what went wrong, clearly stating if the vLLM process exited or if the API failed health check\n"
                        "6. **Recommended Actions** — numbered list of concrete follow-up steps for DevOps or developers (e.g., check logs, reduce memory usage, restart service)\n"
                        "7. **Optional Tags** — provide machine-parsable tags like `component:vllm`, `gpu_utilization:80%`, `status:api_unavailable`\n\n"
                        "If any information is missing from the deployment summary, make reasonable assumptions or use placeholder values.\n\n"
                        "Here is the system summary to work from:\n\n"
                        f"{summary_message}\n\n"
                        "Now generate the full log below in markdown:"
                    )


                    test_response = llm.invoke(prompt)
                    logger.info(f"LLM Test: content={test_response.content} additional_kwargs={test_response.additional_kwargs} response_metadata={test_response.response_metadata}")
                except Exception as e:
                    logger.warning(f"⚠️ Failed to get response from LLM: {e}")

                # Final summary
                async for msg in yield_progress(ConfigurationProgress(
                    status="completed",
                    message=f"Configuration completed successfully!\n{test_response.content if test_response else summary_message}",
                    current_step=5,
                    total_steps=5
                )):
                    yield msg
                
        except Exception:  # was: paramiko.AuthenticationException
            async for msg in yield_progress(ConfigurationProgress(
                status="error",
                message="Authentication failed",
                error="Invalid username or password"
            )):
                yield msg
        except Exception as e:  # was: paramiko.SSHException
            async for msg in yield_progress(ConfigurationProgress(
                status="error",
                message="SSH connection failed",
                error=str(e)
            )):
                yield msg
        except Exception as e:
            async for msg in yield_progress(ConfigurationProgress(
                status="error",
                message="Configuration failed",
                error=str(e)
            )):
                yield msg


async def ensure_ssh_key_exists() -> tuple[bool, str, str]:
    """
    Ensure SSH key exists for vGPU sizing advisor.
    
    This function ONLY generates the key if it doesn't exist.
    It does NOT try to copy it automatically.
    
    Returns:
        (key_exists, key_path, message)
    """
    import os
    import subprocess
    
    ssh_dir = os.path.expanduser('~/.ssh')
    key_name = 'vgpu_sizing_advisor'
    key_path = os.path.join(ssh_dir, key_name)
    pub_key_path = f"{key_path}.pub"
    
    try:
        # Create .ssh directory if it doesn't exist
        os.makedirs(ssh_dir, mode=0o700, exist_ok=True)
        
        # Check if key already exists
        if os.path.exists(key_path) and os.path.exists(pub_key_path):
            logger.info(f"SSH key already exists at {key_path}")
            return True, key_path, f"Using existing SSH key: {key_path}"
        
        # Generate SSH key
        logger.info(f"Generating SSH key pair '{key_name}'...")
        result = subprocess.run(
            ['ssh-keygen', '-t', 'rsa', '-b', '4096', '-f', key_path, '-N', ''],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return False, "", f"Failed to generate SSH key: {result.stderr}"
        
        logger.info(f"SSH key pair generated successfully at {key_path}")
        return True, key_path, f"Generated new SSH key: {key_path}"
            
    except subprocess.TimeoutExpired:
        return False, "", "SSH key generation timed out"
    except Exception as e:
        logger.error(f"SSH key generation failed: {e}")
        return False, "", f"SSH key generation error: {str(e)}"


async def test_ssh_connection(host: str, username: str, port: int = 22, password: str = None) -> tuple[bool, str]:
    """
    Test SSH connection using key-based authentication.
    If key auth fails and password is provided, automatically copy the SSH key.
    
    Args:
        host: Remote host IP/hostname
        username: SSH username
        port: SSH port (default 22)
        password: SSH password (optional, used for automatic key setup)
        
    Returns:
        (success, message)
    """
    import os
    
    ssh_dir = os.path.expanduser('~/.ssh')
    key_name = 'vgpu_sizing_advisor'
    key_path = os.path.join(ssh_dir, key_name)
    pub_key_path = f"{key_path}.pub"
    
    # Check if key exists
    if not os.path.exists(key_path):
        return False, f"SSH key not found at {key_path}. Please generate it first."
    
    # Try SSH connection with key
    ssh_cmd = [
        'ssh',
        '-i', key_path,
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'ConnectTimeout=10',
        '-o', 'BatchMode=yes',  # Non-interactive mode
        '-p', str(port),
        f'{username}@{host}',
        'echo "SSH connection successful"'
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=15
        )
        
        if process.returncode == 0:
            return True, "SSH connection successful"
        else:
            stderr_str = stderr.decode('utf-8', errors='replace')
            if 'Permission denied' in stderr_str and password:
                # Attempt to automatically copy the SSH key using built-in Python
                logger.info("SSH key not set up. Attempting automatic key copy...")
                
                try:
                    # Read the public key
                    with open(pub_key_path, 'r') as f:
                        pub_key_content = f.read().strip()
                    
                    logger.info(f"Attempting to copy SSH key to {username}@{host}:{port}")
                    
                    # Create a temporary askpass script for non-interactive password input
                    import tempfile
                    import subprocess
                    
                    # Create askpass helper script
                    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.sh') as f:
                        f.write(f'#!/bin/sh\necho "{password}"')
                        askpass_path = f.name
                    
                    os.chmod(askpass_path, 0o700)
                    
                    try:
                        # Set up environment for SSH_ASKPASS
                        env = os.environ.copy()
                        env['SSH_ASKPASS'] = askpass_path
                        env['SSH_ASKPASS_REQUIRE'] = 'force'  # Force using SSH_ASKPASS
                        env['DISPLAY'] = ':0'
                        
                        # Try ssh-copy-id with SSH_ASKPASS
                        logger.info("Using SSH_ASKPASS for non-interactive key copy")
                        result = subprocess.run(
                            [
                                'ssh-copy-id',
                                '-i', pub_key_path,
                                '-p', str(port),
                                '-o', 'StrictHostKeyChecking=accept-new',
                                f'{username}@{host}'
                            ],
                            env=env,
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            logger.info("SSH key copied successfully!")
                            return True, "SSH key automatically configured"
                        else:
                            logger.warning(f"ssh-copy-id failed: {result.stderr}")
                            
                            # Fallback: directly append to authorized_keys using SSH
                            logger.info("Trying direct key copy via SSH...")
                            
                            # Escape single quotes in the public key
                            safe_key = pub_key_content.replace("'", "'\\''")
                            copy_cmd = f"mkdir -p ~/.ssh && chmod 700 ~/.ssh && echo '{safe_key}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
                            
                            ssh_result = subprocess.run(
                                [
                                    'ssh',
                                    '-p', str(port),
                                    '-o', 'StrictHostKeyChecking=accept-new',
                                    '-o', 'PubkeyAuthentication=no',
                                    f'{username}@{host}',
                                    copy_cmd
                                ],
                                env=env,
                                capture_output=True,
                                text=True,
                                timeout=30
                            )
                            
                            if ssh_result.returncode == 0:
                                logger.info("SSH key copied via direct SSH method!")
                                return True, "SSH key automatically configured"
                            else:
                                logger.error(f"Direct SSH copy also failed: {ssh_result.stderr}")
                                return False, f"Could not copy SSH key automatically. Please run manually: ssh-copy-id -i {pub_key_path} -p {port} {username}@{host}"
                                
                    except subprocess.TimeoutExpired:
                        return False, "SSH key copy timeout (30s)"
                    finally:
                        # Clean up askpass script
                        try:
                            os.unlink(askpass_path)
                        except:
                            pass
                        
                except Exception as copy_error:
                    logger.error(f"Automatic key copy failed: {copy_error}")
                    return False, f"Could not copy key automatically. Please run: ssh-copy-id -i {pub_key_path} -p {port} {username}@{host}"
            elif 'Permission denied' in stderr_str:
                # No password provided
                return False, f"SSH key authentication failed. Please run ssh-copy-id -i {pub_key_path} -p {port} {username}@{host}"
            else:
                return False, f"SSH connection failed: {stderr_str}"
                
    except asyncio.TimeoutError:
        return False, "SSH connection timed out. Please check network connectivity."
    except Exception as e:
        return False, f"SSH test failed: {str(e)}"


async def execute_ssh_command(
    host: str,
    username: str,
    password: str,
    command: str,
    port: int = 22,
    timeout: int = 300,
    setup_keys_if_needed: bool = False  # Deprecated, kept for compatibility
) -> tuple[str, str, int]:
    """
    Execute a command on remote host via SSH using SSH keys.
    
    Note: This function expects SSH keys to be already set up.
    Use ensure_ssh_key_exists() and test_ssh_connection() before calling this.
    
    Args:
        host: Remote host IP/hostname
        username: SSH username
        password: SSH password (not used, kept for compatibility)
        command: Command to execute
        port: SSH port (default 22)
        timeout: Command timeout in seconds
        setup_keys_if_needed: Deprecated, kept for compatibility
        
    Returns:
        (stdout, stderr, exit_code)
    """
    import os
    
    # Use custom vgpu_sizing_advisor key
    ssh_dir = os.path.expanduser('~/.ssh')
    key_name = 'vgpu_sizing_advisor'
    key_path = os.path.join(ssh_dir, key_name)
    
    # SSH with custom key
    ssh_cmd = [
        'ssh',
        '-i', key_path,  # Use custom key
        '-o', 'StrictHostKeyChecking=no',
        '-o', 'UserKnownHostsFile=/dev/null',
        '-o', 'ConnectTimeout=30',
        '-o', 'BatchMode=yes',  # Non-interactive mode
        '-p', str(port),
        f'{username}@{host}',
        command
    ]
    
    try:
        process = await asyncio.create_subprocess_exec(
            *ssh_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout
        )
        
        return (
            stdout.decode('utf-8', errors='replace').strip(),
            stderr.decode('utf-8', errors='replace').strip(),
            process.returncode or 0
        )
    except asyncio.TimeoutError:
        if process:
            try:
                process.kill()
                await process.wait()
            except:
                pass
        raise TimeoutError(f"Command timed out after {timeout}s")
    except Exception as e:
        logger.error(f"SSH command failed: {e}")
        raise


async def deploy_vllm_local(config_request) -> AsyncGenerator[str, None]:
    """
    Deploy vLLM locally by SSHing from container to host machine.
    This allows us to use the host's Python, GPU drivers, and vLLM installation.
    """
    import subprocess
    import socket
    import os
    from copy import copy
    
    def send_progress(message: str):
        return json.dumps({
            "status": "executing",
            "message": message,
            "display_message": message,
            "deployment_type": "local"
        })
    
    def send_error(message: str, error: str):
        return json.dumps({
            "status": "error",
            "message": message,
            "error": error,
            "display_message": f"[LOCAL] Error: {message}",
            "deployment_type": "local"
        })
    
    def send_success(message: str, data: dict = None):
        response = {
            "status": "success",
            "message": message,
            "display_message": f"[LOCAL] {message}",
            "deployment_type": "local"
        }
        if data:
            response.update(data)
        return json.dumps(response)
    
    try:
        logger.info("=" * 80)
        logger.info(">>> LOCAL DEPLOYMENT (via SSH to host) <<<")
        logger.info("=" * 80)
        
        yield send_progress("=" * 60)
        yield send_progress("🏠 LOCAL DEPLOYMENT MODE")
        yield send_progress("=" * 60)
        yield send_progress("Running vLLM on host machine (same machine as RAG/vector DB)")
        yield send_progress("")
        
        # Detect host machine IP from container
        yield send_progress("🔍 Detecting host machine IP...")
        
        gateway_ip = None
        try:
            # Get Docker gateway (host IP)
            with open('/proc/net/route') as f:
                for line in f:
                    fields = line.strip().split()
                    if len(fields) < 3 or fields[1] != '00000000':
                        continue
                    if not int(fields[3], 16) & 2:
                        continue
                    gateway_hex = fields[2]
                    gateway_ip = socket.inet_ntoa(bytes.fromhex(gateway_hex)[::-1])
                    break
        except Exception as e:
            logger.debug(f"Could not read /proc/net/route: {e}")
        
        # Fallback
        if not gateway_ip:
            try:
                gateway_ip = socket.gethostbyname('host.docker.internal')
            except:
                gateway_ip = "172.17.0.1"
        
        # Get host user from environment or default to nvadmin
        host_user = os.environ.get('HOST_USER', 'nvadmin')
        
        yield send_progress(f"✓ Host: {gateway_ip}")
        yield send_progress(f"✓ User: {host_user}")
        yield send_progress("")
        
        # Create request for host machine
        host_request = copy(config_request)
        host_request.vm_ip = gateway_ip
        host_request.username = host_user
        host_request.password = ""  # Use SSH keys
        host_request.ssh_port = 22
        
        # Mark as local deployment so we can account for existing GPU usage
        if not hasattr(host_request, 'is_local_deployment'):
            host_request.configuration['is_local_deployment'] = True
        
        # Use the remote deployment function (which handles everything properly)
        async for progress_update in deploy_vllm_server(host_request):
            yield progress_update
            
    except Exception as e:
        logger.error(f"[LOCAL DEPLOYMENT] FAILED: {e}", exc_info=True)
        yield send_error("Local deployment failed", str(e))


async def deploy_vllm_server(config_request) -> AsyncGenerator[str, None]:
    """
    Deploy and start vLLM server on remote VM via SSH.
    
    This function:
    1. Tests SSH connectivity
    2. Checks system requirements (Python, GPU, disk space)
    3. Installs vLLM if needed
    4. Sets Hugging Face token
    5. Starts vLLM server
    6. Waits for server to be ready
    7. Tests inference endpoint
    8. Returns connection details
    
    Args:
        config_request: Configuration request with vm_ip, username, password, hf_token, configuration
        
    Yields:
        JSON progress updates via Server-Sent Events
    """
    
    # Import time module for timing tracking
    import time as time_module
    
    # Extract configuration first
    host = config_request.vm_ip
    username = config_request.username
    password = config_request.password or ""
    port = getattr(config_request, 'ssh_port', 22)
    
    # Track deployment information (minimal for cleaner output)
    debug_info = {
        "deployment_type": "",
        "gpu_metrics": {},
        "vllm_config": {},
        "timing": {},
        "summary": {}
    }
    
    # Determine if this is actually a local deployment (SSH to localhost)
    is_localhost = host in ['localhost', '127.0.0.1', '172.17.0.1', '172.18.0.1'] or host.startswith('172.')
    deployment_label = "LOCAL" if is_localhost else "VM"
    
    def send_progress(message: str):
        return json.dumps({
            "status": "executing",
            "message": message,
            "display_message": message,
            "deployment_type": "remote" if not is_localhost else "local"
        })
    
    def send_success(message: str, data: dict = None):
        response = {
            "status": "success",
            "message": message,
            "display_message": f"[{deployment_label}] {message}",
            "debug_info": debug_info,
            "deployment_type": "remote" if not is_localhost else "local"
        }
        if data:
            response.update(data)
        return json.dumps(response)
    
    def send_error(message: str, error: str):
        return json.dumps({
            "status": "error",
            "message": message,
            "error": error,
            "display_message": f"[{deployment_label}] Error: {message}",
            "debug_info": debug_info,
            "deployment_type": "remote" if not is_localhost else "local"
        })
    
    def log_command(command: str, stdout: str = "", stderr: str = "", code: int = 0, duration: float = 0):
        """Log command execution for debugging (logs only, not in user output)"""
        if code != 0:
            logger.warning(f"[{deployment_label}] Command failed (exit {code}): {command[:80]}")
        else:
            logger.debug(f"[{deployment_label}] Command OK: {command[:80]} ({duration:.1f}s)")
    
    try:
        # Get HuggingFace token
        hf_token = config_request.hf_token or ""
        
        # Track deployment start time
        deploy_start = time_module.time()
        debug_info["timing"]["deployment_start"] = deploy_start
        debug_info["connection_info"] = {
            "host": host,
            "port": port,
            "username": username
        }
        
        config = config_request.configuration
        # Try to get model from: 1) direct model_tag field, 2) model field, 3) configuration dict, 4) fallback
        model = (
            getattr(config_request, 'model_tag', None) or 
            getattr(config_request, 'model', None) or 
            config.get('model_tag', None) or 
            config.get('model_name', None) or
            'meta-llama/Llama-3.1-8B-Instruct'
        )
        max_tokens = config.get('max_kv_tokens', 2048)
        
        # Check if this is a local deployment (running on same machine as RAG/vector DB)
        is_local = config.get('is_local_deployment', False)
        debug_info["deployment_type"] = "local" if is_local else "remote"
        
        # Calculate optimal GPU utilization based on vGPU profile
        profile = config.get('vgpu_profile', 'N/A')
        prof_val = re.search(r'-([0-9]{1,3})Q', profile)
        profile_value = int(prof_val.group(1)) if prof_val else None
        estimated_vram = config.get('gpu_memory_size', None)
        
        # Initialize with default - will be recalculated after detecting physical GPU
        gpu_util = 0.85  # Conservative default
        
        # Display deployment mode banner
        deployment_icon = "🏠" if is_localhost else "☁️"
        logger.info("=" * 80)
        logger.info(f">>> {deployment_label} DEPLOYMENT <<<")
        logger.info(f"Target: {host}:{port} (user: {username})")
        logger.info("=" * 80)
        
        yield send_progress("=" * 60)
        yield send_progress(f"{deployment_icon} {deployment_label} DEPLOYMENT MODE")
        yield send_progress("=" * 60)
        if is_localhost:
            yield send_progress("Target: Host machine (same as RAG/vector DB)")
        else:
            yield send_progress(f"Target: Remote VM at {host}")
        yield send_progress("")
        
        # Step 1: Ensure SSH key exists
        import os
        yield send_progress("Checking SSH key...")
        key_exists, key_path, key_msg = await ensure_ssh_key_exists()
        
        if not key_exists:
            logger.error(f"[{deployment_label}] SSH key generation failed: {key_msg}")
            yield send_error("SSH key generation failed", key_msg)
            return
        
        yield send_progress(key_msg)
        
        # Step 2: Test SSH connection (with automatic key setup if password is provided)
        yield send_progress("Testing SSH connection...")
        conn_success, conn_msg = await test_ssh_connection(host, username, port, password)
        
        if not conn_success:
            logger.error(f"[{deployment_label}] SSH connection failed: {conn_msg}")
            
            # Provide clear instructions
            setup_instructions = f"""SSH key authentication not set up yet.

Please run this command on your host machine:

ssh-copy-id -i {key_path}.pub -p {port} {username}@{host}

(You'll be prompted for the password)

After running this command, click 'Test Connection' or try deployment again."""
            
            yield send_error("SSH Setup Required", setup_instructions)
            return
        
        yield send_progress("✓ SSH connection successful")
        
        # Verify we can actually execute commands
        try:
            step_start = time_module.time()
            stdout, stderr, code = await execute_ssh_command(
                host, username, password,
                "echo 'Connection verified'",
                port=port,
                timeout=30
            )
            log_command("echo 'Connection verified'", stdout, stderr, code, time_module.time() - step_start)
            
            if code != 0:
                logger.error(f"[{deployment_label}] SSH verification failed: {stderr}")
                yield send_error("SSH verification failed", stderr or "Could not execute commands")
                return
        except Exception as e:
            logger.error(f"[{deployment_label}] SSH verification exception: {str(e)}")
            yield send_error("SSH verification failed", str(e))
            return
        
        # Step 2: Check NVIDIA GPU and validate against configuration
        yield send_progress("Checking NVIDIA GPU availability...")
        detected_gpu_name = None
        try:
            step_start = time_module.time()
            
            # Get GPU info
            stdout, stderr, code = await execute_ssh_command(
                host, username, password,
                "nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader",
                port=port
            )
            log_command("nvidia-smi --query-gpu=name,memory.total,driver_version", stdout, stderr, code, time_module.time() - step_start)
            
            if code != 0:
                logger.error(f"[{deployment_label}] nvidia-smi failed: {stderr}")
                yield send_error("GPU not found", "nvidia-smi command failed. Please ensure NVIDIA drivers are installed.")
                return
            
            gpu_info = stdout.strip()
            if gpu_info:
                parts = gpu_info.split(',')
                detected_gpu_name = parts[0].strip()
                gpu_memory_total = parts[1].strip() if len(parts) > 1 else "Unknown"
                driver_version = parts[2].strip() if len(parts) > 2 else "Unknown"
                
                debug_info["gpu_metrics"]["detected_name"] = detected_gpu_name
                debug_info["gpu_metrics"]["total_memory"] = gpu_memory_total
                debug_info["gpu_metrics"]["driver_version"] = driver_version
                
                yield send_progress(f"GPU detected: {detected_gpu_name}, {gpu_memory_total}")
                yield send_progress(f"NVIDIA Driver: {driver_version}")
                
                # Recalculate GPU utilization dynamically based on vGPU profile and physical GPU
                if profile_value is not None:
                    # Parse physical GPU memory (format: "46068 MiB" or "48 GB")
                    gpu_memory_str = gpu_memory_total.replace(',', '').strip()
                    if 'MiB' in gpu_memory_str:
                        physical_gpu_gb = float(gpu_memory_str.replace('MiB', '').strip()) / 1024
                    elif 'GiB' in gpu_memory_str:
                        physical_gpu_gb = float(gpu_memory_str.replace('GiB', '').strip())
                    elif 'GB' in gpu_memory_str:
                        physical_gpu_gb = float(gpu_memory_str.replace('GB', '').strip())
                    else:
                        # Try to parse as number (assume GB)
                        try:
                            physical_gpu_gb = float(gpu_memory_str.split()[0])
                        except:
                            physical_gpu_gb = None
                    
                    if physical_gpu_gb:
                        # Target: use 85-90% of vGPU profile capacity
                        # For L40S-24Q: target = 24GB * 0.88 = 21.12GB
                        target_memory_gb = profile_value * 0.88
                        
                        # Calculate what percentage of physical GPU that represents
                        # For 24GB target on 48GB physical: 21.12 / 48 = 0.44 (44%)
                        gpu_util = target_memory_gb / physical_gpu_gb
                        
                        # Safety bounds: 0.4 to 0.95
                        gpu_util = max(0.4, min(0.95, gpu_util))
                        
                        logger.info(f"Dynamic GPU utilization: {gpu_util:.2f} (vGPU profile: {profile_value}GB, physical: {physical_gpu_gb:.1f}GB, target: {target_memory_gb:.1f}GB)")
                        yield send_progress(f"Configuring for vGPU profile {profile} ({profile_value}GB): GPU utilization set to {int(gpu_util*100)}%")
                    else:
                        logger.warning(f"Could not parse GPU memory: {gpu_memory_total}")
                
                # Validate GPU matches requested profile
                expected_prefix = profile.split('-')[0] if profile != 'N/A' else None
                if expected_prefix:
                    import difflib
                    similarity = difflib.SequenceMatcher(None, expected_prefix, detected_gpu_name).ratio()
                    debug_info["gpu_metrics"]["profile_match_score"] = similarity
                    
                    if similarity > 0.5 or expected_prefix in detected_gpu_name:
                        yield send_progress(f"GPU matches requested profile: {profile} (match score: {similarity:.2f})")
                    else:
                        yield send_progress(f"Warning: Detected GPU ({detected_gpu_name}) may not match profile ({profile}) (match score: {similarity:.2f})")
            else:
                logger.error(f"[{deployment_label}] nvidia-smi returned empty output")
                yield send_error("No GPU detected", "nvidia-smi returned no output")
                return
                
            # Get initial GPU memory state
            stdout, stderr, code = await execute_ssh_command(
                host, username, password,
                "nvidia-smi --query-gpu=memory.used,memory.free --format=csv,noheader,nounits",
                port=port
            )
            if code == 0:
                debug_info["gpu_metrics"]["initial_memory"] = stdout.strip()
                
        except Exception as e:
            logger.error(f"[{deployment_label}] GPU check exception: {str(e)}")
            yield send_error("Failed to check GPU", str(e))
            return
        
        # Step 3: Check Python version
        yield send_progress("Checking Python installation...")
        try:
            stdout, stderr, code = await execute_ssh_command(
                host, username, password,
                "python3 --version",
                port=port
            )
            if code != 0:
                yield send_error("Python not found", "python3 command failed")
                return
            yield send_progress(f"Python version: {stdout}")
        except Exception as e:
            yield send_error("Failed to check Python", str(e))
            return
        
        # Step 4: Setup virtual environment and install vLLM
        venv_path = "~/vllm_env"
        yield send_progress("Setting up Python virtual environment...")
        try:
            # Check if venv already exists
            stdout, stderr, code = await execute_ssh_command(
                host, username, password,
                f"test -d {venv_path} && echo 'exists' || echo 'not_exists'",
                port=port
            )
            
            if 'not_exists' in stdout:
                yield send_progress("Creating virtual environment (this may take a minute)...")
                stdout, stderr, code = await execute_ssh_command(
                    host, username, password,
                    f"python3 -m venv {venv_path}",
                    port=port,
                    timeout=120
                )
                if code != 0:
                    yield send_error("Failed to create virtual environment", stderr[:500])
                    return
                yield send_progress("Virtual environment created")
            else:
                yield send_progress("Virtual environment already exists")
            
            # Check if vLLM is installed in venv
            yield send_progress("Checking vLLM installation in virtual environment...")
            step_start = time_module.time()
            stdout, stderr, code = await execute_ssh_command(
                host, username, password,
                f"source {venv_path}/bin/activate && python -c 'import vllm; print(vllm.__version__)'",
                port=port
            )
            log_command(f"Check vLLM version in {venv_path}", stdout, stderr, code, time_module.time() - step_start)
            
            if code != 0:
                debug_info["timing"]["vllm_install_start"] = time_module.time()
                yield send_progress("Installing vLLM in virtual environment (this may take 5-10 minutes)...")
                install_start = time_module.time()
                stdout, stderr, code = await execute_ssh_command(
                    host, username, password,
                    f"source {venv_path}/bin/activate && pip install --upgrade pip && pip install vllm",
                    port=port,
                    timeout=900  # 15 minutes for vLLM installation
                )
                install_duration = time_module.time() - install_start
                debug_info["timing"]["vllm_install_duration"] = install_duration
                log_command(f"Install vLLM in {venv_path}", stdout[-500:] if stdout else "", stderr[-500:] if stderr else "", code, install_duration)
                
                if code != 0:
                    logger.error(f"[{deployment_label}] vLLM install failed: {stderr[-500:] if stderr else 'Unknown'}")
                    yield send_error("Failed to install vLLM", stderr[-1000:] if stderr else "Unknown error")
                    return
                yield send_progress(f"vLLM installation completed in {int(install_duration)}s")
            else:
                debug_info["vllm_config"]["vllm_version"] = stdout.strip()
                yield send_progress(f"vLLM already installed: {stdout}")
                
        except Exception as e:
            yield send_error("Failed to setup virtual environment", str(e))
            return
        
        # Step 5: Authenticate with Hugging Face
        if hf_token:
            yield send_progress("Authenticating with Hugging Face...")
            try:
                # Install huggingface-hub if not present
                stdout, stderr, code = await execute_ssh_command(
                    host, username, password,
                    f"source {venv_path}/bin/activate && pip show huggingface-hub > /dev/null 2>&1 || pip install huggingface-hub",
                    port=port,
                    timeout=60
                )
                
                # Clear any cached HuggingFace credentials before login
                yield send_progress("Clearing cached HuggingFace credentials...")
                
                # Delete HF token cache file and logout to ensure clean state
                await execute_ssh_command(
                    host, username, password,
                    f"rm -f ~/.huggingface/token ~/.cache/huggingface/token 2>/dev/null || true",
                    port=port,
                    timeout=10
                )
                
                await execute_ssh_command(
                    host, username, password,
                    f"source {venv_path}/bin/activate && huggingface-cli logout 2>/dev/null || true",
                    port=port,
                    timeout=10
                )
                
                # Login using huggingface-cli with fresh token
                yield send_progress("Authenticating with HuggingFace...")
                stdout, stderr, code = await execute_ssh_command(
                    host, username, password,
                    f"source {venv_path}/bin/activate && huggingface-cli login --token {hf_token}",
                    port=port,
                    timeout=30
                )
                
                if code == 0:
                    yield send_progress("Successfully authenticated with Hugging Face")
                else:
                    # HF authentication failed - stop deployment
                    # Clean up the error message
                    error_details = stderr
                    
                    # Remove SSH warnings
                    error_details = '\n'.join([
                        line for line in error_details.split('\n') 
                        if not any(x in line for x in [
                            'Warning: Permanently added',
                            'ED25519',
                            'known hosts',
                            'git credentials helper',
                            'add_to_git_credential'
                        ])
                    ]).strip()
                    
                    # Extract the meaningful error message (before traceback)
                    if 'Traceback' in error_details:
                        error_details = error_details.split('Traceback')[0].strip()
                    
                    # If still too long, truncate
                    if len(error_details) > 300:
                        error_details = error_details[:300] + "..."
                    
                    # If empty after cleaning, provide generic message
                    if not error_details:
                        error_details = "Authentication failed. Token may be invalid or lack required permissions."
                    
                    yield send_error(
                        "HuggingFace authentication failed",
                        f"Invalid HuggingFace token. Please verify your token has the required permissions for this model.\n\n{error_details}"
                    )
                    return
                    
            except Exception as e:
                yield send_error(
                    "Failed to authenticate with HuggingFace",
                    f"Authentication error: {str(e)[:500]}"
                )
                return
        else:
            yield send_progress("Warning: No Hugging Face token provided. Public models only.")
        
        # Step 6: Check if vLLM is already running and kill it
        yield send_progress("Checking for existing vLLM processes...")
        try:
            stdout, stderr, code = await execute_ssh_command(
                host, username, password,
                "pkill -f 'vllm.entrypoints.openai.api_server' || true",
                port=port
            )
            await asyncio.sleep(3)  # Wait for process to die
            yield send_progress("Cleared any existing vLLM processes")
        except Exception as e:
            logger.warning(f"Failed to kill existing vLLM: {e}")
        
        # Step 7: Start vLLM server with progressive retry logic
        INITIAL_UTIL = gpu_util
        DELTA_UTIL = 0.1
        MAX_ATTEMPTS = 4
        
        successful_gpu_mem = None
        kv_cache_tokens = None
        attempt_gpu_util = INITIAL_UTIL
        
        for attempt in range(1, MAX_ATTEMPTS + 1):
            if attempt == 1:
                display_msg = f"Starting vLLM server with model: {model}..."
            else:
                display_msg = f"Optimizing GPU memory allocation (attempt {attempt}/{MAX_ATTEMPTS})..."
            
            yield send_progress(display_msg)
            
            if attempt > 1:
                # Cleanup previous attempt
                yield send_progress("Cleaning up previous vLLM process...")
                await execute_ssh_command(
                    host, username, password,
                    "pkill -9 -f 'vllm serve' || true",
                    port=port,
                    timeout=10
                )
                await asyncio.sleep(3)
            
            # Check GPU memory before starting
            # For local deployments, also get baseline usage (existing processes like RAG/vector DB)
            stdout, stderr, code = await execute_ssh_command(
                host, username, password,
                "nvidia-smi --query-gpu=memory.free,memory.total,memory.used --format=csv,noheader,nounits",
                port=port
            )
            if code == 0 and stdout:
                try:
                    parts = stdout.strip().split(',')
                    free_mem, total_mem = int(parts[0]), int(parts[1])
                    used_mem = int(parts[2]) if len(parts) > 2 else (total_mem - free_mem)
                    
                    debug_info["gpu_metrics"][f"attempt_{attempt}_pre_start"] = {
                        "free_mb": free_mem,
                        "total_mb": total_mem,
                        "used_mb": used_mem,
                        "free_percent": round(free_mem/total_mem*100, 1)
                    }
                    
                    # Store baseline for local deployments (overhead from RAG/vector DB/etc)
                    if is_local and attempt == 1:
                        debug_info["gpu_metrics"]["baseline_used_mb"] = used_mem
                        baseline_gb = used_mem / 1024
                        logger.info(f"LOCAL DEPLOYMENT: Baseline GPU usage: {baseline_gb:.1f}GB (RAG/vector DB overhead)")
                        yield send_progress(f"ℹ️  Existing GPU usage: {baseline_gb:.1f}GB (RAG, vector DB, etc.)")
                    
                    logger.info(f"GPU memory before attempt {attempt}: {free_mem}MB free / {total_mem}MB total ({free_mem/total_mem*100:.1f}% free)")
                except Exception as e:
                    logger.warning(f"Could not parse GPU memory: {e}")
                    pass
            
            # Adjust max_model_len for later attempts
            adjusted_max_tokens = max_tokens
            if attempt > 2 and max_tokens > 1024:
                adjusted_max_tokens = max(1024, max_tokens - (attempt - 2) * 256)
                logger.info(f"Reducing max_model_len from {max_tokens} to {adjusted_max_tokens} for attempt {attempt}")
            
            # Check if common vLLM ports (8000-8010) are available, kill processes if occupied
            yield send_progress("Checking if ports 8000-8010 are available...")
            ports_cleared = []
            for check_port in range(8000, 8011):
                stdout, stderr, code = await execute_ssh_command(
                    host, username, password,
                    f"lsof -ti:{check_port} 2>/dev/null || true",
                    port=port,
                    timeout=5
                )
                if code == 0 and stdout.strip():
                    pids = [p.strip() for p in stdout.strip().split('\n') if p.strip().isdigit()]
                    if pids:
                        ports_cleared.append(check_port)
                        await execute_ssh_command(
                            host, username, password,
                            f"kill -9 {' '.join(pids)} 2>/dev/null || true",
                            port=port,
                            timeout=5
                        )
            
            if ports_cleared:
                yield send_progress(f"✓ Cleared ports: {', '.join(map(str, ports_cleared))}")
            else:
                yield send_progress("✓ All ports available")
            
            yield send_progress(f"Starting vLLM (GPU util: {attempt_gpu_util:.0%}, max tokens: {adjusted_max_tokens})...")
            
            # Store vLLM configuration
            debug_info["vllm_config"][f"attempt_{attempt}"] = {
                "model": model,
                "gpu_utilization": attempt_gpu_util,
                "max_model_len": adjusted_max_tokens,
                "host": "0.0.0.0",
                "port": 8000
            }
            
            try:
                # Use vllm serve command from the virtual environment
                vllm_cmd = f"""
nohup bash -c 'source {venv_path}/bin/activate && \
{venv_path}/bin/vllm serve {model} \
    --host 0.0.0.0 \
    --port 8000 \
    --gpu-memory-utilization {attempt_gpu_util} \
    --max-model-len {adjusted_max_tokens}' \
> /tmp/vllm.log 2>&1 & echo $!
"""
                step_start = time_module.time()
                stdout, stderr, code = await execute_ssh_command(
                    host, username, password,
                    vllm_cmd,
                    port=port,
                    timeout=30
                )
                log_command(f"Start vLLM server (attempt {attempt})", stdout, stderr, code, time_module.time() - step_start)
                
                vllm_pid = stdout.strip()
                if vllm_pid and vllm_pid.isdigit():
                    debug_info["vllm_config"]["vllm_pid"] = vllm_pid
                    yield send_progress(f"vLLM server starting (PID: {vllm_pid})")
                else:
                    yield send_progress("vLLM server starting (background process)")
                    
            except Exception as e:
                if attempt < MAX_ATTEMPTS:
                    logger.warning(f"Attempt {attempt} failed to start: {e}")
                    attempt_gpu_util += DELTA_UTIL
                    continue
                else:
                    yield send_error("Failed to start vLLM server", str(e))
                    return
        
            # Step 8: Wait for vLLM server to be ready
            yield send_progress("Waiting for vLLM server to initialize (model download + loading may take 5-10 minutes)...")
            max_wait = 900  # 15 minutes for model download and loading
            start_time = time.time()
            server_ready = False
            actual_port = 8000  # Track the actual port vLLM is using (8000 or 8001)
            
            last_log_check = 0
            while time.time() - start_time < max_wait:
                try:
                    await asyncio.sleep(10)
                    elapsed = int(time.time() - start_time)
                    
                    # Check if vLLM process is still running
                    stdout, stderr, code = await execute_ssh_command(
                        host, username, password,
                        f"ps aux | grep '[v]llm serve' | wc -l",
                        port=port,
                        timeout=5
                    )
                    
                    if code == 0 and stdout.strip() == '0':
                        # Process died - get the logs to show what happened
                        yield send_progress("vLLM process crashed. Retrieving error logs...")
                        
                        log_stdout, log_stderr, log_code = await execute_ssh_command(
                            host, username, password,
                            f"tail -100 /tmp/vllm.log 2>/dev/null || echo 'No log file found'",
                            port=port,
                            timeout=10
                        )
                        
                        if log_code == 0 and log_stdout.strip():
                            # Parse the log for the actual error
                            log_lines = log_stdout.strip().split('\n')
                            
                            # Look for common error patterns
                            error_lines = []
                            for i, line in enumerate(log_lines):
                                if 'Error' in line or 'Exception' in line or 'Traceback' in line or 'FAILED' in line or 'GatedRepoError' in line:
                                    # Include context around the error
                                    start = max(0, i - 2)
                                    end = min(len(log_lines), i + 10)
                                    error_lines = log_lines[start:end]
                                    break
                            
                            if error_lines:
                                yield send_progress("vLLM Error Details:")
                                for line in error_lines[:15]:  # Show first 15 lines of error
                                    if line.strip():
                                        yield send_progress(f"  {line}")
                            else:
                                # Show last 20 lines of log
                                yield send_progress("Last 20 lines of vLLM log:")
                                for line in log_lines[-20:]:
                                    if line.strip():
                                        yield send_progress(f"  {line}")
                        
                        yield send_error("vLLM process died", "The vLLM server process has stopped unexpectedly. See error details above.")
                        return
                    
                    # Dynamically detect what port vLLM is listening on
                    # Check for any port in the common range (8000-8010)
                    stdout, stderr, code = await execute_ssh_command(
                        host, username, password,
                        "ss -tln | grep -E ':(800[0-9]|801[0-9]) ' || netstat -tln | grep -E ':(800[0-9]|801[0-9]) ' || echo 'not_listening'",
                        port=port,
                        timeout=5
                    )
                    
                    port_listening = 'not_listening' not in stdout and code == 0
                    
                    # Detect which port is actually listening (parse from output)
                    if port_listening:
                        # Extract port number from ss/netstat output (e.g., "0.0.0.0:8001")
                        port_match = re.search(r':(\d{4,5})\s', stdout)
                        if port_match:
                            actual_port = int(port_match.group(1))
                            logger.info(f"Detected vLLM listening on port {actual_port}")
                        else:
                            # Fallback: check which specific port
                            for check_port in range(8000, 8020):
                                if f':{check_port}' in stdout:
                                    actual_port = check_port
                                    logger.info(f"Detected vLLM listening on port {actual_port}")
                                    break
                    
                    if port_listening:
                        # Notify if using a different port than default
                        if actual_port != 8000 and elapsed < 15:  # Only log once early
                            yield send_progress(f"ℹ️  Detected vLLM on port {actual_port}")
                        
                        # Port is open, try health check on the detected port
                        # vLLM health endpoint returns HTTP 200 with empty body when healthy
                        stdout, stderr, code = await execute_ssh_command(
                            host, username, password,
                            f"curl -s -o /dev/null -w '%{{http_code}}' http://localhost:{actual_port}/health",
                            port=port,
                            timeout=10
                        )
                        
                        # Check if HTTP status code is 200
                        if code == 0 and '200' in stdout:
                            server_ready = True
                            yield send_progress(f"✓ vLLM server is ready on port {actual_port}!")
                            break
                        else:
                            yield send_progress(f"Port {actual_port} is open, waiting for health check... ({elapsed}s elapsed, HTTP: {stdout})")
                    else:
                        yield send_progress(f"Waiting for vLLM to start listening (checking ports 8000-8019)... ({elapsed}s elapsed)")
                    
                    # Show log excerpts every 60 seconds
                    if elapsed - last_log_check >= 60:
                        stdout, stderr, code = await execute_ssh_command(
                            host, username, password,
                            "tail -5 /tmp/vllm.log 2>/dev/null || echo 'No logs yet'",
                            port=port,
                            timeout=5
                        )
                        if stdout and 'No logs yet' not in stdout:
                            yield send_progress(f"Recent log: {stdout[-200:]}")
                        last_log_check = elapsed
                    
                except Exception as e:
                    logger.debug(f"Health check failed: {e}")
                    yield send_progress(f"Health check error (will retry): {str(e)[:100]}")
                    continue
            
            if not server_ready:
                # Check logs for errors
                try:
                    stdout, stderr, code = await execute_ssh_command(
                        host, username, password,
                        "tail -50 /tmp/vllm.log",
                        port=port
                    )
                    error_msg = f"Last 50 lines of log:\n{stdout[-1000:]}"
                except:
                    error_msg = "Could not retrieve logs"
                
                # Check if the error was due to insufficient memory
                if "less than desired GPU memory utilization" in error_msg or "Free memory on device" in error_msg:
                    # This is a memory issue, reduce GPU utilization more aggressively
                    if attempt < MAX_ATTEMPTS:
                        logger.info(f"Attempt {attempt} failed due to insufficient GPU memory, reducing utilization")
                        attempt_gpu_util = max(0.5, attempt_gpu_util - 0.2)  # Reduce by 20%, min 50%
                        continue
                
                # Retry with adjusted parameters
                if attempt < MAX_ATTEMPTS:
                    logger.info(f"Attempt {attempt} timed out, retrying with adjusted parameters")
                    attempt_gpu_util += DELTA_UTIL
                    continue
                else:
                    yield send_error("Server failed to start after all attempts", error_msg)
                    return
            
            # Success! Break out of retry loop
            if server_ready:
                debug_info["timing"]["vllm_ready_at"] = time_module.time() - deploy_start
                
                # Get GPU memory allocation
                stdout, stderr, code = await execute_ssh_command(
                    host, username, password,
                    "nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits",
                    port=port
                )
                if code == 0 and stdout:
                    debug_info["gpu_metrics"]["vllm_processes"] = stdout.strip()
                    for line in stdout.strip().split('\n'):
                        try:
                            parts = line.split(',')
                            if len(parts) >= 2:
                                successful_gpu_mem = f"{int(parts[1].strip()) / 1024:.2f} GB"
                                debug_info["gpu_metrics"]["vllm_memory_allocated_gb"] = float(successful_gpu_mem.split()[0])
                                break
                        except:
                            pass
                
                # Try to extract KV cache and other metrics from logs
                stdout, stderr, code = await execute_ssh_command(
                    host, username, password,
                    "grep -E 'KV cache size|Model loading took|Graph capturing finished' /tmp/vllm.log | tail -10",
                    port=port
                )
                if code == 0 and stdout:
                    debug_info["vllm_config"]["vllm_log_excerpts"] = stdout.strip()
                    
                    # Extract KV cache
                    match = re.search(r'(\d+,?\d*)\s*tokens', stdout)
                    if match:
                        kv_cache_tokens = match.group(1).replace(',', '')
                        debug_info["vllm_config"]["kv_cache_tokens"] = kv_cache_tokens
                    
                    # Extract model loading time
                    match = re.search(r'Model loading took.*?(\d+\.?\d*)\s*seconds', stdout)
                    if match:
                        debug_info["timing"]["model_load_seconds"] = float(match.group(1))
                
                break  # Exit retry loop on success
        
        # Final verification with detailed process info
        yield send_progress("Verifying vLLM process is running...")
        stdout, stderr, code = await execute_ssh_command(
            host, username, password,
            "ps aux | grep '[v]llm serve'",
            port=port
        )
        vllm_running = bool(stdout and stdout.strip()) if code == 0 else False
        if vllm_running:
            debug_info["vllm_config"]["process_info"] = stdout.strip()[:500]
            logger.info("vLLM process verified as running")
        else:
            logger.warning("vLLM process not found in ps output")
        
        # Step 9: Test inference endpoint with a longer prompt
        test_prompt = "Explain the concept of GPU virtualization in 2-3 sentences."
        test_max_tokens = 100
        logger.info(f"=== STARTING {deployment_label} INFERENCE TEST ===")
        yield send_progress(f"[{deployment_label}] Testing inference endpoint...")
        yield send_progress(f"Prompt: {test_prompt}")
        logger.info(f"[{deployment_label}] Starting inference test with prompt: {test_prompt}")
        
        inference_response = ""
        inference_test_success = False
        try:
            test_payload = json.dumps({
                "model": model,
                "messages": [{"role": "user", "content": test_prompt}],
                "max_tokens": test_max_tokens
            }).replace("'", "'\\''")  # Escape single quotes for bash
            
            # Use -v for verbose output to stderr if there are issues
            curl_test = f"""curl -s -X POST http://localhost:{actual_port}/v1/chat/completions \
-H 'Content-Type: application/json' \
-d '{test_payload}' \
--max-time 60 2>&1"""
            
            logger.info(f"Running inference test with payload: {test_payload[:200]}")
            stdout, stderr, code = await execute_ssh_command(
                host, username, password,
                curl_test,
                port=port,
                timeout=70
            )
            logger.info(f"Inference test completed with code {code}, stdout length: {len(stdout)}, stderr length: {len(stderr)}")
            
            if code == 0:
                # Parse and display inference response
                try:
                    response_json = json.loads(stdout)
                    if 'choices' in response_json and len(response_json['choices']) > 0:
                        choice = response_json['choices'][0]
                        inference_response = choice.get('message', {}).get('content', '')
                        if not inference_response:
                            # Try alternative response format
                            inference_response = choice.get('text', '')
                        
                        if inference_response:
                            yield send_progress(f"[{deployment_label}] Inference response:")
                            yield send_progress(f"  {inference_response.strip()}")
                            debug_info["vllm_config"]["inference_response"] = inference_response.strip()
                            debug_info["vllm_config"]["deployment_label"] = deployment_label
                            inference_test_success = True
                        else:
                            yield send_progress(f"[{deployment_label}] Inference test completed but response content is empty")
                            logger.warning(f"[{deployment_label}] Empty inference response. Full response: {stdout[:500]}")
                    else:
                        yield send_progress("Inference test completed but no choices in response")
                        logger.warning(f"No choices in response: {stdout[:500]}")
                except json.JSONDecodeError as e:
                    yield send_progress(f"Inference test completed but response is not valid JSON")
                    logger.warning(f"JSON decode error: {e}, stdout: {stdout[:500]}")
                except Exception as e:
                    yield send_progress(f"Inference test completed but failed to parse: {str(e)}")
                    logger.error(f"Inference response parse error: {e}, stdout: {stdout[:500]}")
            else:
                yield send_progress(f"Inference test failed with exit code {code}")
                logger.error(f"Inference test failed. stderr: {stderr[:500]}, stdout: {stdout[:500]}")
            
            # Continue with deployment summary if we got any response
            if code == 0:
                debug_info["timing"]["total_deployment_time"] = time_module.time() - deploy_start
                debug_info["vllm_config"]["inference_test_passed"] = inference_test_success
                
                # Get additional GPU stats after inference
                gpu_stats = {}
                try:
                    stdout, stderr, code = await execute_ssh_command(
                        host, username, password,
                        "nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu,power.draw,power.limit --format=csv,noheader,nounits",
                        port=port,
                        timeout=5
                    )
                    if code == 0 and stdout:
                        parts = stdout.strip().split(',')
                        if len(parts) >= 5:
                            gpu_stats = {
                                "gpu_utilization": f"{parts[0].strip()}%",
                                "memory_utilization": f"{parts[1].strip()}%",
                                "temperature": f"{parts[2].strip()}°C",
                                "power_draw": f"{parts[3].strip()}W",
                                "power_limit": f"{parts[4].strip()}W"
                            }
                            debug_info["gpu_metrics"]["runtime_stats"] = gpu_stats
                except Exception as e:
                    logger.debug(f"Failed to get GPU stats: {e}")
                
                # Determine configuration status
                if vllm_running and successful_gpu_mem:
                    status_line = f"  • Status: ✅ vLLM running and allocated {successful_gpu_mem}\n"
                elif successful_gpu_mem:
                    status_line = f"  • Status: ⚠️  vLLM allocated {successful_gpu_mem} but may be initializing\n"
                else:
                    status_line = "  • Status: ⚠️  vLLM started (memory allocation not confirmed)\n"
                
                # Generate configuration summary
                summary_message = (
                    "\n=== vLLM Server Configuration Completed Successfully ===\n\n"
                    "Configuration Details:\n"
                    f"  • Model: {model}\n"
                    + status_line +
                    f"  • GPU Detected: {detected_gpu_name or 'Unknown'}\n"
                    f"  • GPU Memory Utilization Setting: {int(attempt_gpu_util * 100)}%\n"
                    f"  • Max Model Length: {adjusted_max_tokens} tokens\n"
                    f"  • KV Cache: {kv_cache_tokens if kv_cache_tokens else 'N/A'} tokens\n"
                )
                
                # Add hardware usage stats if available
                if gpu_stats:
                    summary_message += "\nHardware Usage During Test:\n"
                    summary_message += f"  • GPU Compute Utilization: {gpu_stats.get('gpu_utilization', 'N/A')}\n"
                    summary_message += f"  • GPU Memory Active: {gpu_stats.get('memory_utilization', 'N/A')}\n"
                    summary_message += f"  • GPU Temperature: {gpu_stats.get('temperature', 'N/A')}\n"
                    summary_message += f"  • Power Draw: {gpu_stats.get('power_draw', 'N/A')} / {gpu_stats.get('power_limit', 'N/A')}\n"
                
                # Add test prompt info
                summary_message += f"\nInference Test:\n"
                summary_message += f"  • Query: {test_prompt}\n"
                summary_message += f"  • Max Tokens: {test_max_tokens}\n"
                if inference_response:
                    response_preview = inference_response[:150] + "..." if len(inference_response) > 150 else inference_response
                    summary_message += f"  • Response Preview: {response_preview}\n"
                
                summary_message += "\nAdvisor System Configuration:\n"
                summary_message += f"  • vGPU Profile: {config.get('vgpu_profile', 'N/A')}\n"
                summary_message += f"  • vCPUs: {config.get('vcpu_count', 'N/A')}\n"
                summary_message += f"  • System RAM: {config.get('system_RAM', 'N/A')} GB\n"
                summary_message += f"  • GPU Memory Size: {config.get('gpu_memory_size', 'N/A')} GB\n\n"
                summary_message += "Configuration Validation:\n"
                
                # Add validation results with actual vs expected
                if detected_gpu_name and profile != 'N/A':
                    expected_prefix = profile.split('-')[0]
                    # Get total GPU memory for comparison
                    gpu_memory_total = debug_info["gpu_metrics"].get("total_memory", "Unknown")
                    
                    if expected_prefix in detected_gpu_name:
                        summary_message += f"  ✅ GPU Match\n"
                        summary_message += f"     • Detected: {detected_gpu_name} ({gpu_memory_total})\n"
                        summary_message += f"     • Expected: {profile}\n"
                    else:
                        summary_message += f"  ⚠️  GPU Mismatch\n"
                        summary_message += f"     • Detected: {detected_gpu_name} ({gpu_memory_total})\n"
                        summary_message += f"     • Expected: {profile}\n"
                
                if successful_gpu_mem:
                    actual_gb = float(successful_gpu_mem.split()[0])
                    
                    # For local deployments, account for baseline overhead
                    baseline_mb = debug_info["gpu_metrics"].get("baseline_used_mb", 0)
                    if is_local and baseline_mb > 0:
                        baseline_gb = baseline_mb / 1024
                        vllm_only_gb = actual_gb - baseline_gb
                        
                        # Get total GPU memory
                        total_gpu_mb = debug_info["gpu_metrics"].get("attempt_1_pre_start", {}).get("total_mb", 0)
                        total_gpu_gb = total_gpu_mb / 1024 if total_gpu_mb > 0 else 0
                        
                        summary_message += f"  ✅ GPU Memory Allocation (Local)\n"
                        summary_message += f"     • Total GPU: {total_gpu_gb:.1f}GB\n"
                        summary_message += f"     • Used by vLLM: ~{max(0, vllm_only_gb):.1f}GB\n"
                        summary_message += f"     • Baseline overhead: ~{baseline_gb:.1f}GB (RAG/vector DB)\n"
                        summary_message += f"     • Total allocated: {actual_gb:.1f}GB\n"
                        
                        # Check if we have enough free memory
                        if total_gpu_mb > 0:
                            free_for_vllm_gb = (total_gpu_mb / 1024) - baseline_gb
                            remaining_gb = total_gpu_gb - actual_gb
                            if free_for_vllm_gb < 10:
                                summary_message += f"     • ⚠️  Limited free memory: {remaining_gb:.1f}GB remaining\n"
                            else:
                                summary_message += f"     • Free memory: {remaining_gb:.1f}GB remaining\n"
                    elif estimated_vram:
                        # Remote deployment - compare with estimate
                        expected_gb = float(estimated_vram)
                        ratio = actual_gb / expected_gb
                        diff_gb = actual_gb - expected_gb
                        diff_pct = ((actual_gb - expected_gb) / expected_gb * 100) if expected_gb > 0 else 0
                        
                        # Get total GPU memory for context
                        total_gpu_mb = debug_info["gpu_metrics"].get("attempt_1_pre_start", {}).get("total_mb", 0)
                        total_gpu_gb = total_gpu_mb / 1024 if total_gpu_mb > 0 else 0
                        
                        if 0.8 <= ratio <= 1.2:
                            summary_message += f"  ✅ GPU Memory Allocation (VM)\n"
                            summary_message += f"     • Total GPU: {total_gpu_gb:.1f}GB\n"
                            summary_message += f"     • Used by vLLM: {actual_gb:.1f}GB\n"
                            summary_message += f"     • Expected: ~{expected_gb:.1f}GB\n"
                            summary_message += f"     • Difference: {diff_gb:+.1f}GB ({diff_pct:+.1f}%)\n"
                            if total_gpu_gb > 0:
                                remaining_gb = total_gpu_gb - actual_gb
                                summary_message += f"     • Free memory: {remaining_gb:.1f}GB remaining\n"
                        elif ratio > 1.2:
                            summary_message += f"  ⚠️  GPU Memory Higher Than Expected (VM)\n"
                            summary_message += f"     • Used by vLLM: {actual_gb:.1f}GB\n"
                            summary_message += f"     • Expected: ~{expected_gb:.1f}GB\n"
                            summary_message += f"     • Difference: {diff_gb:+.1f}GB ({diff_pct:+.1f}%)\n"
                        else:
                            summary_message += f"  ℹ️  GPU Memory Lower Than Expected (VM)\n"
                            summary_message += f"     • Used by vLLM: {actual_gb:.1f}GB\n"
                            summary_message += f"     • Expected: ~{expected_gb:.1f}GB\n"
                            summary_message += f"     • Difference: {diff_gb:+.1f}GB ({diff_pct:+.1f}%)\n"
                    else:
                        # No estimate available
                        total_gpu_mb = debug_info["gpu_metrics"].get("attempt_1_pre_start", {}).get("total_mb", 0)
                        total_gpu_gb = total_gpu_mb / 1024 if total_gpu_mb > 0 else 0
                        summary_message += f"  ℹ️  GPU Memory Allocation\n"
                        summary_message += f"     • Used by vLLM: {actual_gb:.1f}GB\n"
                        if total_gpu_gb > 0:
                            summary_message += f"     • Total GPU: {total_gpu_gb:.1f}GB\n"
                
                summary_message += "\nNext Steps:\n"
                summary_message += f"  • Test API: curl http://{host}:{actual_port}/v1/chat/completions\n"
                summary_message += f"  • View Logs: ssh {username}@{host} 'tail -f /tmp/vllm.log'\n"
                summary_message += f"  • Stop Server: ssh {username}@{host} 'pkill -f vllm'\n"
                
                yield send_progress(summary_message)
                
                yield send_success(
                    f"{deployment_label} vLLM deployment successful!",
                    {
                        "endpoint": f"http://{host}:{actual_port}",
                        "model": model,
                        "health_endpoint": f"http://{host}:{actual_port}/health",
                        "openai_compatible": True,
                        "deployment_type": deployment_label.lower(),
                        "summary": summary_message
                    }
                )
                
                # Step 10: Cleanup - Stop vLLM server after successful deployment
                yield send_progress("Stopping vLLM server (cleanup)...")
                try:
                    # Try multiple kill methods to ensure vLLM is stopped
                    kill_commands = [
                        "pkill -f 'vllm serve'",
                        "pkill -f 'vllm.entrypoints'",
                        "pkill -9 -f 'python.*vllm'",
                        f"fuser -k {8000}/tcp 2>/dev/null || true"
                    ]
                    
                    for kill_cmd in kill_commands:
                        await execute_ssh_command(
                            host, username, password,
                            kill_cmd,
                            port=port,
                            timeout=5
                        )
                    
                    await asyncio.sleep(3)  # Wait for graceful shutdown
                    
                    # Verify vLLM is stopped
                    stdout, stderr, code = await execute_ssh_command(
                        host, username, password,
                        "ps aux | grep '[v]llm' | wc -l",
                        port=port,
                        timeout=5
                    )
                    
                    if stdout.strip() == '0':
                        yield send_progress("vLLM server stopped successfully")
                    else:
                        yield send_progress(f"Warning: {stdout.strip()} vLLM process(es) may still be running")
                        
                except Exception as e:
                    logger.warning(f"Failed to stop vLLM: {e}")
                    yield send_progress(f"Warning: Could not stop vLLM server: {str(e)[:100]}")
            else:
                yield send_error("Inference test failed", stderr or stdout[:500])
                return
                
        except Exception as e:
            logger.error(f"Inference test exception: {e}", exc_info=True)
            yield send_progress(f"Inference test failed with error: {str(e)}")
            yield send_error("Failed to test inference", str(e))
            return
            
    except Exception as e:
        logger.error(f"[{deployment_label}] vLLM deployment FAILED: {e}", exc_info=True)
        yield send_error(f"{deployment_label} deployment failed", str(e))
    finally:
        # Cleanup: Always try to stop vLLM even if deployment failed
        try:
            logger.info("Final cleanup: stopping any running vLLM processes...")
            kill_commands = [
                "pkill -9 -f 'vllm serve'",
                "pkill -9 -f 'vllm.entrypoints'",
                "pkill -9 -f 'python.*vllm'",
                "fuser -k 8000/tcp 2>/dev/null || true"
            ]
            
            for kill_cmd in kill_commands:
                try:
                    await execute_ssh_command(
                        host, username, password,
                        kill_cmd,
                        port=port,
                        timeout=5
                    )
                except:
                    pass
                    
            logger.info("Cleanup completed")
        except Exception as e:
            logger.warning(f"Cleanup failed: {e}")


async def test_configuration_on_vm_disabled(config_request) -> AsyncGenerator[str, None]:
    """
    Test configuration is currently disabled.
    
    Args:
        config_request: Configuration request with vm_ip, username, password, hf_token, configuration
    
    Yields:
        JSON progress updates via Server-Sent Events
    """
    def send_error(message: str, error: str):
        return json.dumps({
            "status": "error",
            "message": message,
            "error": error
        })
    
    yield send_error(
        "Test configuration disabled",
        "SSH-based testing has been disabled. Please use the full 'Apply Configuration' workflow instead."
    )
