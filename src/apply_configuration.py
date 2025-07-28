import asyncio
import json
import logging
import math
import re
import paramiko
from typing import Dict, List, AsyncGenerator, Optional, Any
from pydantic import BaseModel, Field
from contextlib import contextmanager
import time
import difflib
from collections import OrderedDict


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

# Initialize the model extractor with known tags
MODEL_TAGS = [
    "meta-llama/Meta-Llama-3-8B-Instruct",
    "meta-llama/Llama-3.1-8B-Instruct",
    "meta-llama/Llama-3.3-70B-Instruct",
    "meta-llama/Meta-Llama-3-70B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3",
    "Qwen/Qwen3-14B",
    "tiiuae/falcon-40b-instruct",
    "tiiuae/falcon-180B"
]

model_extractor = ModelNameExtractor(MODEL_TAGS, fuzzy_cutoff=0.6)

# Define request and response models
class ApplyConfigurationRequest(BaseModel):
    """Request model for applying vGPU configuration to a remote host."""
    vm_ip: str = Field(..., description="IP address of the VM to configure")
    username: str = Field(..., description="SSH username")
    password: str = Field(..., description="SSH password")
    configuration: Dict[str, Any] = Field(..., description="vGPU configuration to apply")
    ssh_port: int = Field(default=22, description="SSH port")
    timeout: int = Field(default=30, description="SSH connection timeout")
    hf_token: Optional[str] = Field(None, description="Hugging Face token for model downloads")
    description: Optional[str] = Field(None, description="Original query description")

    temperature: Optional[float] = Field(None, description="LLM sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for LLM response")
    model: Optional[str] = Field(None, description="LLM model name")
    llm_endpoint: Optional[str] = Field(None, description="LLM endpoint URL")


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

class VGPUConfigurationApplier:
    """
    Handles applying vGPU configurations to remote hosts via SSH.
    Implements the SSH connection logic from the notebook with streaming updates.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    @contextmanager
    def ssh_connection(self, hostname: str, username: str, password: str, 
                      port: int = 22, timeout: int = 30):
        """
        Context manager for SSH connections using Paramiko.
        """
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
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
        except paramiko.AuthenticationException as e:
            self.logger.error(f"Authentication failed: {e}")
            raise
        except paramiko.SSHException as e:
            self.logger.error(f"SSH connection failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Connection error: {e}")
            raise
        finally:
            ssh_client.close()
            self.logger.info("SSH connection closed")
    
    def execute_command(self, ssh_client: paramiko.SSHClient, command: str, 
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
    
    def exec_raw(self, ssh_client: paramiko.SSHClient, command: str, timeout: int = 300):
        """
        Execute a command and return raw stdin, stdout, stderr channels.
        
        Args:
            ssh_client: Paramiko SSH client
            command: Command to execute
            timeout: Command timeout in seconds
        """
        return ssh_client.exec_command(command, timeout=timeout)
    
    def stream_exec(self, ssh_client: paramiko.SSHClient, command: str, timeout: int = 300):
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
    
    async def stream_command_output(self, ssh_client: paramiko.SSHClient, 
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
                
        except paramiko.AuthenticationException:
            yield "❌ Authentication failed. Please check your credentials."
        except paramiko.SSHException as e:
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
    
    async def wait_for_vllm_live(self, ssh_client: paramiko.SSHClient, gpu_util: float, 
                                    model_ref: str, venv_path: str, total_size: int, port: int = 8000) -> tuple[bool, str, Optional[str]]:
        """
        Start vLLM server and watch output for readiness or failure.
        Returns (success, message)
        """
        serve_cmd = rf"""bash -lc "source $HOME/hf_env/bin/activate && \
        vllm serve '{model_ref}' \
        --host 0.0.0.0 \
        --port {port} \
        --max-model-len {total_size} \
        --max-num-seqs 1 \
        --gpu-memory-utilization {gpu_util:.2f} \
        --kv-cache-dtype auto \
        --dtype float16 \
        --disable-custom-all-reduce \
        --skip-tokenizer-init 2>&1"
        """
        
        logger.info(f"vLLM command: {serve_cmd}")

        
        stdin, stdout, stderr = ssh_client.exec_command(serve_cmd, get_pty=True)
        
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
                                    # Return immediately with success
                                    return True, f"{used:.2f} GB", kv_cache_size if kv_cache_size else None
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
                    pid, used = [x.strip() for x in row.split(",")]
                    # Check process args for venv path
                    ps_cmd = f"ps -p {pid} -o args="
                    tdin3, stdout3, _ = ssh_client.exec_command(ps_cmd)
                    args = stdout3.read().decode().strip()
                    logger.info(f"Process args for PID {pid}: {args}")
                    if re.search(r"/hf_env/bin/python3(\s|$)", args):
                        logger.info(f"Found vLLM process with PID {pid} and used: {used}")
                        used = int(used)
                        # convert to GB
                        used = used / 1024  # Convert from MiB to GB
                        found = True
                        break
                
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
                if status_hp and status_os == 0:
                    hypervisor_layer = map_hypervisor(output)
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
                gpu_info = "No GPU detected" if status != 0 else f"GPU: {output}"
                logger.info(f"request configuration: {request.configuration.get('vgpu_profile', 'N/A')}, detected GPU: {gpu_info}")
                detected_gpu_name = output.strip().split("\n")[0]  # Handles multiple GPUs too
                expected_prefix = request.configuration.get("vgpu_profile", "N/A").split('-')[0]

                similarity = difflib.SequenceMatcher(None, expected_prefix, detected_gpu_name).ratio()
                if gpu_info:
                    if similarity > 0.5 or request.configuration.get("vgpu_profile", "N/A").split('-')[0] in gpu_info:
                        gpu_info += " (matches requested configuration)"
                        async for msg in yield_progress(ConfigurationProgress(
                            status="executing",
                            message=gpu_info,
                            current_step=2,
                            total_steps=5
                        )):
                            yield msg
                        steps_successful.append(f"✓ GPU detected: {detected_gpu_name}")
                    else:
                        gpu_info += " (does not match requested configuration), config gives: " + request.configuration.get("vgpu_profile") + ";you have this GPU: " + gpu_info
                        async for msg in yield_progress(ConfigurationProgress(
                            status="error",
                            message=gpu_info,
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
                    # Check for python3, python3-venv, and python3-pip
                    PYTHON_OK=0
                    command -v python3 >/dev/null 2>&1 || PYTHON_OK=1
                    python3 -m venv --help >/dev/null 2>&1 || PYTHON_OK=1
                    command -v pip3 >/dev/null 2>&1 || PYTHON_OK=1

                    if [ $PYTHON_OK -eq 1 ]; then
                        echo "{request.password}" | sudo -S apt update
                        echo "{request.password}" | sudo -S apt install -y python3 python3-venv python3-pip
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
                        python3 -m venv {VENV_PATH} && echo "✅ venv created" || echo "❌ venv creation failed"
                        
                        # Verify activate script was created
                        if test -f {VENV_PATH}/bin/activate; then
                            echo "✅ Activate script verified"
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
                
                # Step 2: Check and install vLLM
                logger.info("Checking vLLM installation status")
                # Check if vLLM is already installed in the virtual environment
                check_vllm_cmd = rf"""bash -lc '
                source {VENV_PATH}/bin/activate
                pip show vllm
                '"""
                output, error, status = self.execute_command(ssh_client, check_vllm_cmd, timeout=30)
                
                if status != 0:
                    # vLLM not installed, install it
                    logger.info("vLLM not found, installing...")
                    
                    # Install with progress updates
                    pip_cmd = rf"""bash -lc '
                    source {VENV_PATH}/bin/activate
                    pip install vllm --progress-bar on
                    '"""
                    
                    # Start installation
                    start_time = time.time()
                    async for msg in yield_progress(ConfigurationProgress(
                        status="executing",
                        message="Installing vLLM (this may take several minutes)...",
                        current_step=4,
                        total_steps=5,
                        display_message="Installing vLLM framework (this may take 5-10 minutes)..."
                    )):
                        yield msg
                    
                    output, error, status = self.execute_command(ssh_client, pip_cmd, timeout=900)  # 15 min timeout
                    
                    if status != 0:
                        # Installation failed
                        async for msg in yield_progress(ConfigurationProgress(
                            status="error",
                            message="vLLM installation failed",
                            error=f"Failed to install vLLM: {error or output}",
                            current_step=4,
                            total_steps=5
                        )):
                            yield msg
                        return
                    
                    # Installation successful
                    elapsed_time = int(time.time() - start_time)
                    steps_successful.append(f"✓ vLLM installed successfully (took {elapsed_time}s)")

                    
                    test_results.append(CommandResult(
                        command=pip_cmd,
                        output="vLLM installed successfully",
                        error="",
                        success=True,
                        timestamp=time.time()
                    ))
                else:
                    # vLLM already installed
                    logger.info("vLLM is already installed")
                    steps_successful.append("✓ vLLM already installed")
                    
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
                    INITIAL_UTIL = ratio
                    
                else:
                    INITIAL_UTIL = 0.5               # starting default

                DELTA_UTIL   = 0.1               # increment on each retry
                MAX_ATTEMPTS = 4                 # number of attempts to find optimal memory
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

                    if attempt > 1:
                        cleanup_cmds = ["pkill -f 'vllm serve' || true", "pkill -f 'python3 -m vllm.serve.cli' || true", "sleep 3"]
                        for cmd in cleanup_cmds:
                            self.execute_command(ssh_client, cmd)
                            logger.info(f"Cleaned up vLLM process: {cmd}")
                    
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
                            gpu_util += DELTA_UTIL
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
                
        except paramiko.AuthenticationException:
            async for msg in yield_progress(ConfigurationProgress(
                status="error",
                message="Authentication failed",
                error="Invalid username or password"
            )):
                yield msg
        except paramiko.SSHException as e:
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
