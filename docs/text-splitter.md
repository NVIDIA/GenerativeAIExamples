<!--
  SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Customize Your Text Splitter

The text splitter divides documents into smaller chunks for processing. 
The default text splitter is a `RecursiveCharacterTextSplitter` instance.



## Adjust Chunk Size and Overlap

You can control the chunk size and overlap by using environment variables in the `rag-server` section of your `docker-compose.yaml` file.

- **APP_TEXTSPLITTER_CHUNKSIZE** — Set the maximum number of tokens allowed in each chunk
- **APP_TEXTSPLITTER_CHUNKOVERLAP** — Define the number of tokens that overlap between consecutive chunks

```yaml
services:
  rag-server:
    environment:
      APP_TEXTSPLITTER_CHUNKSIZE: 256
      APP_TEXTSPLITTER_CHUNKOVERLAP: 128
```



## Use a Custom Text Splitter

Use the following procedure to implement a custom text splitter for your specific needs. 
Make sure the chunks created by the custom text splitter have a smaller number of tokens than the context length of the embedding model.

1. Install any dependencies for your text splitter in `requirements.txt` file.

1. Modify the `get_text_splitter` method in `src/utils.py` to incorporate your custom text splitter class. 

   ```python
   def get_text_splitter():

      from langchain.text_splitter import RecursiveCharacterTextSplitter

      return RecursiveCharacterTextSplitter(
          chunk_size=get_config().text_splitter.chunk_size - 2,
          chunk_overlap=get_config().text_splitter.chunk_overlap
      )
   ```

1. Restart the service by running the following code.
   
   ```console
   docker compose -f deploy/compose/docker-compose.yaml up -d --build
   ```
