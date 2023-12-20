# NVIDIA Generative AI Examples

## Introduction
State-of-the-art Generative AI examples that are easy to deploy, test, and extend. All examples run on the high performance NVIDIA CUDA-X software stack and NVIDIA GPUs.

## NVIDIA NGC
Generative AI Examples uses resources from the [NVIDIA NGC AI Development Catalog](https://ngc.nvidia.com).

Sign up for a [free NGC developer account](https://ngc.nvidia.com/signin) to access:

- The GPU-optimized NVIDIA containers, models, scripts, and tools used in these examples
- The latest NVIDIA upstream contributions to the respective programming frameworks
- The latest NVIDIA Deep Learning and LLM software libraries
- Release notes for each of the NVIDIA optimized containers
- Links to developer documentation

## Retrieval Augmented Generation (RAG)

A RAG pipeline embeds multimodal data --  such as documents, images, and video -- into a database connected to a Large Language Model.  RAG lets users use an LLM to chat with their own data.

| Name          | Description           | LLM        | Framework               | Multi-GPU | Multi-node | Embedding   | TRT-LLM | Triton | VectorDB | K8s |
|---------------|-----------------------|------------|-------------------------|-----------|------------|-------------|---------|--------|----------|-----|
| [Linux developer RAG](https://github.com/NVIDIA/GenerativeAIExamples/tree/main/RetrievalAugmentedGeneration) | Single VM, single GPU | llama2-13b | Langchain + Llama Index | No        | No         | e5-large-v2 | Yes     | Yes    | Milvus   | No  |
| [Windows developer RAG](https://github.com/NVIDIA/trt-llm-rag-windows) | RAG on Windows | llama2-13b | Llama Index | No        | No         | NA | Yes     | No    | FAISS   | NA  |
| [Developer LLM Operator for Kubernetes](./docs/developer-llm-operator/) | Single node, single GPU | llama2-13b | Langchain + Llama Index |  No | No | e5-large-v2 | Yes | Yes | Milvus | Yes |


## Large Language Models
NVIDIA LLMs are optimized for building enterprise generative AI applications.

| Name          | Description           | Type       | Context Length | Example | License |
|---------------|-----------------------|------------|----------------|---------|---------|
| [nemotron-3-8b-qa-4k](https://huggingface.co/nvidia/nemotron-3-8b-qa-4k) | Q&A LLM customized on knowledge bases | Text Generation | 4096 | No | [NVIDIA AI Foundation Models Community License Agreement](https://developer.nvidia.com/downloads/nv-ai-foundation-models-license) |
| [nemotron-3-8b-chat-4k-steerlm](https://huggingface.co/nvidia/nemotron-3-8b-chat-4k-steerlm) | Best out-of-the-box chat model with flexible alignment at inference | Text Generation | 4096 | No | [NVIDIA AI Foundation Models Community License Agreement](https://developer.nvidia.com/downloads/nv-ai-foundation-models-license) |
| [nemotron-3-8b-chat-4k-rlhf](https://huggingface.co/nvidia/nemotron-3-8b-chat-4k-rlhf) | Best out-of-the-box chat model performance| Text Generation | 4096 | No | [NVIDIA AI Foundation Models Community License Agreement](https://developer.nvidia.com/downloads/nv-ai-foundation-models-license) |


## Integration Examples

## NVIDIA support
In each of the READMEs, we indicate the level of support provided.

## Feedback / Contributions
We're posting these examples on GitHub to better support the community, facilitate feedback, as well as collect and implement contributions using GitHub Issues and pull requests. We welcome all contributions!

## Known issues
- In each of the READMEs, we indicate any known issues and encourage the community to provide feedback.
- The datasets provided as part of this project is under a different license for research and evaluation purposes.
- This project will download and install additional third-party open source software projects. Review the license terms of these open source projects before use.
