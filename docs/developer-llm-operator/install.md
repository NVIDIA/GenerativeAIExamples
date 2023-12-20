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

# Installing the Operator

## Prerequisites

- You have a machine with one or more NVIDIA A100 80 GB or NVIDIA H100 GPUs.
  If you have fewer than four GPUs, you can configure GPU time-slicing.
  Time-slicing oversubscribes the GPUs to simulate the four GPUs that are required,
  though at lower performance.

- You have access to Docker and Docker Compose to build container images.
  Refer to the [installation documentation](https://docs.docker.com/engine/install/ubuntu/)
  for Ubuntu from the Docker documentation.

- You have Kubernetes installed and running on the machine with Ubuntu 22.04 or 20.04.
  Refer to the [Kubernetes documentation](https://kubernetes.io/docs/setup/) or
  the [NVIDIA Cloud Native Stack repository](https://github.com/NVIDIA/cloud-native-stack/)
  for more information.

- You have access to Git and Git LFS to clone the repository to get access to the Dockerfile
  and software for container images.

- You downloaded a Llama2 chat model weights from Meta or HuggingFace.
  Get the 13 billion or 7 billion parameter model.

  Request access to the model from [Meta](https://ai.meta.com/resources/models-and-libraries/llama-downloads/)
  or refer to the [meta-llama/LLama-2-13b-chat-hf](https://huggingface.co/meta-llama/Llama-2-13b-chat-hf)
  page from HuggingFace.

  The directory with the model is shared as a host path volume mount with the Triton Inference Server pod.


## Install the NVIDIA GPU Operator

Use the NVIDIA GPU Operator to install, configure, and manage the NVIDIA GPU driver and
NVIDIA container runtime on the Kubernetes node.

1. Add the NVIDIA Helm repository:

   ```console
   $ helm repo add nvidia https://helm.ngc.nvidia.com/nvidia \
    && helm repo update
   ```

1. Install the Operator:

   ```console
   $ helm install --wait --generate-name \
    -n gpu-operator --create-namespace \
    nvidia/gpu-operator
   ```

1. Optional: Configure GPU time-slicing if you have fewer than four GPUs.

   - Create a file, `time-slicing-config-all.yaml`, with the following content:

     ```yaml
     apiVersion: v1
     kind: ConfigMap
     metadata:
       name: time-slicing-config-all
     data:
       any: |-
         version: v1
         flags:
           migStrategy: none
         sharing:
           timeSlicing:
             resources:
             - name: nvidia.com/gpu
               replicas: 4
     ```

     The sample configuration creates four *replicas* from each GPU on the node.

   - Add the config map to the Operator namespace:

     ```console
     $ kubectl create -n gpu-operator -f time-slicing-config-all.yaml
     ```

   - Configure the device plugin with the config map and set the default time-slicing configuration:

     ```console
     $ kubectl patch clusterpolicy/cluster-policy \
         -n gpu-operator --type merge \
         -p '{"spec": {"devicePlugin": {"config": {"name": "time-slicing-config-all", "default": "any"}}}}'
     ```

   - Verify that at least `4` GPUs are allocatable:

     ```console
     $ kubectl get nodes -l nvidia.com/gpu.present -o json |   jq '.items[0].status.allocatable |
         with_entries(select(.key | startswith("nvidia.com/"))) |
         with_entries(select(.value != "0"))'
     ```

     *Example Output*

     ```output
     {
       "nvidia.com/gpu": "4"
     }
     ```

For more information or to adjust the configuration, refer to
[Install NVIDIA GPU Operator](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/getting-started.html#install-nvidia-gpu-operator) and
[Time-Slicing GPUs in Kubernetes](https://docs.nvidia.com/datacenter/cloud-native/gpu-operator/latest/gpu-sharing.html)
in the NVIDIA GPU Operator documentation.

## Install the Developer LLM Operator

1. Get the Helm chart for the Operator:

   ```console
   $ helm fetch https://helm.ngc.nvidia.com/nvidia/cloud-native/charts/developer-llm-operator-0.1.0.tgz
   ```

1. Install the Operator:

   ```console
   $ helm install --generate-name ./developer-llm-operator-0.1.0.tgz \
       -n kube-trailblazer-system --create-namespace
   ```

1. Optional: Confirm the controller pod is running:

   ```console
   $ kubectl get pods -n kube-trailblazer-system
   ```

   *Example Output*

   ```output
   NAME                                                   READY   STATUS    RESTARTS      AGE
   kube-trailblazer-controller-manager-868bf8dc84-p2zgc   2/2     Running   2 (20h ago)   21h
   ```

## Build the Container Images

1. Clone the repository if you haven't already:

   ```console
   $ git lfs clone https://github.com/NVIDIA/GenerativeAIExamples.git
   ```

1. Build the container images:

   ```console
   $ cd GenerativeAIExamples/deploy/compose
   $ docker compose --env-file compose.env build
   ```

   Building the images requires several minutes.

1. Start a local registry, tag the images, and push the images to the registry.

   - Start a local registry:

     ```console
     $ docker run -d -p 5000:5000 --name registry registry:2.7
     ```

   - Tag and push the images that are not publicly available:

     ```console
     $ docker tag llm-inference-server localhost:5000/llm-inference-server
     $ docker push localhost:5000/llm-inference-server

     $ docker tag chain-server localhost:5000/chain-server
     $ docker push localhost:5000/chain-server

     $ docker tag llm-playground localhost:5000/llm-playground
     $ docker push localhost:5000/llm-playground

     $ docker tag notebook-server localhost:5000/notebook-server
     $ docker push localhost:5000/notebook-server
     ```

   - Optional: Confirm the images are available from the local registry:

     ```console
     $ curl -sSL "http://localhost:5000/v2/_catalog"
     ```

     *Example Output*

     ```json
     {"repositories":["chain-server","llm-inference-server","llm-playground","notebook-server"]}
     ```

## Create a RAG-LLM Pipeline

1. Create a file, such as `rag-llm-pipeline.yaml`, with contents like the following example:

   ```yaml
   apiVersion: package.nvidia.com/v1alpha1
   kind: HelmPipeline
   metadata:
     name: rag-llm-pipeline
   spec:
     pipeline:
     - repoEntry:
         url: "file:///helm-charts/staging"
       chartSpec:
         chart: "rag-llm-pipeline"
       chartValues:
         triton:
           modelDirectory: "<PATH>/llama2_13b_chat_hf_v1/"
   ```

   Modify the `modelDirectory` value to match the location and name of the model directory
   on the Kubernetes node.

1. Apply the manifest:

   ```console
   $ kubectl apply -n kube-trailblazer-system -f rag-llm-pipeline.yaml
   ```

   The Operator creates the `rag-llm-pipeline` namespace and creates deployments and services in the namespace.
   Downloading the container images and starting the pods can require a few minutes.

1. Optional: Monitor progress.

   - View the logs from the Operator controller pod:

     ```console
     $ kubectl logs -n kube-trailblazer-system \
        $(kubectl get pod -n kube-trailblazer-system -o=jsonpath='{.items[0].metadata.name}')
     ```

   - View the pods in the pipeline namespace:

     ```console
     $ kubectl get pods -n rag-llm-pipeline
     ```

     *Example Output*

     ```output
     NAME                                       READY   STATUS    RESTARTS   AGE
     jupyter-notebook-server-6d6b46578d-98xdq   1/1     Running   0          21h
     llm-playground-6fd649ff8f-r2hp6            1/1     Running   0          22h
     milvu-etcd-6559759884-9rvpz                1/1     Running   0          22h
     milvus-minio-6fc5b9bdd4-d7l4z              1/1     Running   0          22h
     milvus-standalone-9bfb5d974-tsjtp          1/1     Running   0          22h
     query-router-77499f5459-6jjr9              1/1     Running   0          22h
     triton-inference-server-79d5c499b-26nqq    0/1     Running   0          22h
     ```

1. View the services and node ports:

   ```console
   $ kubectl get svc -n rag-llm-pipeline
   ```

   *Example Output*

   ```output
   NAME                       TYPE        CLUSTER-IP       EXTERNAL-IP   PORT(S)          AGE
   frontend-service           NodePort    10.111.66.10     <none>        8090:30001/TCP   22h
   jupyter-notebook-service   NodePort    10.110.101.174   <none>        8888:30000/TCP   22h
   llm                        ClusterIP   10.107.213.112   <none>        8001/TCP         22h
   milvus                     ClusterIP   10.102.86.183    <none>        19530/TCP        22h
   milvus-etcd                ClusterIP   10.109.74.142    <none>        2379/TCP         22h
   milvus-minio               ClusterIP   10.103.238.28    <none>        9000/TCP         22h
   query                      ClusterIP   10.110.199.69    <none>        8081/TCP         22h
   ```

   The output shows that the chat web application, `frontend-service`, is mapped to port `30001`
   on the Kubernetes host through a node port.
   The output also shows the Jupyter Notebook server is mapped to port `30000` on the host.

## Access the Chat Web Application

- Open a browser and access `http://localhost:30001` or replace localhost with the IP address
  of the Kubernetes node.

  ![Chat web application](../rag/images/image4.jpg)

- Upload a PDF file as a knowledge base for retrieval.

  - Access `http://localhost:30001/converse` and click **Knowledge Base**.

  - Browse to a local file and upload it to the web application.

  - When you return to the **Converse** tab to ask a question, enable the **Use knowledge base** checkbox.

## Access the Jupyter Notebooks

- Open a browser and access `http://localhost:30000` or replace localhost with the IP address
  of the Kubernetes node.

  Browse and run the notebooks that are part of the container image.

