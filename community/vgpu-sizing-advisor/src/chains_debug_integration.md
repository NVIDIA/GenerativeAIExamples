# Debugging Workload Configuration Parameters in chains.py

Here are several methods to access and debug the user parameters from the workload configuration step:

## Method 1: Quick Logging (Minimal Changes)

Add these logging statements to your `llm_chain` and `rag_chain` methods in chains.py:

```python
def llm_chain(self, query: str, chat_history: List[Dict[str, Any]], **kwargs) -> Generator[str, None, None]:
    # Add debugging at the start
    logger.info("=== DEBUGGING LLM_CHAIN PARAMETERS ===")
    logger.info(f"Query: {query[:200]}...")  # First 200 chars
    logger.info(f"Kwargs keys: {list(kwargs.keys())}")
    
    # Check if query contains embedded vGPU calculator data
    import re
    match = re.search(r'<!--VGPU_CALC:(.*?)-->', query)
    if match:
        import json
        try:
            calc_data = json.loads(match.group(1))
            logger.info("=== FOUND VGPU CALCULATOR DATA ===")
            logger.info(f"Workload Type: {calc_data.get('workloadType')}")
            logger.info(f"Model: {calc_data.get('model')}")
            logger.info(f"GPU: {calc_data.get('selectedGPU')}")
            logger.info(f"Prompt Size: {calc_data.get('promptSize')}")
            logger.info(f"Response Size: {calc_data.get('responseSize')}")
            logger.info(f"Concurrent Requests: {calc_data.get('concurrentRequests')}")
        except Exception as e:
            logger.error(f"Failed to parse vGPU calc data: {e}")
    
    # Continue with existing logic...
```

## Method 2: Using the Debug Utilities

1. Import the debug utilities at the top of chains.py:
```python
from .chains_debug import WorkloadParameterDebugger, debug_decorator
```

2. Add debugger to your class:
```python
class UnstructuredRAG(BaseExample):
    def __init__(self):
        super().__init__()
        self.debugger = WorkloadParameterDebugger()
```

3. Use in your methods:
```python
def llm_chain(self, query: str, chat_history: List[Dict[str, Any]], **kwargs) -> Generator[str, None, None]:
    # Extract and debug parameters
    calc_data = self.debugger.debug_llm_chain_params(query, chat_history, **kwargs)
    
    # Use the extracted data
    if calc_data:
        # Access workload configuration
        model_requested = calc_data.get('model')
        gpu_requested = calc_data.get('selectedGPU')
        prompt_size = calc_data.get('promptSize', 1024)
        response_size = calc_data.get('responseSize', 256)
        
        # You can now use these parameters in your vGPU calculator
        from .vgpu_calculator import VGPUCalculator, VGPURequest
        
        calculator = VGPUCalculator()
        vgpu_request = VGPURequest(
            model_name=model_requested,
            vgpu_profile=gpu_requested,
            prompt_size=prompt_size,
            response_size=response_size,
            n_concurrent_request=calc_data.get('concurrentRequests', 1),
            quantization=calc_data.get('precision', 'fp16')
        )
        
        # Calculate optimal configuration
        vgpu_result = calculator.calculate(vgpu_request)
        logger.info(f"Optimal GPU: {vgpu_result.resultant_configuration.gpu_name}")
    
    # Continue with existing logic...
```

## Method 3: Interactive Debugging with Breakpoints

Add breakpoints to inspect variables in real-time:

```python
def llm_chain(self, query: str, chat_history: List[Dict[str, Any]], **kwargs) -> Generator[str, None, None]:
    # Option 1: Using pdb
    import pdb; pdb.set_trace()
    
    # Option 2: Using Python 3.7+ breakpoint
    breakpoint()
    
    # When execution stops, you can inspect:
    # - query
    # - chat_history
    # - kwargs
    # - Extract embedded data manually
```

## Method 4: Environment Variable for Debug Mode

Set an environment variable to enable detailed debugging:

```python
import os

def llm_chain(self, query: str, chat_history: List[Dict[str, Any]], **kwargs) -> Generator[str, None, None]:
    if os.environ.get("DEBUG_WORKLOAD_PARAMS", "false").lower() == "true":
        # Save all parameters to a file
        import json
        debug_data = {
            "query": query,
            "chat_history": [{"role": m.role, "content": m.content[:100]} for m in chat_history],
            "kwargs": {k: str(v)[:100] for k, v in kwargs.items()},
            "timestamp": datetime.now().isoformat()
        }
        
        with open("debug_workload_params.json", "w") as f:
            json.dump(debug_data, f, indent=2)
        
        logger.info("Debug data saved to debug_workload_params.json")
```

## Method 5: Structured Logging with Context

Create a context manager for debugging:

```python
from contextlib import contextmanager
import json

@contextmanager
def debug_context(function_name: str, **params):
    logger.info(f"=== ENTERING {function_name} ===")
    for key, value in params.items():
        logger.info(f"{key}: {value}")
    yield
    logger.info(f"=== EXITING {function_name} ===")

# Usage in chains.py:
def llm_chain(self, query: str, chat_history: List[Dict[str, Any]], **kwargs) -> Generator[str, None, None]:
    with debug_context("llm_chain", 
                      query_length=len(query),
                      history_length=len(chat_history),
                      kwargs_keys=list(kwargs.keys())):
        # Your existing logic here
        pass
```

## Running with Debug Mode

1. Set logging level to DEBUG:
```bash
export LOG_LEVEL=DEBUG
```

2. Enable workload parameter debugging:
```bash
export DEBUG_WORKLOAD_PARAMS=true
```

3. Run your application and check the logs:
```bash
tail -f logs/app.log | grep -E "(VGPU_CALC|WORKLOAD|DEBUG)"
```

## Viewing Debug Output

The debug information will appear in:
1. Console logs (if running in development)
2. Log files (check your logging configuration)
3. `debug_workload_params.json` file (if using file output)

## Example Debug Output

```
2024-01-01 12:00:00 INFO === LLM CHAIN DEBUG INFO ===
2024-01-01 12:00:00 INFO Query: Generate vGPU configuration...
2024-01-01 12:00:00 INFO === FOUND VGPU CALCULATOR DATA ===
2024-01-01 12:00:00 INFO Workload Type: inference
2024-01-01 12:00:00 INFO Model: llama-3-8b
2024-01-01 12:00:00 INFO GPU: a40
2024-01-01 12:00:00 INFO Prompt Size: 1024
2024-01-01 12:00:00 INFO Response Size: 256
2024-01-01 12:00:00 INFO Concurrent Requests: 1
``` 