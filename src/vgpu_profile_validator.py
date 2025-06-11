# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""vGPU Profile Validator for configuration validation and capacity calculation."""

import logging
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DeploymentMode(Enum):
    """GPU deployment modes."""
    VGPU = "vgpu"
    PASSTHROUGH = "passthrough"
    MIG = "mig"
    BARE_METAL = "bare_metal"


class ProfileMode(Enum):
    """vGPU profile deployment modes."""
    EQUAL_SIZE = "equal_size"
    MIXED_SIZE = "mixed_size"


@dataclass
class GPUSpecs:
    """Physical GPU specifications."""
    model: str
    total_memory_gb: int
    architecture: str
    max_vgpus: int
    compute_capability: float
    power_watts: int
    

@dataclass
class VGPUProfile:
    """vGPU profile definition."""
    name: str
    frame_buffer_gb: int
    max_instances_equal: int  # Max instances in equal-size mode
    max_instances_mixed: int  # Max instances in mixed-size mode
    use_cases: List[str]
    gpu_models: List[str]  # Compatible GPU models
    min_driver_version: str
    

@dataclass
class VMConfiguration:
    """Complete VM configuration specification."""
    vgpu_profile: Optional[str]
    deployment_mode: DeploymentMode
    total_cpus: int
    vcpu_count: int
    gpu_memory_gb: int
    system_ram_gb: int
    storage_capacity_gb: int
    storage_type: str
    gpu_count: int  # Number of GPUs assigned
    max_vms: int  # Maximum VMs with this config
    performance_tier: str
    concurrent_users: int


class VGPUProfileValidator:
    """Validates vGPU profiles and calculates capacity."""
    
    # Official NVIDIA vGPU profiles (as per documentation)
    VGPU_PROFILES: Dict[str, VGPUProfile] = {
        # A100 Profiles
        "A100-1-5C": VGPUProfile("A100-1-5C", 5, 8, 8, ["VDI", "light compute"], ["A100"], "450.00"),
        "A100-2-10C": VGPUProfile("A100-2-10C", 10, 4, 4, ["VDI", "compute"], ["A100"], "450.00"),
        "A100-4-20C": VGPUProfile("A100-4-20C", 20, 2, 2, ["AI/ML", "compute"], ["A100"], "450.00"),
        "A100-40C": VGPUProfile("A100-40C", 40, 1, 1, ["AI/ML", "HPC"], ["A100"], "450.00"),
        "A100-80C": VGPUProfile("A100-80C", 80, 1, 1, ["AI/ML", "HPC"], ["A100-80GB"], "450.00"),
        
        # A40 Profiles
        "A40-1Q": VGPUProfile("A40-1Q", 1, 48, 32, ["VDI"], ["A40"], "460.00"),
        "A40-2Q": VGPUProfile("A40-2Q", 2, 24, 16, ["VDI", "vWS"], ["A40"], "460.00"),
        "A40-4Q": VGPUProfile("A40-4Q", 4, 12, 8, ["vWS", "AI inference"], ["A40"], "460.00"),
        "A40-8Q": VGPUProfile("A40-8Q", 8, 6, 4, ["vWS", "AI workloads"], ["A40"], "460.00"),
        "A40-12Q": VGPUProfile("A40-12Q", 12, 4, 2, ["AI/ML", "rendering"], ["A40"], "460.00"),
        "A40-16Q": VGPUProfile("A40-16Q", 16, 3, 2, ["AI/ML", "compute"], ["A40"], "460.00"),
        "A40-24Q": VGPUProfile("A40-24Q", 24, 2, 1, ["AI/ML", "HPC"], ["A40"], "460.00"),
        "A40-48Q": VGPUProfile("A40-48Q", 48, 1, 1, ["AI/ML", "HPC"], ["A40"], "460.00"),
        
        # L40S Profiles
        "L40S-1Q": VGPUProfile("L40S-1Q", 1, 48, 32, ["VDI"], ["L40S"], "525.00"),
        "L40S-2Q": VGPUProfile("L40S-2Q", 2, 24, 16, ["VDI", "vWS"], ["L40S"], "525.00"),
        "L40S-4Q": VGPUProfile("L40S-4Q", 4, 12, 8, ["vWS", "AI inference"], ["L40S"], "525.00"),
        "L40S-8Q": VGPUProfile("L40S-8Q", 8, 6, 4, ["vWS", "AI workloads"], ["L40S"], "525.00"),
        "L40S-12Q": VGPUProfile("L40S-12Q", 12, 4, 2, ["AI/ML", "rendering"], ["L40S"], "525.00"),
        "L40S-16Q": VGPUProfile("L40S-16Q", 16, 3, 2, ["AI/ML", "compute"], ["L40S"], "525.00"),
        "L40S-24Q": VGPUProfile("L40S-24Q", 24, 2, 1, ["AI/ML", "HPC"], ["L40S"], "525.00"),
        "L40S-48Q": VGPUProfile("L40S-48Q", 48, 1, 1, ["AI/ML", "HPC"], ["L40S"], "525.00"),
        
        # L40 Profiles (same memory as L40S)
        "L40-1Q": VGPUProfile("L40-1Q", 1, 48, 32, ["VDI"], ["L40"], "525.00"),
        "L40-2Q": VGPUProfile("L40-2Q", 2, 24, 16, ["VDI", "vWS"], ["L40"], "525.00"),
        "L40-4Q": VGPUProfile("L40-4Q", 4, 12, 8, ["vWS", "AI inference"], ["L40"], "525.00"),
        "L40-8Q": VGPUProfile("L40-8Q", 8, 6, 4, ["vWS", "AI workloads"], ["L40"], "525.00"),
        "L40-12Q": VGPUProfile("L40-12Q", 12, 4, 2, ["AI/ML", "rendering"], ["L40"], "525.00"),
        "L40-16Q": VGPUProfile("L40-16Q", 16, 3, 2, ["AI/ML", "compute"], ["L40"], "525.00"),
        "L40-24Q": VGPUProfile("L40-24Q", 24, 2, 1, ["AI/ML", "HPC"], ["L40"], "525.00"),
        "L40-48Q": VGPUProfile("L40-48Q", 48, 1, 1, ["AI/ML", "HPC"], ["L40"], "525.00"),
        
        # L4 Profiles
        "L4-1Q": VGPUProfile("L4-1Q", 1, 24, 16, ["VDI", "inference"], ["L4"], "525.00"),
        "L4-2Q": VGPUProfile("L4-2Q", 2, 12, 8, ["VDI", "AI inference"], ["L4"], "525.00"),
        "L4-4Q": VGPUProfile("L4-4Q", 4, 6, 4, ["AI inference", "vWS"], ["L4"], "525.00"),
        "L4-8Q": VGPUProfile("L4-8Q", 8, 3, 2, ["AI workloads"], ["L4"], "525.00"),
        "L4-12Q": VGPUProfile("L4-12Q", 12, 2, 1, ["AI/ML"], ["L4"], "525.00"),
        "L4-24Q": VGPUProfile("L4-24Q", 24, 1, 1, ["AI/ML", "compute"], ["L4"], "525.00"),
        
        # RTX 6000 Ada Profiles
        "RTX6000-1Q": VGPUProfile("RTX6000-1Q", 1, 48, 32, ["VDI"], ["RTX6000Ada"], "525.00"),
        "RTX6000-2Q": VGPUProfile("RTX6000-2Q", 2, 24, 16, ["VDI", "vWS"], ["RTX6000Ada"], "525.00"),
        "RTX6000-4Q": VGPUProfile("RTX6000-4Q", 4, 12, 8, ["vWS", "creative"], ["RTX6000Ada"], "525.00"),
        "RTX6000-8Q": VGPUProfile("RTX6000-8Q", 8, 6, 4, ["creative", "AI"], ["RTX6000Ada"], "525.00"),
        "RTX6000-12Q": VGPUProfile("RTX6000-12Q", 12, 4, 2, ["AI/ML", "rendering"], ["RTX6000Ada"], "525.00"),
        "RTX6000-16Q": VGPUProfile("RTX6000-16Q", 16, 3, 2, ["AI/ML", "compute"], ["RTX6000Ada"], "525.00"),
        "RTX6000-24Q": VGPUProfile("RTX6000-24Q", 24, 2, 1, ["AI/ML", "rendering"], ["RTX6000Ada"], "525.00"),
        "RTX6000-48Q": VGPUProfile("RTX6000-48Q", 48, 1, 1, ["AI/ML", "HPC"], ["RTX6000Ada"], "525.00"),
    }
    
    # GPU specifications
    GPU_SPECS: Dict[str, GPUSpecs] = {
        "A100": GPUSpecs("A100", 40, "Ampere", 8, 8.0, 250),
        "A100-80GB": GPUSpecs("A100-80GB", 80, "Ampere", 8, 8.0, 300),
        "A40": GPUSpecs("A40", 48, "Ampere", 48, 8.6, 300),
        "L40S": GPUSpecs("L40S", 48, "Ada Lovelace", 48, 8.9, 350),
        "L40": GPUSpecs("L40", 48, "Ada Lovelace", 48, 8.9, 300),
        "L4": GPUSpecs("L4", 24, "Ada Lovelace", 24, 8.9, 72),
        "RTX6000Ada": GPUSpecs("RTX6000Ada", 48, "Ada Lovelace", 48, 8.9, 300),
        "H100": GPUSpecs("H100", 80, "Hopper", 7, 9.0, 700),
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def validate_profile(self, profile_name: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a vGPU profile exists.
        
        Args:
            profile_name: Name of the vGPU profile
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not profile_name:
            return False, "Profile name cannot be empty"
            
        if profile_name not in self.VGPU_PROFILES:
            # Suggest similar profiles
            suggestions = self._find_similar_profiles(profile_name)
            if suggestions:
                return False, f"Profile '{profile_name}' does not exist. Did you mean: {', '.join(suggestions)}?"
            return False, f"Profile '{profile_name}' does not exist"
            
        return True, None
    
    def _find_similar_profiles(self, profile_name: str, max_suggestions: int = 3) -> List[str]:
        """Find similar profile names for suggestions."""
        profile_upper = profile_name.upper()
        suggestions = []
        
        # Check for GPU model matches
        for gpu_model in ["A100", "A40", "L40S", "L40", "L4", "RTX6000"]:
            if gpu_model in profile_upper:
                gpu_profiles = [p for p in self.VGPU_PROFILES.keys() if p.startswith(gpu_model)]
                suggestions.extend(gpu_profiles[:max_suggestions])
                break
                
        return suggestions[:max_suggestions]
    
    def get_compatible_profiles(self, gpu_model: str, memory_requirement_gb: int = 0,
                              use_case: str = None) -> List[str]:
        """
        Get compatible vGPU profiles for a GPU model.
        
        Args:
            gpu_model: GPU model name
            memory_requirement_gb: Minimum memory requirement
            use_case: Intended use case
            
        Returns:
            List of compatible profile names
        """
        compatible = []
        
        for profile_name, profile in self.VGPU_PROFILES.items():
            # Check GPU compatibility
            if gpu_model not in profile.gpu_models:
                continue
                
            # Check memory requirement
            if profile.frame_buffer_gb < memory_requirement_gb:
                continue
                
            # Check use case if specified
            if use_case and use_case not in profile.use_cases:
                continue
                
            compatible.append(profile_name)
            
        return sorted(compatible, key=lambda x: self.VGPU_PROFILES[x].frame_buffer_gb)
    
    def calculate_vm_capacity(self, gpu_inventory: Dict[str, int], 
                            profile_name: str,
                            mode: ProfileMode = ProfileMode.EQUAL_SIZE) -> Dict[str, Union[int, str]]:
        """
        Calculate VM capacity for given GPU inventory and profile.
        
        Args:
            gpu_inventory: Dict of GPU model to count
            profile_name: vGPU profile name
            mode: Profile deployment mode
            
        Returns:
            Dict with capacity information
        """
        is_valid, error = self.validate_profile(profile_name)
        if not is_valid:
            return {"error": error, "max_vms": 0}
            
        profile = self.VGPU_PROFILES[profile_name]
        total_vms = 0
        gpu_breakdown = {}
        
        for gpu_model, gpu_count in gpu_inventory.items():
            if gpu_model in profile.gpu_models:
                max_per_gpu = (profile.max_instances_equal if mode == ProfileMode.EQUAL_SIZE 
                             else profile.max_instances_mixed)
                vms_from_gpu = gpu_count * max_per_gpu
                total_vms += vms_from_gpu
                gpu_breakdown[gpu_model] = {
                    "gpu_count": gpu_count,
                    "vms_per_gpu": max_per_gpu,
                    "total_vms": vms_from_gpu
                }
        
        return {
            "profile": profile_name,
            "mode": mode.value,
            "max_vms": total_vms,
            "gpu_breakdown": gpu_breakdown,
            "frame_buffer_gb": profile.frame_buffer_gb
        }
    
    def recommend_deployment_strategy(self, gpu_inventory: Dict[str, int],
                                    workload_requirements: Dict[str, any]) -> List[VMConfiguration]:
        """
        Recommend deployment strategies for given requirements.
        
        Args:
            gpu_inventory: Available GPU inventory
            workload_requirements: Workload requirements including model size, users, etc.
            
        Returns:
            List of recommended VM configurations
        """
        recommendations = []
        
        # Extract requirements
        model_memory_gb = workload_requirements.get("model_memory_gb", 0)
        concurrent_users = workload_requirements.get("concurrent_users", 1)
        deployment_preference = workload_requirements.get("deployment_mode", "vgpu")
        
        # Handle passthrough mode
        if deployment_preference == "passthrough":
            return self._recommend_passthrough(gpu_inventory, workload_requirements)
        
        # Find compatible profiles for each GPU in inventory
        for gpu_model, gpu_count in gpu_inventory.items():
            if gpu_count == 0:
                continue
                
            compatible_profiles = self.get_compatible_profiles(
                gpu_model, 
                model_memory_gb,
                workload_requirements.get("use_case")
            )
            
            for profile_name in compatible_profiles:
                profile = self.VGPU_PROFILES[profile_name]
                
                # Calculate VM capacity
                capacity_equal = self.calculate_vm_capacity(
                    {gpu_model: gpu_count}, 
                    profile_name,
                    ProfileMode.EQUAL_SIZE
                )
                
                # Check if it meets user requirements
                if capacity_equal["max_vms"] >= concurrent_users:
                    # Calculate resource requirements
                    vcpus = self._calculate_vcpus(profile.frame_buffer_gb)
                    ram = self._calculate_ram(profile.frame_buffer_gb, model_memory_gb)
                    storage = self._calculate_storage(workload_requirements)
                    
                    config = VMConfiguration(
                        vgpu_profile=profile_name,
                        deployment_mode=DeploymentMode.VGPU,
                        total_cpus=vcpus * 2,  # Assume 2:1 oversubscription
                        vcpu_count=vcpus,
                        gpu_memory_gb=profile.frame_buffer_gb,
                        system_ram_gb=ram,
                        storage_capacity_gb=storage["capacity"],
                        storage_type=storage["type"],
                        gpu_count=gpu_count,
                        max_vms=capacity_equal["max_vms"],
                        performance_tier=self._determine_performance_tier(profile.frame_buffer_gb),
                        concurrent_users=min(capacity_equal["max_vms"], concurrent_users)
                    )
                    
                    recommendations.append(config)
        
        # Sort by efficiency (users per GPU)
        recommendations.sort(key=lambda x: x.concurrent_users / x.gpu_count, reverse=True)
        
        return recommendations[:5]  # Return top 5 recommendations
    
    def _recommend_passthrough(self, gpu_inventory: Dict[str, int],
                             workload_requirements: Dict[str, any]) -> List[VMConfiguration]:
        """Recommend passthrough configurations."""
        recommendations = []
        model_memory_gb = workload_requirements.get("model_memory_gb", 0)
        
        for gpu_model, gpu_count in gpu_inventory.items():
            if gpu_count == 0 or gpu_model not in self.GPU_SPECS:
                continue
                
            gpu_spec = self.GPU_SPECS[gpu_model]
            
            # Check if model fits
            if gpu_spec.total_memory_gb >= model_memory_gb:
                vcpus = 16  # Standard for passthrough
                ram = max(64, model_memory_gb * 2)  # 2x GPU memory
                storage = self._calculate_storage(workload_requirements)
                
                config = VMConfiguration(
                    vgpu_profile=None,
                    deployment_mode=DeploymentMode.PASSTHROUGH,
                    total_cpus=vcpus,
                    vcpu_count=vcpus,
                    gpu_memory_gb=gpu_spec.total_memory_gb,
                    system_ram_gb=ram,
                    storage_capacity_gb=storage["capacity"],
                    storage_type=storage["type"],
                    gpu_count=1,  # One GPU per VM in passthrough
                    max_vms=gpu_count,  # One VM per GPU
                    performance_tier="Maximum Performance",
                    concurrent_users=gpu_count  # One user per GPU
                )
                
                recommendations.append(config)
        
        return recommendations
    
    def _calculate_vcpus(self, gpu_memory_gb: int) -> int:
        """Calculate recommended vCPUs based on GPU memory."""
        if gpu_memory_gb <= 4:
            return 4
        elif gpu_memory_gb <= 8:
            return 8
        elif gpu_memory_gb <= 16:
            return 16
        elif gpu_memory_gb <= 24:
            return 24
        else:
            return 32
    
    def _calculate_ram(self, gpu_memory_gb: int, model_memory_gb: int) -> int:
        """Calculate recommended system RAM."""
        # Base RAM is 2x GPU memory or 2x model memory, whichever is larger
        base_ram = max(gpu_memory_gb * 2, model_memory_gb * 2)
        
        # Add overhead for OS and applications
        overhead = 16
        
        # Round up to standard sizes
        total_ram = base_ram + overhead
        standard_sizes = [32, 64, 96, 128, 192, 256, 384, 512, 768, 1024]
        
        for size in standard_sizes:
            if total_ram <= size:
                return size
                
        return 1024  # Max out at 1TB
    
    def _calculate_storage(self, workload_requirements: Dict[str, any]) -> Dict[str, Union[int, str]]:
        """Calculate storage requirements."""
        model_size_gb = workload_requirements.get("model_size_gb", 50)
        dataset_size_gb = workload_requirements.get("dataset_size_gb", 100)
        
        # Base storage = OS + Model + Dataset + Workspace
        base_storage = 100 + model_size_gb + dataset_size_gb + 200
        
        # Round up to standard sizes
        standard_sizes = [256, 512, 1024, 2048, 4096, 8192]
        for size in standard_sizes:
            if base_storage <= size:
                capacity = size
                break
        else:
            capacity = 8192
        
        # Determine storage type based on performance requirements
        if workload_requirements.get("performance_level") in ["high", "maximum"]:
            storage_type = "NVMe"
        else:
            storage_type = "SSD"
            
        return {"capacity": capacity, "type": storage_type}
    
    def _determine_performance_tier(self, gpu_memory_gb: int) -> str:
        """Determine performance tier based on GPU memory."""
        if gpu_memory_gb <= 4:
            return "Entry"
        elif gpu_memory_gb <= 12:
            return "Standard"
        elif gpu_memory_gb <= 24:
            return "High Performance"
        else:
            return "Maximum Performance" 