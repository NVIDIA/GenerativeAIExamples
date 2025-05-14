<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Enable image captioning support
Enabling image captioning will yield higher accuracy for querstions relevant to images in the ingested documents at the cost of higher ingestion latency.
Once you have followed [steps in quick start guide](./quickstart.md#deploy-with-docker-compose) to launch the blueprint, to enable image captioning support, developers have two options:
- [Enable image captioning support](#enable-image-captioning-support)
  - [Using on-prem VLM model (Recommended)](#using-on-prem-vlm-model-recommended)
  - [Using cloud hosted VLM model](#using-cloud-hosted-vlm-model)
  - [Using Helm chart deployment (On-prem only)](#using-helm-chart-deployment-on-prem-only)

## Using on-prem VLM model (Recommended)
1. Deploy the VLM model on-prem. You need a H100 or A100 GPU to deploy this model.
   ```bash
   export VLM_MS_GPU_ID=<AVAILABLE_GPU_ID>
   USERID=$(id -u) docker compose -f deploy/compose/nims.yaml --profile vlm up -d
   ```

2. Make sure the vlm container is up and running
   ```bash
   docker ps --filter "name=nemo-vlm-microservice" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*

   ```output
   NAMES                                   STATUS
   nemo-vlm-microservice                   Up 5 minutes (healthy)
   ```

3. Enable image captioning
   Export the below environment variable and relaunch the ingestor-server container.
   ```bash
   export APP_NVINGEST_EXTRACTIMAGES="True"
   export VLM_CAPTION_ENDPOINT="http://vlm-ms:8000/v1/chat/completions"
   docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
   ```

   Alternatively, you can enable this at runtime during ingestion by setting `extract_images: True` as part of the schema of POST /documents API, without relaunching the containers. Refer to the [ingestion notebook](../notebooks/ingestion_api_usage.ipynb).

## Using cloud hosted VLM model
1. Set caption endpoint to API catalog
   ```bash
   export VLM_CAPTION_ENDPOINT="https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions"
   ```

2. Enable image captioning
   Export the below environment variable and relaunch the ingestor-server container.
   ```bash
   export APP_NVINGEST_EXTRACTIMAGES="True"
   docker compose -f deploy/compose/docker-compose-ingestor-server.yaml up -d
   ```

[!TIP]: You can change the model name and model endpoint in case of an externally hosted VLM model by setting these two environment variables and restarting the ingestion services
```bash
export VLM_CAPTION_ENDPOINT="<vlm_nim_http_endpoint_url>"
export VLM_CAPTION_MODEL_NAME="<model_name>"
```

## Using Helm chart deployment (On-prem only)

To enable image captioning in Helm-based deployments by using an on-prem VLM model, use the following procedure.


1. In the `values.yaml` file, in the `ingestor-server.envVars` section, set the following environment variables.

   ```yaml
   APP_NVINGEST_EXTRACTIMAGES: "True"
   APP_NVINGEST_CAPTIONENDPOINTURL: "http://nim-vlm-image-captioning:8000/v1/chat/completions"
   APP_NVINGEST_CAPTIONMODELNAME: "meta/llama-3.2-11b-vision-instruct"
   ```

2. Enable the VLM image captioning model in your `values.yaml` file.

   ```yaml
   nv-ingest:
     nim-vlm-image-captioning:
       deployed: true
   ```

3. Apply the updated Helm chart by running the following code.

   ```bash
   helm upgrade --install rag -n rag https://helm.ngc.nvidia.com/nvidia/blueprint/charts/nvidia-blueprint-rag-v2.1.0.tgz \
   --username '$oauthtoken' \
   --password "${NGC_API_KEY}" \
   --set imagePullSecret.password=$NGC_API_KEY \
   --set ngcApiSecret.password=$NGC_API_KEY \
   -f rag-server/values.yaml
   ```

> [!Note]
> Enabling the on-prem VLM model increases the total GPU requirement to 10xH100 GPUs.