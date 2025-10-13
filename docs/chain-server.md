<!--
  SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Customizing the Chain Server

<!-- TOC -->

* [About the Chain Server](#about-the-chain-server)
* [Running the Chain Server Independently](#running-the-chain-server-independently)
* [Supporting Additional Document File Types](#supporting-additional-document-file-types)
* [Chain Server REST API Reference](#chain-server-rest-api-reference)

<!-- /TOC -->

## About the Chain Server

The chain server is implemented as a sample FastAPI-based server so that you can experience a Q&A chat bot.
The server wraps calls made to different components and orchestrates the entire flow for all the generative AI examples.


## Running the Chain Server Independently

To run the server for development purposes, run the following commands:

1. Build the container from source:

   ```console
   cd RAG/examples/advanced_rag/multi_turn_rag
   docker compose build chain-server
   ```

1. Start the container, which starts the server:

   ```console
   docker compose up -d chain-server
   ```

1. Open a browser to <http://host-ip:8081/docs> to view the REST API try the exposed endpoints.

## Supporting Additional Document File Types

Most of the examples support reading text files, Markdown files, and PDF files.
The [multimodal example](../RAG/examples/advanced_rag/multimodal_rag/) supports PDF, PowerPoint, and PNG files.

As a simple example, consider the following steps that show how to add support for ingesting Jupyter Notebooks with LangChain.

1. Optional: Edit the `RAG/src/chain-server/requirements.txt` file to add document loader packages.

   In this case, the basic LangChain example already includes the `langchain_community` package, so no edit is necessary.

1. Edit the `RAG/examples/basic_rag/langchain/chains.py` file and make the following edits.

   - Import the notebook document loader:

     ```python
     from langchain_community.document_loaders import NotebookLoader
     ```

   - Update the `ingest_docs` function and make changes like the following example:

     ```python
     if not filename.endswith((".txt", ".pdf", ".md", ".ipynb")):
         raise ValueError(f"{filename} is not a valid Text, PDF, Markdown, or Jupyter Notebook file")
     try:
         # Load raw documents from the directory
         _path = filepath
         if filename.endswith(".ipynb"):
             raw_documents = NotebookLoader(_path, include_outputs=True).load()
         else:
             raw_documents = UnstructuredFileLoader(_path).load()
     ```

1. Build and start the containers:

   ```console
   docker compose up -d --build
   ```

After the containers start, ingest a Juypter Notebook to the knowledge base and then query the LLM about the notebook.

## Chain Server REST API Reference

You can view the server REST API schema from the chain server by accessing <http://host-ip:8081/docs>.

Alternatively, you can view the OpenAPI specification from the [openapi_schema.json](api_reference/openapi_schema.json) file.
