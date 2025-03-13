/* 

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

*/

// APIConfig.js

const API_BASE_URL = "http://localhost:5050";

const API_ENDPOINTS = {
    SIMPLE_CHAT: "/v1/chat/simple",
    NV_INGEST_CHAT: "/v1/chat/nvingest",
    PDF_UPLOAD: "/v1/api/upload_pdf",
    PDF_DOWNLOAD: "/v1/api/download_pdf",
    ASSISTANT_RESPONSE_AUDIO_DOWNLOAD: "/v1/api/download_audio",
    GENERATE_WELCOME_AUDIO: "/v1/api/generate_welcome_audio"
};

const WELCOME_TEXT = "Hey there. Welcome to PDF Speak. Upload your document of interest and talk to it in real-time! Be it a simple summary OR a complex analysis, PDF Speak has got you covered. Ask away!!";

export {API_BASE_URL, API_ENDPOINTS, WELCOME_TEXT};
