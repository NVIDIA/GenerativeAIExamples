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
    
def calculate_gpu_memory_utilization(
    vgpu_profile: str,
    physical_gpu_memory_gb: Optional[float] = None,
    is_vgpu_environment: bool = False,
    recommended_workload_gb: Optional[float] = None,
    kv_cache_gb: Optional[float] = None
) -> float:
    """
    Calculate BARE MINIMUM GPU memory utilization for local testing.
    
    Args:
        vgpu_profile: Recommended vGPU profile (e.g., "DC-12Q", "L40S-48Q")
        physical_gpu_memory_gb: Total physical GPU memory in GB (if detected)
        is_vgpu_environment: True if running on actual vGPU, False if bare metal
        recommended_workload_gb: Total workload memory (model + KV cache) from calculator
        kv_cache_gb: Estimated KV cache memory requirement (for logging only)
    
    Returns:
        Float between 0.0 and 1.0 representing GPU memory utilization percentage
    
    Logic:
        - Formula: workload / physical_memory (NO safety buffer for bare minimum)
        - Uses FULL workload (model + KV cache) - vLLM allocates this as total budget
        - If on actual vGPU: use 0.9 (90%) since hypervisor limits memory
        - If unknown: use conservative 0.4 (40%)
        - Always passes max_kv_tokens to cap context length at calculated minimum
    
    Example:
        - 15GB workload (13GB model + 2GB KV) on 48GB: 15 / 48 = 31.25%
        - 24GB workload (20GB model + 4GB KV) on 96GB: 24 / 96 = 25.0%
    """
    logger.info(f"Calculating GPU memory utilization for profile: {vgpu_profile}")
    logger.info(f"  Physical GPU memory: {physical_gpu_memory_gb}GB")
    logger.info(f"  Is vGPU environment: {is_vgpu_environment}")
    logger.info(f"  Recommended workload size: {recommended_workload_gb}GB" if recommended_workload_gb else "  Recommended workload size: Not provided")
    logger.info(f"  Estimated KV cache: {kv_cache_gb}GB" if kv_cache_gb else "  KV cache size: Not provided")
    
    # If running on actual vGPU, use high utilization since hypervisor limits it
    if is_vgpu_environment:
        logger.info("  → Running on vGPU, using 90% utilization")
        return 0.9
    
    # Use recommended workload size if provided, otherwise extract from profile
    workload_memory_gb = recommended_workload_gb
    
    if not workload_memory_gb:
        # Extract profile memory size from vGPU profile name (e.g., "DC-12Q" → 12)
        try:
            import re
            match = re.search(r'-(\d+)Q', vgpu_profile)
            if match:
                workload_memory_gb = int(match.group(1))
                logger.info(f"  Profile memory extracted: {workload_memory_gb}GB")
            else:
                logger.warning(f"  Could not extract memory size from profile '{vgpu_profile}'")
        except Exception as e:
            logger.warning(f"  Error parsing vGPU profile: {e}")
    
    if workload_memory_gb:
        # Use FULL workload (model + KV cache) - vLLM needs total memory allocation
        # The calculator already computed the exact minimum needed
        logger.info(f"  Total workload memory: {workload_memory_gb:.2f}GB (includes model + KV cache)")
        if kv_cache_gb and kv_cache_gb > 0:
            logger.info(f"    ├─ KV cache portion: ~{kv_cache_gb:.2f}GB (for {kv_cache_gb/0.0005 if kv_cache_gb < 10 else 'large'} tokens)")
            logger.info(f"    └─ Model + overhead: ~{workload_memory_gb - kv_cache_gb:.2f}GB")
        
        # If we know physical GPU size, calculate ratio
        if physical_gpu_memory_gb and physical_gpu_memory_gb > 0:
            # BARE MINIMUM for local testing: No safety buffer, just what's needed
            # This gives maximum GPU efficiency for testing purposes
            safety_factor = 1.0
            target_memory = workload_memory_gb * safety_factor
            
            # Calculate utilization - NO HARD CAPS, let it run even if high
            utilization = target_memory / physical_gpu_memory_gb
            
            # Warn if utilization is very high, but don't prevent deployment
            if utilization > 0.90:
                logger.warning(f"  ⚠️  HIGH UTILIZATION: {utilization:.1%} - May have limited KV cache space")
                logger.warning(f"  ⚠️  Consider using a larger GPU or reducing max_kv_tokens")
            elif utilization > 0.75:
                logger.info(f"  ⚠️  MODERATE-HIGH UTILIZATION: {utilization:.1%} - Monitor memory usage")
            
            # Don't go below 10% utilization (minimum practical)
            utilization = max(utilization, 0.10)
            
            logger.info(f"  → BARE MINIMUM utilization: {workload_memory_gb:.2f}GB / {physical_gpu_memory_gb}GB = {utilization:.2%}")
            logger.info(f"  → vLLM will allocate: {physical_gpu_memory_gb * utilization:.1f}GB of {physical_gpu_memory_gb:.1f}GB")
            if utilization < 1.0:
                logger.info(f"  → Remaining {physical_gpu_memory_gb * (1 - utilization):.1f}GB available for other workloads")
            else:
                logger.warning(f"  → ⚠️  Workload exceeds physical GPU - vLLM will try to fit within available memory")
            logger.info(f"  → This is the MINIMUM needed for testing (max_kv_tokens capped)")
            return utilization
        else:
            # Physical GPU unknown, estimate based on vGPU profile family
            if vgpu_profile.startswith("DC") or vgpu_profile.startswith("BSE"):
                estimated_physical = 96
            elif vgpu_profile.startswith(("L40S", "L40", "A40")):
                estimated_physical = 48
            elif vgpu_profile.startswith("L4"):
                estimated_physical = 24
            else:
                estimated_physical = 48  # Default
            
            # Use same calculation with estimated physical memory - BARE MINIMUM
            safety_factor = 1.0
            target_memory = workload_memory_gb * safety_factor
            utilization = target_memory / estimated_physical
            
            # Warn if utilization is very high
            if utilization > 0.90:
                logger.warning(f"  ⚠️  HIGH UTILIZATION: {utilization:.1%} (estimated)")
            elif utilization > 0.75:
                logger.info(f"  ⚠️  MODERATE-HIGH UTILIZATION: {utilization:.1%} (estimated)")
            
            utilization = max(utilization, 0.10)
            
            logger.info(f"  → BARE MINIMUM utilization: {workload_memory_gb:.2f}GB / {estimated_physical}GB (estimated) = {utilization:.2%}")
            logger.info(f"  → vLLM will allocate: {estimated_physical * utilization:.1f}GB of {estimated_physical}GB (estimated)")
            if utilization < 1.0:
                logger.info(f"  → Remaining {estimated_physical * (1 - utilization):.1f}GB available for other workloads")
            else:
                logger.warning(f"  → ⚠️  Workload exceeds physical GPU - vLLM will try to fit within available memory")
            logger.info(f"  → This is the MINIMUM needed for testing (max_kv_tokens capped)")
            return utilization
    
    # Fallback to conservative default
    logger.info("  → Using fallback conservative utilization: 40%")
    return 0.4


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
    """Request model for applying vGPU configuration locally with Docker."""
    deployment_mode: str = Field(default="local", description="Deployment mode (always 'local')")
    configuration: Dict[str, Any] = Field(..., description="vGPU configuration to apply")
    hf_token: str = Field(..., description="Hugging Face token for model downloads (required)")
    description: Optional[str] = Field(None, description="Original query description")
    
    temperature: Optional[float] = Field(None, description="LLM sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for LLM response")
    model: Optional[str] = Field(None, description="LLM model name")
    model_tag: Optional[str] = Field(None, description="Model tag/ID for vLLM deployment (e.g., mistralai/Mistral-7B-Instruct-v0.3)")
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

async def deploy_vllm_local(config_request) -> AsyncGenerator[str, None]:
    """
    Deploy vLLM locally using Docker container.
    This runs vLLM in a Docker container with GPU access on the local machine.
    """
    import subprocess
    import socket
    import os
    from datetime import datetime
    
    # Collect debug logs to output at the end
    debug_logs = []
    
    def send_progress(message: str, is_debug: bool = False):
        """Send progress message. If is_debug=True, save for later output."""
        if is_debug:
            debug_logs.append(message)
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
            "display_message": f"{message}",
            "deployment_type": "local"
        })
    
    def send_success(message: str, data: dict = None):
        response = {
            "status": "success",
            "message": message,
            "display_message": f"{message}",
            "deployment_type": "local"
        }
        if data:
            response.update(data)
        return json.dumps(response)
    
    def run_command(cmd: str, shell: bool = True) -> tuple:
        """Run a command and return (stdout, stderr, returncode)"""
        try:
            result = subprocess.run(
                cmd,
                shell=shell,
                capture_output=True,
                text=True,
                timeout=300
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            return "", "Command timed out", 1
        except Exception as e:
            return "", str(e), 1
    
    try:
        # Get configuration
        config = config_request.configuration
        model = (
            getattr(config_request, 'model_tag', None) or 
            getattr(config_request, 'model', None) or 
            config.get('model_tag', None) or 
            config.get('model_name', None) or
            'meta-llama/Llama-3.1-8B-Instruct'
        )
        hf_token = config_request.hf_token or os.environ.get('HUGGING_FACE_HUB_TOKEN', '')
        max_tokens = config.get('max_kv_tokens', None)
        vgpu_profile = config.get('vgpu_profile', 'N/A')
        
        # Use calculated max_kv_tokens from calculator if available
        # This ensures KV cache fits within the allocated GPU memory
        if max_tokens:
            # Cap at reasonable model limits to avoid exceeding max_position_embeddings
            # Common model limits: Mistral/Llama-2: 32K, Llama-3: 8K, GPT-2: 1K
            # Use 16K as safe default since KV cache scales with context length
            # 32K requires ~4GB KV cache which often exceeds available memory with bare minimum utilization
            MAX_SAFE_CONTEXT = 16384  # 16K tokens - safe for most bare minimum deployments
            if max_tokens > MAX_SAFE_CONTEXT:
                logger.warning(f"Calculator max_tokens ({max_tokens}) exceeds safe limit ({MAX_SAFE_CONTEXT})")
                logger.warning(f"Capping at {MAX_SAFE_CONTEXT} to ensure KV cache fits within GPU memory")
                max_tokens = MAX_SAFE_CONTEXT
            logger.info(f"Using calculator-determined max_tokens: {max_tokens} (fits within GPU utilization)")
        else:
            # Fallback: let vLLM auto-detect, but this may fail if GPU utilization is low
            logger.info(f"No max_tokens provided, vLLM will auto-detect (may fail with low GPU utilization)")
            max_tokens = None
        
        # Detect physical GPU memory and calculate appropriate utilization
        physical_gpu_memory = None
        is_vgpu = False
        try:
            stdout, stderr, code = run_command("nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits")
            if code == 0 and stdout:
                physical_gpu_memory = float(stdout.strip()) / 1024  # Convert MB to GB
                logger.info(f"Detected physical GPU memory: {physical_gpu_memory:.1f}GB")
                
                # Detect if running on vGPU by checking if memory matches common vGPU profiles
                # Only consider smaller sizes as vGPU - 96GB+ are typically bare metal datacenter GPUs
                common_vgpu_sizes = [12, 16, 24, 32, 48]
                is_vgpu = any(abs(physical_gpu_memory - size) < 1.0 for size in common_vgpu_sizes)
                logger.info(f"Environment detected as: {'vGPU' if is_vgpu else 'Bare Metal'}")
        except Exception as e:
            logger.warning(f"Could not detect GPU memory: {e}")
        
        # Calculate GPU utilization based on vGPU profile recommendation
        if 'gpu_memory_utilization' in config:
            # Use explicitly provided value if exists
            gpu_util = config['gpu_memory_utilization']
            logger.info(f"Using provided GPU utilization: {gpu_util:.0%}")
        else:
            # Get recommended workload size from calculator
            recommended_workload_gb = config.get('gpu_memory_size', None)
            logger.info(f"Configuration gpu_memory_size: {recommended_workload_gb}GB" if recommended_workload_gb else "Configuration gpu_memory_size: NOT PROVIDED")
            
            # Estimate KV cache size from max_kv_tokens dynamically based on model
            # KV cache per token varies with model size and parameters
            # Extract model size from name to estimate KV cache per token
            kv_cache_gb = None
            if max_tokens and recommended_workload_gb:
                # Dynamic estimation: KV cache per token scales with model size
                # Typical: 0.3-0.8 MB/token depending on model
                # Use workload size as proxy for model complexity
                if recommended_workload_gb <= 10:  # Small models (1-3B)
                    kv_mb_per_token = 0.3
                elif recommended_workload_gb <= 20:  # Medium models (7-13B)
                    kv_mb_per_token = 0.5
                elif recommended_workload_gb <= 50:  # Large models (30-70B)
                    kv_mb_per_token = 0.7
                else:  # Very large models (70B+)
                    kv_mb_per_token = 1.0
                
                kv_cache_gb = max_tokens * (kv_mb_per_token / 1024)  # Convert MB to GB
                logger.info(f"Dynamic KV cache estimate: {kv_cache_gb:.2f}GB ({kv_mb_per_token}MB/token × {max_tokens} tokens)")
            elif max_tokens:
                # Fallback if no workload size: use conservative estimate
                kv_cache_gb = max_tokens * 0.0005  # 0.5 MB/token
                logger.info(f"Conservative KV cache estimate: {kv_cache_gb:.2f}GB for {max_tokens} tokens")
            elif recommended_workload_gb:
                # Fallback: estimate as ~10% of total workload
                kv_cache_gb = recommended_workload_gb * 0.10
                logger.info(f"Fallback KV cache estimate (10% of workload): {kv_cache_gb:.2f}GB")
            
            # Calculate based on vGPU profile, physical GPU, and recommended workload
            gpu_util = calculate_gpu_memory_utilization(
                vgpu_profile=vgpu_profile,
                physical_gpu_memory_gb=physical_gpu_memory,
                is_vgpu_environment=is_vgpu,
                recommended_workload_gb=recommended_workload_gb,
                kv_cache_gb=kv_cache_gb
            )
            logger.info(f"Calculated GPU utilization: {gpu_util:.0%} for profile {vgpu_profile}")
        
        # Determine workload type from description if available
        description = config_request.description or ""
        workload_type = "Inference"  # default
        if description:
            desc_lower = description.lower()
            if "rag" in desc_lower or "retrieval" in desc_lower:
                workload_type = "RAG"
            elif "fine-tun" in desc_lower or "training" in desc_lower:
                workload_type = "Training"
        
        # Start deployment
        logger.info("=" * 80)
        logger.info(">>> LOCAL DOCKER DEPLOYMENT <<<")
        logger.info("=" * 80)
        
        # Output header
        yield send_progress("=== vLLM Deployment Export ===")
        yield send_progress(f"Date: {datetime.now().strftime('%m/%d/%Y, %I:%M:%S %p')}")
        yield send_progress(f"Mode: Local Docker Deployment")
        yield send_progress("=" * 60)
        yield send_progress("")
        
        # Display RAG workload notice if applicable
        if workload_type == "RAG":
            yield send_progress("⚠️  RAG WORKLOAD DETECTED")
            yield send_progress("⚠️  NOTE: This deployment tests only the chat model inference.")
            yield send_progress("⚠️  You must separately account for vector database size and embedding model")
            yield send_progress("⚠️  when deploying a complete RAG system.")
            yield send_progress("")
            logger.info("RAG workload detected - displaying vector DB and embedding model notice")
        
        # Step 1: Starting configuration test
        yield send_progress("Step 1: Starting configuration test...")
        debug_logs.append("Starting configuration test...")
        
        # Step 2: Check NVIDIA GPU availability
        yield send_progress("Step 2: Checking NVIDIA GPU availability...")
        debug_logs.append("Checking NVIDIA GPU availability...")
        stdout, stderr, code = run_command("nvidia-smi --query-gpu=name,memory.total --format=csv,noheader")
        
        if code != 0:
            yield send_error("No GPU detected", f"nvidia-smi failed: {stderr}")
            return
        
        gpu_info = stdout.split(',')
        gpu_name = gpu_info[0].strip() if len(gpu_info) > 0 else "Unknown"
        gpu_memory = gpu_info[1].strip() if len(gpu_info) > 1 else "Unknown"
        
        yield send_progress(f"GPU detected: {gpu_name}, {gpu_memory}")
        debug_logs.append(f"GPU detected: {gpu_name}, {gpu_memory}")
        
        # Get NVIDIA Driver version
        stdout, stderr, code = run_command("nvidia-smi --query-gpu=driver_version --format=csv,noheader")
        driver_version = stdout if code == 0 else "Unknown"
        yield send_progress(f"NVIDIA Driver: {driver_version}")
        debug_logs.append(f"NVIDIA Driver: {driver_version}")
        
        # Validate GPU matches profile
        gpu_matches = False
        if vgpu_profile != 'N/A':
            expected_prefix = vgpu_profile.split('-')[0].upper()
            gpu_name_upper = gpu_name.upper()
            
            # Map common vGPU profile prefixes to their full names
            profile_name_mapping = {
                'BSE': 'BLACKWELL SERVER EDITION',
                'L40S': 'L40S',
                'L40': 'L40',
                'A100': 'A100',
                'H100': 'H100',
                'A10': 'A10',
                'RTX6000': 'RTX',
            }
            
            # Get the full name to search for
            search_term = profile_name_mapping.get(expected_prefix, expected_prefix)
            
            import difflib
            similarity = difflib.SequenceMatcher(None, expected_prefix, gpu_name_upper).ratio()
            
            # Check if the search term or prefix is in the GPU name
            gpu_matches = (search_term in gpu_name_upper or 
                          expected_prefix in gpu_name_upper or 
                          similarity > 0.4)
            
            debug_logs.append(f"GPU profile matching: {vgpu_profile} (prefix: {expected_prefix}, search: {search_term}) vs {gpu_name} - Match: {gpu_matches} (similarity: {similarity:.2f})")
        
        # Step 3: Check if Docker is available
        yield send_progress("Step 3: Checking Docker installation...")
        debug_logs.append("Checking Docker installation...")
        stdout, stderr, code = run_command("docker --version")
        if code != 0:
            yield send_error("Docker not found", "Please install Docker to use local deployment")
            return
        yield send_progress(f"{stdout}")
        debug_logs.append(f"Docker version: {stdout}")
        
        # Step 4: Authenticate with HuggingFace
        yield send_progress("Step 4: Authenticating with HuggingFace...")
        if hf_token:
            yield send_progress("Logging into HuggingFace CLI...")
            # Login to HuggingFace CLI to cache credentials
            login_cmd = f"huggingface-cli login --token {hf_token}"
            stdout, stderr, code = run_command(login_cmd)
            if code != 0:
                yield send_error("Inputted token not authorized", "Please verify your HuggingFace token is valid and has the correct permissions")
                return
            yield send_progress("✓ Successfully authenticated with HuggingFace")
            debug_logs.append("HuggingFace CLI login successful")
        else:
            yield send_progress("No HuggingFace token provided (some models may not be accessible)")
            debug_logs.append("Warning: No HuggingFace token")
        
        # Step 5: Stop and remove existing container if it exists
        yield send_progress("Step 5: Checking for existing vLLM containers...")
        debug_logs.append("Checking for existing vLLM processes...")
        container_name = "my_vllm_container"
        run_command(f"docker stop {container_name}", shell=True)
        run_command(f"docker rm {container_name}", shell=True)
        yield send_progress("Cleared any existing vLLM processes")
        debug_logs.append("Cleared any existing vLLM processes")
        
        # Step 6: Pull Docker image and start vLLM server
        yield send_progress("Step 6: Pulling vLLM Docker image (this may take a few minutes)...")
        yield send_progress(f"Step 7: Starting vLLM server with model: {model}...")
        debug_logs.append(f"Starting vLLM server with model: {model}...")
        debug_logs.append(f"Starting vLLM (GPU util: {int(gpu_util*100)}%, max tokens: {max_tokens})...")
        
        # Build docker command - only include max-model-len if specified
        # Note: gpu_util may exceed 0.90 intentionally - vLLM will adapt KV cache to available memory
        docker_cmd_parts = [
            "docker run -d --runtime nvidia --gpus all",
            f"--name {container_name}",
            "-v ~/.cache/huggingface:/root/.cache/huggingface",
            f'-e "HUGGING_FACE_HUB_TOKEN={hf_token}"',
            "-p 8000:8000",
            "--ipc=host",
            "vllm/vllm-openai:latest",
            f"--model {model}",
            f"--gpu-memory-utilization {gpu_util:.2f}"
        ]
        
        # Only add max-model-len if explicitly specified (let vLLM auto-detect otherwise)
        if max_tokens is not None:
            docker_cmd_parts.append(f"--max-model-len {max_tokens}")
            
        docker_cmd = " \\\n            ".join(docker_cmd_parts)
        
        stdout, stderr, code = run_command(docker_cmd)
        
        if code != 0:
            yield send_error("Failed to start vLLM container", stderr)
            return
        
        container_id = stdout[:12] if stdout else "unknown"
        yield send_progress(f"vLLM container started (Container ID: {container_id})")
        debug_logs.append(f"vLLM server starting (Container: {container_id})")
        
        # Step 8: Wait for vLLM to be ready
        yield send_progress("Step 8: Waiting for vLLM server to initialize (model download + loading may take 5-10 minutes)...")
        debug_logs.append("Waiting for vLLM server to initialize (model download + loading may take 5-10 minutes)...")
        
        max_wait = 600  # 10 minutes
        wait_interval = 10
        elapsed = 0
        
        while elapsed < max_wait:
            await asyncio.sleep(wait_interval)
            elapsed += wait_interval
            
            # First check if container is still running
            stdout, _, code = run_command(f"docker ps -q -f name={container_name}")
            if code != 0 or not stdout.strip():
                # Container has stopped, get logs and exit
                stdout, _, _ = run_command(f"docker logs {container_name} 2>&1 | tail -50")
                yield send_error("vLLM container stopped unexpectedly", f"Container exited. Last logs:\n{stdout}")
                return
            
            # Check if port 8000 is listening (use gateway IP since we're in a container)
            stdout, _, code = run_command("curl -s http://172.18.0.1:8000/health 2>/dev/null || echo 'not ready'")
            
            if code == 0 and "not ready" not in stdout:
                yield send_progress(f"✓ vLLM server is ready (took {elapsed}s)")
                debug_logs.append("vLLM server is ready")
                break
            
            yield send_progress(f"Waiting for vLLM to start listening on port 8000... ({elapsed}s elapsed)")
            debug_logs.append(f"Waiting for vLLM to start listening on port 8000... ({elapsed}s elapsed)")
        
        if elapsed >= max_wait:
            # Get recent logs from vLLM container
            stdout, _, _ = run_command(f"docker logs {container_name} 2>&1 | tail -30")
            
            # Extract the most relevant error from logs
            last_error = None
            error_keywords = [
                'error', 'failed', 'exception', 'traceback',
                'unauthorized', '401', '403', 'permission denied',
                'not found', 'cannot', 'unable to', 'invalid'
            ]
            
            # Search for error lines (newest first)
            if stdout:
                lines = [line.strip() for line in stdout.split('\n') if line.strip()]
                for line in reversed(lines):
                    line_lower = line.lower()
                    if any(keyword in line_lower for keyword in error_keywords):
                        # Clean up common log prefixes
                        cleaned_line = line
                        for prefix in ['(APIServer pid=', 'ERROR:', 'Error:', 'EXCEPTION:']:
                            if prefix in line:
                                cleaned_line = line.split(prefix)[-1].strip()
                        last_error = cleaned_line[:300]  # Limit to 300 chars
                        break
            
            if not last_error:
                last_error = "No specific error found in container logs"
            
            # Log the error
            debug_logs.append("=== Last vLLM Error ===")
            debug_logs.append(last_error)
            
            # Cleanup container before returning error
            yield send_progress("Cleaning up container...")
            run_command(f"docker stop {container_name}", shell=True)
            run_command(f"docker rm {container_name}", shell=True)
            
            # Build clear error message
            error_msg = (
                f"vLLM deployment timed out after {max_wait} seconds.\n\n"
                f"Last error from logs:\n{last_error}\n\n"
                f"Common causes:\n"
                f"• Gated model requiring access you don't have\n"
                f"• Insufficient disk space for model download\n"
                f"• Invalid or expired HuggingFace token\n"
                f"• GPU memory insufficient for model size\n"
                f"• Network issues downloading model files"
            )
            
            yield send_error("Deployment timeout", error_msg)
            return
        
        # Step 9: Verify vLLM process is running
        yield send_progress("Step 9: Verifying vLLM process and capturing metrics...")
        debug_logs.append("Verifying vLLM process is running...")
        
        # Get GPU memory usage
        stdout, stderr, code = run_command("nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits")
        gpu_memory_used = stdout if code == 0 else "Unknown"
        
        # Get GPU utilization (sampled after inference, may show low values as GPU returns to idle)
        stdout, stderr, code = run_command("nvidia-smi --query-gpu=utilization.gpu,utilization.memory,temperature.gpu,power.draw,power.limit --format=csv,noheader,nounits")
        if code == 0:
            metrics = stdout.split(',')
            gpu_compute_raw = metrics[0].strip() if len(metrics) > 0 else "0"
            gpu_mem_active_raw = metrics[1].strip() if len(metrics) > 1 else "0"
            gpu_temp = metrics[2].strip() if len(metrics) > 2 else "N/A"
            power_draw = metrics[3].strip() if len(metrics) > 3 else "N/A"
            power_limit = metrics[4].strip() if len(metrics) > 4 else "N/A"
            
            # Show N/A for compute/memory utilization if 0 (sampled after workload finished)
            gpu_compute = "N/A (idle after test)" if gpu_compute_raw == "0" else f"{gpu_compute_raw}"
            gpu_mem_active = "N/A (idle after test)" if gpu_mem_active_raw == "0" else f"{gpu_mem_active_raw}"
        else:
            gpu_compute = gpu_mem_active = "N/A"
            gpu_temp = power_draw = power_limit = "N/A"
        
        # Get KV cache info from container logs
        kv_cache_tokens = max_tokens  # Default fallback
        stdout, stderr, code = run_command(f"docker logs {container_name} 2>&1 | grep 'GPU KV cache size:' | tail -1")
        if code == 0 and stdout:
            import re
            match = re.search(r'GPU KV cache size:\s*(\d+[,\d]*)\s*tokens', stdout)
            if match:
                kv_cache_tokens = match.group(1).replace(',', '')
        
        # Step 10: Test inference endpoint
        yield send_progress("Step 10: Testing inference endpoint...")
        test_prompt = "Explain the concept of GPU virtualization in 2-3 sentences."
        debug_logs.append(f"Testing inference endpoint with prompt: {test_prompt}")
        
        curl_cmd = f"""curl -s -X POST "http://172.18.0.1:8000/v1/chat/completions" \
            -H "Content-Type: application/json" \
            --data '{{"model": "{model}", "messages": [{{"role": "user", "content": "{test_prompt}"}}], "max_tokens": 100}}'"""
        
        stdout, stderr, code = run_command(curl_cmd)
        
        inference_response = "No response"
        if code == 0:
            try:
                response_json = json.loads(stdout)
                inference_response = response_json.get('choices', [{}])[0].get('message', {}).get('content', 'No response')
                yield send_progress("Inference test successful")
                debug_logs.append(f"Inference response: {inference_response}")
            except:
                yield send_progress("Inference test completed")
                debug_logs.append("Inference test completed successfully")
        else:
            yield send_progress(f"Inference test had issues: {stderr}")
            debug_logs.append(f"Warning: Inference test had issues: {stderr}")
        
        # Step 11: Stop and remove container (cleanup)
        yield send_progress("Step 11: Stopping vLLM container (cleanup)...")
        debug_logs.append("Stopping vLLM container...")
        
        stdout_stop, stderr_stop, code_stop = run_command(f"docker stop {container_name}", shell=True)
        if code_stop == 0:
            yield send_progress(f"Container stopped")
        
        stdout_rm, stderr_rm, code_rm = run_command(f"docker rm {container_name}", shell=True)
        if code_rm == 0:
            yield send_progress(f"Container removed")
        
        debug_logs.append("Container cleanup completed")
        
        # Output DEPLOYMENT RESULTS first
        yield send_progress("")
        yield send_progress("=== DEPLOYMENT RESULTS ===")
        yield send_progress("")
        yield send_progress("Status: Deployment Successful")
        yield send_progress("")
        yield send_progress("Workload details:")
        yield send_progress(f"• Workload type: {workload_type}")
        yield send_progress(f"• Model: {model}")
        yield send_progress(f"• vLLM running and allocated {float(gpu_memory_used)/1024:.2f} GB" if gpu_memory_used != "Unknown" else "• vLLM running")
        yield send_progress(f"• GPU Memory Utilization Setting: {int(gpu_util*100)}%")
        yield send_progress(f"• Max Model Length: {max_tokens} tokens")
        yield send_progress(f"• KV Cache: {kv_cache_tokens} tokens")
        yield send_progress("System details:")
        yield send_progress(f"• GPU Detected: {gpu_name}")
        yield send_progress(f"• NVIDIA Driver: {driver_version}")
        yield send_progress("")
        yield send_progress("Hardware Usage During Test:")
        # Format metrics, handling N/A values
        compute_display = f"{gpu_compute}%" if "N/A" not in str(gpu_compute) else str(gpu_compute)
        memory_display = f"{gpu_mem_active}%" if "N/A" not in str(gpu_mem_active) else str(gpu_mem_active)
        temp_display = f"{gpu_temp}°C" if gpu_temp != "N/A" else "N/A"
        power_display = f"{power_draw}W / {power_limit}W" if power_draw != "N/A" and power_limit != "N/A" else "N/A"
        
        yield send_progress(f"• GPU Compute Utilization: {compute_display}")
        yield send_progress(f"• GPU Memory Active: {memory_display}")
        yield send_progress(f"• GPU Temperature: {temp_display}")
        yield send_progress(f"• Power Draw: {power_display}")
        yield send_progress("")
        yield send_progress("Actual vs Expected:")
        yield send_progress(f"• vGPU Profile: {vgpu_profile}")
        yield send_progress(f"• vCPUs: {config.get('vcpu_count', 'N/A')}")
        yield send_progress(f"• System RAM: {config.get('system_RAM', 'N/A')} GB")
        
        # Initialize memory comparison variables
        estimated_gb = 0
        diff_pct = 0
        memory_within_range = False
        
        if gpu_memory_used != "Unknown":
            estimated_gb = config.get('gpu_memory_size', 0)
            actual_gb = float(gpu_memory_used) / 1024
            if estimated_gb > 0:
                diff_gb = actual_gb - estimated_gb
                diff_pct = (diff_gb / estimated_gb * 100) if estimated_gb > 0 else 0
                memory_within_range = abs(diff_pct) <= 20  # Within 20% tolerance
                
                # Describe the relationship more accurately
                if diff_pct > 0:
                    yield send_progress(f"• GPU memory usage: {actual_gb:.1f}GB (target was {estimated_gb}GB)")
                else:
                    yield send_progress(f"• GPU memory usage: {actual_gb:.1f}GB within expected range ({estimated_gb}GB target)")
                yield send_progress(f"• Actual usage vs expected: {100 + diff_pct:.0f}%")
                
                # Extract profile capacity from vgpu_profile (e.g., "L40S-24Q" → 24)
                profile_capacity = None
                try:
                    import re
                    match = re.search(r'-(\d+)Q', vgpu_profile)
                    if match:
                        profile_capacity = int(match.group(1))
                except Exception:
                    pass
                
                # Provide usage feedback based on actual vs expected vs profile
                if profile_capacity:
                    yield send_progress("")
                    if actual_gb > profile_capacity:
                        # Scenario 1: Actual exceeds profile capacity
                        yield send_progress(f"• ⚠️  Actual usage ({actual_gb:.1f}GB) exceeds profile capacity ({profile_capacity}GB)")
                        yield send_progress(f"• Recommendation: Size up to next larger profile")
                    elif actual_gb > estimated_gb:
                        # Scenario 2: Actual > Expected but still fits in profile
                        usage_pct_of_profile = (actual_gb / profile_capacity) * 100
                        yield send_progress(f"• Profile capacity usage: {actual_gb:.1f}GB / {profile_capacity}GB ({usage_pct_of_profile:.0f}%)")
                        if usage_pct_of_profile > 90:
                            yield send_progress(f"• Status: Within limits but running close to capacity")
                        else:
                            yield send_progress(f"• Status: Within acceptable range for testing")
                    else:
                        # Scenario 3: Actual <= Expected
                        usage_pct_of_profile = (actual_gb / profile_capacity) * 100
                        yield send_progress(f"• Profile capacity usage: {actual_gb:.1f}GB / {profile_capacity}GB ({usage_pct_of_profile:.0f}%)")
                        yield send_progress(f"• Status: Usage at or below expected")
        
        yield send_progress("")
        yield send_progress("Results:")
        
        # Check if actual usage exceeded profile capacity
        actual_exceeds_profile = False
        actual_usage_gb = None
        if gpu_memory_used != "Unknown" and profile_capacity:
            actual_usage_gb = float(gpu_memory_used) / 1024
            if actual_usage_gb > profile_capacity:
                actual_exceeds_profile = True
        
        if gpu_matches:
            if actual_exceeds_profile and actual_usage_gb:
                yield send_progress(f"• ⚠️  GPU model matches ({vgpu_profile}), but actual usage ({actual_usage_gb:.1f}GB) exceeds profile capacity ({profile_capacity}GB)")
                yield send_progress(f"• Recommendation: Size up to {vgpu_profile.split('-')[0]}-48Q for production use")
            else:
                # Display friendly profile name
                profile_display = vgpu_profile
                if vgpu_profile.startswith('BSE-'):
                    profile_display = f"{vgpu_profile} (Blackwell Server Edition)"
                yield send_progress(f"• GPU matches recommended profile ({profile_display})")
        else:
            # Display friendly profile name in error message
            profile_display = vgpu_profile
            if vgpu_profile.startswith('BSE-'):
                profile_display = f"{vgpu_profile} (Blackwell Server Edition)"
            yield send_progress(f"• ⚠️  GPU profile mismatch - Expected: {profile_display}, Detected: {gpu_name}")
            yield send_progress(f"• Note: Deployment will continue, but performance may vary from recommendations")
        
        # Now output DEPLOYMENT LOG at the end
        yield send_progress("")
        yield send_progress("")
        yield send_progress("=== DEPLOYMENT LOG ===")
        yield send_progress("")
        for log in debug_logs:
            yield send_progress(log)
        
        # Logout from HuggingFace CLI to clear cached credentials
        if hf_token:
            yield send_progress("Logging out of HuggingFace CLI...")
            run_command("huggingface-cli logout")
            debug_logs.append("HuggingFace CLI logout completed")
        
        # Send final success message
        yield send_success("Deployment completed successfully", {
            "endpoint": "http://localhost:8000",
            "model": model,
            "container": container_name,
            "gpu": gpu_name
        })
            
    except Exception as e:
        logger.error(f"[LOCAL DEPLOYMENT] FAILED: {e}", exc_info=True)
        # Cleanup container on error
        try:
            container_name = "my_vllm_container"
            run_command(f"docker stop {container_name}", shell=True)
            run_command(f"docker rm {container_name}", shell=True)
            yield send_progress("Container cleaned up after error")
        except:
            pass
        
        # Logout from HuggingFace CLI to clear cached credentials even on error
        try:
            if hf_token:
                run_command("huggingface-cli logout")
                yield send_progress("HuggingFace CLI logout completed")
        except:
            pass
            
        yield send_error("Local deployment failed", str(e))