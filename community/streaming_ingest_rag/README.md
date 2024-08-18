<!--
SPDX-FileCopyrightText: Copyright (c) 2023-2024, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# RAG Example: Streaming Data Ingest

## Table of Contents

1. [Background Information](#Background-Information)
    - [Purpose](#Purpose)
    - [Source Documents](#Source-Documents)
    - [Embedding Model](#Embedding-Model)
    - [Vector Database Service](#Vector-Database-Service)
2. [Implementation and Design Decisions](#Implementation-and-Design-Decisions)
3. [Getting Started](#Getting-Started)
    - [Prerequisites](#Prerequisites)
    - [Build the Containers](#Build-the-Containers)
    - [Start the Streaming Ingest Cluster](#Start-the-Streaming-Ingest-Cluster)
    - [Performance Instrumentation](#Performance-Instrumentation)
    - [Pipeline Customization](#Pipeline-Customization)
    - [Cluster Management](#Cluster-Management)
4. [Configuration Settings](#Configuration-Settings)
5. [Additional Options](#Additional-Options)
    - [Exporting and Deploying a Different Model from Huggingface](#Exporting-and-Deploying-a-Different-Model-from-Huggingface)

## Background Information

### Purpose

The primary objective of this example is to demonstrate the construction of a performance-oriented pipeline that performs the following tasks:

- Accepts a stream of heterogenous documents
- Divides the documents into smaller segments or chunks.
- Computes the embedding vector for each of these chunks.
- Uploads the text chunks along with their associated embeddings to a Vector Database (VDB).

This pipeline builds on the [Morpheus SDK](https://docs.nvidia.com/morpheus/index.html) to take advantage of end-to-end asynchronous processing. This pipeline showcases pipeline parallelism (including CPU and GPU-accelerated nodes), as well as, a mechanism to horizontally scale out data ingestion workers.

### Source Documents

- The pipeline is designed to process text-based input from various document types. Possible use cases could
  include structured documents like PDFs, dynamic sources such as web pages, and image-based documents through future
  Optical Character Recognition (OCR) integration.

- For this demonstration, the source documents are obtained from raw text published to Kakfa, URLs to be scraped from Kafka, and static list of RSS feeds combined with a web scraper, and sample PDF documents. The rationale
  behind this selection includes:
  - Emulating practical scenarios: Cybersecurity RSS feeds can serve as the foundation for a comprehensive
      knowledge database, such as for a security chatbot.
  - Minimizing external dependencies: Relying on RSS feeds and web scraping avoids the need for specialized datasets
      or API keys.
  - Representing heterogeneous data: Enterprises may have static and streaming data sources that flow through this data pipeline

### Embedding Model

- The pipeline can accommodate various embedding models that transform text into vectors of floating-point numbers.
  Several models from Huggingface, such as `paraphrase-multilingual-mpnet-base-v2`, `e5-large-v2`,
  and `all-mpnet-base-v2`, have been evaluated for compatibility. These models are not stored in this repository, but are downloaded from community sources at build time.

- For the purposes of this demonstration, the model `all-MiniLM-L6-v2` will be employed for its efficiency and compactness, characterized by a smaller embedding dimension.

### Vector Database Service

- The architecture is agnostic to the choice of Vector Database (VDB) for storing embeddings and their metadata. While
  the present implementation employs Milvus due to its GPU-accelerated indices, the design supports easy integration
  with other databases like Chroma or FAISS, should the need arise.

## Implementation and Design Decisions

### Implementation Details

[Original GitHub issue](https://github.com/nv-morpheus/Morpheus/issues/1298)

The pipeline is composed of three primary components:

1. **Document Source Handler**: This component is responsible for acquiring and preprocessing the text data. Given that
   we are using RSS feeds and a web scraper in this example, the handler's function is to fetch the latest updates from
   the feeds, perform preliminary data cleaning, and standardize the format for subsequent steps.

2. **Embedding Generator**: This is the heart of the pipeline, which takes the preprocessed text chunks and computes
   their embeddings. Leveraging the model `all-MiniLM-L6-v2` from Huggingface, the text data is transformed into
   embeddings with a dimension of 384.

3. **Vector Database Uploader**: Post embedding generation, this module takes the embeddings alongside their associated
   metadata and pushes them to a Vector Database (VDB). For our implementation, [Milvus](https://milvus.io/), a GPU-accelerated vector
   database, has been chosen.

### Rationale Behind Design Decisions

The selection of specific components and models was influenced by several factors:

- **Document Source Choice**: RSS feeds and web scraping offer a dynamic and continuously updating source of data. For
  the use-case of building a repository for a cybersecurity, real-time information fetching is a reasonable choice.

- **Model Selection for Embeddings**: `all-MiniLM-L6-v2` was chosen due to its efficiency in generating embeddings. Its
  smaller dimension ensures quick computations without compromising the quality of embeddings.

- **Vector Database**: For the purposes of this pipeline, [Milvus](https://milvus.io/) was chosen due to its popularity, ease of use, and
  availability.

## Getting Started

### Prerequisites

Before running the pipeline, we need to ensure that the following services are running:

- Operating System: Ubuntu 22.04
- Volta architecture GPU or better
- [NVIDIA driver 520.61.05 or higher](https://docs.nvidia.com/datacenter/tesla/tesla-installation-notes/index.html)
- [Docker](https://docs.docker.com/desktop/install/linux-install/)
- [Docker Compose](https://docs.docker.com/compose/install/standalone/) - 1.28.0 or higher of Docker Compose, and preferably v2. If you encounter an error similar to:

  ```none
  ERROR: The Compose file './docker-compose.yml' is invalid because:
  services.jupyter.deploy.resources.reservations value Additional properties are not allowed ('devices' was
  unexpected)
  ```

  This is most likely due to using an older version of the docker-compose command, instead re-run the build with docker compose. Refer to Migrate to Compose V2 for more information.
  
- [The NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
- [Git LFS](https://git-lfs.com/)

### Build the Containers

This step can take a while, as some containers are built from source.

#### Option 1: Build all Convience Script

Step 1: Run All Container Build Convienience Script

This is useful the first time you build out the infrastructure.

```bash
./docker/build_all.sh
```

#### Option 2: Build Components Individually

Step 1: Bring in [Morpheus SDK](https://docs.nvidia.com/morpheus/index.html) dependencies

```bash
./docker/build_morpheus.sh
```

Step 2: Bring in [Attu](https://milvus.io/docs/v2.1.x/attu_collection.md) dependencies

```bash
./docker/build_attu.sh
```

Step 3: Build and pull containers

```bash
docker-compose build attu streaming-ingest-dev ingest-worker producer
```

```bash
docker-compose pull etcd minio standalone zookeeper kafka init-kafka triton
```

### Start the Streaming Ingest Cluster

Step 1: Start containers

```bash
docker-compose up -d
```

Step 2: Stream some data into the Kafka cluster

Output from help utility:

```bash
./utils/produce_messages.sh: option requires an argument -- h

usage: ./utils/produce_messages.sh [-s SOURCE_TYPE] [-n N_MESSAGES]
options:
  -h             Show this help message and exit.
  -s SOURCE_TYPE Source type to generate (url, raw, or both)
  -n N_MESSAGES  Number of messages to publish to Kafka. (Default value: 1000)
```

Example usage, streaming 1000 url and raw data examples into Kafka:

```bash
./utils/produce_messages.sh -s both -n 1000
```

Step 3: Login to [Attu](https://milvus.io/docs/v2.1.x/attu_collection.md) for [Milvus](https://milvus.io/) administration and interaction with stored vectors:

`localhost:3000`

When logging in to [Attu](https://milvus.io/docs/v2.1.x/attu_collection.md), paste the url below as the "Milvus Address":

`http://milvus:19530`

### Performance Instrumentation

Step 1: View docker logs to inspect the performance of each `ingest-worker`

```bash
docker logs streaming_ingest_rag_ingest-worker_1 -f
```

Note - In this example, we are leveraging [Triton Inference Server's](https://developer.nvidia.com/triton-inference-server) support for [ONNX with TensorRT Optimization](https://github.com/triton-inference-server/server/blob/main/docs/user_guide/optimization.md#onnx-with-tensorrt-optimization-ort-trt). As a result, the first few inferences will be slow as the ONNX embedding model is converted to a [TensorRT](https://developer.nvidia.com/tensorrt) engine.

### Pipeline Customization

This pipeline builds on the Morpheus SDK to implement the streaming ingest pipeline. Customizations can be made within the `streaming-ingest-dev` container defined in the `docker-compose.yml` file. 

A Jupyer Notebook, including [NVdashboard](https://github.com/rapidsai/jupyterlab-nvdashboard) extensions to monitor resource utilziation, is made available at:

`http://localhost:8888`

To start, consider tuning values in the yaml file below:

`/workspace/examples/llm/vdb_upload/kafka_config.yaml` (the default example)

or

`/workspace/examples/llm/vdb_upload/vdb_config` (for additional heterogenous ingest workflows)

For more advanced customizations, following references will describe how to build custom Morpheus [Modules](https://docs.nvidia.com/morpheus/developer_guide/guides/7_python_modules.html) and [Stages](https://docs.nvidia.com/morpheus/developer_guide/architecture.html#stage-details) to further extend these examples to custom data types, transformations, etc.

- [Developer Guide](https://docs.nvidia.com/morpheus/developer_guide/guides/index.html)
- [Developer Guide Source Code](https://github.com/nv-morpheus/Morpheus/tree/branch-24.03/examples/developer_guide)

### Cluster Management

Step 1: (Optional) Scale up streaming ingest workers to increase hardware saturation and boost throughput

```bash
docker-compose up --scale ingest-worker=3 -d
```

Step 2: (Optional) Stop or tear down all or named running containers, note, Triton will need to recompile TRT engines after this step

```bash
docker-compose stop
```

```bash
docker-compose stop <containers>
```

```bash
docker-compose down
```

```bash
docker-compose down <containers>
```

## Configuration Settings

The configuration for this streaming ingest pipeline is expose by a YAML file at the following location:

`./morpheus_examples/streaming_ingest_rag/vdb_upload/kafka_config.yaml`

Users are empowered to tune configuration settings (e.g. new kafka topics for additional experiments). When
configuring the Morpheus Pipeline, especially for stages like the RSS source and the Vector Database Upload, it's
important to balance responsiveness and performance.

- **Kafka Source Stage**: The Kafka source stage is responsible for subscribing to a Kafka topic and yielding payloads links
  for processing. In the pure web scraping example, larger batch size can lead to decreased responsiveness, as the subsequent
  pure web scraping stage may take considerable time to retrieve and process all messages in the same batch. It is suggested
  to configure this stage with a smaller batch size, as this change has minimal impact on overall performance, while balancing
  responsiveness.

- **RSS Source Stage**: The RSS source stage is responsible for yielding webpage links for processing. A larger batch size
  at this stage can lead to decreased responsiveness, as the subsequent web scraper stage may take a considerable amount of
  time to retrieve and process all the items in each batch. To ensure a responsive experience for users, it's recommended
  to configure the RSS source stage with a relatively smaller batch size. This adjustment tends to have minimal impact on
  overall performance while significantly improving the time to process each batch of links.

- **Vector Database Upload Stage**: At the other end of the pipeline, the Vector Database Upload stage has its own
  considerations. This stage experiences a significant transaction overhead. To mitigate this, it is advisable to configure
  this stage with the largest batch size possible. This approach helps in efficiently managing transaction overheads and
  improves the throughput of the pipeline, especially when dealing with large volumes of data.

Balancing these configurations ensures that the pipeline runs efficiently, with optimized responsiveness at the RSS
source stage and improved throughput at the Vector Database Upload stage.

### YAML Configuration Examples

*Example: Defining sources via a config file*
Note: see `vdb_config.yaml` for a full configuration example.

`vdb_config.yaml`

```yaml
vdb_pipeline:
  sources:
    - type: filesystem
      name: "demo_filesystem_source"
      config:
        batch_size: 1024
        enable_monitor: False
        extractor_config:
          chunk_size: 512
          chunk_overlap: 50
          num_threads: 10 # Number of threads to use for file reads
        filenames:
          - "/path/to/data/*"
        watch: false
```

*Example: Defining a custom source via a config file*
Note: See `vdb_config.yaml` for a full configuration example.
Note: This example uses the same module and config as the filesystem source example above, but explicitly specifies the
module to load

`vdb_config.yaml`

```yaml
vdb_pipeline:
  sources:
    - type: custom
      name: "demo_custom_filesystem_source"
      module_id: "file_source_pipe"  # Required for custom source, defines the source module to load
      module_output_id: "output"  # Required for custom source, defines the output of the module to use
      namespace: "morpheus_examples_llm"  # Required for custom source, defines the namespace of the module to load
      config:
        batch_size: 1024
        extractor_config:
          chunk_size: 512
          num_threads: 10  # Number of threads to use for file reads
        config_name_mapping: "file_source_config"
        filenames:
          - "/path/to/data/*"
        watch: false
```

```bash
python examples/llm/main.py vdb_upload pipeline \
  --vdb_config_path "./vdb_config.yaml"
```

### Morpheus Pipeline Configuration Schema

The Morpheus Pipeline configuration allows for detailed specification of various pipeline stages, including source
definitions (like RSS feeds and filesystem paths), embedding configurations, and vector database settings.

### Sources Configuration

The `sources` section allows you to define multiple data sources of different types: RSS, filesystem, and custom.

#### Embeddings Configuration

- **isolate_embeddings**: Boolean to isolate embeddings.
- **model_kwargs**:
  - **force_convert_inputs**: Boolean to force the conversion of inputs.
  - **model_name**: Name of the model, e.g., `"all-MiniLM-L6-v2"`.
  - **server_url**: URL of the server, e.g., `"triton:8001"`.
  - **use_shared_memory**: Boolean to use shared memory.

#### Pipeline Configuration

- **edge_buffer_size**: Size of the edge buffer, e.g., `128`.
- **feature_length**: Length of the features, e.g., `512`.
- **max_batch_size**: Maximum size of the batch, e.g., `256`.
- **num_threads**: Number of threads, e.g., `10`.
- **pipeline_batch_size**: Size of the batch for the pipeline, e.g., `1024`.

#### Kafka Source Configuration - Web Scraper

- **type**: `'kafka'`
- **name**: Name of the Kafka source.
- **config**:
  - **stage_config**:
    - **enable_monitor**: Boolean to enable monitoring.
    - **namespace**: Name of namespace of stage modules.
    - **module_id**: Name of source module.
    - **module_output_id**: Name of output port of source module.
    - **transform_type**: Name of module to transform data.
  - **deserialize_config**:
    - output_batch_size: Number of elements per batch emitted from source stage.
  - **kafka_config**:
    - **max_batch_size**: Number of kafka messages per batch emitted from kafka source module.
    - **bootstrap_servers**: URL to a Kafka broker that can serve data.
    - **input_topic**: Name of topic containing messages to process.
    - **group_id**: Consumer group this worker/stage will belong to.
    - **poll_interval**: How often to poll Kafka for new data (pandas format).
    - **disable_commit**: Boolean to control possible arrival of duplicate messages.
    - **disable_pre_filtering**: Boolean controling skipping committing messages as they are pulled off the server.
    - **auto_offset_reset**: Decision to consume from the beginning of a topic partition or only new messages.
    - **stop_after**: Number of records before stopping ingestion of new messages.
    - **async_commits**: Boolean to decided to asynchronously acknowledge consuming Kafka messages.
  - **web_scraper_config**:
    - **chunk_overlap**: Overlap size for chunks.
    - **chunk_size**: Size of content chunks for processing.
    - **enable_cache**: Boolean to enable caching.
    - **cache_path**: Path to sqlite database for caching.
    - **enable_cache**: Directory container sqlite database for caching.
    - **link_column**: Column containing url to be scraped.
  - **vdb_config**:
    - **vdb_resource_name**: Name of collection in VectorDB.

#### Kafka Source Configuration - Raw Text

- **type**: `'kafka'`
- **name**: Name of the Kafka source.
- **config**:
  - **stage_config**:
    - **enable_monitor**: Boolean to enable monitoring.
    - **namespace**: Name of namespace of stage modules.
    - **module_id**: Name of source module.
    - **module_output_id**: Name of output port of source module.
    - **transform_type**: Name of module to transform data.
  - **deserialize_config**:
    - output_batch_size: Number of elements per batch emitted from source stage.
  - **kafka_config**:
    - **max_batch_size**: Number of kafka messages per batch emitted from kafka source module.
    - **bootstrap_servers**: URL to a Kafka broker that can serve data.
    - **input_topic**: Name of topic containing messages to process.
    - **group_id**: Consumer group this worker/stage will belong to.
    - **poll_interval**: How often to poll Kafka for new data (pandas format).
    - **disable_commit**: Boolean to control possible arrival of duplicate messages.
    - **disable_pre_filtering**: Boolean controling skipping committing messages as they are pulled off the server.
    - **auto_offset_reset**: Decision to consume from the beginning of a topic partition or only new messages.
    - **stop_after**: Number of records before stopping ingestion of new messages.
    - **async_commits**: Boolean to decided to asynchronously acknowledge consuming Kafka messages.
  - **raw_chunker_config**:
    - **chunk_overlap**: Overlap size for chunks.
    - **chunk_size**: Size of content chunks for processing.
    - **payload_column**: Column containing text to be processed.
  - **vdb_config**:
    - **vdb_resource_name**: Name of collection in VectorDB.  

#### RSS Source Configuration

- **type**: `'rss'`
- **name**: Name of the RSS source.
- **config**:
  - **batch_size**: Number of RSS feeds to process at a time.
  - **cache_dir**: Directory for caching.
  - **cooldown_interval_sec**: Cooldown interval in seconds.
  - **enable_cache**: Boolean to enable caching.
  - **enable_monitor**: Boolean to enable monitoring.
  - **feed_input**: List of RSS feed URLs.
  - **interval_sec**: Interval in seconds for fetching new feed items.
  - **request_timeout_sec**: Timeout in seconds for RSS feed requests.
  - **run_indefinitely**: Boolean to indicate continuous running.
  - **stop_after**: Stop after emitting a specific number of records.
  - **web_scraper_config**:
    - **chunk_overlap**: Overlap size for chunks.
    - **chunk_size**: Size of content chunks for processing.
    - **enable_cache**: Boolean to enable caching.

#### Filesystem Source Configuration

- **type**: `'filesystem'`
- **name**: Name of the filesystem source.
- **config**:
  - **batch_size**: Number of files to process at a time.
  - **chunk_overlap**: Overlap size for chunks.
  - **chunk_size**: Size of chunks for processing.
  - **converters_meta**: Metadata for converters.
    - **csv**:
      - **chunk_size**: Chunk size for CSV processing.
      - **text_column_names**: Column names to be used as text.
        - **column_name_0** Column name 0.
        - **column_name_1** Column name 1.
  - **enable_monitor**: Boolean to enable monitoring.
  - **extractor_config**:
    - **chunk_size**: Size of chunks for the extractor.
    - **num_threads**: Number of threads for file reads.
  - **filenames**: List of file paths to be processed.
  - **watch**: Boolean to watch for file changes.

#### Custom Source Configuration

- **type**: `'custom'`
- **name**: Name of the custom source.
- **config**:
  - **config_name_mapping**: Mapping name for file source config.
  - **module_id**: Identifier of the module to use.
  - **module_output_id**: Output identifier of the module.
  - **namespace**: Namespace of the module.
  - **other_config_parameter_1**: Other config parameter 1.
  - **other_config_parameter_2**: Other config parameter 2.

#### Tokenizer Configuration

- **model_kwargs**:
  - **add_special_tokens**: Boolean to add special tokens.
  - **column**: Column name, e.g., `"content"`.
  - **do_lower_case**: Boolean to convert to lowercase.
  - **truncation**: Boolean to truncate.
  - **vocab_hash_file**: Path to the vocabulary hash file.
- **model_name**: Name of the tokenizer model.

#### Vector Database (VDB) Configuration

- **batch_size**: Size of the embeddings to store in the vector.
- **resource_name**: Size of the embeddings to store in the vector.
- **embedding_size**: Size of the embeddings to store in the vector database.
- **recreate**: Boolean to recreate the resource if it exists.
- **resource_name**: Identifier for the resource in the vector database.
- **service**: Type of vector database service (e.g., `"milvus"`).
- **uri**: URI for connecting to the Vector Database server.

## Additional Options

Within one of Morpheus containers, the `vdb_upload` command has its own set of options and commands:

- `export-triton-model`
- `langchain`
- `pipeline`

### Exporting and Deploying a Different Model from Huggingface

If you're looking to incorporate a different embedding model from Huggingface into the pipeline, follow the steps below
using `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` as an example:

1. **Identify the Desired Model**:
    - Head over to the [Huggingface Model Hub](https://huggingface.co/models) and search for the model you want. For
      this example, we are looking at `e5-large-v2`.

2. **Run the Pipeline Call with the Chosen Model**:
    - Execute the following command with the model name you've identified:

      ```bash
      python examples/llm/main.py vdb_upload export-triton-model  \
         --model_name sentence-transformers/paraphrase-multilingual-mpnet-base-v2 \
         --triton_repo ./models/triton-model-repo \
         --output_model_name paraphrase-multilingual-mpnet-base-v2
      ```

3. **Handling Unauthorized Errors**:
    - Please ensure you provide the correct model name. A common pitfall is encountering an `unauthorized error`. If
      you see the following error:

      ```text
      requests.exceptions.HTTPError: 401 Client Error: Unauthorized for url:
      ```

      This typically means the model name you provided does not match the one available on Huggingface. Double-check
      the model name and try again.

4. **Confirm Successful Model Export**:
    - After running the command, ensure that the specified `--triton_repo` directory now contains the exported model in
      the correct format, ready for deployment.

    ```bash
    ls /workspace/models/triton-model-repo | grep paraphrase-multilingual-mpnet-base-v2

    sentence-transformers/paraphrase-multilingual-mpnet-base-v2
    ```

5. **Deploy the Model**:
    - Leverage the Triton REST API to load this model.

    ```bash
    curl -X POST triton:8000/v2/repository/models/paraphrase-multilingual-mpnet-base-v2/load
    ```

    - Leverage the Triton REST API validate the load of this model.You should see something similar to the following, indicating Triton has successfully loaded the model:

    ```bash
    curl -X POST triton:8000/v2/repository/index

    [{"name":"paraphrase-multilingual-mpnet-base-v2","version":"1","state":"READY"}]
    ```

6. **Update the Pipeline Call**:

    - Now that the model has been exported and deployed, we can update the yaml file to use the new model:

    ```bash
    python examples/llm/main.py vdb_upload pipeline \
      --vdb_config_path "examples/llm/vdb_upload/kafka_config.yaml"
    ```
