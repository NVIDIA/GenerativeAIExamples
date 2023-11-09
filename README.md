# NVIDIA Generative AI Examples

## Introduction

This repository provides Generative AI examples targetted for different usecases. Modern enterprise applications are becoming more cloud-native and based on a microservices architecture. Microservices, by definition, consist of a collection of small independent services that communicate over well-defined APIs. AI applications, in most instances, adhere well to this same architectural design, as there are typically many different components that all need to work together in both training and inferencing workflows.

To deploy an application in a production environment, the application must also meet the following criteria:

- Reliability
- Security
- Performance
- Scalability
- Interoperability

## What are NVIDIA AI Workflows?
-----------------------------
NVIDIA AI Workflows are intended to provide reference solutions of how to leverage NVIDIA frameworks to build AI solutions for solving common use cases. These workflows provide guidance like fine tuning and AI model creation to build upon NVIDIA frameworks. The pipelines to create applications are highlighted, as well as opinions on how to deploy customized applications and integrate them with various components typically found in enterprise environments, such as components for orchestration and management, storage, security, networking, etc.

By leveraging an AI workflow for your specific use case, you can streamline development of AI solutions following the example provided by the workflow to:

- Reduce development time, at lower cost
- Improve accuracy and performance
- Gain confidence in outcome, by leveraging NVIDIA AI expertise

Using the example workflow provided in this repository, you know exactly what AI framework to use, how to bring data into the pipeline, and what to do with the data output. AI Workflows are designed as microservices, which means they can be deployed on Kubernetes alone or with other microservices to create a production-ready application for seamless scaling. The workflow cloud deployable package can be used across different cloud instances and is automatable and interoperable.

NVIDIA AI Workflows are available on NVIDIA NGC for [NVIDIA AI Enterprise](https://www.nvidia.com/en-us/data-center/products/ai-enterprise/) software customers.

## Examples
--------------------------

This AI Workflow includes different examples illustrating generative AI workflow. While all should be relatively easy to follow, they are targeted towards different intended audiences. For more information about the detailed components and software stacks, please refer to the guides for each workflow.

- [Retrieval Augmented Generation](./RetrievalAugmentedGeneration/README.md): A reference RAG workflow to a chatbot which can answer questions off public press releases & tech blogs.

*Note::*
- This project is releasing a [sample dataset](./RetrievalAugmentedGeneration/notebooks/dataset.zip) to quickly get started with the Retrieval Augmented Generation(RAG) workflow under [NVIDIA Asset License Agreement](./RetrievalAugmentedGeneration/notebooks/LICENSE.NSCL). Review the license terms and agree before using the dataset.
- This project will download and install additional third-party open source software projects. Review the license terms of these open source projects before use.
- The components and instructions used in the workflow are intended to be used as examples for integration, and may not be sufficiently production-ready or enterprise ready on their own as stated. The workflow should be customized and integrated into one’s own infrastructure, using the workflow as reference. For example, all of the instructions in these workflows assume a single node infrastructure, whereas production deployments should be performed in a high availability (HA) environment.
