<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Change the Inference or Embedding Model

You can change inference or embedding models by using the following procedures.

- [Change the Inference or Embedding Model](#change-the-inference-or-embedding-model)
  - [Change the Inference Model](#change-the-inference-model)
  - [Change the Embedding Model to a Model from the API Catalog](#change-the-embedding-model-to-a-model-from-the-api-catalog)
  - [On Premises Microservices](#on-premises-microservices)



## Change the Inference Model

To change the inference model to a model from the API catalog,
specify the model in the `APP_LLM_MODELNAME` environment variable when you start the RAG Server.
The following example uses the `Mistral AI Mixtral 8x7B Instruct` model.

```console
APP_LLM_MODELNAME='mistralai/mixtral-8x7b-instruct-v0.1' docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d --build
```

To get a list of valid model names, use one of the following methods:

- Browse the models at <https://build.ngc.nvidia.com/explore/discover>.
  View the sample Python code and get the model name from the `model` argument to the `client.chat.completions.create` method.

- Install the [langchain-nvidia-ai-endpoints](https://pypi.org/project/langchain-nvidia-ai-endpoints/) Python package from PyPi.
  Use the `get_available_models()` method on an instance of a `ChatNVIDIA` object to list the models.
  Refer to the package web page for sample code to list the models.



## Change the Embedding Model to a Model from the API Catalog

To change the embedding model to a model from the API catalog,
specify the model in the `APP_EMBEDDINGS_MODELNAME` environment variable when you start the RAG server.
The following example uses the `NVIDIA Embed QA 4` model.

```console
APP_EMBEDDINGS_MODELNAME='NV-Embed-QA' docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
APP_EMBEDDINGS_MODELNAME='NV-Embed-QA' docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d --build
```

As an alternative you can also specify the model names at runtime using `/generate` API call. Please refer to the `Generate Answer Endpoint` and `Document Search Endpoint` payload schema in [this](../notebooks/retriever_api_usage.ipynb) notebook.

To get a list of valid model names, use one of the following methods:

- Browse the models at <https://build.ngc.nvidia.com/explore/retrieval>.
  View the sample Python code and get the model name from the `model` argument to the `client.embeddings.create` method.

- Install the [langchain-nvidia-ai-endpoints](https://pypi.org/project/langchain-nvidia-ai-endpoints/) Python package from PyPi.
  Use the `get_available_models()` method to on an instance of an `NVIDIAEmbeddings` object to list the models.
  Refer to the package web page for sample code to list the models.

[!TIP] Always use same embedding model or model having same tokinizers for both ingestion and retrieval to yield good accuracy.


## On Premises Microservices

You can specify the model for NVIDIA NIM containers to use in the [nims.yaml](../deploy/compose/nims.yaml) file.

1. Edit the `deploy/nims.yaml` file and specify an image that includes the model to deploy.

   ```yaml
   services:
     nim-llm:
       container_name: nim-llm-ms
       image: nvcr.io/nim/meta/<image>:<tag>
       ...

     nemoretriever-embedding-ms:
       container_name: nemoretriever-embedding-ms
       image: nvcr.io/nim/<image>:<tag>


     nemoretriever-ranking-ms:
       container_name: nemoretriever-ranking-ms
       image: nvcr.io/nim/<image>:<tag>
   ```

   To get a list of valid model names, use one of the following methods:

   - Run `ngc registry image list "nim/*"`.

   - Browse the NGC catalog at <https://catalog.ngc.nvidia.com/containers>.

2. Follow the steps specified [here](quickstart.md#start-using-on-prem-models) to relaunch the containers with the updated models. Make sure to specify the correct model names using appropriate environment variables.
