<!--
SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
All rights reserved.
SPDX-License-Identifier: Apache-2.0
-->


## PDFSpeak: Unlocking Multimodal PDF Intelligence through Speech 

PDFSpeak is an innovative approach to interacting with complex PDF documents using NVIDIA's cutting-edge AI technologies through speech, vision, and text.

### Table of Contents
1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Setting up PDFSpeak](#Setting-up-PDFSpeak)

## Introduction

### What PDFSpeak Is ✔️

It is a cohesive solution enabling you to talk to your pdf with a familiar chat UI of the webapp which connects to which you can upload your pdf. You can then ask your queries out load, which are converted to prompts by [RIVA ASR pipeline](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/asr/asr-overview.html).; a GPU-accelerated compute pipeline, with optimized performance and accuracy. The prompt, along with the the pdf, reaches NV-Ingest. 
NVIDIA-Ingest is a scalable, performance-oriented document content and metadata extraction microservice. It enables parallelization of the process of splitting documents into pages where contents are classified (as tables, charts, images, text), extracted into discrete content, and further contextualized via optical character recognition (OCR) into a well defined JSON schema. From there, NVIDIA Ingest can optionally manage computation of embeddings for the extracted content, and also optionally manage storing into a vector database [Milvus](https://milvus.io/).
The textual response from NV-Ingest then goes to [RIVA TTS pipeline](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/asr/asr-overview.html); a two-stage pipeline,  generateing a mel-spectrogram using the first model, and then generating speech using the second model. This speech response is further processed by the webapp to be played back to you.

## Prerequisites

### Hardware

| GPU | Family | Memory | # of GPUs (min.) |
| ------ | ------ | ------ | ------ |
| A100 | SXM or PCIe | 80GB | 4 |

### Software

- Linux operating systems (Ubuntu 22.04 or later recommended)
- [Docker](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- [CUDA Toolkit](https://developer.nvidia.com/cuda-downloads) (NVIDIA Driver >= `550`, CUDA >= `12.6`)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)

> NOTE: The frontend-server container which leverages the `webapp/src/main/ui/web/pdf-speak/server` directory as the source is essentially a proxy server that ensures seamless SSL-secure streaming of audio from HTTPS frontend to the RIVA ASR container via gRPC. For more information on how this proxy was built, please refer to the published [RIVA Contact](https://github.com/nvidia-riva/sample-apps/tree/main/riva-contact) example project. 

## Setting up PDFSpeak
1. Git clone `nv-ingest` into the repository, and use commit `d0a3008c`:
- `git clone https://github.com/NVIDIA/nv-ingest.git`
- `cd nv-ingest`
- `git checkout d0a3008c`
- `cd ../`
2. Make sure you are logged in to NGC via docker. Follow directions [here](https://docs.nvidia.com/launchpad/ai/base-command-coe/latest/bc-coe-docker-basics-step-02.html#logging-in-to-ngc-on-a-workstation).
3. Add your NV_API_KEY, NVIDIA_API_KEY, OPENAI_API_KEY environment variables to access NVIDIA NIM endpoints (all set to the same key) to the `.env` file. Also add your `NGC_API_KEY` to this file.
> [Note]: To generate, `NGC_API_KEY`, follow [Generate API keys](docs/docs/user-guide/developer-guide/ngc-api-key.md).

> If you require early access (EA), your `NGC_API_KEY` key must be created as a member of `nemo-microservice / ea-participants` which you may join by applying for early access [here](https://developer.nvidia.com/nemo-microservices-early-access/join). When approved, switch your profile to this org / team, then the key you generate will have access to the resources outlined below.

4. Start the containers:

`docker compose up`

5. Check if all components of NV-Ingest is up and healthy

`curl http://172.17.0.1:7670/v1/health/ready` 

5. Check if all containers are up with `docker ps`

6. To access the UI. Go to https://localhost:3002/ . Click on Advanced and Proceed (Unsafe) option [This warning can be safely ignored as it shows up if a self signed certificate is used on X-platform CORS]. JupyterLab with exercises will be available on http://localhost:8888/.