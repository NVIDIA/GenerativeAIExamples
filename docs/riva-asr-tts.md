<!--
  SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
  SPDX-License-Identifier: Apache-2.0
-->

# Optional: Enable NVIDIA Riva ASR and TTS

<!-- TOC -->

* [RAG Playground Integration](#rag-playground-integration)
* [Local Riva Server](#local-riva-server)
* [Hosted Riva API Endpoint](#hosted-riva-api-endpoint)
* [Start the RAG Example](#start-the-rag-example)
* [Next Steps](#next-steps)

<!-- /TOC -->

## RAG Playground Integration

If you perform the following steps, you can use your voice to submit queries to the RAG Playground
and the playground can read aloud the LLM responses.

## Local Riva Server

To launch a Riva server locally, refer to the [Riva Quick Start Guide](https://docs.nvidia.com/deeplearning/riva/user-guide/docs/quick-start-guide.html).

- In the provided `config.sh` script, make or confirm the following settings:

  - Set `service_enabled_asr=true` and `service_enabled_tts=true`.
  - Set the ASR and TTS languages by adding the language codes to `asr_language_code` and `tts_language_code`.
  - Set the `models_tts` variable to include a Rad-TTS model such as `rmir_tts_radtts_hifigan_${modified_lang_code}_ipa`.

## Riva API Endpoint on NVIDIA API Catalog

You can [access several GPU-accelerated speech models](https://build.nvidia.com/explore/speech) from NVIDIA API Catalog instead of hosting them locally.
To access these models you need an API key.
You can follow the steps [to get an API key for the speech models](common-prerequisites.md#get-an-api-key-for-the-accessing-models-on-the-api-catalog).

## Start the RAG Example

After you have access to a Riva server, perform the following steps to start any RAG example with speech support.

1. Export the `PLAYGROUND_MODE` environment variable in your terminal:

   ```console
   export PLAYGROUND_MODE=speech
   ```

1. Edit the `docker-compose.yaml` file for the example and add the following environment variables to the `rag-playground` service:

   * Use [speech models](https://build.nvidia.com/explore/speech) from NVIDIA API Catalog:

     ```yaml
     rag-playgound:
       ...
       environment:
         RIVA_API_URI: grpc.nvcf.nvidia.com:443
         NVIDIA_API_KEY: ${NVIDIA_API_KEY}
         RIVA_ASR_FUNCTION_ID: 1598d209-5e27-4d3c-8079-4751568b1081 # nvidia/parakeet-ctc-riva-1-1b
         RIVA_TTS_FUNCTION_ID: 5e607c81-7aa6-44ce-a11d-9e08f0a3fe49 # nvidia/radtts-hifigan-riva
         TTS_SAMPLE_RATE: 48000
     ```

     To obtain your API key and function ID, navigate to the speech model and select **Try API**.
     From there, click **Get API Key** to generate your API key and refer **Run python client** to get function-id.

   * Use locally hosted RIVA models:

     ```yaml
     rag-playgound:
       ...
       environment:
         RIVA_API_URI: <riva-ip-address>:50051
         TTS_SAMPLE_RATE: 48000
     ```

   * `RIVA_API_URI` is the Riva IP address or hostname and port number.
   * `NVIDIA_API_KEY` is the API Catalog key for a hosted Riva API endpoint.
   * `RIVA_ASR_FUNCTION_ID` is the Riva Function ID for a Riva API endpoint hosting ASR.
   * `RIVA_TTS_FUNCTION_ID` is the Riva Function ID for a Riva API endpoint hosting TTS.
   * `TTS_SAMPLE_RATE` is the text-to-speech sample rate in hertz.

1. Start the containers:

   ```console
   docker compose up -d --build
   ```

## Next Steps

Refer to [Using the Sample Web Application](./using-sample-web-application.md) for information
about enabling the Riva ASR and TTS features.
