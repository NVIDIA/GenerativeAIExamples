module.exports = {

"[project]/.next-internal/server/app/api/generate/route/actions.js [app-rsc] (server actions loader, ecmascript)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
}}),
"[externals]/next/dist/compiled/next-server/app-route-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-route-turbo.runtime.dev.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-route-turbo.runtime.dev.js"));

module.exports = mod;
}}),
"[externals]/next/dist/compiled/@opentelemetry/api [external] (next/dist/compiled/@opentelemetry/api, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/compiled/@opentelemetry/api", () => require("next/dist/compiled/@opentelemetry/api"));

module.exports = mod;
}}),
"[externals]/next/dist/compiled/next-server/app-page-turbo.runtime.dev.js [external] (next/dist/compiled/next-server/app-page-turbo.runtime.dev.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js", () => require("next/dist/compiled/next-server/app-page-turbo.runtime.dev.js"));

module.exports = mod;
}}),
"[externals]/next/dist/server/app-render/work-unit-async-storage.external.js [external] (next/dist/server/app-render/work-unit-async-storage.external.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/server/app-render/work-unit-async-storage.external.js", () => require("next/dist/server/app-render/work-unit-async-storage.external.js"));

module.exports = mod;
}}),
"[externals]/next/dist/server/app-render/work-async-storage.external.js [external] (next/dist/server/app-render/work-async-storage.external.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/server/app-render/work-async-storage.external.js", () => require("next/dist/server/app-render/work-async-storage.external.js"));

module.exports = mod;
}}),
"[externals]/next/dist/server/app-render/after-task-async-storage.external.js [external] (next/dist/server/app-render/after-task-async-storage.external.js, cjs)": (function(__turbopack_context__) {

var { g: global, __dirname, m: module, e: exports } = __turbopack_context__;
{
const mod = __turbopack_context__.x("next/dist/server/app-render/after-task-async-storage.external.js", () => require("next/dist/server/app-render/after-task-async-storage.external.js"));

module.exports = mod;
}}),
"[project]/src/app/api/utils/api-utils.ts [app-route] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname } = __turbopack_context__;
{
// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
__turbopack_context__.s({
    "APIError": (()=>APIError),
    "createErrorResponse": (()=>createErrorResponse),
    "createSuccessResponse": (()=>createSuccessResponse),
    "validateRequiredFields": (()=>validateRequiredFields)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/server.js [app-route] (ecmascript)");
;
class APIError extends Error {
    message;
    statusCode;
    details;
    constructor(message, statusCode = 500, details){
        super(message), this.message = message, this.statusCode = statusCode, this.details = details;
        this.name = "APIError";
    }
}
function createSuccessResponse(data, status = 200) {
    return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json(data, {
        status
    });
}
function createErrorResponse(error) {
    if (error instanceof APIError) {
        return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
            error: error.message,
            details: error.details
        }, {
            status: error.statusCode
        });
    }
    console.error("Unhandled error:", error);
    return __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$server$2e$js__$5b$app$2d$route$5d$__$28$ecmascript$29$__["NextResponse"].json({
        error: "Internal server error"
    }, {
        status: 500
    });
}
function validateRequiredFields(obj, fields) {
    const missingFields = fields.filter((field)=>!obj[field]);
    if (missingFields.length > 0) {
        throw new APIError(`Missing required fields: ${missingFields.join(", ")}`, 400);
    }
}
}}),
"[project]/src/app/config/api.ts [app-route] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname } = __turbopack_context__;
{
// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// API Configuration
__turbopack_context__.s({
    "API_CONFIG": (()=>API_CONFIG),
    "buildQueryUrl": (()=>buildQueryUrl),
    "createMessage": (()=>createMessage)
});
const API_CONFIG = {
    VDB: {
        BASE_URL: process.env.NEXT_PUBLIC_VDB_BASE_URL ?? "http://localhost:8082/v1",
        ENDPOINTS: {
            DOCUMENTS: {
                LIST: "/documents",
                UPLOAD: "/documents",
                DELETE: "/documents"
            },
            COLLECTIONS: {
                LIST: "/collections",
                CREATE: "/collections",
                DELETE: "/collections"
            }
        },
        VDB_ENDPOINT: process.env.NEXT_PUBLIC_VDB_ENDPOINT ?? "http://milvus:19530"
    },
    CHAT: {
        BASE_URL: process.env.NEXT_PUBLIC_CHAT_BASE_URL ?? "http://localhost:8081/v1",
        ENDPOINTS: {
            RAG: {
                GENERATE: "/generate",
                CHAT_COMPLETIONS: "/chat/completions"
            },
            SEARCH: {
                QUERY: "/search"
            }
        }
    }
};
const buildQueryUrl = (url, params)=>{
    const queryParams = new URLSearchParams();
    queryParams.append("vdb_endpoint", API_CONFIG.VDB.VDB_ENDPOINT);
    // Add other params
    Object.entries(params).forEach(([key, value])=>{
        queryParams.append(key, value.toString());
    });
    return `${url}?${queryParams.toString()}`;
};
const createMessage = (role, content)=>({
        role,
        content
    });
}}),
"[project]/src/app/api/generate/route.ts [app-route] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname } = __turbopack_context__;
{
// SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
__turbopack_context__.s({
    "POST": (()=>POST)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$api$2f$utils$2f$api$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/api/utils/api-utils.ts [app-route] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$config$2f$api$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/config/api.ts [app-route] (ecmascript)");
;
;
const RAG_API_URL = `${__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$config$2f$api$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["API_CONFIG"].CHAT.BASE_URL}${__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$config$2f$api$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["API_CONFIG"].CHAT.ENDPOINTS.RAG.GENERATE}`;
async function POST(request) {
    try {
        const body = await request.json();
        if (!body.messages || body.messages.length === 0) {
            throw new __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$api$2f$utils$2f$api$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["APIError"]("messages array is required and cannot be empty", 400);
        }
        // Forward the request to the RAG API and stream the response
        const response = await fetch(RAG_API_URL, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            throw new __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$api$2f$utils$2f$api$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["APIError"](`RAG API error: ${response.statusText}`, response.status, await response.text());
        }
        // Set up SSE response
        const stream = new ReadableStream({
            async start (controller) {
                const reader = response.body?.getReader();
                if (!reader) throw new Error("No response body");
                try {
                    while(true){
                        const { done, value } = await reader.read();
                        if (done) break;
                        // Decode and log the chunk
                        const text = new TextDecoder().decode(value);
                        console.log("Streaming chunk:", text);
                        // Forward the chunks as they come
                        controller.enqueue(value);
                    }
                } finally{
                    reader.releaseLock();
                    controller.close();
                }
            }
        });
        return new Response(stream, {
            headers: {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                Connection: "keep-alive"
            }
        });
    } catch (error) {
        console.error("Error in generate route:", error);
        return (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$api$2f$utils$2f$api$2d$utils$2e$ts__$5b$app$2d$route$5d$__$28$ecmascript$29$__["createErrorResponse"])(error);
    }
}
}}),

};

//# sourceMappingURL=%5Broot-of-the-server%5D__bb078162._.js.map