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

# Using the Sample Chat Web Application

```{contents}
---
depth: 2
local: true
backlinks: none
---
```

## Prerequisites

- You deployed one of the samples, such as [](./api-catalog.md) or [](./local-gpu.md).

## Access the Web Application

- Connect to the sample web application at `http://<host-ip>:8090`.

  ![Sample chat web application](./images/sample-web-application.png)

## Use Unstructured Documents as a Knowledge Base

1. Optional: If you configured your deployment with NVIDIA Riva, check **[X] Enable TTS output** to enable the web application to read aloud the answers to your queries.

   Select the desired ASR language (`English (en-US)` for this test), TTS language (`English (en-US)` for this test) and TTS voice from the dropdown menus below the checkboxes to use the voice-to-voice interaction capabilities.

1. On the **Converse** tab, enter "How many cores does the Grace superchip contain?" in the chat box and click **Submit**.

   Alternatively, click on the microphone button to the right of the text box and ask the question verbally.

   ![Grace query failure](../../notebooks/imgs/grace_noanswer_with_riva.png)

1. Upload the sample data to the knowledge base.

   Click the **Knowledge Base** tab and then click **Add File**.

   Navigate to the `dataset.zip` file that is located in the `notebooks` directory. Unzip the archive and upload the PDFs.

1. Return to **Converse** tab and select **[X] Use knowledge base**.

1. Reenter the question: "How many cores does the Grace superchip contain?"

   ![Grace query success](../../notebooks/imgs/grace_answer_with_riva.png)

   ```{tip}
   The default prompts are optimized for Llama chat model.
   If you use a completion model, then you must fine tune the prompts.
   ```

## Troubleshooting

If you receive the following "Media devices could not be accessed" error message when you first attempt to transcribe a voice query, perform the following steps.

![Media device access error window.](./images/media-device-access-error.png)

1. Open another browser tab and enter `chrome://flags` in the location field.

1. Enter `insecure origins treated as secure` in the search field.

   ![Browser viewing the chrome://flags URL.](./images/chrome-flags-fix-media-device-access-error.png)

1. Enter `http://<host-ip>:8090` in the text box and select **Enabled** from the menu.

1. Click **Relaunch**.

1. After the browser opens, grant `http://host-ip:8090` access to your microphone.

1. Retry your request.
