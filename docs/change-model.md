<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Changing the Inference or Embedding Model

<!-- TOC -->

* [Models from the API Catalog](#models-from-the-api-catalog)
    * [Changing the Inference Model](#changing-the-inference-model)
    * [Changing the Embedding Model](#changing-the-embedding-model)
* [On Premises Microservices](#on-premises-microservices)

<!-- /TOC -->

## Models from the API Catalog

### Changing the Inference Model

You can specify the model to use in the `APP_LLM_MODELNAME` environment variable when you start the Chain Server. The following sample command uses the Mistral AI Mixtral 8x7B Instruct model.

```console
APP_LLM_MODELNAME='mistralai/mixtral-8x7b-instruct-v0.1' docker compose up -d --build
```

You can determine the available model names using one of the following methods:

- Browse the models at <https://build.ngc.nvidia.com/explore/discover>.
  View the sample Python code and get the model name from the `model` argument to the `client.chat.completions.create` method.

- Install the [langchain-nvidia-ai-endpoints](https://pypi.org/project/langchain-nvidia-ai-endpoints/) Python package from PyPi.
  Use the `get_available_models()` method on an instance of a `ChatNVIDIA` object to list the models.
  Refer to the package web page for sample code to list the models.

### Changing the Embedding Model

You can specify the embedding model to use in the `APP_EMBEDDINGS_MODELNAME` environment variable when you start the Chain Server.
The following sample command uses the NVIDIA Embed QA 4 model.

```console
APP_EMBEDDINGS_MODELNAME='NV-Embed-QA' docker compose up -d --build
```

You can determine the available model names using one of the following methods:

- Browse the models at <https://build.ngc.nvidia.com/explore/retrieval>.
  View the sample Python code and get the model name from the `model` argument to the `client.embeddings.create` method.

- Install the [langchain-nvidia-ai-endpoints](https://pypi.org/project/langchain-nvidia-ai-endpoints/) Python package from PyPi.
  Use the `get_available_models()` method to on an instance of an `NVIDIAEmbeddings` object to list the models.
  Refer to the package web page for sample code to list the models.


## On Premises Microservices

You can specify the model for NVIDIA NIM containers to use in the `docker-compose-nim-ms.yaml` file.

Edit the `RAG/examples/local_deploy/docker-compose-nim-ms.yaml` file and specify an image name that includes the name of the model to deploy.

```yaml
services:
  nemollm-inference:
    container_name: nemollm-inference-microservice
    image: nvcr.io/nim/meta/<image>:<tag>
    ...

  nemollm-embedding:
    container_name: nemo-retriever-embedding-microservice
    image: nvcr.io/nim/<image>:<tag>


  ranking-ms:
    container_name: nemo-retriever-ranking-microservice
    image: nvcr.io/nim/<image>:<tag>
```

You can determine the available model names using one of the following methods:

- Run `ngc registry image list "nim/*"`.

- Browse the NGC catalog at <https://catalog.ngc.nvidia.com/containers>.
