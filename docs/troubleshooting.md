<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Troubleshoot NVIDIA RAG Blueprint

The following issues might arise when you work with the NVIDIA RAG Blueprint.


## Known issues

- The Blueprint responses can have significant latency when using [NVIDIA API Catalog cloud hosted models](quickstart.md#deploy-with-docker-compose).
- The accuracy of the pipeline is optimized for certain file types like `.pdf`, `.txt`, `.docx`. The accuracy may be poor for other file types supported by NvIngest, since image captioning is disabled by default.
- The `rag-playground` container needs to be rebuild if the `APP_LLM_MODELNAME`, `APP_EMBEDDINGS_MODELNAME` or `APP_RANKING_MODELNAME` environment variable values are changed.
- Optional features reflection, nemoguardrails and image captioning are not available in helm based deployment.
- The NeMo LLM microservice may take upto 5-6 mins to start for every deployment.


## pymilvus error: not allowed to retrieve raw data of field sparse
```
pymilvus.exceptions.MilvusException: <MilvusException: (code=65535, message=not allowed to retrieve raw data of field sparse)>
```
This happens when a collection created with vector search type `hybrid` is accessed using vector search type `dense` on retrieval side. Make sure both the search types are same in ingestor-server-compose and rag-server-compose file using `APP_VECTORSTORE_SEARCHTYPE` environment variable.

## DNS resolution failed for <service_name:port>
This category of errors in either `rag-server` or `ingestor-server` container logs indicates:
The server is trying to reach a on-prem deployed NIM at `service_name:port` but it is unreachable. You can ensure that the service is up using `docker ps`.

For example, the below logs in ingestor server container indicates `page-elements` service is unreachable at port `8001`:

```output
Original error: Error during NimClient inference [yolox-page-elements, grpc]: [StatusCode.UNAVAILABLE] DNS resolution failed for page-elements:8001: C-ares status is not ARES_SUCCESS qtype=AAAA name=page-elements is_balancer=0: Could not contact DNS servers
```

In case you were expecting to use cloud hosted model for this NIM, then ensure the corresponding environment variables were set in the same terminal from where you did docker compose up. Following the above example the environment variables which are expected to be set are:

```output
   export YOLOX_HTTP_ENDPOINT="https://ai.api.nvidia.com/v1/cv/nvidia/nemoretriever-page-elements-v2"
   export YOLOX_INFER_PROTOCOL="http"
```

## Device error

You might encounter an `unknown device` error during the [container build process for self-hosted NIMs](quickstart.md#start-the-containers-using-on-prem-models).
This error typically indicates that the container is attempting to access GPUs that are unavailable or non-existent on the host.
To resolve this issue, verify the GPU count specified in the [nims.yaml](../deploy/compose/nims.yaml) configuration file.

```bash
nvidia-container-cli: device error: {n}: unknown device: unknown
```

## Deploy.Resources.Reservations.devices error

You might encounter an error resembling the following during the [container build process for self-hosted NIMs](quickstart.md#start-the-containers-using-on-prem-models) process.
This is likely caused by an [outdated Docker Compose version](https://github.com/docker/compose/issues/11097).
To resolve this issue, upgrade Docker Compose to version `v2.29.0` or later.

```
1 error(s) decoding:

* error decoding 'Deploy.Resources.Reservations.devices[0]': invalid string value for 'count' (the only value allowed is 'all')
```


## Resetting the entire cache

To reset the entire cache, you can run the following command.
This deletes all the volumes associated with the containers, including the cache.

```bash
docker compose down -v
```


## External Vector databases

We've integrated VDB and embedding creation directly into the pipeline with caching included for expediency.
However, in a production environment, it's better to use a separately managed VDB service.

NVIDIA offers optimized models and tools like NIMs ([build.nvidia.com/explore/retrieval](https://build.nvidia.com/explore/retrieval))
and cuVS ([github.com/rapidsai/cuvs](https://github.com/rapidsai/cuvs)).


## Running out of credits

If you run out of credits for the NVIDIA API Catalog,
you will need to obtain more credits to continue using the API.
Please contact your NVIDIA representative to get more credits.


## Password Issue Fix

If you encounter any `password authentication failed` issues with the structured retriever container,
consider removing the volumes directory located at `deploy/compose/volumes`.
In this case, you may need to reprocess the data ingestion.

## Node exporter pod crash with prometheus stack enabled in helm deployment

If you experience issues with the `prometheus-node-exporter` pod crashing after enabling the `kube-prometheus-stack`, and you encounter an error message like:

```sh
msg="listen tcp 0.0.0.0:9100: bind: address already in use"
```

This error indicates that the port `9100` is already in use. To resolve this, you can update the port for `prometheus-node-exporter` in the `values.yaml` file.

Update the following in `values.yaml`:

```yaml
kube-prometheus-stack:
   # ... existing code ...
  prometheus-node-exporter:
    service:
      port: 9101 # Changed from 9100 to 9101
      targetPort: 9101  # Changed from 9100 to 9101
```