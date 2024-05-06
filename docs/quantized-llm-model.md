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

# Quantized LLM Inference Model

```{contents}
---
depth: 2
local: true
backlinks: none
---
```


## Example Features

This example deploys a developer RAG pipeline for chat Q&A and serves inferencing with the NeMo Framework Inference container across multiple local GPUs with a
quantized version of the Llama 7B chat model.

This example uses a local host with an NVIDIA A100, H100, or L40S GPU.

```{list-table}
:header-rows: 1

* - Model
  - Embedding
  - Framework
  - Description
  - Multi-GPU
  - TRT-LLM
  - Model Location
  - Triton
  - Vector Database

* - llama-2-7b-chat
  - UAE-Large-V1
  - LlamaIndex
  - QA chatbot
  - YES
  - YES
  - Local Model
  - YES
  - Milvus
```

## Prerequisites

- Clone the Generative AI examples Git repository using Git LFS:

  ```console
  $ sudo apt -y install git-lfs
  $ git clone git@github.com:NVIDIA/GenerativeAIExamples.git
  $ cd GenerativeAIExamples/
  $ git lfs pull
  ```

- A host with one or more NVIDIA A100, H100, or L40S GPU.

- Verify NVIDIA GPU driver version 535 or later is installed and that the GPU is in compute mode:

  ```console
  $ nvidia-smi -q -d compute
  ```

  *Example Output*

  ```{code-block} output
  ---
  emphasize-lines: 4,9
  ---
  ==============NVSMI LOG==============

  Timestamp                                 : Sun Nov 26 21:17:25 2023
  Driver Version                            : 535.129.03
  CUDA Version                              : 12.2

  Attached GPUs                             : 2
  GPU 00000000:CA:00.0
      Compute Mode                          : Default

  GPU 00000000:FA:00.0
      Compute Mode                          : Default
  ```

  If the driver is not installed or below version 535, refer to the [*NVIDIA Driver Installation Quickstart Guide*](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html).

- Install Docker Engine and Docker Compose.
  Refer to the instructions for [Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

- Install the NVIDIA Container Toolkit.

  1. Refer to the [installation documentation](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html).

  1. When you configure the runtime, set the NVIDIA runtime as the default:

     ```console
     $ sudo nvidia-ctk runtime configure --runtime=docker --set-as-default
     ```

     If you did not set the runtime as the default, you can reconfigure the runtime by running the preceding command.

  1. Verify the NVIDIA container toolkit is installed and configured as the default container runtime:

     ```console
     $ cat /etc/docker/daemon.json
     ```

     *Example Output*

     ```json
     {
         "default-runtime": "nvidia",
         "runtimes": {
             "nvidia": {
                 "args": [],
                 "path": "nvidia-container-runtime"
             }
         }
     }
     ```

  1. Run the `nvidia-smi` command in a container to verify the configuration:

     ```console
     $ sudo docker run --rm --runtime=nvidia --gpus all ubuntu nvidia-smi -L
     ```

     *Example Output*

     ```output
     GPU 0: NVIDIA A100 80GB PCIe (UUID: GPU-d8ce95c1-12f7-3174-6395-e573163a2ace)
     GPU 1: NVIDIA A100 80GB PCIe (UUID: GPU-1d37ef30-0861-de64-a06d-73257e247a0d)
     ```

- Optional: Enable NVIDIA Riva automatic speech recognition (ASR) and text to speech (TTS).

  - To launch a Riva server locally, refer to the [Riva Quick Start Guide](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/quick-start-guide.html).

    - In the provided `config.sh` script, set `service_enabled_asr=true` and `service_enabled_tts=true`, and select the desired ASR and TTS languages by adding the appropriate language codes to `asr_language_code` and `tts_language_code`.

    - After the server is running, assign its IP address (or hostname) and port (50051 by default) to `RIVA_API_URI` in `deploy/compose/compose.env`.

  - Alternatively, you can use a hosted Riva API endpoint. You might need to obtain an API key and/or Function ID for access.

    In `deploy/compose/compose.env`, make the following assignments as necessary:

    ```bash
    export RIVA_API_URI="<riva-api-address/hostname>:<port>"
    export RIVA_API_KEY="<riva-api-key>"
    export RIVA_FUNCTION_ID="<riva-function-id>"
    ```

## Download the Llama 2 Model and Weights

1. Go to <https://huggingface.co/models>.

   - Locate the model to download, such as [Llama 2 7B chat HF](https://huggingface.co/meta-llama/Llama-2-7b-chat-hf).
   - Follow the information about accepting the license terms from Meta.
   - Log in or sign up for an account with Hugging Face.

1. After you are granted access, clone the repository by clicking the vertical ellipses button and selecting **Clone repository**.

   During the clone, you might be asked for your username and password multiple times.
   Provide the information until the clone is complete.


## Download TensorRT-LLM and Quantize the Model

The following steps summarize downloading the TensorRT-LLM repository,
building a container image, and quantizing the model.

1. Clone the NVIDIA TensorRT-LLM repository:

   ```console
   $ git clone https://github.com/NVIDIA/TensorRT-LLM.git
   $ cd TensorRT-LLM
   $ git checkout release/0.5.0
   $ git submodule update --init --recursive
   $ git lfs install
   $ git lfs pull
   ```

1. Build the TensorRT-LLM Docker image:

   ```console
   $ make -C docker release_build
   ```

   Building the image can require more than 30 minutes and requires approximately 30 GB.
   The image is named tensorrt_llm/release:latest.

1. Start the container.
   Ensure that the container has one volume mount to the model directory and one volume mount to the TensorRT-LLM repository:

   ```console
   $ docker run --rm -it --gpus all --ipc=host \
       -v <path-to-llama-2-7b-chat-model>:/model-store \
       -v $(pwd):/repo -w /repo \
       --ulimit memlock=-1 --shm-size=20g \
       tensorrt_llm/release:latest bash
   ```

1. Install NVIDIA AMMO Toolkit in the container:

   ```console
   # Obtain the cuda version from the system. Assuming nvcc is available in path.
   $ cuda_version=$(nvcc --version | grep 'release' | awk '{print $6}' | awk -F'[V.]' '{print $2$3}')
   # Obtain the python version from the system.
   $ python_version=$(python3 --version 2>&1 | awk '{print $2}' | awk -F. '{print $1$2}')
   # Download and install the AMMO package from the DevZone.
   $ wget https://developer.nvidia.com/downloads/assets/cuda/files/nvidia-ammo/nvidia_ammo-0.3.0.tar.gz
   $ tar -xzf nvidia_ammo-0.3.0.tar.gz
   $ pip install nvidia_ammo-0.3.0/nvidia_ammo-0.3.0+cu$cuda_version-cp$python_version-cp$python_version-linux_x86_64.whl
   # Install the additional requirements
   $ pip install -r examples/quantization/requirements.txt
   ```

1. Install version `0.25.0` of the accelerate Python package:

   ```console
   $ pip install accelerate==0.25.0
   ```

1. Run the quantization with the container:

   ```console
   $ python3 examples/llama/quantize.py --model_dir /model-store \
       --dtype float16 --qformat int4_awq \
       --export_path ./llama-2-7b-4bit-gs128-awq.pt --calib_size 32
   ```

   Quantization can require more than 15 minutes to complete.
   The sample command creates a `llama-2-7b-4bit-gs128-awq.pt`
   quantized checkpoint.

1. Copy the quantized checkpoint directory to the model directory:

   ```console
   $ cp <quantized-checkpoint>.pt <model-dir>
   ```

The preceding steps summarize several documents from the NVIDIA TensorRT-LLM GitHub repository.
Refer to the repository for more detail about the following topics:

- Building the TensorRT-LLM image, refer to the [installation.md](https://github.com/NVIDIA/TensorRT-LLM/blob/release/0.5.0/docs/source/installation.md) file in the release/0.5.0 branch.

- Installing NVIDIA AMMO Toolkit, refer to the [README](https://github.com/NVIDIA/TensorRT-LLM/blob/release/0.5.0/examples/quantization/README.md) file in the `examples/quantization` directory.

- Running the `quantize.py` command, refer to [AWQ](https://github.com/NVIDIA/TensorRT-LLM/blob/release/0.5.0/examples/llama/README.md#awq) in the `examples/llama` directory.


## Build and Start the Containers

1. In the Generative AI Examples repository, edit the `deploy/compose/compose.env` file.

   - Update the `MODEL_DIRECTORY` variable to identify the Llama 2 model directory that contains the quantized checkpoint.

   - Uncomment the `QUANTIZATION` variable:

     ```text
     export QUANTIZATION="int4_awq"
     ```

1. From the root of the repository, build the containers:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/rag-app-text-chatbot.yaml build
   ```

1. Start the containers:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/rag-app-text-chatbot.yaml up -d
   ```

   NVIDIA Triton Inference Server can require 5 minutes to start. The `-d` flag starts the services in the background.

   *Example Output*

   ```output
   ✔ Network nvidia-rag              Created
   ✔ Container llm-inference-server  Started
   ✔ Container notebook-server       Started
   ✔ Container chain-server          Started
   ✔ Container rag-playground        Started
   ```

1. Start the Milvus vector database:

   ```console
   $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/docker-compose-vectordb.yaml up -d milvus
   ```

   *Example Output*

   ```output
   ✔ Container milvus-minio       Started
   ✔ Container milvus-etcd        Started
   ✔ Container milvus-standalone  Started
   ```

1. Confirm the containers are running:

   ```console
   $ docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*

   ```output
   CONTAINER ID   NAMES                  STATUS
   256da0ecdb7b   rag-playground         Up 48 minutes
   2974aa4fb2ce   chain-server           Up 48 minutes
   4a8c4aebe4ad   notebook-server        Up 48 minutes
   5be2b57bb5c1   milvus-standalone      Up 48 minutes (healthy)
   ecf674c8139c   llm-inference-server   Up 48 minutes (healthy)
   a6609c22c171   milvus-minio           Up 48 minutes (healthy)
   b23c0858c4d4   milvus-etcd            Up 48 minutes (healthy)
   ```

## Stopping the Containers

- To uninstall, stop and remove the running containers from the root of the Generative AI Examples repository:

  ```console
  $ docker compose --env-file deploy/compose/compose.env -f deploy/compose/rag-app-text-chatbot.yaml down
  $ docker compose -f deploy/compose/docker-compose-vectordb.yaml down

  ```

## Next Steps

- Use the [](./using-sample-web-application.md).
- [](./vector-database.md)
- Run the sample Jupyter notebooks to learn about optional features.
