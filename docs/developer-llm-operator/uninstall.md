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

# Uninstalling the Operator

To uninstall the Operator, perform the following steps:

1. Delete the RAG pipeline:

   ```console
   $ kubectl delete helmpipeline -n kube-trailblazer-system rag-llm-pipeline
   ```

   *Example Output*

   ```output
   helmpipeline.package.nvidia.com "rag-llm-pipeline" deleted
   ```

1. Optional: Delete the namespace for the RAG pipeline:

   ```console
   $ kubectl delete namespace rag-llm-pipeline
   ```

1. Uninstall the Operator:

   ```console
   $ helm delete -n kube-trailblazer-system $(helm list -n kube-trailblazer-system | grep developer-llm-operator | awk '{print $1}')
   ```

   *Example Output*

   ```output
   release "developer-llm-operator-0-1705070979" uninstalled
   ```
