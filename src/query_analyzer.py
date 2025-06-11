# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Query Analyzer for intelligent document routing based on query components."""

import re
import logging
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentCategory(Enum):
    """Categories of documents for vGPU configuration."""
    BASELINE = "baseline"
    HYPERVISOR = "hypervisor"
    COST_EFFICIENCY = "cost_efficiency"
    GPU_SPECIFIC = "gpu_specific"
    DEPLOYMENT_MODE = "deployment_mode"
    PERFORMANCE = "performance"
    SIZING = "sizing"


@dataclass
class QueryComponents:
    """Parsed components from user query."""
    gpu_models: List[str]
    hypervisors: List[str]
    workload_types: List[str]
    performance_requirements: List[str]
    deployment_modes: List[str]
    user_counts: List[int]
    model_sizes: List[str]
    cost_considerations: bool
    passthrough_requested: bool
    

class QueryAnalyzer:
    """Analyzes queries and determines which document collections to search."""
    
    # Mapping of keywords to document categories
    KEYWORD_MAPPINGS = {
        DocumentCategory.HYPERVISOR: {
            "esxi", "vmware", "vsphere", "xenserver", "citrix", "hyper-v", 
            "kvm", "proxmox", "nutanix", "ahv"
        },
        DocumentCategory.COST_EFFICIENCY: {
            "cost", "efficient", "budget", "optimize", "economical", 
            "save", "pricing", "tco", "roi"
        },
        DocumentCategory.GPU_SPECIFIC: {
            "a100", "a40", "l40", "l40s", "l4", "h100", "rtx", 
            "tesla", "quadro", "ada", "hopper", "ampere"
        },
        DocumentCategory.DEPLOYMENT_MODE: {
            "passthrough", "vgpu", "mig", "bare metal", "containerized",
            "kubernetes", "docker"
        },
        DocumentCategory.PERFORMANCE: {
            "performance", "latency", "throughput", "concurrent", "users",
            "real-time", "batch", "inference", "training"
        }
    }
    
    # GPU model patterns
    GPU_PATTERNS = {
        r'\b(A100|a100)(-\d+GB?)?\b': 'A100',
        r'\b(A40|a40)\b': 'A40',
        r'\b(L40S?|l40s?)\b': 'L40S',
        r'\b(L4|l4)\b': 'L4',
        r'\b(H100|h100)(-\d+GB?)?\b': 'H100',
        r'\b(RTX\s*\d+|rtx\s*\d+)\b': 'RTX'
    }
    
    # Model size patterns
    MODEL_SIZE_PATTERNS = {
        r'\b(\d+)[Bb]\+?\b': lambda x: int(x.group(1)),
        r'\b(small|tiny|base)\s+(model|llm)?\b': 'small',
        r'\b(medium|standard)\s+(model|llm)?\b': 'medium',
        r'\b(large|big)\s+(model|llm)?\b': 'large'
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def analyze_query(self, query: str) -> Tuple[QueryComponents, Set[DocumentCategory]]:
        """
        Analyze query and determine which document categories to search.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (QueryComponents, Set[DocumentCategory])
        """
        query_lower = query.lower()
        
        # Extract components
        components = QueryComponents(
            gpu_models=self._extract_gpu_models(query),
            hypervisors=self._extract_hypervisors(query_lower),
            workload_types=self._extract_workload_types(query_lower),
            performance_requirements=self._extract_performance_requirements(query_lower),
            deployment_modes=self._extract_deployment_modes(query_lower),
            user_counts=self._extract_user_counts(query),
            model_sizes=self._extract_model_sizes(query),
            cost_considerations=self._check_cost_considerations(query_lower),
            passthrough_requested=self._check_passthrough_request(query_lower)
        )
        
        # Determine document categories
        categories = self._determine_categories(components, query_lower)
        
        # Always include baseline
        categories.add(DocumentCategory.BASELINE)
        
        self.logger.info(f"Query components: {components}")
        self.logger.info(f"Document categories: {[cat.value for cat in categories]}")
        
        return components, categories
        
    def _extract_gpu_models(self, query: str) -> List[str]:
        """Extract GPU models from query."""
        models = []
        for pattern, model_name in self.GPU_PATTERNS.items():
            if re.search(pattern, query, re.IGNORECASE):
                models.append(model_name)
        return list(set(models))
    
    def _extract_hypervisors(self, query_lower: str) -> List[str]:
        """Extract hypervisor mentions from query."""
        hypervisors = []
        for hypervisor in self.KEYWORD_MAPPINGS[DocumentCategory.HYPERVISOR]:
            if hypervisor in query_lower:
                hypervisors.append(hypervisor)
        return hypervisors
    
    def _extract_workload_types(self, query_lower: str) -> List[str]:
        """Extract workload types from query."""
        workload_keywords = {
            "rag", "llm", "inference", "training", "fine-tuning", 
            "embedding", "chat", "completion", "generation"
        }
        return [w for w in workload_keywords if w in query_lower]
    
    def _extract_performance_requirements(self, query_lower: str) -> List[str]:
        """Extract performance requirements from query."""
        perf_keywords = {
            "real-time", "batch", "high performance", "low latency",
            "high throughput", "concurrent users"
        }
        return [p for p in perf_keywords if p in query_lower]
    
    def _extract_deployment_modes(self, query_lower: str) -> List[str]:
        """Extract deployment mode preferences."""
        modes = []
        if "passthrough" in query_lower or "pass-through" in query_lower:
            modes.append("passthrough")
        if "vgpu" in query_lower or "v-gpu" in query_lower:
            modes.append("vgpu")
        if not modes:  # Default to vGPU if not specified
            modes.append("vgpu")
        return modes
    
    def _extract_user_counts(self, query: str) -> List[int]:
        """Extract user count requirements."""
        user_patterns = [
            r'(\d+)[-–]\s*(\d+)\s*(?:concurrent\s*)?users?',
            r'(\d+)\s*(?:concurrent\s*)?users?',
            r'support\s*(\d+)'
        ]
        
        counts = []
        for pattern in user_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    counts.extend([int(x) for x in match if x.isdigit()])
                else:
                    counts.append(int(match))
        return counts
    
    def _extract_model_sizes(self, query: str) -> List[str]:
        """Extract AI model sizes from query."""
        sizes = []
        for pattern, extractor in self.MODEL_SIZE_PATTERNS.items():
            matches = re.finditer(pattern, query, re.IGNORECASE)
            for match in matches:
                if callable(extractor):
                    size = extractor(match)
                    sizes.append(f"{size}B")
                else:
                    sizes.append(extractor)
        return sizes
    
    def _check_cost_considerations(self, query_lower: str) -> bool:
        """Check if query mentions cost considerations."""
        cost_keywords = self.KEYWORD_MAPPINGS[DocumentCategory.COST_EFFICIENCY]
        return any(keyword in query_lower for keyword in cost_keywords)
    
    def _check_passthrough_request(self, query_lower: str) -> bool:
        """Check if query requests GPU passthrough."""
        return "passthrough" in query_lower or "pass-through" in query_lower
    
    def _determine_categories(self, components: QueryComponents, 
                            query_lower: str) -> Set[DocumentCategory]:
        """Determine which document categories to search."""
        categories = set()
        
        # Check each category's keywords
        for category, keywords in self.KEYWORD_MAPPINGS.items():
            if any(keyword in query_lower for keyword in keywords):
                categories.add(category)
        
        # Add GPU-specific docs if GPU models mentioned
        if components.gpu_models:
            categories.add(DocumentCategory.GPU_SPECIFIC)
        
        # Add performance docs if user counts or performance mentioned
        if components.user_counts or components.performance_requirements:
            categories.add(DocumentCategory.PERFORMANCE)
        
        # Add sizing docs if model sizes mentioned
        if components.model_sizes:
            categories.add(DocumentCategory.SIZING)
        
        return categories


def get_collection_names_for_categories(categories: Set[DocumentCategory], 
                                      gpu_models: List[str] = None) -> List[str]:
    """
    Map document categories to actual collection names.
    
    Args:
        categories: Set of document categories
        gpu_models: List of GPU models mentioned in query
        
    Returns:
        List of collection names to search
    """
    collection_mapping = {
        DocumentCategory.BASELINE: "vgpu_baseline",
        DocumentCategory.HYPERVISOR: "vgpu_hypervisor",
        DocumentCategory.COST_EFFICIENCY: "vgpu_cost_efficiency",
        DocumentCategory.DEPLOYMENT_MODE: "vgpu_deployment",
        DocumentCategory.PERFORMANCE: "vgpu_performance",
        DocumentCategory.SIZING: "vgpu_sizing"
    }
    
    collections = []
    
    # Add base collections
    for category in categories:
        if category in collection_mapping:
            collections.append(collection_mapping[category])
    
    # Add GPU-specific collections if applicable
    if DocumentCategory.GPU_SPECIFIC in categories and gpu_models:
        for gpu_model in gpu_models:
            gpu_collection = f"vgpu_{gpu_model.lower()}"
            collections.append(gpu_collection)
    
    # Remove duplicates and return
    return list(set(collections)) 