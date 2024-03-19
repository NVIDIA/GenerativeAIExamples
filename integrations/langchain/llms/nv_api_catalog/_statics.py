from typing import Optional

from langchain_core.pydantic_v1 import BaseModel


class Model(BaseModel):
    id: str
    model_type: Optional[str] = None
    model_name: Optional[str] = None
    client: Optional[str] = None
    path: str


MODEL_SPECS = {
    "playground_smaug_72b": {"model_type": "chat"},
    "playground_kosmos_2": {"model_type": "image_in"},
    "playground_llama2_70b": {"model_type": "chat"},
    "playground_nvolveqa_40k": {"model_type": "embedding"},
    "playground_nemotron_qa_8b": {"model_type": "qa"},
    "playground_gemma_7b": {"model_type": "chat"},
    "playground_mistral_7b": {"model_type": "chat"},
    "playground_mamba_chat": {"model_type": "chat"},
    "playground_phi2": {"model_type": "chat"},
    "playground_sdxl": {"model_type": "image_out"},
    "playground_nv_llama2_rlhf_70b": {"model_type": "chat"},
    "playground_neva_22b": {"model_type": "image_in"},
    "playground_yi_34b": {"model_type": "chat"},
    "playground_nemotron_steerlm_8b": {"model_type": "chat"},
    "playground_cuopt": {"model_type": "cuopt"},
    "playground_llama_guard": {"model_type": "classifier"},
    "playground_starcoder2_15b": {"model_type": "completion"},
    "playground_deplot": {"model_type": "image_in"},
    "playground_llama2_code_70b": {"model_type": "chat"},
    "playground_gemma_2b": {"model_type": "chat"},
    "playground_seamless": {"model_type": "translation"},
    "playground_mixtral_8x7b": {"model_type": "chat"},
    "playground_fuyu_8b": {"model_type": "image_in"},
    "playground_llama2_code_34b": {"model_type": "chat"},
    "playground_llama2_code_13b": {"model_type": "chat"},
    "playground_steerlm_llama_70b": {"model_type": "chat"},
    "playground_clip": {"model_type": "similarity"},
    "playground_llama2_13b": {"model_type": "chat"},
}

MODEL_SPECS.update(
    {
        'ai-codellama-70b': {'model_type': 'chat', 'model_name': 'meta/codellama-70b'},
        # 'ai-embedding-2b': {'model_type': 'embedding'},
        'ai-fuyu-8b': {'model_type': 'image_in'},
        'ai-gemma-7b': {'model_type': 'chat', 'model_name': 'google/gemma-7b'},
        'ai-google-deplot': {'model_type': 'image_in'},
        'ai-llama2-70b': {'model_type': 'chat', 'model_name': 'meta/llama2-70b'},
        'ai-microsoft-kosmos-2': {'model_type': 'image_in'},
        'ai-mistral-7b-instruct-v2': {'model_type': 'chat', 'model_name': 'mistralai/mistral-7b-instruct-v0.2'},
        'ai-mixtral-8x7b-instruct': {'model_type': 'chat', 'model_name': 'mistralai/mixtral-8x7b-instruct-v0.1'},
        'ai-neva-22b': {'model_type': 'image_in'},
        # 'ai-reranking-4b': {'model_type': 'chat'},
        # 'ai-sdxl-turbo': {'model_type': 'image_out'},
        # 'ai-stable-diffusion-xl-base': {'model_type': 'iamge_out'},
    }
)


MODEL_SPECS.update(
    {
        "babbage-002": {"model_type": "completion"},
        "dall-e-2": {"model_type": "image_out"},
        "dall-e-3": {"model_type": "image_out"},
        "davinci-002": {"model_type": "completion"},
        "gpt-3.5-turbo-0125": {"model_type": "chat"},
        "gpt-3.5-turbo-0301": {"model_type": "chat"},
        "gpt-3.5-turbo-0613": {"model_type": "chat"},
        "gpt-3.5-turbo-1106": {"model_type": "chat"},
        "gpt-3.5-turbo-16k-0613": {"model_type": "chat"},
        "gpt-3.5-turbo-16k": {"model_type": "chat"},
        "gpt-3.5-turbo-instruct-0914": {"model_type": "completion"},
        "gpt-3.5-turbo-instruct": {"model_type": "completion"},
        "gpt-3.5-turbo": {"model_type": "chat"},
        "gpt-4-0125-preview": {"model_type": "chat"},
        "gpt-4-0613": {"model_type": "chat"},
        "gpt-4-1106-preview": {"model_type": "chat"},
        "gpt-4-turbo-preview": {"model_type": "chat"},
        "gpt-4-vision-preview": {"model_type": "chat"},
        "gpt-4": {"model_type": "chat"},
        "text-embedding-3-large": {"model_type": "embedding"},
        "text-embedding-3-small": {"model_type": "embedding"},
        "text-embedding-ada-002": {"model_type": "embedding"},
        "tts-1-1106": {"model_type": "tts"},
        "tts-1-hd-1106": {"model_type": "tts"},
        "tts-1-hd": {"model_type": "tts"},
        "tts-1": {"model_type": "tts"},
        "whisper-1": {"model_type": "asr"},
    }
)

client_map = {
    "asr": "None",
    "chat": "ChatNVIDIA",
    "classifier": "None",
    "completion": "NVIDIA",
    "cuopt": "None",
    "embedding": "NVIDIAEmbeddings",
    "image_in": "ChatNVIDIA",
    "image_out": "ImageGenNVIDIA",
    "qa": "ChatNVIDIA",
    "similarity": "None",
    "translation": "None",
    "tts": "None",
}

MODEL_SPECS = {
    k: {**v, "client": client_map[v["model_type"]]} for k, v in MODEL_SPECS.items()
}
