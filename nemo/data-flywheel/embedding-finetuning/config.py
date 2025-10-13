# (Required) NeMo Microservices URLs
NDS_URL = "http://data-store.test" # Data Store
NEMO_URL = "http://nemo.test" # Customizer, Entity Store, Evaluator
NIM_URL = "http://nim.test" # NIM

# (Required) Hugging Face Token
HF_TOKEN = ""

# (Optional) To observe training with WandB
WANDB_API_KEY = ""

# (Optional) Modify if you've configured a NeMo Data Store token
NDS_TOKEN = "token"

# (Optional) Use a dedicated namespace and dataset name for tutorial assets
NMS_NAMESPACE = "embed-sft-ns"
DATASET_NAME = "embed-sft-data"

# (Optional) Configure the base model for finetuning. Must be one supported by the NeMo Customizer deployment!
BASE_MODEL = "nvidia/llama-3.2-nv-embedqa-1b"
BASE_MODEL_VERSION = "v2"

# (Optional) Image name and tag for Retriever NIM deployment
BASE_MODEL_IMAGE_NAME_EMBEDDING = "nvcr.io/nim/nvidia/llama-3.2-nv-embedqa-1b-v2"
BASE_MODEL_IMAGE_TAG_EMBEDDING = "1.6.0" # Released 2025-05-01

# (Optional) Configure the custom model name.
OUTPUT_MODEL_NAME_EMBEDDING = "fullweight_sft_embedding"