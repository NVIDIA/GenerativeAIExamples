# RAG Documentation

The RAG documentation is divided into the following sections:

- [RAG Documentation](#rag-documentation)
  - [Getting Started](#getting-started)
  - [User Guides](#user-guides)
  - [Architecture Guide](#architecture-guide)
  - [Evaluation Tools](#evaluation-tools)
  - [Other](#other)

## Getting Started

This section will help you get started quickly with the sample RAG example.

* [Installation guide](../RetrievalAugmentedGeneration/README.md#prerequisites): This guide walks you through the process of setting up your environment and utilizing the
* [Getting Started guides](../RetrievalAugmentedGeneration/README.md#getting-started): A series of quick start steps that will help you to understand the core concepts and start the pipeline quickly. These guides include Jupyter notebooks that you can experiment with.

## User Guides

The user guides cover the core details of the provided example and how to configure and use different features to make your own chains.

* [LLM Inference Server](./rag/llm_inference_server.md): Learn about the service which accelerates LLM inference time using TRT-LLM.
* [Integration with Nvidia AI Playground](./rag/aiplayground.md): Understand how to access **NVIDIA AI Playground** on NGC which allows developers to experience state of the art LLMs accelerated on NVIDIA DGX Cloud with NVIDIA TensorRT nd Triton Inference Server.
* [Configuration Guide](./rag/configuration.md): The complete guide to all the configuration options available in the `config.yaml` file.
* [Frontend](./rag/frontend.md): Learn more about the sample playground provided as part of the workflow.
* [Chat Server Guide](./rag/chat_server.md): Learn about the chat server which exposes core API's for end user.
* [Jupyter Server Guide](./rag/jupyter_server.md): Learn about the different notebooks available and the server which can be used to access them.

## Architecture Guide

This guide sheds more light on the infrastructure details and the execution flow for a query when the runtime is used:

* [Architecture](./rag/architecture.md): Understand the architecture of the sample RAG workflow.

## Evaluation Tools

The sample RAG worlflow provides a set of evaluation pipelines via notebooks which developers can use for benchmarking.
There are also detailed guides on how to reproduce results and create datasets for the evaluation.
* [RAG Evaluation](../evaluation/README.md): Understand the different notebooks available.

## Other

* [Support Matrix](./rag/support_matrix.md)
* [Open API schema references](./rag/api_reference/openapi_schema.json)
