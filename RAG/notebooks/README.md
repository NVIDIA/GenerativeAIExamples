<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Running RAG Example Notebooks
<!-- TOC -->

* [About the Notebooks](#about-the-notebooks)
* [Prerequisites](#prerequisites)
* [Running the Notebooks](#running-the-notebooks)

<!-- /TOC -->

## About the Notebooks

The notebooks show how to use the `langchain-nvidia-ai-endpoints` and `llama-index-embeddings-nvidia` Python packages.
These packages provide the basics for developing a RAG application and performing inference either from NVIDIA API Catalog endpoints or a local deployment of NVIDIA microservices.

## Prerequisites

- You have Python 3 installed.
- Complete the [common prerequisites](../../docs/common-prerequisites.md).
   
## Running the Notebooks

1. Export your NVIDIA API key as an environment variable:

   ```text
   export NVIDIA_API_KEY="nvapi-<...>"
   ```

1. Create a virtual environment:

   ```console
   python3 -m venv .venv
   source .venv/bin/activate
   ```

1. Install JupyterLab in the virtual environment:

   ```console
   pip3 install jupyterlab
   ```

1. Start the JupyterLab server:

   ```console
   jupyter lab --allow-root --ip=0.0.0.0 --NotebookApp.token='' --port=8889
   ```

1. Open a web browser and access <http://localhost:8889/lab>.

   Browse to the `RAG/notebooks` directory to open an execute the cells of the notebooks.
