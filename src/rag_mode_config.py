# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

"""Configuration for RAG mode selection and feature toggles."""

import os
from enum import Enum
from typing import Dict, Any


class RAGMode(Enum):
    """RAG operation modes."""
    STANDARD = "standard"
    ENHANCED = "enhanced"
    HYBRID = "hybrid"  # Use enhanced for vGPU queries, standard for others


class RAGModeConfig:
    """Configuration for RAG mode selection."""
    
    def __init__(self):
        # Default to enhanced mode if environment variable is set
        self.mode = RAGMode(os.getenv("RAG_MODE", "enhanced"))
        
        # Feature flags
        self.features = {
            "multi_collection_retrieval": os.getenv("ENABLE_MULTI_COLLECTION", "true").lower() == "true",
            "profile_validation": os.getenv("ENABLE_PROFILE_VALIDATION", "true").lower() == "true",
            "query_analysis": os.getenv("ENABLE_QUERY_ANALYSIS", "true").lower() == "true",
            "capacity_calculation": os.getenv("ENABLE_CAPACITY_CALC", "true").lower() == "true",
            "passthrough_support": os.getenv("ENABLE_PASSTHROUGH", "true").lower() == "true",
            "response_validation": os.getenv("ENABLE_RESPONSE_VALIDATION", "true").lower() == "true"
        }
        
        # Performance settings
        self.performance = {
            "max_collections_per_query": int(os.getenv("MAX_COLLECTIONS_PER_QUERY", "5")),
            "parallel_retrieval": os.getenv("ENABLE_PARALLEL_RETRIEVAL", "true").lower() == "true",
            "cache_collections": os.getenv("CACHE_COLLECTIONS", "true").lower() == "true",
            "retrieval_timeout": int(os.getenv("RETRIEVAL_TIMEOUT", "30"))
        }
        
        # vGPU specific settings
        self.vgpu_settings = {
            "strict_profile_validation": os.getenv("STRICT_PROFILE_VALIDATION", "true").lower() == "true",
            "suggest_alternatives": os.getenv("SUGGEST_ALTERNATIVES", "true").lower() == "true",
            "calculate_tco": os.getenv("CALCULATE_TCO", "false").lower() == "true",
            "validate_drivers": os.getenv("VALIDATE_DRIVERS", "false").lower() == "true"
        }
    
    def should_use_enhanced(self, query: str) -> bool:
        """Determine if enhanced RAG should be used for a query."""
        if self.mode == RAGMode.ENHANCED:
            return True
        elif self.mode == RAGMode.STANDARD:
            return False
        else:  # HYBRID mode
            # Use enhanced for vGPU-related queries
            vgpu_keywords = [
                "vgpu", "v-gpu", "gpu", "profile", "passthrough",
                "virtualization", "vm", "concurrent users", "esxi",
                "vmware", "citrix", "configuration", "deploy"
            ]
            query_lower = query.lower()
            return any(keyword in query_lower for keyword in vgpu_keywords)
    
    def get_feature_config(self) -> Dict[str, Any]:
        """Get complete feature configuration."""
        return {
            "mode": self.mode.value,
            "features": self.features,
            "performance": self.performance,
            "vgpu_settings": self.vgpu_settings
        }
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a specific feature is enabled."""
        return self.features.get(feature, False)


# Global instance
rag_config = RAGModeConfig()


def get_rag_config() -> RAGModeConfig:
    """Get the global RAG configuration instance."""
    return rag_config 