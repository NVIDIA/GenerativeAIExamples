# NVIDIA Generative AI with AzureML Example

## Introduction
This example shows how to modify the canonical RAG example to use a remote NVIDIA Nemotron-8B LLM hosted in AzureML. A custom LangChain connector is used to instantiate the LLM from within a sample notebook.

### Setup Guide
1. Comment out the `llm`, `query` and `frontend` services from the [docker compose file](../../deploy/compose/docker-compose.yaml) since we will be using a notebook server and milvus vector DB server for this flow.
2. Build and deploy the services using the modified compose file
   ```
   $ source deploy/compose/compose.env;  docker compose -f deploy/compose/docker-compose.yaml build
   $ docker compose -f deploy/compose/docker-compose.yaml up -d

   $ docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   CONTAINER ID   NAMES                  STATUS
   4a8c4aebe4ad   notebook-server        Up 1 minutes
   5be2b57bb5c1   milvus-standalone      Up 1 minutes (healthy)
   a6609c22c171   milvus-minio           Up 1 minutes (healthy)
   b23c0858c4d4   milvus-etcd            Up 1 minutes (healthy)
   ```
3. Upload the `02.5_langchain_simple_AzureML.ipynb` and `trt_llm_azureml.py` files from this directory into the Jupyter environment by going to the URL ``http://host-ip:8888``.
4. Follow the steps mentioned in `02.5_langchain_simple_AzureML.ipynb` after uploading it to Jupyter Lab environment.

The Nemotron-8B models are curated by Microsoft in the ‘nvidia-ai’ Azure Machine Learning (AzureML)  registry and show up on the model catalog under the NVIDIA Collection. Explore the model card to learn more about the model architecture, use-cases and limitations.

## Large Language Models
NVIDIA LLMs are optimized for building enterprise generative AI applications.

| Name          | Description           | Type       | Context Length | Example | License |
|---------------|-----------------------|------------|----------------|---------|---------|
| [nemotron-3-8b-qa-4k](https://huggingface.co/nvidia/nemotron-3-8b-qa-4k) | Q&A LLM customized on knowledge bases | Text Generation | 4096 | No | [NVIDIA AI Foundation Models Community License Agreement](https://developer.nvidia.com/downloads/nv-ai-foundation-models-license) |
| [nemotron-3-8b-chat-4k-steerlm](https://huggingface.co/nvidia/nemotron-3-8b-chat-4k-steerlm) | Best out-of-the-box chat model with flexible alignment at inference | Text Generation | 4096 | No | [NVIDIA AI Foundation Models Community License Agreement](https://developer.nvidia.com/downloads/nv-ai-foundation-models-license) |
| [nemotron-3-8b-chat-4k-rlhf](https://huggingface.co/nvidia/nemotron-3-8b-chat-4k-rlhf) | Best out-of-the-box chat model performance| Text Generation | 4096 | No | [NVIDIA AI Foundation Models Community License Agreement](https://developer.nvidia.com/downloads/nv-ai-foundation-models-license) |
| [nemotron-3-8b-chat-sft](https://huggingface.co/nvidia/nemotron-3-8b-chat-4k-sft) | building block for instruction tuning custom models, user-defined alignment, such as RLHF or SteerLM models. | Text Generation | 4096 | No | [NVIDIA AI Foundation Models Community License Agreement](https://developer.nvidia.com/downloads/nv-ai-foundation-models-license) |
| [nemotron-3-8b-base-4k](https://huggingface.co/nvidia/nemotron-3-8b-base-4k) | enables customization, including parameter-efficient fine-tuning and continuous pre-training for domain-adapted LLMs | Text Generation | 4096 | No | [NVIDIA AI Foundation Models Community License Agreement](https://developer.nvidia.com/downloads/nv-ai-foundation-models-license) |


## NVIDIA support
This example is experimental and the workflow may not be streamlined with other examples in this repository.

## Feedback / Contributions
We're posting these examples on GitHub to better support the community, facilitate feedback, as well as collect and implement contributions using GitHub Issues and pull requests. We welcome all contributions!