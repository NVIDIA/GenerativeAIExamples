# (Required) NeMo Microservices URLs
NDS_URL = "http://data-store.test" # Data Store
NEMO_URL = "http://nemo.test" # Customizer, Entity Store, Evaluator, Guardrails
NIM_URL = "http://nim.test" # NIM

# (Required) Hugging Face Token
HF_TOKEN = ""

# (Optional) To observe training with WandB
WANDB_API_KEY = ""

# (Optional) Modify if you've configured a NeMo Data Store token
NDS_TOKEN = "token"

# (Optional) Use a dedicated namespace and dataset name for tutorial assets
NMS_NAMESPACE = "xlam-tutorial-ns"
DATASET_NAME = "xlam-ft-dataset"

# (Optional) Configure the base model. Must be one supported by the NeMo Customizer deployment!
BASE_MODEL = "meta/llama-3.2-1b-instruct"
BASE_MODEL_VERSION = "v1.0.0+A100"

# (Optional) Configure the finetuned model name. So that we can use the same finetuned model name in the all steps in the notebook.
CUSTOM_MODEL = f"{NMS_NAMESPACE}/llama-3.2-1b-xlam-run1@v1"
