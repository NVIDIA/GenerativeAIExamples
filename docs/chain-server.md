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

# Chain Server

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## About the Chain Server

The chain server is implemented as a sample FastAPI-based server so that you can experience a Q&A chat bot.
The server wraps calls made to different components and orchestrates the entire flow for all the generative AI examples.


## Running the Chain Server Independently

To run the server for development purposes, run the following commands:

- Build the container from source:

  ```console
  $ source deploy/compose/compose.env
  $ docker compose -f deploy/compose/rag-app-text-chatbot.yaml build chain-server
  ```

- Start the container, which starts the server:

  ```console
  $ source deploy/compose/compose.env
  $ docker compose -f deploy/compose/rag-app-text-chatbot.yaml up chain-server
  ```

- Open the swagger URL at ``http://host-ip:8081`` to try out the exposed endpoints.

## Chain Server REST API Reference

You can view the server REST API schema from the chain server by accessing <http://host-ip:8081/docs>.

Alternatively, you can view the same documentation in the following section.

```{eval-rst}
.. inline-swagger::
   :id: chain-server-api
```