<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Get Started With AI Blueprint: RAG

Use the following documentation to get started with the NVIDIA RAG Blueprint.

- [Obtain an API Key](#obtain-an-api-key)
- [Deploy With Docker Compose](#deploy-with-docker-compose)
- [Deploy With Helm Chart](#deploy-with-helm-chart)
- [Data Ingestion](#data-ingestion)


## Obtain an API Key

You need to obtain a single API key for accessing NIM services, to pull models on-prem, or to access models hosted in the NVIDIA API Catalog.
Use one of the following methods to generate an API key:

  - Sign in to the [NVIDIA Build](https://build.nvidia.com/explore/discover?signin=true) portal with your email.
    - Click any [model](https://build.nvidia.com/meta/llama-3_1-70b-instruct), then click **Get API Key**, and finally click **Generate Key**.

  - Sign in to the [NVIDIA NGC](https://ngc.nvidia.com/) portal with your email.
    - Select your organization from the dropdown menu after logging in. You must select an organization which has NVIDIA AI Enterprise (NVAIE) enabled.
    - Click your account in the top right, and then select **Setup**.
    - Click **Generate Personal Key**, and then click **+ Generate Personal Key** to create your API key.
      - Later, you use this key in the `NVIDIA_API_KEY` environment variables.

## Common Prerequisites
1. Export your NVIDIA API key as an environment variable. Ensure you followed steps [in previous section](#obtain-an-api-key) to get an API key.

   ```bash
   export NVIDIA_API_KEY="nvapi-..."
   ```


## Deploy With Docker Compose

Use these procedures to deploy with Docker Compose for a single node deployment. Alternatively, you can [Deploy With Helm Chart](#deploy-with-helm-chart) to deploy on a Kubernetes cluster.


### Prerequisites

1. Verify that you meet the [common prerequisites](#common-prerequisites).

1. Install Docker Engine. For more information, see [Ubuntu](https://docs.docker.com/engine/install/ubuntu/).

1. Install Docker Compose. For more information, see [install the Compose plugin](https://docs.docker.com/compose/install/linux/).

   a. Ensure the Docker Compose plugin version is 2.29.1 or later.

   b. After you get the Docker Compose plugin installed, run `docker compose version` to confirm.

1. To pull images required by the blueprint from NGC, you must first authenticate Docker with NGC. Use the NGC API Key you created in [Obtain an API Key](#obtain-an-api-key).

   ```bash
   export NVIDIA_API_KEY="nvapi-..."
   echo "${NVIDIA_API_KEY}" | docker login nvcr.io -u '$oauthtoken' --password-stdin
   ```

1. (Optional) You can run some containers with GPU acceleration, such as Milvus and NVIDIA NIMS deployed on-prem. To configure Docker for GPU-accelerated containers, [install](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html), the NVIDIA Container Toolkit, and ensure you meet [the hardware requirements](../README.md#hardware-requirements).

1. (Optional) You can enable GPU acceleration for the Milvus vector database container, if you have at least one L40/A100/H100 GPU available. For more information, see [Configuring Milvus with GPU Acceleration](./vector-database.md#configuring-milvus-with-gpu-acceleration).


### Start the Containers using cloud hosted models (no GPU by default)

Use the following procedure to start the containers using cloud-hosted models.

[!IMPORTANT]
To start the containers using on-premises models, use the procedure in the next section instead.

1. Export `NVIDIA_API_KEY` environment variable to pull the containers and models. Check the [Common Prerequisites](#common-prerequisites) section for the same.

1. Start the containers from the repo root. This pulls the prebuilt containers from NGC and deploys it on your system.

   ```bash
   docker compose -f deploy/compose/docker-compose.yaml up -d
   ```

   *Example Output*

   ```output
    ✔ Network nvidia-rag           Created
    ✔ Container rag-playground     Started
    ✔ Container milvus-minio       Started
    ✔ Container rag-server         Started
    ✔ Container milvus-etcd        Started
    ✔ Container milvus-standalone  Started
   ```

   [!TIP]
   You can add a `--build` argument in case you have made some code changes or have any requirement of re-building containers from source code:

   ```bash
   docker compose -f deploy/compose/docker-compose.yaml up -d --build
   ```

1. Confirm that the containers are running.

   ```bash
   docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Status}}"
   ```

   *Example Output*

   ```output
   CONTAINER ID   NAMES               STATUS
   39a8524829da   rag-playground      Up 2 minutes
   bfbd0193dbd2   rag-server          Up 2 minutes
   ec02ff3cc58b   milvus-standalone   Up 3 minutes
   6969cf5b4342   milvus-minio        Up 3 minutes (healthy)
   57a068d62fbb   milvus-etcd         Up 3 minutes (healthy)
   ```

1. Open a web browser and access `http://localhost:8090` to use the RAG Playground. You can use the upload tab to ingest files into the server or follow [the notebooks](../notebooks/) to understand the API usage.


### Start the Containers using on-prem models

Use the following procedure to start the containers using on-premises models.

[!IMPORTANT]
To start the containers using cloud-hosted models, see the procedure in the previous section instead.

1. Verify that you meet the [hardware requirements](../README.md#hardware-requirements).

1. Export `NVIDIA_API_KEY` environment variable to pull the containers and models. Check the [Common Prerequisites](#common-prerequisites) section for the same.

1. Create a directory to cache the models and export the path to the cache as an environment variable.

   ```bash
   mkdir -p ~/.cache/model-cache
   export MODEL_DIRECTORY=~/.cache/model-cache
   ```

1. Export the connection information for the inference and retriever services. Replace the host address of the below URLs with workstation IPs, if the NIMs are deployed in a different workstation or outside the `nvidia-rag` docker network on the same system.

   ```bash
   export APP_LLM_SERVERURL="nemollm-inference:8000"
   export APP_EMBEDDINGS_SERVERURL="embedding-ms:8000"
   export APP_RANKING_SERVERURL="ranking-ms:8000"
   ```

   [!TIP]: To change the GPUs used for NIM deployment, set the following environment variables before triggering the docker compose. You can check available GPU details on your system using `nvidia-smi`

   ```bash
   LLM_MS_GPU_ID: Update this to specify the LLM GPU IDs (e.g., 0,1,2,3).
   EMBEDDING_MS_GPU_ID: Change this to set the embedding GPU ID.
   RANKING_MS_GPU_ID: Modify this to adjust the reranking LLM GPU ID.
   RANKING_MS_GPU_ID: Modify this to adjust the reranking LLM GPU ID.
   VECTORSTORE_GPU_DEVICE_ID : Modify to adjust the Milvus vector database GPU ID. This is applicable only if GPU acceleration is enabled for milvus.
   ```

1. Start the containers. Ensure all containers go into `up` status before testing. The NIM containers may take around 10-15 mins to start at first launch. The models are downloaded and cached in the path specified by `MODEL_DIRECTORY`.

    ```bash
    USERID=$(id -u) docker compose -f deploy/compose/docker-compose.yaml --profile local-nim up -d
    ```

   *Example Output*

   ```output
   ✔ Container milvus-minio                           Running
   ✔ Container rag-server                             Running
   ✔ Container nemo-retriever-embedding-microservice  Running
   ✔ Container milvus-etcd                            Running
   ✔ Container nemollm-inference-microservice         Running
   ✔ Container nemollm-retriever-ranking-microservice Running
   ✔ Container rag-playground                         Running
   ✔ Container milvus-standalone                      Running
   ```

1. Open a web browser and access `http://localhost:8090` to use the RAG Playground. You can use the upload tab to ingest files into the server or follow [the notebooks](../notebooks/) to understand the API usage.



## Deploy With Helm Chart

Use these procedures to deploy with Helm Chart to deploy on a Kubernetes cluster. Alternatively, you can [Deploy With Docker Compose](#deploy-with-docker-compose) for a single node deployment.


### Prerequisites

- Verify that you meet the [common prerequisites](#common-prerequisites).

- Verify that you meet the [hardware requirements](../README.md#hardware-requirements).

- Verify that you have the NGC CLI available on your client machine. You can download the CLI from <https://ngc.nvidia.com/setup/installers/cli>.

- Verify that you have Kubernetes installed and running Ubuntu 22.04. For more information, see [Kubernetes documentation](https://kubernetes.io/docs/setup/) and [NVIDIA Cloud Native Stack repository](https://github.com/NVIDIA/cloud-native-stack/).

- Verify that you have a default storage class available in the cluster for PVC provisioning.
  One option is the local path provisioner by Rancher.
  Refer to the [installation](https://github.com/rancher/local-path-provisioner?tab=readme-ov-file#installation)
  section of the README in the GitHub repository.

  ```console
  kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/v0.0.26/deploy/local-path-storage.yaml
  kubectl get pods -n local-path-storage
  kubectl get storageclass
  ```

- If the local path storage class is not set as default, it can be made default by using the following command.

  ```
  kubectl patch storageclass local-path -p '{"metadata": {"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
  ```

- Verify that you have installed the NVIDIA GPU Operator following steps [here](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html).

### Helm deployment

Run the deploy.sh script

```bash
cd deploy/helm/
bash deploy.sh
```

If the deployment is successful, all the following pods should be in a ready and running state.

```bash
kubectl get pods -n rag

NAME                                                              READY   STATUS    RESTARTS      AGE
rag-etcd-0                                           1/1     Running   0             24m
rag-milvus-standalone-f9cd85fb7-h7g9v                1/1     Running   1 (24m ago)   24m
rag-minio-596fcd5b5f-6kg7p                           1/1     Running   0             24m
rag-nim-llm-0                                        1/1     Running   0             24m
rag-nvidia-nim-llama-32-nv-embedqa-1b-v2-6664fwfpf   1/1     Running   0             24m
rag-text-reranking-nim-6b749ccb74-pfbkz              1/1     Running   0             24m
rag-playground-0                                                  1/1     Running   0             24m
rag-server-0                                                      1/1     Running   0             24m
```


### Interacting with UI service

The UI service exposes a nodePort to access the UI.

List the services
```bash
kubectl get svc -n rag
```

The output of the command should list the following services.

```bash
NAME                             TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)              AGE
rag-etcd            ClusterIP      <none>        2379/TCP,2380/TCP    25m
rag-etcd-headless   ClusterIP      <none>        2379/TCP,2380/TCP    25m
rag-minio           ClusterIP      <none>        9000/TCP             25m
milvus                           ClusterIP      <none>        19530/TCP,9091/TCP   25m
nemo-embedding-ms                ClusterIP      <none>        8000/TCP             25m
nemo-ranking-ms                  ClusterIP      <none>        8000/TCP             25m
nim-llm                          ClusterIP      <none>        8000/TCP             25m
nim-llm-sts                      ClusterIP      <none>        8000/TCP             25m
rag-playground                   NodePort       <none>        8090:32661/TCP       25m
rag-server                       NodePort       <none>        8081:31783/TCP       25m
```

Look for the UI service `rag-playground`. The port type is listed as NodePort.
The NodePort is the one that follows the container port`8090:<nodePort>/TCP`

In this example case, the node port is listed as`32661`, hence the UI can be accessed at `http://0.0.0.0:32661/`


### Interacting with RAG server service

List the services

```bash
kubectl get svc -n rag
```

Look for the RAG server service `rag-server`, the port type is listed as NodePort.
The NodePort is the one that follows the container port`8081:<nodePort>/TCP`

In this example case, the node port is listed as`31783`, hence the RAG server can be accessed at `http://0.0.0.0:31783/docs#`


### Using notebooks with Helm

As an alternate to the UI, you can use the [notebooks](../notebooks/).

Point RAG_PORT to the rag-server node port. For more information, see [Interacting with RAG server service](#interacting-with-rag-server-service).

```bash
IPADDRESS = "localhost"

# Value from rag-server service NodePort
RAG_PORT = "<NodePort>"
# For our example case the value would be set to
RAG_PORT = "31783"
```


### Uninstalling the chart

Run the following command to uninstall the chart.

```bash
helm uninstall rag -n rag
```


### Clearing the pvcs

Run the following command to clear the pvcs.

```bash
kubectl delete pvc -n rag --all
```


## Data Ingestion

To highlight the ingestion pipeline, we will download the sample PDF files to the `data/dataset` folder, and then ingest them using the APIs.

[!IMPORTANT]
Before you can use this procedure, you must deploy the blueprint by using [Deploy With Docker Compose](#deploy-with-docker-compose) or [Deploy With Helm Chart](#deploy-with-helm-chart).


1. Download and install Git LFS by following the [installation instructions](https://git-lfs.com/).

1. Initialize Git LFS in your environment.

   ```bash
   git lfs install
   ```

1. Pull the dataset into the current repo.

   ```bash
   git-lfs pull
   ```

1. Install jupyterlab.

   ```bash
   pip install jupyterlab
   ```

1. Use this command to run Jupyter Lab so that you can execute this IPython notebook.

   ```bash
   jupyter lab --allow-root --ip=0.0.0.0 --NotebookApp.token='' --port=8889
   ```

1. Run the [ingestion_api_usage](../notebooks/ingestion_api_usage.ipynb) notebook.

Follow the cells in the notebook to ingest the PDF files from the data/dataset folder into the vector store.



## Next Steps

- [Change the Inference or Embedding Model](change-model.md)
- [Customize Your Vector Database](vector-database.md)
- [Customize Your Text Splitter](text-splitter.md)
- [Customize Prompts](prompt-customization.md)
- [Customize LLM Parameters at Runtime](llm-params.md)
- [Support Multi-Turn Conversations](multiturn.md)
- [Troubleshoot NVIDIA RAG Blueprint](troubleshooting.md)
