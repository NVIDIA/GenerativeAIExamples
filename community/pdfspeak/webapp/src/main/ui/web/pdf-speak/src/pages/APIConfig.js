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
