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

A RAG pipeline embeds multimodal data --  such as documents, images, and video -- into a database connected to a Large Language Model.  RAG lets users chat with their own data. 

| Name                                                                                                                 | LLM   | Framework  | Multi-GPU | Multi-Node | Embedding | TRT-LLM | Triton                                                                                                    | VectorDB  | K8s                                                                                                                                          |
|------------------------------------------------------------------------------------------------------------------------|-------------|------|-----------|------------|----------|------|-----------------------------------------------------------------------------------------------------------|------|---------------------------------------------------------------------------------------------------------------------------------------------|
| [Developer RAG](https://github.com/NVIDIA/GenerativeAIExamples/tree/main/RetrievalAugmentedGeneration)                       | llama2-13b     | Langchain + Llama Index  | Yes       | No        | e5-large-v2| Yes    | Yes    | Milvus  | No                                                                                                                                           |
 

## Large Language Models
The NVIDIA family of Large Language Models (LLMs) is optimized for building production-ready generative AI applications for the enterprise.


## Integration Examples

## NVIDIA support
In each of the network READMEs, we indicate the level of support that will be provided. The range is from ongoing updates and improvements to a point-in-time release for thought leadership.

## Feedback / Contributions
We're posting these examples on GitHub to better support the community, facilitate feedback, as well as collect and implement contributions using GitHub Issues and pull requests. We welcome all contributions!

## Known issues
In each of the network READMEs, we indicate any known issues and encourage the community to provide feedback.

*Note::*
- The datasets provided as part of this project is under a different license for research and evaluation purposes.
- This project will download and install additional third-party open source software projects. Review the license terms of these open source projects before use.
