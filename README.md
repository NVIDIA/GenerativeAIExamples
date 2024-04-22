# NVIDIA Generative AI Examples

[![documentation](https://img.shields.io/badge/documentation-blue.svg)](https://nvidia.github.io/GenerativeAIExamples/latest)

## Introduction

State-of-the-art Generative AI examples that are easy to deploy, test, and extend. All examples run on the high performance NVIDIA CUDA-X software stack and NVIDIA GPUs.

## NVIDIA NGC

Generative AI Examples can use models and GPUs from the [NVIDIA NGC: AI Development Catalog](https://catalog.ngc.nvidia.com).

Sign up for a [free NGC developer account](https://ngc.nvidia.com/signin) to access:

- GPU-optimized containers used in these examples
- Release notes and developer documentation

## Retrieval Augmented Generation (RAG)

A RAG pipeline embeds multimodal data --  such as documents, images, and video -- into a database connected to a LLM.
RAG lets users chat with their data!

### Developer RAG Examples

The developer RAG examples run on a single VM.
The examples demonstrate how to combine NVIDIA GPU acceleration with popular LLM programming frameworks using NVIDIA's [open source connectors](#open-source-integrations).
The examples are easy to deploy with [Docker Compose](https://docs.docker.com/compose/).

Examples support local and remote inference endpoints.
If you have a GPU, you can inference locally with [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM).
If you don't have a GPU, you can inference and embed remotely with [NVIDIA API Catalog endpoints](https://build.nvidia.com/explore/discover).

| Model                              | Embedding        | Framework  | Description                                                                                                                                                                                               | Multi-GPU                                                                  | TRT-LLM | NVIDIA Endpoints | Triton | Vector Database    |
| ---------------------------------- | ---------------- | ---------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- | ------- | ---------------- | ------ | ------------------ |
| mixtral_8x7b                       | nvolveqa_40k     | LangChain  | NVIDIA API Catalog endpoints chat bot [[code](./RetrievalAugmentedGeneration/examples/nvidia_api_catalog/), [docs](https://nvidia.github.io/GenerativeAIExamples/latest/api-catalog.html)]                | No                                                                         | No      | Yes              | Yes    | Milvus or pgvector |
| llama-2                            | e5-large-v2      | LlamaIndex | Canonical QA Chatbot [[code](./RetrievalAugmentedGeneration/examples/developer_rag/), [docs](https://nvidia.github.io/GenerativeAIExamples/latest/local-gpu.html)]                                        | [Yes](https://nvidia.github.io/GenerativeAIExamples/latest/multi-gpu.html) | Yes     | No               | Yes    | Milvus or pgvector |
| llama-2                            | all-MiniLM-L6-v2 | LlamaIndex | Chat bot, GeForce, Windows [[repo](https://github.com/NVIDIA/trt-llm-rag-windows/tree/release/1.0)]                                                                                                       | No                                                                         | Yes     | No               | No     | FAISS              |
| llama-2                            | nvolveqa_40k     | LangChain  | Chat bot with query decomposition agent [[code](./RetrievalAugmentedGeneration/examples/query_decomposition_rag/), [docs](https://nvidia.github.io/GenerativeAIExamples/latest/query-decomposition.html)] | No                                                                         | No      | Yes              | Yes    | Milvus or pgvector |
| mixtral_8x7b                       | nvolveqa_40k     | LangChain  | Minimilastic example: RAG with NVIDIA AI Foundation Models [[code](./examples/5_mins_rag_no_gpu/), [README](./examples/README.md#rag-in-5-minutes-example)]                                               | No                                                                         | No      | Yes              | Yes    | FAISS              |
| mixtral_8x7b<br>Deplot<br>Neva-22b | nvolveqa_40k     | Custom     | Chat bot with multimodal data [[code](./RetrievalAugmentedGeneration/examples/multimodal_rag/), [docs](https://nvidia.github.io/GenerativeAIExamples/latest/multimodal-data.html)]                        | No                                                                         | No      | Yes              | No     | Milvus or pvgector |
| llama-2                            | e5-large-v2      | LlamaIndex | Chat bot with quantized LLM model [[docs](https://nvidia.github.io/GenerativeAIExamples/latest/quantized-llm-model.html)]                                                                                 | Yes                                                                        | Yes     | No               | Yes    | Milvus or pgvector |
| mixtral_8x7b                       | none             | PandasAI   | Chat bot with structured data [[code](./RetrievalAugmentedGeneration/examples/structured_data_rag/), [docs](https://nvidia.github.io/GenerativeAIExamples/latest/structured-data.html)]                   | No                                                                         | No      | Yes              | No     | none               |
| llama-2                            | nvolveqa_40k     | LangChain  | Chat bot with multi-turn conversation [[code](./RetrievalAugmentedGeneration/examples/multi_turn_rag/), [docs](https://nvidia.github.io/GenerativeAIExamples/latest/multi-turn.html)]                     | No                                                                         | No      | Yes              | No     | Milvus or pgvector |

### Enterprise RAG Examples

The enterprise RAG examples run as microservices distributed across multiple VMs and GPUs.
These examples show how to orchestrate RAG pipelines with [Kubernetes](https://kubernetes.io/) and deployed with [Helm](https://helm.sh/).

Enterprise RAG examples include a [Kubernetes operator](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/) for LLM lifecycle management.
It is compatible with the [NVIDIA GPU operator](https://catalog.ngc.nvidia.com/orgs/nvidia/containers/gpu-operator) that automates GPU discovery and lifecycle management in a Kubernetes cluster.

Enterprise RAG examples also support local and remote inference with [TensorRT-LLM](https://github.com/NVIDIA/TensorRT-LLM) and [NVIDIA API Catalog endpoints](https://build.nvidia.com/explore/discover).

| Model   | Embedding   | Framework  | Description                                                                | Multi-GPU | Multi-node | TRT-LLM | NVIDIA Endpoints | Triton | Vector Database |
| ------- | ----------- | ---------- | -------------------------------------------------------------------------- | --------- | ---------- | ------- | ---------------- | ------ | --------------- |
| llama-2 | NV-Embed-QA | LlamaIndex | Chat bot, Kubernetes deployment [[README](./docs/developer-llm-operator/)] | No        | No         | Yes     | No               | Yes    | Milvus          |


### Generative AI Model Examples

The generative AI model examples include end-to-end steps for pre-training, customizing, aligning and running inference on state-of-the-art generative AI models leveraging the [NVIDIA NeMo Framework](https://github.com/NVIDIA/NeMo)

| Model   | Resources(s) | Framework | Description |
| ------- | ----------- | ----------- | ----------- |
| gemma | [Docs](./models/Gemma/), [LoRA](./models/Gemma/lora.ipynb), [SFT](./models/Gemma/sft.ipynb) | NeMo | Aligning and customizing Gemma, and exporting to TensorRT-LLM format for inference |
| codegemma | [Docs](./models/Codegemma/), [LoRA](./models/Codegemma/lora.ipynb) | NeMo | Customizing Codegemma, and exporting to TensorRT-LLM format for inference |
| starcoder-2 | [LoRA](./models/StarCoder2/lora.ipynb), [Inference](./models/StarCoder2/inference.ipynb) | NeMo | Customizing Starcoder-2 with NeMo Framework, optimizing with NVIDIA TensorRT-LLM, and deploying with NVIDIA Triton Inference Server |
| small language models (SLMs) | [Docs](./models/NeMo/slm/), [Pre-training and SFT](./models/NeMo/slm/slm_pretraining_sft.ipynb), [Eval](./models/NeMo/slm/megatron_gpt_eval_server.ipynb) | NeMo | Training, alignment, and running evaluation on SLMs using various techniques |


## Tools

Example tools and tutorials to enhance LLM development and productivity when using NVIDIA RAG pipelines.

| Name          | Description                                                                                                                                                                   | NVIDIA Endpoints |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| Evaluation    | RAG evaluation using synthetic data generation and LLM-as-a-judge [[code](./tools/evaluation/), [docs](https://nvidia.github.io/GenerativeAIExamples/latest/evaluation.html)] | Yes              |
| Observability | Monitoring and debugging RAG pipelines [[code](./tools/observability/), [docs](https://nvidia.github.io/GenerativeAIExamples/latest/observability.html)]                      | Yes              |

## Open Source Integrations

These are open source connectors for NVIDIA-hosted and self-hosted API endpoints. These open source connectors are maintained and tested by NVIDIA engineers.

| Name | Framework | Chat | Text Embedding | Python | Description |
|------|-----------|------|----------------|--------|-------------|
|[NVIDIA AI Foundation Endpoints](https://python.langchain.com/docs/integrations/providers/nvidia) | [Langchain](https://www.langchain.com/) |[Yes](https://python.langchain.com/docs/integrations/chat/nvidia_ai_endpoints)|[Yes](https://python.langchain.com/docs/integrations/text_embedding/nvidia_ai_endpoints)|[Yes](https://pypi.org/project/langchain-nvidia-ai-endpoints/)|Easy access to NVIDIA hosted models. Supports chat, embedding, code generation, steerLM, multimodal, and RAG.|
|[NVIDIA Triton + TensorRT-LLM](https://github.com/langchain-ai/langchain/tree/master/libs/partners/nvidia-trt) | [Langchain](https://www.langchain.com/) |[Yes](https://github.com/langchain-ai/langchain-nvidia/blob/main/libs/trt/docs/llms.ipynb)|[Yes](https://github.com/langchain-ai/langchain-nvidia/blob/main/libs/trt/docs/llms.ipynb)|[Yes](https://pypi.org/project/langchain-nvidia-trt/)|This connector allows Langchain to remotely interact with a Triton inference server over GRPC or HTTP for optimized LLM inference.|
|[NVIDIA Triton Inference Server](https://docs.llamaindex.ai/en/stable/examples/llm/nvidia_triton.html) | [LlamaIndex](https://www.llamaindex.ai/) |Yes|Yes|No|Triton inference server provides API access to hosted LLM models over gRPC. |
|[NVIDIA TensorRT-LLM](https://docs.llamaindex.ai/en/stable/examples/llm/nvidia_tensorrt.html) | [LlamaIndex](https://www.llamaindex.ai/) |Yes|Yes|No|TensorRT-LLM provides a Python API to build TensorRT engines with state-of-the-art optimizations for LLM inference on NVIDIA GPUs. |

## Support, Feedback, and Contributing

We're posting these examples on GitHub to support the NVIDIA LLM community and facilitate feedback.
We invite contributions via GitHub Issues or pull requests!

## Known Issues

- Some known issues are identified as TODOs in the Python code.
- The datasets provided as part of this project are under a different license for research and evaluation purposes.
- This project downloads and installs third-party open source software projects. Review the license terms of these open source projects before use.
