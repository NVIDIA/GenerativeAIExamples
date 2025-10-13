"""
Debug utilities for chains.py to capture workload configuration parameters
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class WorkloadParameterDebugger:
    """Helper class to debug and capture workload configuration parameters"""
    
    def __init__(self):
        self.captured_params = {}
        self.vgpu_calc_data = None
    
    def extract_vgpu_calc_data(self, query: str) -> Optional[Dict[str, Any]]:
        """Extract vGPU calculator metadata from the query"""
        # Look for embedded vGPU calculator data in HTML comments
        match = re.search(r'<!--VGPU_CALC:(.*?)-->', query)
        if match:
            try:
                data = json.loads(match.group(1))
                logger.info("=== EXTRACTED VGPU CALC DATA ===")
                logger.info(json.dumps(data, indent=2))
                self.vgpu_calc_data = data
                return data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse calculator data: {e}")
        return None
    
    def debug_llm_chain_params(self, query: str, chat_history: List[Dict[str, Any]], **kwargs):
        """Debug parameters passed to llm_chain"""
        logger.info("=== LLM CHAIN DEBUG INFO ===")
        logger.info(f"Query: {query}")
        logger.info(f"Chat History Length: {len(chat_history)}")
        logger.info("Kwargs:")
        for key, value in kwargs.items():
            logger.info(f"  {key}: {value}")
        
        # Extract vGPU calc data if present
        calc_data = self.extract_vgpu_calc_data(query)
        if calc_data:
            logger.info("=== WORKLOAD CONFIGURATION ===")
            logger.info(f"Workload Type: {calc_data.get('workloadType')}")
            logger.info(f"Model: {calc_data.get('model')}")
            logger.info(f"Selected GPU: {calc_data.get('selectedGPU')}")
            logger.info(f"Prompt Size: {calc_data.get('promptSize')}")
            logger.info(f"Response Size: {calc_data.get('responseSize')}")
            logger.info(f"Concurrent Requests: {calc_data.get('concurrentRequests')}")
            logger.info(f"Precision: {calc_data.get('precision')}")
        
        return calc_data
    
    def debug_rag_chain_params(self, query: str, chat_history: List[Dict[str, Any]], 
                               reranker_top_k: int, vdb_top_k: int, 
                               collection_name: str, **kwargs):
        """Debug parameters passed to rag_chain"""
        logger.info("=== RAG CHAIN DEBUG INFO ===")
        logger.info(f"Query: {query}")
        logger.info(f"Chat History Length: {len(chat_history)}")
        logger.info(f"Reranker Top K: {reranker_top_k}")
        logger.info(f"VDB Top K: {vdb_top_k}")
        logger.info(f"Collection Name: {collection_name}")
        logger.info("Kwargs:")
        for key, value in kwargs.items():
            logger.info(f"  {key}: {value}")
        
        # Extract vGPU calc data if present
        calc_data = self.extract_vgpu_calc_data(query)
        return calc_data
    
    def save_debug_info(self, filename: str = "debug_workload_params.json"):
        """Save captured parameters to a file for analysis"""
        debug_data = {
            "captured_params": self.captured_params,
            "vgpu_calc_data": self.vgpu_calc_data
        }
        with open(filename, 'w') as f:
            json.dump(debug_data, f, indent=2)
        logger.info(f"Debug info saved to {filename}")


def debug_decorator(func):
    """Decorator to automatically debug function parameters"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"=== DEBUGGING FUNCTION: {func.__name__} ===")
        logger.info(f"Args: {args}")
        logger.info(f"Kwargs: {kwargs}")
        
        # Special handling for query parameter
        if args and isinstance(args[0], str):
            query = args[0]
            # Try to extract vGPU calc data
            match = re.search(r'<!--VGPU_CALC:(.*?)-->', query)
            if match:
                try:
                    data = json.loads(match.group(1))
                    logger.info("=== FOUND VGPU CALC DATA IN QUERY ===")
                    logger.info(json.dumps(data, indent=2))
                except:
                    pass
        
        result = func(*args, **kwargs)
        return result
    return wrapper


# Modified chains functions with debugging
def debug_llm_chain(self, query: str, chat_history: List[Dict[str, Any]], **kwargs):
    """Debug version of llm_chain that captures all parameters"""
    
    # Initialize debugger
    debugger = WorkloadParameterDebugger()
    calc_data = debugger.debug_llm_chain_params(query, chat_history, **kwargs)
    
    # You can also use Python debugger here
    # import pdb; pdb.set_trace()
    
    # Or use breakpoint() in Python 3.7+
    # breakpoint()
    
    # Continue with normal llm_chain logic...
    # (rest of the function implementation)


def debug_structured_response(query: str, **kwargs):
    """Debug structured response generation"""
    logger.info("=== DEBUGGING STRUCTURED RESPONSE ===")
    
    # Extract any embedded configuration data
    config_pattern = r'<!--CONFIG:(.*?)-->'
    config_match = re.search(config_pattern, query)
    if config_match:
        try:
            config_data = json.loads(config_match.group(1))
            logger.info("Found embedded configuration:")
            logger.info(json.dumps(config_data, indent=2))
        except:
            pass
    
    # Log the full query for analysis
    logger.info(f"Full query content:\n{query}")
    
    # Log any additional parameters
    logger.info("Additional parameters:")
    for key, value in kwargs.items():
        logger.info(f"  {key}: {value}")


# Example usage in chains.py
"""
To use these debug utilities in chains.py:

1. Import the debugger:
   from .chains_debug import WorkloadParameterDebugger, debug_decorator

2. Initialize debugger in your class:
   self.debugger = WorkloadParameterDebugger()

3. Add debugging to llm_chain:
   def llm_chain(self, query: str, chat_history: List[Dict[str, Any]], **kwargs):
       # Debug parameters
       calc_data = self.debugger.debug_llm_chain_params(query, chat_history, **kwargs)
       
       # Use the extracted data
       if calc_data:
           model_name = calc_data.get('model')
           gpu_type = calc_data.get('selectedGPU')
           # ... use these parameters
       
       # Continue with normal logic...

4. Or use the decorator:
   @debug_decorator
   def llm_chain(self, query: str, chat_history: List[Dict[str, Any]], **kwargs):
       # Function will automatically log all parameters
       ...

5. Use breakpoints for interactive debugging:
   import pdb; pdb.set_trace()  # or breakpoint() in Python 3.7+
""" 