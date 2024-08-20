<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Software Component Configuration
<!-- TOC -->

* [Configuration with Environment Variables](#configuration-with-environment-variables)
* [Milvus](#milvus)
* [Pgvector](#pgvector)
* [Chain Server](#chain-server)
* [RAG Playground](#rag-playground)

<!-- /TOC -->

## Configuration with Environment Variables

The following sections identify the environment variables that are used in the `docker-compose.yaml` files.

## Milvus

Milvus is the default vector database server.
You can configure Milvus using the following environment variable:

<dl>
<dt>DOCKER_VOLUME_DIRECTORY</dt>
<dd>Specifies the location of the volume mount on the host for the vector database files.
The default value is `./volumes/milvus` in the current working directory.
</dd>
</dl>

## Pgvector

Pgvector is an alternative vector database server.
You can configure pgvector using the following environment variables:

<dl>
<dt>DOCKER_VOLUME_DIRECTORY</dt>
<dd>Specifies the location of the volume mount on the host for the vector database files.
The default value is `./volumes/data` in the current working directory.
</dd>
<dt>POSTGRES_PASSWORD</dt>
<dd>Specifies the password for authenticating to pgvector.
The default value is `password`.
</dd>
<dt>POSTGRES_USER</dt>
<dd>Specifies the user name for authenticating to pgvector.
The default value is `postgres`.
</dd>
<dt>POSTGRES_DB</dt>
<dd>Specifies the name of the database instance.
The default value is `api`.
</dd>
</dl>


## Chain Server

The chain server is the core component that interacts with the LLM Inference Server and the Milvus server to obtain responses.
You can configure the server using the following environment variable:

<dl>
<dt>APP_VECTORSTORE_URL</dt>
<dd>Specifies the URL of the vector database server.</dd>
<dt>APP_VECTORSTORE_NAME</dt>
<dd>Specifies the vendor name of the vector database. Values are `milvus` or `pgvector`.</dd>
<dt>COLLECTION_NAME</dt>
<dd>Specifies the example-specific collection in the vector database.</dd>
<dt>APP_LLM_SERVERURL</dt>
<dd>Specifies the URL of NVIDIA NIM for LLMs.</dd>
<dt>APP_LLM_MODELNAME</dt>
<dd>The model name used by NIM for LLMs.</dd>
<dt>APP_LLM_MODELENGINE</dt>
<dd>Specifies the backend name hosting the model.
The only supported value is `nvidia-ai-endpoints` to use models hosted using NIM for LLMs in cloud based API Catalog or locally.
</dd>
<dt>APP_RETRIEVER_TOPK</dt>
<dd>Number of relevant results to retrieve. The default value is `4`.</dd>
<dt>APP_RETRIEVER_SCORETHRESHOLD</dt>
<dd>The minimum confidence score for the retrieved values to be considered. The default value is `0.25`.</dd>
<dt>LOGLEVEL</dt>
<dd>Set the logging verbosity level for the logs printed by container. Chain server uses the standard python logging module. Possible values are NOTSET, DEBUG, INFO, WARN, ERROR, CRITICAL.</dd>
</dl>

## RAG Playground

The RAG playground component is the user interface web application that interacts with the chain server to retrieve responses and provide a user interface to upload documents.
You can configure the server using the following environment variables:

<dl>
<dt>APP_SERVERURL</dt>
<dd>Specifies the URL for the chain server.</dd>
<dt>APP_SERVERPORT</dt>
<dd>Specifies the network port number for the chain server.</dd>
<dt>APP_MODELNAME</dt>
<dd>Specifies the name of the large language model used in the deployment.
This information is for display purposes only and does not affect the inference process.</dd>
<dt>RIVA_API_URI</dt>
<dd>Specifies the host name and port of the NVIDIA Riva server.
This field is optional and provides automatic speech recognition (ASR) and text-to-speech (TTS) functionality.</dd>
<dt>RIVA_API_KEY</dt>
<dd>Specifies a key to access the Riva API.
This field is optional.</dd>
<dt>RIVA_FUNCTION_ID</dt>
<dd>Specifies the function ID to access the Riva API.
This field is optional.</dd>
<dt>TTS_SAMPLE_RATE</dt>
<dd>Specifies the sample rate in hertz (Hz).
The default value is `48000`.</dd>
</dl>
