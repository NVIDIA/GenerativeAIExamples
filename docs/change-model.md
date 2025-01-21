<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Change the Inference or Embedding Model

You can change inference or embedding models by using the following procedures.

- [Change the Inference Model](#change-the-inference-model)
- [Change the Embedding Model](#change-the-embedding-model)
- [On Premises Microservices](#on-premises-microservices)



## Change the Inference Model

To change the inference model to a model from the API catalog, 
specify the model in the `APP_LLM_MODELNAME` environment variable when you start the RAG Server. 
The following example uses the `Mistral AI Mixtral 8x7B Instruct` model.

```console
APP_LLM_MODELNAME='mistralai/mixtral-8x7b-instruct-v0.1' docker compose -f deploy/compose/docker-compose.yaml up -d
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
APP_EMBEDDINGS_MODELNAME='NV-Embed-QA' docker compose -f deploy/compose/docker-compose.yaml up -d
```

To get a list of valid model names, use one of the following methods:

- Browse the models at <https://build.ngc.nvidia.com/explore/retrieval>.
  View the sample Python code and get the model name from the `model` argument to the `client.embeddings.create` method.

- Install the [langchain-nvidia-ai-endpoints](https://pypi.org/project/langchain-nvidia-ai-endpoints/) Python package from PyPi.
  Use the `get_available_models()` method to on an instance of an `NVIDIAEmbeddings` object to list the models.
  Refer to the package web page for sample code to list the models.



## On Premises Microservices

You can specify the model for NVIDIA NIM containers to use in the [nims.yaml](../deploy/compose/nims.yaml) file.

1. Edit the `deploy/nims.yaml` file and specify an image that includes the model to deploy.

   ```yaml
   services:
     nemollm-inference:
       container_name: nemollm-inference-microservice
       image: nvcr.io/nim/meta/<image>:<tag>
       ...

     embedding-ms:
       container_name: nemo-retriever-embedding-microservice
       image: nvcr.io/nim/<image>:<tag>


     ranking-ms:
       container_name: nemo-retriever-ranking-microservice
       image: nvcr.io/nim/<image>:<tag>
   ```

   To get a list of valid model names, use one of the following methods:

   - Run `ngc registry image list "nim/*"`.

   - Browse the NGC catalog at <https://catalog.ngc.nvidia.com/containers>.

1. Follow the steps specified [here](quickstart.md#start-the-containers-using-on-prem-models) to relaunch the containers with the updated models.
