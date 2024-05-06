<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0

  Licensed under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License.
  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

  Unless required by applicable law or agreed to in writing, software
  distributed under the License is distributed on an "AS IS" BASIS,
  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
  See the License for the specific language governing permissions and
  limitations under the License.
-->

# Developing Simple Examples

## About the Purpose and Process

The purpose of the example is to show how to develop a RAG example.
The example uses models from the NVIDIA API Catalog.
Using models from the catalog simplifies the initial setup by avoiding the steps to download a model and run an inference server.
The endpoints from the catalog serve as both an embedding and an inference server.

The following pages show the sample code for gradually implementing the methods of a chain server that use LlamaIndex utility functions.

```{toctree}
:titlesonly:

boilerplate-api-catalog.md
ingest-api-catalog.md
documents-api-catalog.md
llm-api-catalog.md
rag-api-catalog.md
```

## Key Considerations for the Simple RAG

The simple example uses the build and configuration approach that NVIDIA provided examples use.
Reusing the build and configuration enables the sample to focus on the basics of developing the RAG code.

The key consideration for the RAG code is to implement three required methods and one optional method:

ingest_docs
: The chain server run this method when you upload documents to use as a knowledge base.

llm_chain
: The chain server runs this method when a query does not rely on retrieval.

rag_chain
: The chain server runs this method when you request to use the knowledge base and use retrieval to answer a query.

get_documents
: The chain server runs this method when you access the `/documents` endpoint with a GET request.

delete_documents
: The chain server runs this method when you access the `/documents` endpoint with a DELETE request.

document_search
: This is an optional method that enables you to perform the same document search that the `rag_chain` method runs.

## Prerequisites

The following prerequisites are common for using models from the NVIDIA API Catalog.
If you already performed these steps, you do not need to repeat them.

```{include} ./api-catalog.md
:start-after: start-prerequisites
:end-before: end-prerequisites
```

## Get an NVIDIA API Key

The following steps describe how to get an NVIDIA API key for the Mixtral 8x7B Instruct API Endpoint.
If you already performed these steps, you do not need to repeat them.

```{include} ./api-catalog.md
:start-after: api-key-start
:end-before: api-key-end
```

## Custom Requirements

The sample code for implementing the Chain Server is basic.
As you experiment and implement custom requirements, you might need to use additional Python packages.
You can install your Python dependencies by creating a `requirements.txt` file in your example directory.
When you build the Docker image, the build process automatically installs the packages from the requirements file.

You might find conflicts in the dependencies from the requirements file and the common dependencies used by the Chain Server.
In these cases, the custom requirements file is given a higher priority when Python resolves dependencies.
Your packages and versions can break some of the functionality of the utility methods in the chain server.

If your example uses any utility methods, check the chain server logs to troubleshoot dependency conflicts.
If any of the packages required by the utility methods causes an error, the error is logged by the chain server during initialization.
These errors do not stop the execution of the chain server.
However, if your example attempts to use a utility method that depends on a broken package, the chain server can produce unexpected behavior or crashes.
You must use dependencies that do not conflict with the chain server requirements, or do not rely on utility methods that are affected by the dependency conflict.
