<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Common Prerequisites for RAG Examples
<!-- TOC -->

* [Clone the Repository and Install Software](#clone-the-repository-and-install-software)
* [Get an API Key for the Accessing Models on the API Catalog](#get-an-api-key-for-the-accessing-models-on-the-api-catalog)
* [Get an NVIDIA NGC API Key](#get-an-nvidia-ngc-api-key)

<!-- /TOC -->

## Clone the Repository and Install Software

- Clone the Generative AI examples Git repository using Git LFS:

  ```console
  sudo apt -y install git-lfs
  git clone git@github.com:NVIDIA/GenerativeAIExamples.git
  cd GenerativeAIExamples/
  git lfs pull
  ```

- Install Docker Engine and Docker Compose.
  Refer to the instructions for [Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

  Ensure the Docker Compose plugin version is 2.20 or higher.
  Run `docker compose version` to confirm.
  Refer to [Install the Compose plugin](https://docs.docker.com/compose/install/linux/)
  in the Docker documentation for more information.

- Optional: You can run some containers with GPU acceleration, such as Milvus and NVIDIA NIM for LLMs.
  To configure Docker for GPU-accelerated containers, [install](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html) the NVIDIA Container Toolkit.

## Get an API Key for the Accessing Models on the API Catalog

Perform the following steps if you do not already have an API key.
You can use different model API endpoints with the same API key.

1. Navigate to <https://build.nvidia.com/explore/discover>.

2. Find the **Llama 3 70B Instruct** card and click the card.

   ![Llama 3 70B Instruct model card](images/llama3-70b-instruct-model-card.png)

3. Click **Get API Key**.

   ![API section of the model page.](images/llama3-70b-instruct-get-api-key.png)

4. Click **Generate Key**.

   ![Generate key window.](images/api-catalog-generate-api-key.png)

5. Click **Copy Key** and then save the API key.
   The key begins with the letters nvapi-.

   ![Key Generated window.](images/key-generated.png)

## Get an NVIDIA NGC API Key

The NVIDIA NGC API Key is required to log in to the NVIDIA container registry, nvcr.io, and to pull secure base container images used in the RAG examples.

Refer to [Generating NGC API Keys](https://docs.nvidia.com/ngc/gpu-cloud/ngc-user-guide/index.html#generating-api-key)
in the _NVIDIA NGC User Guide_ for more information.

After you get your NGC API key, you can run `docker login nvcr.io` to confirm the key is valid.
