# Embedding Fine-tuning with NVIDIA NeMo Microservices

## Introduction

This guide shows how to fine-tune embedding models using the NVIDIA NeMo Microservices platform to improve performance on domain-specific tasks.

### Why Fine-tune Embedding Models?

Retrieval quality determines AI application quality. Better retrieval means more accurate RAG (Retrieval Augmented Generation) responses, smarter agents, and more relevant search results. Embedding models power this retrieval by converting text into semantic vectors, but pre-trained models aren't optimized for your domain's specific vocabulary and context.

Fine-tuning adapts embedding models to your data (whether scientific literature, legal documents, or enterprise knowledge bases) to achieve measurably better retrieval performance. NeMo Microservices makes this practical by providing production-ready infrastructure that handles data preparation, training, deployment, and evaluation, letting you focus on improving models rather than building pipelines.

> **New to NeMo Microservices?** Learn about Data Flywheel workflows in the [main repository README](../../../README.md#data-flywheel) or explore the [NeMo Microservices documentation](https://docs.nvidia.com/nemo/microservices/latest/about/index.html).

<div style="text-align: center;">
  <img src="./img/e2e-embedding-ft.png" alt="Embedding Fine-tuning workflow with NeMo Microservices" width="80%" />
  <p><strong>Figure 1:</strong> End-to-end workflow for fine-tuning embedding models using NeMo Microservices</p>
</div>

The diagram below shows the embedding fine-tuning workflow that NeMo Microservices orchestrates:

1. **Data Preparation**: Download and format raw data locally into query-document triplets, then upload to the NeMo Data Store.
2. **Fine-tuning**: The NeMo Customizer service orchestrates training by launching a dedicated job that retrieves the base model and training data, performs supervised fine-tuning on GPU(s), and saves the fine-tuned weights to the Entity Store (model registry).
3. **Deployment**: The Deployment Management Service deploys the fine-tuned model as a NVIDIA Inference Microservice (NIM). It retrieves the model weights from the Entity Store and starts the NIM inference service.
4. **Evaluation**: The NeMo Evaluator service measures performance by querying the deployed NIM with benchmark tasks (such as Benchmarking Information Retrieval (BEIR) SciDocs) and calculating retrieval metrics like recall and NDCG.

This modular architecture enables each component to be independently scaled and managed.

## Objectives

This tutorial shows how to use the NeMo Microservices platform to fine-tune the [nvidia/llama-3.2-nv-embedqa-1b-v2](https://build.nvidia.com/nvidia/llama-3_2-nv-embedqa-1b-v2/modelcard) embedding model using the [SPECTER](https://huggingface.co/datasets/sentence-transformers/specter) dataset, then evaluate its performance on the [BEIR Scidocs](https://huggingface.co/datasets/BeIR/scidocs) benchmark against baseline metrics.

By the end of this tutorial, you will:
- Fine-tune an embedding model on scientific domain data
- Deploy the fine-tuned model as a NIM
- Evaluate retrieval performance on the [BEIR Scidocs](https://huggingface.co/datasets/BeIR/scidocs) benchmark
- Compare results against baseline model metrics to demonstrate measurable improvement

The tutorial covers the following steps:

1. [Download and prepare data for fine-tuning](./1_data_preparation.ipynb)
2. [Fine-tune the embedding model with SFT (Supervised Fine-Tuning)](./2_finetuning_and_inference.ipynb)
3. [Evaluate the model on a zero-shot Scidocs task](./3_evaluation.ipynb)

### About the SPECTER Dataset

The [SPECTER](https://huggingface.co/datasets/embedding-data/SPECTER) dataset contains approximately 684K triplets from the scientific domain designed for training embedding models. Each triplet consists of:

- **Query**: A paper title representing a search query
- **Positive**: A related paper that should be retrieved (e.g., papers that cite each other)
- **Negative**: An unrelated paper that should not be retrieved

**Example triplet:**
```
Query:    "Deep Residual Learning for Image Recognition"
Positive: "Identity Mappings in Deep Residual Networks"
Negative: "Attention Is All You Need"
```

During fine-tuning, the model learns through **contrastive learning** to maximize the similarity between the query and positive document while minimizing similarity with negative documents. This trains the model to produce embeddings that effectively capture semantic relationships in the scientific literature domain.

## Prerequisites

### Deploy NeMo Microservices

To follow this tutorial, you will need at least two NVIDIA GPUs:

- **Fine-tuning:** One GPU for fine-tuning the `llama-3.2-nv-embedqa-1b-v2` model with NeMo Customizer.
- **Inference:** One GPU for deploying the fine-tuned model as a NIM.

If you're new to NeMo Microservices, follow the [Demo Cluster Setup on Minikube](https://docs.nvidia.com/nemo/microservices/latest/get-started/setup/minikube/index.html) guide to get started. For production deployments, refer to the [platform prerequisites and installation guide](https://docs.nvidia.com/nemo/microservices/latest/get-started/platform-prereq.html).

> **NOTE:** Fine-tuning for embedding models is supported starting with NeMo Microservices version 25.8.0. Please ensure you deploy NeMo Microservices Helm chart version 25.8.0 or later to use these notebooks.

### Register the Base Model

After deploying NeMo Microservices, register the `llama-3.2-nv-embedqa-1b-v2` base model with NeMo Customizer:

```bash
helm upgrade nemo nmp/nemo-microservices-helm-chart --namespace default --reuse-values \
  --set customizer.customizationTargets.overrideExistingTargets=false \
  --set 'customizer.customizationTargets.targets.nvidia/llama-3\.2-nv-embedqa-1b@v2.enabled=true' && \
kubectl delete pod -n default -l app.kubernetes.io/name=nemo-customizer && \
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=nemo-customizer -n default --timeout=5m
```

This restarts the customizer to register the model (~2-3 minutes). The base checkpoint downloads from NGC on first use.

### Client-Side Requirements

Ensure you have access to:

1. A Python-enabled machine capable of running Jupyter Lab.
2. Network access to the NeMo Microservices IP and ports.

## Get Started

1. Create a virtual environment using uv (recommended for better dependency management):

   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Create and activate virtual environment
   uv venv nemo_env
   source nemo_env/bin/activate
   ```

2. Install the required Python packages using requirements.txt with uv:

   ```bash
   uv pip install -r requirements.txt
   ```

3. Update the following variables in [config.py](./config.py) with your specific URLs and API keys.

   **How to obtain the required values:**
   
   - **NeMo Microservices URLs**: If you followed the [Demo Cluster Setup on Minikube](https://docs.nvidia.com/nemo/microservices/latest/get-started/setup/minikube/index.html) guide, run `cat /etc/hosts` on your deployment machine to view the configured service hostnames and IP addresses.
   - **Hugging Face Token**: Generate a token at [https://huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) to download the SPECTER dataset.

   ```python
   # (Required) NeMo Microservices URLs
   NDS_URL = "http://data-store.test" # Data Store
   NEMO_URL = "http://nemo.test" # Customizer, Entity Store, Evaluator
   NIM_URL = "http://nim.test" # NIM

   # (Required) Hugging Face Token
   HF_TOKEN = ""

   # (Optional) To observe training with WandB
   WANDB_API_KEY = ""
   ```

4. Launch Jupyter Lab to begin working with the provided tutorials:

   ```bash
   uv run jupyter lab --ip 0.0.0.0 --port=8888 --allow-root
   ```

5. Navigate to the [data preparation notebook](./1_data_preparation.ipynb) to get started.
