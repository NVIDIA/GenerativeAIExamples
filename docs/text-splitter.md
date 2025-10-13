<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Text Splitter Customizations
<!-- TOC -->

* [Updating model name](#updating-model-name)
* [Adjusting Chunk Size and Overlap](#adjusting-chunk-size-and-overlap)
* [Using a Custom Text Splitter](#using-a-custom-text-splitter)
* [Build and start the container](#build-and-start-the-container)

<!-- /TOC -->

## Updating the Model Name

The default text splitter is a `SentenceTransformersTokenTextSplitter` instance.
The text splitter uses a pre-trained model from Hugging Face to identify sentence boundaries.
You can change the model used by setting the `APP_TEXTSPLITTER_MODELNAME` environment variable in the `chain-server` service of your `docker-compose.yaml` file like the following example:

```yaml
services:
  chain-server:
    environment:
      APP_TEXTSPLITTER_MODELNAME: intfloat/e5-large-v2
```

## Adjusting Chunk Size and Overlap

The text splitter divides documents into smaller chunks for processing.
You can control the chunk size and overlap using environment variables in `chain-server` service of your `docker-compose.yaml` file:

- `APP_TEXTSPLITTER_CHUNKSIZE`: Sets the maximum number of tokens allowed in each chunk.
- `APP_TEXTSPLITTER_CHUNKOVERLAP`: Defines the number of tokens that overlap between consecutive chunks.

```yaml
services:
  chain-server:
    environment:
      APP_TEXTSPLITTER_CHUNKSIZE: 256
      APP_TEXTSPLITTER_CHUNKOVERLAP: 128
```

## Using a Custom Text Splitter

While the default text splitter works well, you can also implement a custom splitter for specific needs.

1. Modify the `get_text_splitter` method in `RAG/src/chain_server/utils.py`.
   Update it to incorporate your custom text splitter class.

   ```python
   def get_text_splitter():

      from langchain.text_splitter import RecursiveCharacterTextSplitter

      return RecursiveCharacterTextSplitter(
          chunk_size=get_config().text_splitter.chunk_size - 2,
          chunk_overlap=get_config().text_splitter.chunk_overlap
      )
   ```

   Make sure the chunks created by the function have a smaller number of tokens than the context length of the embedding model.

## Build and Start the Container

After you change the `get_text_splitter` function, build and start the container.

1. Navigate to the example directory.

   ```console
   cd RAG/examples/basic_rag/llamaindex
   ```

2. Build and deploy the microservice.

   ```console
   docker compose up -d --build
   ```
