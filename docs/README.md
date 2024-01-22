# RAG Documentation

The RAG documentation is divided into the following sections:

- [RAG Documentation](#rag-documentation)
  - [Getting Started](#getting-started)
  - [User Guides](#user-guides)
  - [Architecture Guide](#architecture-guide)
  - [Evaluation Tool](#evaluation-tool)
  - [Observability Tool](#observability-tool)
  - [Others](#others)

## Getting Started

* [Getting Started guides](../RetrievalAugmentedGeneration/README.md): A series of quick start steps that will help you to understand the core concepts and start the pipeline quickly for the different examples and usecases provided in this repository. These guides also include Jupyter notebooks that you can experiment with.

## User Guides

The user guides cover the core details of the provided sample canonical developer rag example and how to configure and use different features to make your own chains.

* [LLM Inference Server](./rag/llm_inference_server.md): Learn about the service which accelerates LLM inference time using TRT-LLM.
* [Integration with Nvidia AI Playground](./rag/aiplayground.md): Understand how to access **NVIDIA AI Playground** on NGC which allows developers to experience state of the art LLMs and embedding models accelerated on NVIDIA DGX Cloud with NVIDIA TensorRT and Triton Inference Server.
* [Configuration Guide](./rag/configuration.md): The complete guide to all the configuration options available in the `config.yaml` file.
* [Frontend](./rag/frontend.md): Learn more about the sample playground provided as part of the workflow used by all the examples.
* [Chat Server Guide](./rag/chat_server.md): Learn about the chat server which exposes core API's for the end user. All the different examples are deployed behind these standardized API's, exposed by this server.
* [Notebooks Guide](./rag/jupyter_server.md): Learn about the different notebooks available and the server which can be used to access them.

## Architecture Guide

This guide sheds more light on the infrastructure details and the execution flow for a query when the runtime is used for the default canonical RAG example:

* [Architecture](./rag/architecture.md): Understand the architecture of the sample RAG workflow.

## Evaluation Tool

The sample RAG worlflow provides a set of evaluation pipelines via notebooks which developers can use for benchmarking the default canonical RAG example.
There are also detailed guides on how to reproduce results and create datasets for the evaluation.
* [RAG Evaluation](./rag/evaluation.md): Understand the different notebooks available.

## Observability Tool

Observability is a crucial aspect that facilitates the monitoring and comprehension of the internal state and behavior of a system or application.
* [Observability tool](./rag/observability.md): Understand the tool and deployment steps for the observability tool.

## Others

* [Support Matrix](./rag/support_matrix.md)
* [Open API schema references](./rag/api_reference/openapi_schema.json)
