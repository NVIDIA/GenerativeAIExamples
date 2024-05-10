<!--
  SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# Standalone Examples

This directory contains standalone examples that have a seperate and distinct end-to-end workflow than the examples deployed from the `deploy` directory of the repository.
These examples can have a unique user interface, deployment method, and tools, to showcase different use cases.


## RAG in 5 Minutes

This is a simple standalone implementation showing a minimal RAG pipeline that uses models available from [NVIDIA API Catalog](https://catalog.ngc.nvidia.com/ai-foundation-models).
The catalog enables you to experience state-of-the-art LLMs accelerated by NVIDIA.
Developers get free credits for 10K requests to any of the models.

The example uses an [integration package to LangChain](https://python.langchain.com/docs/integrations/providers/nvidia) to access the models.
NVIDIA engineers develop, test, and maintain the open source integration.
This example uses a simple [Streamlit](https://streamlit.io/) based user interface and has a one-file implementation.
Because the example uses the models from the NVIDIA API Catalog, you do not need a GPU to run the example.

### Steps

1. Create a python virtual environment and activate it:

   ```comsole
   python3 -m virtualenv genai
   source genai/bin/activate
   ```

1. From the root of this repository, `GenerativeAIExamples`, install the requirements:

   ```console
   pip install -r examples/5_mins_rag_no_gpu/requirements.txt
   ```

1. Add your NVIDIA API key as an environment variable:

   ```console
   export NVIDIA_API_KEY="nvapi-*"
   ```

   Refer to [Get an API Key for the Mixtral 8x7B Instruct API Endpoint](https://nvidia.github.io/GenerativeAIExamples/latest/api-catalog.html#get-an-api-key-for-the-mixtral-8x7b-instruct-api-endpoint)
   for information about how to get an NVIDIA API key.

1. Run the example using Streamlit:

   ```console
   streamlit run examples/5_mins_rag_no_gpu/main.py
   ```

1. Test the deployed example by going to `http://<host_ip>:8501` in a web browser.

   Click **Browse Files** and select your knowledge source.
   After selecting, click **Upload!** to complete the ingestion process.

You are all set now! Try out queries related to the knowledge base using text from the user interface.
