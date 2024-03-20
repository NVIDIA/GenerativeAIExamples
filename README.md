# NVIDIA Generative AI Examples

[![documentation](https://img.shields.io/badge/documentation-blue.svg)](https://nvidia.github.io/GenerativeAIExamples/latest)

## Introduction

State-of-the-art Generative AI examples that are easy to deploy, test, and extend. All examples run on the high performance NVIDIA CUDA-X software stack and NVIDIA GPUs.

## NVIDIA NGC
Generative AI Examples uses resources from the [NVIDIA NGC AI Development Catalog](https://ngc.nvidia.com).

Sign up for a [free NGC developer account](https://ngc.nvidia.com/signin) to access:

- GPU-optimized containers used in these examples
- Release notes and developer documentation

## Retrieval Augmented Generation (RAG)

A RAG pipeline embeds multimodal data --  such as documents, images, and video -- into a database connected to a LLM.  RAG lets users chat with their data!

### Developer RAG Examples

The developer RAG examples run on a single VM. They demonstrate how to combine NVIDIA GPU acceleration with popular LLM programming frameworks using NVIDIA's [open source connectors](#open-source-integrations). The examples are easy to deploy via [Docker Compose](https://docs.docker.com/compose/).

Examples support local and remote inference endpoints. If you have a GPU, you can inference locally via [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM). If you don't have a GPU, you can inference and embed remotely via [NVIDIA AI Foundations endpoints](https://www.nvidia.com/en-us/ai-data-science/foundation-models/).

| Model         | Embedding           | Framework        | Description               | Multi-GPU | TRT-LLM | NVIDIA AI Foundation | Triton | Vector Database |
|---------------|-----------------------|------------|-------------------------|-----------|------------|-------------|---------|--------|
| llama-2 | e5-large-v2 | Llamaindex | Canonical QA Chatbot | [YES](RetrievalAugmentedGeneration/README.md#3-qa-chatbot-multi-gpu----a100h100l40s)        | [YES](RetrievalAugmentedGeneration/README.md#2-qa-chatbot----a100h100l40s-gpu)       | No | YES     | Milvus/[PGVector]((RetrievalAugmentedGeneration/README.md#2-qa-chatbot----a100h100l40s-gpu))|
| mixtral_8x7b | nvolveqa_40k | Langchain | [Nvidia AI foundation based QA Chatbot](RetrievalAugmentedGeneration/README.md#1-qa-chatbot----nvidia-ai-foundation-inference-endpoint)  | No        | No       | YES | YES     | Milvus|
| llama-2 | all-MiniLM-L6-v2 | Llama Index | [QA Chatbot, GeForce, Windows](https://github.com/NVIDIA/trt-llm-rag-windows/tree/release/1.0)  | NO        | YES        | NO | NO     | FAISS |
| llama-2 | nvolveqa_40k | Langchain | [QA Chatbot, Task Decomposition Agent](./RetrievalAugmentedGeneration/README.md#5-qa-chatbot-with-task-decomposition-example----a100h100l40s) | No | No | YES | YES | FAISS
| mixtral_8x7b | nvolveqa_40k | Langchain | [Minimilastic example showcasing RAG using Nvidia AI foundation models](./examples/README.md#rag-in-5-minutes-example)  | No        | No       | YES | YES     | FAISS|



### Enterprise RAG Examples

The enterprise RAG examples run as microservies distributed across multiple VMs and GPUs. They show how RAG pipelines can be orchestrated with [Kubernetes](https://kubernetes.io/) and deployed with [Helm](https://helm.sh/).

Enterprise RAG examples include a [Kubernetes operator](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) for LLM lifecycle management. It is compatible with the [NVIDIA GPU operator](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/gpu-operator) that automates GPU discovery and lifecycle management in a Kubernetes cluster.

Enterprise RAG examples also support local and remote inference via [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM) and [NVIDIA AI Foundations endpoints](https://www.nvidia.com/en-us/ai-data-science/foundation-models/).

| Model         | Embedding           | Framework        | Description               | Multi-GPU | Multi-node | TRT-LLM | NVIDIA AI Foundation | Triton | Vector Database |
|---------------|-----------------------|------------|--------|-------------------------|-----------|------------|-------------|---------|--------|
| llama-2 | NV-Embed-QA | Llamaindex | QA Chatbot, Helm, k8s  | NO        | NO | [YES](./docs/developer-llm-operator/)         | NO | YES     | Milvus|

## Tools

Example tools and tutorials to enhance LLM development and productivity when using NVIDIA RAG pipelines.

| Name | Description | Deployment | Tutorial |
|------|-------------|------|--------|
| Evaluation | Example open source RAG eval tool that uses synthetic data generation and LLM-as-a-judge |  [Docker compose file](./deploy/compose/docker-compose-evaluation.yaml) | [README](./docs/rag/evaluation.md) |]
| Observability | Observability serves as an efficient mechanism for both monitoring and debugging RAG pipelines. |  [Docker compose file](./deploy/compose/docker-compose-observability.yaml) | [README](./docs/rag/observability.md) |]

## Open Source Integrations

These are open source connectors for NVIDIA-hosted and self-hosted API endpoints. These open source connectors are maintained and tested by NVIDIA engineers.

| Name | Framework | Chat | Text Embedding | Python | Description |
|------|-----------|------|-----------|--------|-------------|
|[NVIDIA AI Foundation Endpoints](https://python.langchain.com/docs/integrations/providers/nvidia) | [Langchain](https://www.langchain.com/) |[YES](https://python.langchain.com/docs/integrations/chat/nvidia_ai_endpoints)|[YES](https://python.langchain.com/docs/integrations/text_embedding/nvidia_ai_endpoints)|[YES](https://pypi.org/project/langchain-nvidia-ai-endpoints/)|Easy access to NVIDIA hosted models. Supports chat, embedding, code generation, steerLM, multimodal, and RAG.|
|[NVIDIA Triton + TensorRT-LLM](https://github.com/langchain-ai/langchain/tree/master/libs/partners/nvidia-trt) | [Langchain](https://www.langchain.com/) |[YES](https://github.com/langchain-ai/langchain-nvidia/blob/main/libs/trt/docs/llms.ipynb)|[YES](https://github.com/langchain-ai/langchain-nvidia/blob/main/libs/trt/docs/llms.ipynb)|[YES](https://pypi.org/project/langchain-nvidia-trt/)|This connector allows Langchain to remotely interact with a Triton inference server over GRPC or HTTP tfor optimized LLM inference.|
|[NVIDIA Triton Inference Server](https://docs.llamaindex.ai/en/stable/examples/llm/nvidia_triton.html) | [LlamaIndex](https://www.llamaindex.ai/) |YES|YES|NO|Triton inference server provides API access to hosted LLM models over gRPC. |
|[NVIDIA TensorRT-LLM](https://docs.llamaindex.ai/en/stable/examples/llm/nvidia_tensorrt.html) | [LlamaIndex](https://www.llamaindex.ai/) |YES|YES|NO|TensorRT-LLM provides a Python API to build TensorRT engines with state-of-the-art optimizations for LLM inference on NVIDIA GPUs. |


## NVIDIA support
In each example README we indicate the level of support provided.

## Feedback / Contributions
We're posting these examples on GitHub to support the NVIDIA LLM community, facilitate feedback. We invite contributions via GitHub Issues or pull requests!

## Known issues
- In each of the READMEs, we indicate any known issues and encourage the community to provide feedback.
- The datasets provided as part of this project is under a different license for research and evaluation purposes.
- This project will download and install additional third-party open source software projects. Review the license terms of these open source projects before use.
