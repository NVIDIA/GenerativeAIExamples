
<h1><img align="center" src="https://github.com/user-attachments/assets/cbe0d62f-c856-4e0b-b3ee-6184b7c4d96f">AI Blueprint: RAG</h1>

Use the following documentation to learn about the NVIDIA RAG Blueprint.

- [Overview](#overview)
- [Target Audience](#target-audience)
- [Software Components](#software-components)
- [Technical Diagram](#technical-diagram)
- [Hardware Requirements](#hardware-requirements)
  - [Driver versions](#driver-versions)
  - [Minimum hardware requirements for self hosting all NVIDIA NIM microservices](#minimum-hardware-requirements-for-self-hosting-all-NVIDIA-NIM-microservices)
- [Next Steps](#next-steps)
- [Available Customizations](#available-customizations)
- [Inviting the community to contribute](#inviting-the-community-to-contribute)
- [License](#license)


## Overview

This blueprint serves as a reference solution for a foundational Retrieval Augmented Generation (RAG) pipeline.
One of the key use cases in Generative AI is enabling users to ask questions and receive answers based on their enterprise data corpus.
This blueprint demonstrates how to set up a RAG solution that uses NVIDIA NIM and GPU-accelerated components.
By default, this blueprint leverages the NVIDIA-hosted models available in the [NVIDIA API Catalog](https://build.nvidia.com).
However, you can replace these models with your own locally-deployed NVIDIA NIM microservices to meet specific data governance and latency requirements.

## Target Audience

This blueprint is for:

- **Developers**: Developers who want a quick start to set up a RAG solution for unstructured data with a path-to-production with the NVIDIA NIM.


## Software Components

The following are the default components included in this blueprint:

* NVIDIA NIM Microservices
   * Response Generation (Inference)
      * [NIM of meta/llama-3.1-70b-instruct](https://build.nvidia.com/meta/llama-3_1-70b-instruct)
    * Retriever Models
      * [NIM of nvidia/llama-3_2-nv-embedqa-1b-v2]( https://build.nvidia.com/nvidia/llama-3_2-nv-embedqa-1b-v2)
      * [NIM of nvidia/llama-3_2-nv-rerankqa-1b-v2](https://build.nvidia.com/nvidia/llama-3_2-nv-rerankqa-1b-v2)
* Orchestrator server - Langchain based
* Milvus Vector Database
* Text Splitter: [Recursive Character Text Splitter](https://python.langchain.com/v0.1/docs/modules/data_connection/document_transformers/recursive_text_splitter/)
* Document parsers: [Unstructured.io](https://docs.unstructured.io)
* File Types: [File types supported](https://docs.unstructured.io/platform/supported-file-types) by unstructured.io. Accuracy is best optimized for files with extension `.pdf`, `.txt` and `.md`.

We provide Docker Compose scripts that deploy the microservices on a single node.
When you are ready for a large-scale deployment,
you can use the included Helm charts to deploy the necessary microservices.
You use sample Jupyter notebooks with the JupyterLab service to interact with the code directly.

The Blueprint contains sample data from the [NVIDIA Developer Blog](https://developer.nvidia.com/blog/).
You can build on this blueprint by customizing the RAG application to your specific use case.

We also provide a sample user interface named `rag-playground`.


## Technical Diagram

  <p align="center">
  <img src="./docs/arch_diagram.png" width="750">
  </p>


The image represents the high level architecture and workflow. The core business logic is defined in the `rag_chain_with_multiturn()` method of `chains.py` file. Here's a step-by-step explanation of the workflow from end-user perspective:

1. **User Interaction via RAG Playground**:
   - The user interacts with this blueprint by typing queries into the sample UI microservice named as **RAG Playground**. These queries are sent to the system through the `POST /generate` API exposed by the RAG server microservice. There are separate [notebooks](./notebooks/) available which showcase API usage as well.

2. **Query Processing**:
   - The query enters the **RAG Server**, which is based on LangChain. An optional **Query Rewriter** component may refine or decontextualize the query for better retrieval results.

3. **Retrieval of Relevant Documents**:
   - The refined query is passed to the **Retriever** module. This component queries the **Milvus Vector Database microservice**, which stores embeddings of unstructured data, generated using **NeMo Retriever Embedding microservice**. The retriever module identifies the top 20 most relevant chunks of information related to the query.

4. **Reranking for Precision**:
   - The top 20 chunks are passed to the optional **NeMo Retriever Ranker microservice**. The reranker narrows down the results to the top 4 most relevant chunks, improving precision.

5. **Response Generation**:
   - The top 4 chunks are injected in the prompt and sent to the **Response Generation** module, which leverages **NeMo LLM inference Microservice** to generate a natural language response based on the retrieved information.

6. **Delivery of Response**:
   - The generated response is sent back to the **RAG Playground**, where the user can view the answer to their query as well as check the output of the retriever module using the `Show Context` option.

7. **Ingestion of Data**:
   - Separately, unstructured data is ingested into the system via the `POST /documents` API using the `Knowledge Base` tab of **RAG Playground microservice**. This data is preprocessed, split into chunks and stored in the **Milvus Vector Database** using embeddings generated by models hosted by **NeMo Retriever Embedding microservice**.

This modular design ensures efficient query processing, accurate retrieval of information, and easy customization.


## Hardware Requirements

Following are the hardware requirements for each component.
The reference code in the solution (glue code) is referred to as as the "pipeline".

The overall hardware requirements depend on whether you
[Deploy With Docker Compose](/docs/quickstart.md#deploy-with-docker-compose) or [Deploy With Helm Chart](/docs/quickstart.md#deploy-with-helm-chart).


### Driver versions

- GPU Driver -  530.30.02 or later
- CUDA version - 12.6 or later


### Minimum hardware requirements for self hosting all NVIDIA NIM microservices

**The NIM and hardware requirements only need to be met if you are self-hosting them.**
See [Using self-hosted NVIDIA NIM microservices](/docs/quickstart.md#start-the-containers-using-on-prem-models).

- 8XH100, 8XA100 or 8xL40

- **Pipeline operation**: 1x L40 GPU or similar recommended. It is needed for Milvus vector store database, if you plan to enable GPU acceleration.
- (If locally deployed) **LLM NIM**: [Meta Llama 3.1 70B Instruct Support Matrix](https://docs.nvidia.com/nim/large-language-models/latest/support-matrix.html#llama-3-1-70b-instruct)
  - For improved paralleled performance, we recommend 8x or more H100s for LLM inference.
  - The pipeline can share the GPU with the LLM NIM, but it is recommended to have a separate GPU for the LLM NIM for optimal performance.
- (If locally deployed) **Embedding NIM**: [Llama-3.2-NV-EmbedQA-1B-v2 Support Matrix](https://docs.nvidia.com/nim/nemo-retriever/text-embedding/latest/support-matrix.html#llama-3-2-nv-embedqa-1b-v2)
  - The pipeline can share the GPU with the Embedding NIM, but it is recommended to have a separate GPU for the Embedding NIM for optimal performance.
- (If locally deployed) **Reranker NIM**: [llama-3_2-nv-rerankqa-1b-v1 Support Matrix](https://docs.nvidia.com/nim/nemo-retriever/text-reranking/latest/support-matrix.html#llama-3-2-nv-rerankqa-1b-v2)


## Next Steps

- Do the procedures in [Get Started](/docs/quickstart.md) to deploy this blueprint
- See the [OpenAPI Specification](/docs/api_reference/openapi_schema.json)
- Explore notebooks that demonstrate how to use the APIs [here](/notebooks/)


## Available Customizations

The following are some of the customizations that you can make after you complete the steps in [Get Started](/docs/quickstart.md).

- [Change the Inference or Embedding Model](docs/change-model.md)
- [Customize Your Vector Database](docs/vector-database.md)
- [Customize Your Text Splitter](docs/text-splitter.md)
- [Customize Prompts](docs/prompt-customization.md)
- [Customize LLM Parameters at Runtime](docs/llm-params.md)
- [Support Multi-Turn Conversations](docs/multiturn.md)


## Inviting the community to contribute

We're posting these examples on GitHub to support the NVIDIA LLM community and facilitate feedback.
We invite contributions!
To open a GitHub issue or pull request, see the [contributing guidelines](./CONTRIBUTING.md).


## License

This NVIDIA NIM-AGENT BLUEPRINT is licensed under the [Apache License, Version 2.0.](./LICENSE) This project will download and install additional third-party open source software projects. Review [the license terms of these open source projects](./LICENSE-3rd-party.txt) before use.

The software and materials are governed by the NVIDIA Software License Agreement (found at https://www.nvidia.com/en-us/agreements/enterprise-software/nvidia-software-license-agreement/) and the Product-Specific Terms for NVIDIA AI Products (found at https://www.nvidia.com/en-us/agreements/enterprise-software/product-specific-terms-for-ai-products/), except that models are governed by the AI Foundation Models Community License Agreement (found at NVIDIA Agreements | Enterprise Software | NVIDIA Community Model License) and NVIDIA dataset is governed by the NVIDIA Asset License Agreement found [here](./data/LICENSE.DATA).

For Meta/llama-3.1-70b-instruct model the Llama 3.1 Community License Agreement, for nvidia/llama-3.2-nv-embedqa-1b-v2model the Llama 3.2 Community License Agreement, and for the nvidia/llama-3.2-nv-rerankqa-1b-v2 model the Llama 3.2 Community License Agreement. Built with Llama.
