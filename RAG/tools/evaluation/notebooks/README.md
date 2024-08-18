<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Running RAG Evaluation Notebooks
<!-- TOC -->

* [Prerequisites](#prerequisites)
* [Running the Notebooks](#running-the-notebooks)

<!-- /TOC -->

## Prerequisites

- You have Python 3 installed.
- Complete the [common prerequisites](../../docs/common-prerequisites.md).
- Start a RAG example to evaluate, such as `RAG/examples/basic_rag/lang_chain`.

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

1. Install the Python package dependencies in the virtual environment:

   ```console
   pip3 install -r requirements.txt
   ```

1. Start the JupyterLab server:

   ```console
   jupyter lab --allow-root --ip=0.0.0.0 --NotebookApp.token='' --port=8889
   ```

1. Open a web browser and access <http://localhost:8889/lab>.

   Browse to the `RAG/tools/evaluation/notebooks` directory to open and execute the cells of the notebooks.
