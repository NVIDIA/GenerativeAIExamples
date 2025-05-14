<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Enable query rewriting support
Query rewriting enables higher accuracy for multiturn queries by making an additional LLM call to decontextualize the incoming question, before sending it to the retrieval pipeline.

Once you have followed [steps in quick start guide](./quickstart.md#deploy-with-docker-compose) to launch the blueprint, to enable query rewriting support, developers have two options:

- [Enable query rewriting support](#enable-query-rewriting-support)
  - [Using on-prem model (Recommended)](#using-on-prem-model-recommended)
  - [Using cloud hosted model](#using-cloud-hosted-model)
  - [Using Helm Chart (on-prem only)](#using-helm-chart-on-prem-only)


## Using on-prem model (Recommended)
1. Deploy the `llama3.1-8b-instruct` model on-prem. You need a H100 or A100 GPU to deploy this model.
   ```bash
   export LLM_8B_MS_GPU_ID=<AVAILABLE_GPU_ID>
   USERID=$(id -u) docker compose -f deploy/compose/nims.yaml --profile llama-8b up -d
   ```

2. Make sure the nim-llm container is up and in healthy state before proceeding further
   ```bash
   docker ps --filter "name=nim-llm-llama-8b" --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*

   ```output
   NAMES                                   STATUS
   nim-llm-llama-8b                     Up 38 minutes (healthy)
   ```

3. Enable query rewriting
   Export the below environment variable and relaunch the rag-server container.
   ```bash
   export APP_QUERYREWRITER_SERVERURL="nim-llm-llama-8b:8000"
   export ENABLE_QUERYREWRITER="True"
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

   Alternatively, you can enable this at runtime during retrieval by setting `enable_query_rewriting: True` as part of the schema of POST /generate API, without relaunching the containers. Refer to the [retrieval notebook](../notebooks/retriever_api_usage.ipynb).


## Using cloud hosted model
1. Set the server url to empty string to point towards cloud hosted model
   ```bash
   export APP_QUERYREWRITER_SERVERURL=""
   ```

2. Relaunch the rag-server container by enabling query rewriter.
   ```bash
   export ENABLE_QUERYREWRITER="True"
   docker compose -f deploy/compose/docker-compose-rag-server.yaml up -d
   ```

[!TIP]: You can change the model name and model endpoint in case of an externally hosted LLM model by setting these two environment variables and restarting the rag services
```bash
export APP_QUERYREWRITER_SERVERURL="<llm_nim_http_endpoint_url>"
export APP_QUERYREWRITER_MODELNAME="<model_name>"
```


## Using Helm Chart (on-prem only)

This section describes how to enable Query Rewriting when you deploy by using Helm, using an on-prem deployment of the LLM model.

> [!NOTE]
> Only on-prem deployment of the LLM is supported. The model must be deployed separately using the NIM LLM Helm chart.

### 1. Deploy the Query Rewriter LLM using Helm

To deploy the `llama-3.1-8b-instruct` model in a separate namespace (`query-rewriter`), use the following procedure.


1. Export your [NGC API key](https://org.ngc.nvidia.com/setup/api-keys).

    ```bash
    export NGC_API_KEY=<your_ngc_api_key>
    ```
2. Create a namespace.

    ```bash
    kubectl create ns query-rewriter
    ```

3. Create required secrets.

    ```bash
    kubectl create secret -n query-rewriter docker-registry ngc-secret \
      --docker-server=nvcr.io \
      --docker-username='$oauthtoken' \
      --docker-password=$NGC_API_KEY

    kubectl create secret -n query-rewriter generic ngc-api \
      --from-literal=NGC_API_KEY=$NGC_API_KEY
    ```

4. Create a `custom_values.yaml` file with the following content.

    ```yaml
    service:
      name: "nim-llm"
    image:
      repository: nvcr.io/nim/meta/llama-3.1-8b-instruct
      pullPolicy: IfNotPresent
      tag: "1.3.0"
    resources:
      limits:
        nvidia.com/gpu: 1
      requests:
        nvidia.com/gpu: 1
    model:
      ngcAPISecret: ngc-api
      name: "meta/llama-3.1-8b-instruct"
    persistence:
      enabled: true
    imagePullSecrets:
      - name: ngc-secret
    ```


5. Install the Helm chart.

    ```bash
    helm upgrade --install nim-llm -n query-rewriter https://helm.ngc.nvidia.com/nim/charts/nim-llm-1.7.0.tgz \
      --username='$oauthtoken' \
      --password=$NGC_API_KEY \
      -f custom_values.yaml
    ```

### 2. Enable Query Rewriter in `rag-server` Helm deployment
1. Modify the [values.yaml](../deploy/helm/rag-server/values.yaml) file, in the `envVars` section, and set the following values.

    ```yaml
       envVars:
          ##===Query Rewriter Model specific configurations===
          APP_QUERYREWRITER_MODELNAME: "meta/llama-3.1-8b-instruct"
          APP_QUERYREWRITER_SERVERURL: "nim-llm.query-rewriter:8000"  # Fully qualified service name
          ENABLE_QUERYREWRITER: "True"
    ```

Follow the steps from [Quick Start Helm Deployment](./quickstart.md#deploy-with-helm-chart) and use the following command to deploy the chart.

```bash
helm install rag -n rag https://helm.ngc.nvidia.com/nvidia/blueprint/charts/nvidia-blueprint-rag-v2.1.0.tgz \
   --username '$oauthtoken' \
   --password "${NGC_API_KEY}" \
   --set imagePullSecret.password=$NGC_API_KEY \
   --set ngcApiSecret.password=$NGC_API_KEY \
   -f rag-server/values.yaml
```

> [!NOTE]
> This setup increases the total GPU requirement to 10xH100.

