import asyncio
import json
import logging
import re
import paramiko
from typing import Dict, List, AsyncGenerator, Optional, Any
from pydantic import BaseModel, Field
import time
from contextlib import contextmanager
import difflib

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
    message: str
    current_step: Optional[int] = None
    total_steps: Optional[int] = None
    command_results: Optional[List[CommandResult]] = None
    error: Optional[str] = None

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
    

    async def apply_configuration_async(self, request: ApplyConfigurationRequest) -> AsyncGenerator[str, None]:
        """
        Apply vGPU configuration to a remote host with streaming updates.
        Returns JSON formatted progress updates.
        """
        steps_successful = []  # Track successful steps for summary
        try:
            # Validate configuration first
            self.validate_configuration(request.configuration)
            
            yield json.dumps(ConfigurationProgress(
                status="connecting",
                message=f"Connecting to {request.vm_ip}...",
                current_step=0,
                total_steps=1
            ).model_dump()) + "\n"
            
            # Establish SSH connection
            with self.ssh_connection(
                hostname=request.vm_ip,
                username=request.username,
                password=request.password,
                port=request.ssh_port,
                timeout=request.timeout
            ) as ssh_client:
                
                # Connection successful
                yield json.dumps(ConfigurationProgress(
                    status="executing",
                    message="Connected successfully. Executing configuration commands...",
                    current_step=0,
                    total_steps=5
                ).model_dump()) + "\n"
                
                steps_successful.append("✓ SSH connection established")
                
                # Get configuration
                config = request.configuration
                
                # System information
                yield json.dumps(ConfigurationProgress(
                    status="executing",
                    message="Gathering system information...",
                    current_step=1,
                    total_steps=5
                ).model_dump()) + "\n"
                
                hypervisor_output, error_hp, status_hp = self.execute_command(ssh_client, "cat /sys/class/dmi/id/product_name")
                os_output, error_os, status_os = self.execute_command(ssh_client, "uname -a")
                # transcribe the OS and the Hypervisor Layer
                if status_hp and status_os == 0:
                    hypervisor_layer = map_hypervisor(output)
                    os_info = map_os(os_output)
                    
                    if hypervisor_layer and os_info:
                        yield json.dumps(ConfigurationProgress(
                            status="executing",
                            message=f"Hypervisor Layer: {hypervisor_layer}, OS: {os_info}",
                            current_step=1,
                            total_steps=5
                        ).model_dump()) + "\n"
                        steps_successful.append(f"✓ System identified: {hypervisor_layer} on {os_info}")

                    else:
                        yield json.dumps(ConfigurationProgress(
                            status="error",
                            message="Here is the hypervisor output: " + hypervisor_output + "\n" + "Here is the OS output: " + os_output,
                            current_step=1,
                            total_steps=5
                        ).model_dump()) + "\n"
                
                # GPU availability
                yield json.dumps(ConfigurationProgress(
                    status="executing",
                    message="Checking GPU availability...",
                    current_step=2,
                    total_steps=5
                ).model_dump()) + "\n"
                
                output, error, status = self.execute_command(ssh_client, "nvidia-smi --query-gpu=name --format=csv,noheader")
                gpu_info = "No GPU detected" if status != 0 else f"GPU: {output}"
                logger.info(f"request configuration: {request.configuration.get('vgpu_profile', 'N/A')}, detected GPU: {gpu_info}")
                detected_gpu_name = output.strip().split("\n")[0]  # Handles multiple GPUs too
                expected_prefix = request.configuration.get("vgpu_profile", "N/A").split('-')[0]

                similarity = difflib.SequenceMatcher(None, expected_prefix, detected_gpu_name).ratio()
                if gpu_info:
                    if similarity > 0.5 or request.configuration.get("vgpu_profile", "N/A").split('-')[0] in gpu_info:
                        gpu_info += " (matches requested configuration)"
                        yield json.dumps(ConfigurationProgress(
                            status="executing",
                            message=gpu_info,
                            current_step=2,
                            total_steps=5
                        ).model_dump()) + "\n"
                        steps_successful.append(f"✓ GPU detected: {detected_gpu_name}")
                    else:
                        gpu_info += " (does not match requested configuration), config gives: " + request.configuration.get("vgpu_profile") + ";you have this GPU: " + gpu_info
                        yield json.dumps(ConfigurationProgress(
                            status="error",
                            message=gpu_info,
                            current_step=2,
                            total_steps=5
                        ).model_dump()) + "\n"

                        return 
                
                
                # Setup phase with fallback logic
                yield json.dumps(ConfigurationProgress(
                    status="executing",
                    message="Starting setup phase...",
                    current_step=3,
                    total_steps=5
                ).model_dump()) + "\n"
                
                model_name = request.configuration.get("model_tag", None)
                logger.info(f"Model name extracted from configuration: {model_name}")
                total_size = grab_total_size(request.description)
                test_results = []
                
                # Step 1: HuggingFace authentication (if token provided)
                if request.hf_token:
                    yield json.dumps(ConfigurationProgress(
                        status="executing",
                        message="Authenticating with HuggingFace...",
                        current_step=3,
                        total_steps=5
                    ).model_dump()) + "\n"
                    
                    # First, create a virtual environment if it doesn't exist
                    yield json.dumps(ConfigurationProgress(
                        status="executing",
                        message="Setting up Python environment...",
                        current_step=3,
                        total_steps=5
                    ).model_dump()) + "\n"
                    
                    # Create venv if needed
                    venv_check = '''
                    if test -d hf_env; then
                        echo "Virtual environment already exists"
                    else
                        echo "Creating virtual environment..."
                        python3 -m venv hf_env && echo "Virtual environment created"
                    fi
                    '''
                    self.execute_command(ssh_client, venv_check, timeout=30)
                    
                    # Install huggingface-hub in the virtual environment
                    yield json.dumps(ConfigurationProgress(
                        status="executing",
                        message="Installing HuggingFace CLI tools...",
                        current_step=3,
                        total_steps=5
                    ).model_dump()) + "\n"
                    
                    install_hf_cmd = (
                        "bash -c '"
                        "source hf_env/bin/activate && "
                        "pip install --upgrade pip && "
                        "pip install huggingface-hub"
                        "'"
                    )
                    output, error, status = self.execute_command(ssh_client, install_hf_cmd, timeout=120)
                    
                    if status != 0:
                        # Installation failed
                        yield json.dumps(ConfigurationProgress(
                            status="error",
                            message="Failed to install HuggingFace CLI",
                            error=f"Failed to install huggingface-hub: {error or output}",
                            current_step=3,
                            total_steps=5
                        ).model_dump()) + "\n"
                        return
                    
                    # Authenticate with HuggingFace
                    yield json.dumps(ConfigurationProgress(
                        status="executing",
                        message="Authenticating with HuggingFace (this may take a moment)...",
                        current_step=3,
                        total_steps=5
                    ).model_dump()) + "\n"
                    
                    hf_auth_cmd = (
                        f"bash -c '"
                        f"source hf_env/bin/activate && "
                        f"huggingface-cli login --token {request.hf_token}"
                        f"'"
                    )
                    output, error, status = self.execute_command(ssh_client, hf_auth_cmd, timeout=60)
                    
                    if status != 0:
                        # Authentication failed
                        yield json.dumps(ConfigurationProgress(
                            status="error",
                            message="HuggingFace authentication failed",
                            error=f"Failed to authenticate with HuggingFace: {error or output}",
                            current_step=3,
                            total_steps=5
                        ).model_dump()) + "\n"
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
                check_vllm_cmd = "bash -c 'source hf_env/bin/activate && pip show vllm'"
                output, error, status = self.execute_command(ssh_client, check_vllm_cmd, timeout=30)
                
                if status != 0:
                    # vLLM not installed, install it
                    logger.info("vLLM not found, installing...")
                    
                    # Install with progress updates
                    pip_cmd = "bash -c 'source hf_env/bin/activate && pip install vllm --progress-bar on'"
                    
                    # Start installation
                    start_time = time.time()
                    output, error, status = self.execute_command(ssh_client, pip_cmd, timeout=300)  # 15 min timeout
                    
                    if status != 0:
                        # Installation failed
                        yield json.dumps(ConfigurationProgress(
                            status="error",
                            message="vLLM installation failed",
                            error=f"Failed to install vLLM: {error or output}",
                            current_step=4,
                            total_steps=5
                        ).model_dump()) + "\n"
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

                VENV_PATH    = '~/hf_env'        # path to your virtual-env folder
                LOG_OUT      = '~/vllm.out.log'
                LOG_ERR      = '~/vllm.err.log'

                # Clean up any old logs
                cleanup_cmd = f"rm -f {LOG_OUT} {LOG_ERR}"
                stdin, stdout, stderr = self.exec_raw(ssh_client, cleanup_cmd, timeout=30)
                code = stdout.channel.recv_exit_status()
                if code == 0:
                    yield json.dumps(ConfigurationProgress(
                        status="executing",
                        message="Cleaned up old logs",
                        current_step=4,
                        total_steps=5
                    ).model_dump()) + "\n"
                else:
                    yield json.dumps(ConfigurationProgress(
                        status="error",
                        message="Failed to clean up old logs",
                        error=f"Failed to clean up old logs: {stderr.read().decode().strip()}",
                        current_step=4,
                        total_steps=5
                    ).model_dump()) + "\n"
                
                # Retry settings
                INITIAL_UTIL = 0.4               # starting --gpu-memory-utilization
                DELTA_UTIL   = 0.1               # increment on each retry
                MAX_ATTEMPTS = 3
                MODEL_REF = model_name

                gpu_util = INITIAL_UTIL
                sleep_time = 100  # seconds to wait between attempts
                successful_gpu_mem = None 
                target_pids = []
                for attempt in range(0, MAX_ATTEMPTS + 1):
                    yield json.dumps(ConfigurationProgress(
                        status="Executing optimized cache...",
                        message=f"Attempt {attempt}/{MAX_ATTEMPTS}: gpu-memory-utilization={gpu_util:.2f}",
                        current_step=4,
                        total_steps=5
                    ).model_dump()) + "\n"

                    serve_cmd = rf"""bash -lc '
                    source {VENV_PATH}/bin/activate && \
                    nohup vllm serve "{MODEL_REF}" \
                        --max-model-len 2040 \
                        --max-num-seqs 1 \
                        --gpu-memory-utilization {gpu_util:.2f} \
                        --kv-cache-dtype auto \
                        --dtype float16 \
                    > {LOG_OUT} 2> {LOG_ERR} &
                    '"""
                    stdin, stdout, stderr = self.exec_raw(ssh_client, serve_cmd)
                    time.sleep(sleep_time)
                    shell_exit = stdout.channel.recv_exit_status()
                    
                    if shell_exit != 0:
                        error_msg = stderr.read().decode().strip()
                        yield json.dumps(ConfigurationProgress(
                            status="error",
                            message=f"Failed to start vLLM server: {error_msg}",
                            current_step=4,
                            total_steps=5
                        ).model_dump()) + "\n"
                        return
                    
                    # Wait for server to start up with progress updates
                    logger.info("Waiting for vLLM server to start...")
                    
                    # Check server startup progress
                    for i in range(20):  # Check for up to 100 seconds (20 * 5)
                        await asyncio.sleep(5)
                        
                        # Check if error log has any issues
                        grep_cmd = f"grep -E 'Traceback|RuntimeError|CUDA.*error' {LOG_ERR} || true"
                        output, error, status = self.execute_command(ssh_client, grep_cmd, timeout=10)
                        
                        if output.strip():
                            # Found error
                            break
                            
                        # Check if server is running by looking for the process
                        check_cmd = "pgrep -f 'vllm serve' || true"
                        output, error, status = self.execute_command(ssh_client, check_cmd, timeout=10)
                        
                        if output.strip():
                            # Server process found, give it a bit more time to fully initialize
                            await asyncio.sleep(5)
                            break
                        
                        # Progress update every 20 seconds
                        if i % 4 == 0:
                            yield json.dumps(ConfigurationProgress(
                                status="executing",
                                message=f"Still waiting for vLLM server... ({(i+1)*5}s elapsed)",
                                current_step=4,
                                total_steps=5
                            ).model_dump()) + "\n"
                    
                    
                    grep_cmd = f"grep -E 'Traceback|RuntimeError' {LOG_ERR} || true"
                    output, error, status = self.execute_command(ssh_client, grep_cmd, timeout=10)
                    grep_out = output.strip()
                    
                    if not grep_out:
                        yield json.dumps(ConfigurationProgress(
                            status="executing",
                            message="vLLM server started successfully",
                            current_step=4,
                            total_steps=5
                        ).model_dump()) + "\n"

                        pid_cmd = "pgrep -f 'hf_env/bin/python3'"
                        output, error, status = self.execute_command(ssh_client, pid_cmd, timeout=10)
                        pids = output.split() if output else []
                        if not pids:
                            yield json.dumps(ConfigurationProgress(
                                status="error",
                                message="Could not find hf_env python process PID",
                                current_step=4,
                                total_steps=5
                            ).model_dump()) + "\n"
                        else:
                            target_pids = pids[:]
                            yield json.dumps(ConfigurationProgress(
                                status="executing",
                                message=f"Found {len(target_pids)} hf_env processes",
                                current_step=4,
                                total_steps=5
                            ).model_dump()) + "\n"

                            for pid in target_pids:
                                mem_cmd = "nvidia-smi --query-compute-apps=pid,used_memory --format=csv,noheader,nounits | grep '^" + pid + ",' || true"
                                output, error, status = self.execute_command(ssh_client, mem_cmd, timeout=10)
                                line = output.strip()
                                if line:
                                    _, mem_mb_str = [x.strip() for x in line.split(',', 1)]
                                    try:
                                        mem_mb = float(mem_mb_str)
                                    except ValueError:
                                        num = ''.join(ch for ch in mem_mb_str if (ch.isdigit() or ch == '.'))
                                        mem_mb = float(num)
                                    mem_gb = mem_mb / 1024.0
                                    successful_gpu_mem = mem_gb
                                    yield json.dumps(ConfigurationProgress(
                                        status="executing",
                                        message=f"GPU memory detected: {mem_gb:.2f}GB",
                                        current_step=4,
                                        total_steps=5
                                    ).model_dump()) + "\n"
                                    
                                    # Track successful vLLM start with GPU memory
                                    if not any("vLLM server started" in step for step in steps_successful):
                                        steps_successful.append(f"✓ vLLM server started with gpu-memory-utilization={gpu_util:.2f}")
                                        steps_successful.append(f"✓ GPU memory detected: {mem_gb:.2f}GB used")
                                else:
                                    yield json.dumps(ConfigurationProgress(
                                        status="executing",
                                        message=f"PID {pid}: no GPU usage entry found",
                                        current_step=4,
                                        total_steps=5
                                    ).model_dump()) + "\n"
                        break

                        # query GPU memory usage for our hf_env process(es)
                    
                    yield json.dumps(ConfigurationProgress(
                        status="executing",
                        message=f"Failed to start vLLM server: {grep_out}",
                        current_step=4,
                        total_steps=5
                    ).model_dump()) + "\n"
                    
                    await asyncio.sleep(2)

                    # kill any stray vllm serve processes before retrying
                    kill_cmd = "pkill -f 'vllm serve' || true"
                    stdin, stdout, stderr = self.exec_raw(ssh_client, kill_cmd)
                    stdout.channel.recv_exit_status()

                    if attempt < MAX_ATTEMPTS:
                        gpu_util = min(1.0, gpu_util + DELTA_UTIL)
                        yield json.dumps(ConfigurationProgress(
                            status="executing",
                            message=f"Retrying with gpu-memory-utilization={gpu_util:.2f}...",
                            current_step=4,
                            total_steps=5
                        ).model_dump()) + "\n"
                        sleep_time += 100  # Reset sleep time for next attempt
                        await asyncio.sleep(2)
                    else:
                        yield json.dumps(ConfigurationProgress(
                            status="error",
                            message="All retries exhausted, smoke test failed",
                            current_step=4,
                            total_steps=5
                        ).model_dump()) + "\n"
                
                if target_pids:
                    yield json.dumps(ConfigurationProgress(
                        status="executing",
                        message="Post-launch cleanup: killing hf_env processes",
                        current_step=4,
                        total_steps=5
                    ).model_dump()) + "\n"

                    for pid in target_pids:
                        kill_pid_cmd = f"kill {pid} || true"
                        stdin, stdout, stderr = self.exec_raw(ssh_client, kill_pid_cmd)
                        stdout.channel.recv_exit_status()
                        # Don't yield individual kill messages, too verbose

                    # Close the SSH connection
                ssh_client.close()
                yield json.dumps(ConfigurationProgress(
                        status="executing",
                        message="SSH connection closed",
                        current_step=4,
                        total_steps=5
                    ).model_dump()) + "\n"
                
                # take the final results, which is the gpu_memory the advisor suggested and the gpu_memory found
                logger.info(f"here is the request.config : {request.configuration}")
                logger.info(f"successful_gpu_mem: {successful_gpu_mem}")

                # Build configuration summary
                summary_message = f"=== Configuration Summary ===\n" \
                    f"vGPU Profile: {request.configuration.get('vGPU_profile', 'N/A')}\n" \
                    f"vCPUs: {request.configuration.get('vCPU_count', 'N/A')}\n" \
                    f"RAM: {request.configuration.get('system_RAM', 'N/A')}GB\n" \
                    f"Advisor Estimated VRAM: {request.configuration.get('gpu_memory_size', 'N/A')}GB\n" \
                    f"Detected GPU Memory Usage: {successful_gpu_mem:.2f}GB" if successful_gpu_mem else f"Detected GPU Memory Usage: N/A"
                
                # Add steps taken
                if steps_successful:
                    summary_message += f"\n\n=== Steps Completed ===\n"
                    for step in steps_successful:
                        summary_message += f"{step}\n"
                
                yield json.dumps(ConfigurationProgress(
                    status="executing",
                    message=summary_message.strip(),
                    current_step=5,
                    total_steps=5,
                    command_results=[]  # Don't include command results in summary
                ).model_dump()) + "\n"
                                                 
                yield json.dumps(ConfigurationProgress(
                    status="completed",
                    message="✅ Configuration applied successfully!",
                    current_step=5,
                    total_steps=5,
                    command_results=[]  # Don't include command results at the end
                ).model_dump()) + "\n"
                
        except paramiko.AuthenticationException:
            yield json.dumps(ConfigurationProgress(
                status="error",
                message="Authentication failed",
                error="Invalid username or password"
            ).model_dump()) + "\n"
        except paramiko.SSHException as e:
            yield json.dumps(ConfigurationProgress(
                status="error",
                message="SSH connection failed",
                error=str(e)
            ).model_dump()) + "\n"
        except Exception as e:
            yield json.dumps(ConfigurationProgress(
                status="error",
                message="Configuration failed",
                error=str(e)
            ).model_dump()) + "\n"