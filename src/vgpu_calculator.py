from langchain.tools import tool
from calculator import VGPUCalculator, VGPURequest 

@tool(args_schema=VGPURequest)
def vgpu_calculator(
    num_gpu: int,
    prompt_size: int = 1024,
    response_size: int = 250,
    n_concurrent_request: int = 1,
    quantization: str = "fp16",
    model_name: str = "Llama-3-8B",
    vgpu_profile: str = "A40-12Q"
) -> dict:
    """
    Calculate optimal vGPU configuration for LLM workloads.

    Input:
    - model_name
    - vgpu_profile
    - num_gpu
    - prompt_size
    - response_size
    - n_concurrent_request
    - quantization

    Returns:
        Dict in API response format
    """
    request = VGPURequest(
        num_gpu=num_gpu,
        prompt_size=prompt_size,
        response_size=response_size,
        n_concurrent_request=n_concurrent_request,
        quantization=quantization,
        model_name=model_name,
        vgpu_profile=vgpu_profile
    )
    calculator = VGPUCalculator()
    result = calculator.calculate(request)
    return result.to_api_response()