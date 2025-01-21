<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Troubleshoot AI Blueprint: RAG

The following issues might arise when you work with the NVIDIA RAG Blueprint.


## Known issues

- The Blueprint responses can have significant latency when using [NVIDIA API Catalog cloud hosted models](quickstart.md#start-the-containers-using-cloud-hosted-models-no-gpu-by-default).
- Negative confidence scores for the retrieved document chunks is seen as part of the retriever API output for a given query.
- The accuracy of the pipeline is optimized for certain file types like `.pdf`, `.txt`, `.md`. The accuracy may be poor for other file types supported by unstructured.io like `.svg`, `.ppt`, `.png`.
- In some cases ingestion of the certain file types like `.pdf` with images, `.xlsb`, `.doc`, `.gif` etc.  will require the user to manually install some packages to get it functional.


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
