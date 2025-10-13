(globalThis.TURBOPACK = globalThis.TURBOPACK || []).push([typeof document === "object" ? document.currentScript : undefined, {

"[project]/src/app/components/RightSidebar/Citations.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "default": (()=>Citations)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$image$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/image.js [app-client] (ecmascript)");
"use client";
;
;
const renderCitationContent = (citation)=>{
    switch(citation.document_type){
        case "image":
        case "table":
        case "chart":
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "relative h-48 w-full",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$image$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                    src: `data:image/png;base64,${citation.text}`,
                    alt: `Citation ${citation.document_type}`,
                    fill: true,
                    className: "object-contain"
                }, void 0, false, {
                    fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                    lineNumber: 32,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                lineNumber: 31,
                columnNumber: 9
            }, this);
        case "text":
        default:
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                className: "mb-4 text-sm text-gray-400",
                children: citation.text
            }, void 0, false, {
                fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                lineNumber: 43,
                columnNumber: 14
            }, this);
    }
};
function Citations({ citations = [] }) {
    if (!citations || citations.length === 0) {
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "p-4 text-center text-gray-400",
            children: "No citations available for this response."
        }, void 0, false, {
            fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
            lineNumber: 50,
            columnNumber: 7
        }, this);
    }
    // Debug the received citations
    console.log("Citations component received:", citations);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "space-y-6 text-gray-400",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mb-2 p-2 text-center text-sm",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                    className: "font-medium",
                    children: [
                        "Showing ",
                        citations.length,
                        " citations"
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                    lineNumber: 62,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                lineNumber: 61,
                columnNumber: 7
            }, this),
            citations.map((citation, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "max-h-72 overflow-y-auto rounded-lg border border-neutral-800 p-4",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "mb-2 flex items-center justify-between",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                    className: "text-sm font-medium",
                                    children: [
                                        "Source ",
                                        index + 1
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                                    lineNumber: 70,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-xs px-2 py-1 rounded bg-neutral-900",
                                    children: [
                                        "Score: ",
                                        citation.score !== undefined ? citation.score.toFixed(2) : "N/A"
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                                    lineNumber: 71,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                            lineNumber: 69,
                            columnNumber: 11
                        }, this),
                        renderCitationContent(citation),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center gap-2",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-xs text-gray-500",
                                    children: "Source:"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                                    lineNumber: 77,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-xs text-gray-400",
                                    children: citation.source
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                                    lineNumber: 78,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                            lineNumber: 76,
                            columnNumber: 11
                        }, this)
                    ]
                }, index, true, {
                    fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
                    lineNumber: 65,
                    columnNumber: 9
                }, this))
        ]
    }, void 0, true, {
        fileName: "[project]/src/app/components/RightSidebar/Citations.tsx",
        lineNumber: 60,
        columnNumber: 5
    }, this);
}
_c = Citations;
var _c;
__turbopack_context__.k.register(_c, "Citations");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/components/RightSidebar/RightSidebar.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "default": (()=>RightSidebar)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$RightSidebar$2f$Citations$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/components/RightSidebar/Citations.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SidebarContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/context/SidebarContext.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
function RightSidebar() {
    _s();
    const { activePanel, closeSidebar, activeCitations } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SidebarContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useSidebar"])();
    const [displayPanel, setDisplayPanel] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(activePanel);
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "RightSidebar.useEffect": ()=>{
            if (activePanel) {
                setDisplayPanel(activePanel);
            } else {
                const timer = setTimeout({
                    "RightSidebar.useEffect.timer": ()=>{
                        setDisplayPanel(null);
                    }
                }["RightSidebar.useEffect.timer"], 300); // Match the transition duration
                return ({
                    "RightSidebar.useEffect": ()=>clearTimeout(timer)
                })["RightSidebar.useEffect"];
            }
        }
    }["RightSidebar.useEffect"], [
        activePanel
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: `fixed bottom-0 right-0 top-14 w-[400px] transform border-l border-neutral-800 bg-black transition-transform duration-300 ease-in-out ${!!activePanel ? "translate-x-0" : "translate-x-full"}`,
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "flex h-full flex-col",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center justify-between border-b border-neutral-800 p-4",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                            className: "text-xl font-semibold text-white",
                            children: "Citations"
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/RightSidebar/RightSidebar.tsx",
                            lineNumber: 45,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                            onClick: closeSidebar,
                            className: "text-gray-400 transition-colors hover:text-white",
                            "aria-label": "Close sidebar",
                            children: "×"
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/RightSidebar/RightSidebar.tsx",
                            lineNumber: 48,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/RightSidebar/RightSidebar.tsx",
                    lineNumber: 44,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex-1 overflow-y-auto p-4",
                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$RightSidebar$2f$Citations$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        citations: activeCitations
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/RightSidebar/RightSidebar.tsx",
                        lineNumber: 57,
                        columnNumber: 11
                    }, this)
                }, void 0, false, {
                    fileName: "[project]/src/app/components/RightSidebar/RightSidebar.tsx",
                    lineNumber: 56,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/src/app/components/RightSidebar/RightSidebar.tsx",
            lineNumber: 43,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/src/app/components/RightSidebar/RightSidebar.tsx",
        lineNumber: 38,
        columnNumber: 5
    }, this);
}
_s(RightSidebar, "uDoQYxTBGNEptz7G5C7RXgXEUVk=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SidebarContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useSidebar"]
    ];
});
_c = RightSidebar;
var _c;
__turbopack_context__.k.register(_c, "RightSidebar");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/components/Chat/VGPUConfigCard.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "default": (()=>VGPUConfigCard)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature(), _s1 = __turbopack_context__.k.signature();
"use client";
;
// Tooltip component
const Tooltip = ({ content, children })=>{
    _s();
    const [isVisible, setIsVisible] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "relative inline-block",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                onMouseEnter: ()=>setIsVisible(true),
                onMouseLeave: ()=>setIsVisible(false),
                className: "cursor-help",
                children: children
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 60,
                columnNumber: 7
            }, this),
            isVisible && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "absolute z-10 px-3 py-2 text-xs text-white bg-gradient-to-br from-[#76b900]/20 to-[#76b900]/10 border border-[#76b900]/30 rounded-md shadow-lg backdrop-blur-sm -top-8 left-1/2 transform -translate-x-1/2 whitespace-nowrap",
                children: [
                    content,
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "absolute w-2 h-2 bg-[#76b900]/15 border-l border-b border-[#76b900]/30 transform rotate-45 -bottom-1 left-1/2 -translate-x-1/2"
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 70,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 68,
                columnNumber: 9
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
        lineNumber: 59,
        columnNumber: 5
    }, this);
};
_s(Tooltip, "QjDZesRvLCmcrZLxgN677nXnVLA=");
_c = Tooltip;
// Parameter definitions for tooltips
const parameterDefinitions = {
    vgpu_profile: "Virtual GPU profile that defines the GPU partitioning and resource allocation",
    vGPU_profile: "Virtual GPU profile that defines the GPU partitioning and resource allocation",
    vcpu_count: "Number of virtual CPU cores allocated to this configuration",
    vCPU_count: "Number of virtual CPU cores allocated to this configuration",
    gpu_memory_size: "Total VRAM (in GB) needed = sum(model_params in billions) × precision_factor × 1.2 overhead × concurrent_users",
    system_RAM: "System memory (in GB) allocated to this VM, including OS and framework overhead",
    concurrent_users: "Number of simultaneous inference users expected on this VM",
    // Legacy fields (kept for backward compatibility)
    video_card_total_memory: "Total physical memory available on the GPU hardware",
    storage_capacity: "Total storage space allocated for the workload",
    storage_type: "Type of storage (SSD, NVMe, HDD) for optimal performance",
    driver_version: "NVIDIA driver version required for this configuration",
    AI_framework: "AI/ML framework optimized for this configuration",
    performance_tier: "Performance level classification for this setup"
};
// Key parameters that should be in the primary section
const keyParameters = [
    'vgpu_profile',
    'vGPU_profile',
    'gpu_memory_size',
    'system_RAM',
    'vcpu_count',
    'vCPU_count',
    'concurrent_users'
];
// Icon component using SVG instead of emojis
const ParameterIcon = ({ type, className = "w-4 h-4" })=>{
    const iconClass = className;
    switch(type){
        case 'vGPU_profile':
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: iconClass,
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    strokeWidth: 2,
                    d: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                }, void 0, false, {
                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                    lineNumber: 106,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 105,
                columnNumber: 9
            }, this);
        case 'cpu':
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: iconClass,
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    strokeWidth: 2,
                    d: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2z"
                }, void 0, false, {
                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                    lineNumber: 112,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 111,
                columnNumber: 9
            }, this);
        case 'memory':
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: iconClass,
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    strokeWidth: 2,
                    d: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
                }, void 0, false, {
                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                    lineNumber: 118,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 117,
                columnNumber: 9
            }, this);
        case 'storage':
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: iconClass,
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    strokeWidth: 2,
                    d: "M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4"
                }, void 0, false, {
                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                    lineNumber: 124,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 123,
                columnNumber: 9
            }, this);
        case 'framework':
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: iconClass,
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    strokeWidth: 2,
                    d: "M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                }, void 0, false, {
                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                    lineNumber: 130,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 129,
                columnNumber: 9
            }, this);
        case 'users':
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: iconClass,
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                    strokeLinecap: "round",
                    strokeLinejoin: "round",
                    strokeWidth: 2,
                    d: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
                }, void 0, false, {
                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                    lineNumber: 136,
                    columnNumber: 11
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 135,
                columnNumber: 9
            }, this);
        default:
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                className: iconClass,
                fill: "none",
                stroke: "currentColor",
                viewBox: "0 0 24 24",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                        strokeLinecap: "round",
                        strokeLinejoin: "round",
                        strokeWidth: 2,
                        d: "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 142,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                        strokeLinecap: "round",
                        strokeLinejoin: "round",
                        strokeWidth: 2,
                        d: "M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 143,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 141,
                columnNumber: 9
            }, this);
    }
};
_c1 = ParameterIcon;
// Circular Progress Chart Component
const VRAMUsageChart = ({ usedVRAM, totalVRAM, numGPUs })=>{
    const percentage = Math.min(usedVRAM / totalVRAM * 100, 100);
    const radius = 80;
    const strokeWidth = 12;
    const normalizedRadius = radius - strokeWidth * 2;
    const circumference = normalizedRadius * 2 * Math.PI;
    const strokeDashoffset = circumference - percentage / 100 * circumference;
    // Determine fit category and color
    const getFitCategory = (pct)=>{
        if (pct >= 90) {
            return {
                label: "TIGHT",
                color: "#ef4444",
                bgColor: "rgba(239, 68, 68, 0.1)",
                textColor: "#fca5a5" // red-300
            };
        } else if (pct >= 60) {
            return {
                label: "MODERATE",
                color: "#76b900",
                bgColor: "rgba(118, 185, 0, 0.1)",
                textColor: "#a3e635" // lime-400
            };
        } else {
            return {
                label: "COMFORTABLE",
                color: "#10b981",
                bgColor: "rgba(16, 185, 129, 0.1)",
                textColor: "#6ee7b7" // emerald-300
            };
        }
    };
    const fitCategory = getFitCategory(percentage);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex flex-col items-center",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "relative",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                        height: radius * 2,
                        width: radius * 2,
                        className: "transform -rotate-90",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("circle", {
                                stroke: "rgba(0, 0, 0, 0.3)",
                                fill: "transparent",
                                strokeWidth: strokeWidth + 4,
                                r: normalizedRadius,
                                cx: radius,
                                cy: radius
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 203,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("circle", {
                                stroke: "#1f2937",
                                fill: "transparent",
                                strokeWidth: strokeWidth,
                                r: normalizedRadius,
                                cx: radius,
                                cy: radius
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 212,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("circle", {
                                stroke: fitCategory.color,
                                fill: "transparent",
                                strokeWidth: strokeWidth,
                                strokeDasharray: circumference + ' ' + circumference,
                                style: {
                                    strokeDashoffset
                                },
                                strokeLinecap: "round",
                                r: normalizedRadius,
                                cx: radius,
                                cy: radius,
                                className: "transition-all duration-700 ease-out filter drop-shadow-lg"
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 221,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 197,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "absolute inset-0 flex flex-col items-center justify-center",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-2xl font-bold text-gray-200",
                                children: [
                                    percentage.toFixed(1),
                                    "%"
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 236,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-xs text-gray-500 uppercase tracking-wider mt-0.5",
                                children: "VRAM"
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 239,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 235,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 196,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mt-5 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider transition-all duration-300",
                style: {
                    backgroundColor: fitCategory.bgColor,
                    color: fitCategory.color,
                    border: `2px solid ${fitCategory.color}`,
                    boxShadow: `0 0 25px ${fitCategory.bgColor}`
                },
                children: fitCategory.label
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 244,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "mt-4 text-center",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-lg font-semibold text-gray-100",
                        children: [
                            usedVRAM.toFixed(1),
                            " GB"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 258,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "text-sm text-gray-500",
                        children: [
                            "of ",
                            totalVRAM.toFixed(0),
                            " GB VRAM"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 261,
                        columnNumber: 9
                    }, this),
                    numGPUs > 1 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-1 text-xs text-[#76b900] font-medium",
                        children: [
                            "(",
                            numGPUs,
                            " GPUs × ",
                            (totalVRAM / numGPUs).toFixed(0),
                            " GB each)"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 265,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 257,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
        lineNumber: 195,
        columnNumber: 5
    }, this);
};
_c2 = VRAMUsageChart;
const getIconType = (key)=>{
    switch(key){
        case 'vgpu_profile':
        case 'vGPU_profile':
            return 'vGPU_profile';
        case 'vcpu_count':
        case 'vCPU_count':
            return 'cpu';
        case 'gpu_memory_size':
        case 'video_card_total_memory':
        case 'system_RAM':
        case 'RAM':
            return 'memory';
        case 'storage_capacity':
        case 'storage_type':
            return 'storage';
        case 'AI_framework':
        case 'relevant_aiwb_toolkit':
            return 'framework';
        case 'concurrent_users':
            return 'users';
        default:
            return 'default';
    }
};
function VGPUConfigCard({ config }) {
    _s1();
    const [isExpanded, setIsExpanded] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(true);
    const [showAdvancedDetails, setShowAdvancedDetails] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [showRawJSON, setShowRawJSON] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [copied, setCopied] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    // Function to extract GPU memory capacity from vGPU profile
    const getGPUCapacityFromProfile = (profile)=>{
        if (!profile) return null;
        // Extract the number after the hyphen (e.g., "L40S-24Q" -> 24)
        const match = profile.match(/-(\d+)Q?/i);
        if (match && match[1]) {
            return parseInt(match[1]);
        }
        return null;
    };
    // Check if multi-GPU is needed
    const isMultiGPU = ()=>{
        const profile = config.parameters.vgpu_profile || config.parameters.vGPU_profile;
        const gpuMemoryRequired = config.parameters.gpu_memory_size;
        if (!profile || !gpuMemoryRequired) return false;
        const singleGPUCapacity = getGPUCapacityFromProfile(profile);
        if (!singleGPUCapacity) return false;
        return gpuMemoryRequired > singleGPUCapacity;
    };
    const handleCopy = async ()=>{
        try {
            const text = JSON.stringify(config, null, 2);
            // Try modern clipboard API first
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(text);
                setCopied(true);
                setTimeout(()=>setCopied(false), 2000);
            } else {
                // Fallback for older browsers or non-HTTPS contexts
                const textArea = document.createElement('textarea');
                textArea.value = text;
                textArea.style.position = 'fixed';
                textArea.style.left = '-999999px';
                textArea.style.top = '-999999px';
                document.body.appendChild(textArea);
                textArea.focus();
                textArea.select();
                try {
                    const successful = document.execCommand('copy');
                    if (successful) {
                        setCopied(true);
                        setTimeout(()=>setCopied(false), 2000);
                    }
                } catch (err) {
                    console.error('Fallback copy failed: ', err);
                }
                document.body.removeChild(textArea);
            }
        } catch (err) {
            console.error('Failed to copy: ', err);
        }
    };
    const formatParameterValue = (key, value)=>{
        if (value === null || value === undefined) {
            return "Not specified";
        }
        switch(key){
            case 'gpu_memory_size':
            case 'video_card_total_memory':
            case 'system_RAM':
            case 'RAM':
            case 'storage_capacity':
                return `${value} GB`;
            case 'vgpu_profile':
            case 'vGPU_profile':
                return value;
            case 'vcpu_count':
            case 'vCPU_count':
                return `${value} cores`;
            case 'concurrent_users':
                return `${value} users`;
            case 'storage_type':
            case 'driver_version':
            case 'AI_framework':
            case 'relevant_aiwb_toolkit':
            case 'performance_tier':
                return String(value);
            default:
                return String(value);
        }
    };
    const getParameterLabel = (key)=>{
        switch(key){
            case 'vgpu_profile':
            case 'vGPU_profile':
                return 'vGPU Profile';
            case 'vcpu_count':
            case 'vCPU_count':
                return 'vCPU Count';
            case 'gpu_memory_size':
                return 'Estimated VRAM';
            case 'video_card_total_memory':
                return 'Video Card Total Memory';
            case 'system_RAM':
                return 'System RAM';
            case 'RAM':
                return 'RAM';
            case 'storage_capacity':
                return 'Storage Capacity';
            case 'storage_type':
                return 'Storage Type';
            case 'driver_version':
                return 'Driver Version';
            case 'AI_framework':
                return 'AI Framework';
            case 'relevant_aiwb_toolkit':
                return 'AI Toolkit';
            case 'performance_tier':
                return 'Performance Tier';
            case 'concurrent_users':
                return 'Concurrent Users';
            default:
                return key.replace(/_/g, ' ').replace(/^./, (str)=>str.toUpperCase());
        }
    };
    const isRelevantConfig = Object.values(config.parameters).some((value)=>value !== null && value !== undefined);
    // Fields to exclude from display
    const excludedFields = [
        'total_CPU_count',
        'total_cpu_count'
    ];
    // Separate key and advanced parameters, excluding unwanted fields
    const keyParams = Object.entries(config.parameters).filter(([key])=>keyParameters.includes(key) && config.parameters[key] !== null && !excludedFields.includes(key));
    const advancedParams = Object.entries(config.parameters).filter(([key])=>!keyParameters.includes(key) && config.parameters[key] !== null && !excludedFields.includes(key));
    // Get VRAM usage data with multi-GPU calculation
    const getVRAMUsageData = ()=>{
        const profile = config.parameters.vgpu_profile || config.parameters.vGPU_profile;
        const estimatedVRAM = config.parameters.gpu_memory_size;
        if (!profile || !estimatedVRAM) return null;
        const singleGPUCapacity = getGPUCapacityFromProfile(profile);
        if (!singleGPUCapacity) return null;
        // Calculate number of GPUs needed (ceiling)
        const numGPUs = Math.ceil(estimatedVRAM / singleGPUCapacity);
        // Calculate total capacity across all GPUs
        const totalCapacity = numGPUs * singleGPUCapacity;
        return {
            used: estimatedVRAM,
            total: totalCapacity,
            numGPUs: numGPUs,
            singleGPUCapacity: singleGPUCapacity
        };
    };
    const vramUsage = getVRAMUsageData();
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "bg-neutral-900 border border-neutral-700 rounded-lg overflow-hidden shadow-lg",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "bg-gradient-to-r from-[#76b900] to-[#5a8c00] text-white px-6 py-4",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "flex items-center justify-between",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center gap-3",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                                className: "text-lg font-semibold",
                                                children: "vGPU Configuration Recommendation"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 484,
                                                columnNumber: 15
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                className: "text-sm text-green-100 mt-0.5 opacity-90",
                                                children: "Optimized for your AI workload requirements"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 485,
                                                columnNumber: 15
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 483,
                                        columnNumber: 13
                                    }, this),
                                    vramUsage && vramUsage.numGPUs > 1 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full border border-white/30",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "text-sm font-medium flex items-center gap-1.5",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                    className: "w-4 h-4",
                                                    fill: "none",
                                                    stroke: "currentColor",
                                                    viewBox: "0 0 24 24",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                        strokeLinecap: "round",
                                                        strokeLinejoin: "round",
                                                        strokeWidth: 2,
                                                        d: "M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                        lineNumber: 491,
                                                        columnNumber: 21
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 490,
                                                    columnNumber: 19
                                                }, this),
                                                vramUsage.numGPUs,
                                                " GPUs"
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 489,
                                            columnNumber: 17
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 488,
                                        columnNumber: 15
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 482,
                                columnNumber: 11
                            }, this),
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "flex items-center gap-2",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: ()=>setShowRawJSON(!showRawJSON),
                                        className: "p-2 hover:bg-white/10 rounded transition-colors",
                                        title: showRawJSON ? "Show Visualization" : "Show JSON Code",
                                        children: showRawJSON ? /* Chart/Graph icon when viewing JSON - click to see visualization */ /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                            className: "w-4 h-4",
                                            fill: "none",
                                            stroke: "currentColor",
                                            viewBox: "0 0 24 24",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                strokeLinecap: "round",
                                                strokeLinejoin: "round",
                                                strokeWidth: 2,
                                                d: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 507,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 506,
                                            columnNumber: 17
                                        }, this) : /* Code icon when viewing visualization - click to see JSON */ /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                            className: "w-4 h-4",
                                            fill: "none",
                                            stroke: "currentColor",
                                            viewBox: "0 0 24 24",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                strokeLinecap: "round",
                                                strokeLinejoin: "round",
                                                strokeWidth: 2,
                                                d: "M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 512,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 511,
                                            columnNumber: 17
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 499,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: handleCopy,
                                        className: "p-2 hover:bg-white/10 rounded transition-colors",
                                        title: "Copy JSON",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                            className: "w-4 h-4",
                                            fill: "none",
                                            stroke: "currentColor",
                                            viewBox: "0 0 24 24",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                strokeLinecap: "round",
                                                strokeLinejoin: "round",
                                                strokeWidth: 2,
                                                d: "M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 522,
                                                columnNumber: 17
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 521,
                                            columnNumber: 15
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 516,
                                        columnNumber: 13
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: ()=>setIsExpanded(!isExpanded),
                                        className: "p-2 hover:bg-white/10 rounded transition-colors",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                            className: `w-4 h-4 transform transition-transform ${isExpanded ? 'rotate-180' : ''}`,
                                            fill: "none",
                                            stroke: "currentColor",
                                            viewBox: "0 0 24 24",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                strokeLinecap: "round",
                                                strokeLinejoin: "round",
                                                strokeWidth: 2,
                                                d: "M19 9l-7 7-7-7"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 530,
                                                columnNumber: 17
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 529,
                                            columnNumber: 15
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 525,
                                        columnNumber: 13
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 498,
                                columnNumber: 11
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 481,
                        columnNumber: 9
                    }, this),
                    copied && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mt-2 text-sm text-green-100 flex items-center gap-1",
                        children: [
                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                className: "w-4 h-4",
                                fill: "none",
                                stroke: "currentColor",
                                viewBox: "0 0 24 24",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                    strokeLinecap: "round",
                                    strokeLinejoin: "round",
                                    strokeWidth: 2,
                                    d: "M5 13l4 4L19 7"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                    lineNumber: 538,
                                    columnNumber: 15
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 537,
                                columnNumber: 13
                            }, this),
                            "Copied to clipboard"
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 536,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 480,
                columnNumber: 7
            }, this),
            isExpanded && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "p-6",
                children: [
                    config.description && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mb-6 p-5 bg-gradient-to-br from-[#76b900]/10 to-[#76b900]/5 rounded-lg border border-[#76b900]/20 backdrop-blur-sm",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-gray-100 text-sm leading-relaxed",
                            children: config.description
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                            lineNumber: 551,
                            columnNumber: 15
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 550,
                        columnNumber: 13
                    }, this),
                    (config.rationale || isRelevantConfig) && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mb-6 p-4 bg-blue-950/30 border border-blue-900/50 rounded-lg",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-start gap-3",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                    className: "w-5 h-5 text-blue-400 mt-0.5",
                                    fill: "none",
                                    stroke: "currentColor",
                                    viewBox: "0 0 24 24",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                        strokeLinecap: "round",
                                        strokeLinejoin: "round",
                                        strokeWidth: 2,
                                        d: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 562,
                                        columnNumber: 19
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                    lineNumber: 561,
                                    columnNumber: 17
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                            className: "text-blue-300 font-medium text-sm mb-1",
                                            children: "Why this configuration?"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 565,
                                            columnNumber: 19
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-blue-200/80 text-sm",
                                            children: config.rationale || "This configuration balances performance and resource efficiency for your specific AI workload, ensuring optimal GPU utilization while maintaining cost-effectiveness."
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 566,
                                            columnNumber: 19
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                    lineNumber: 564,
                                    columnNumber: 17
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                            lineNumber: 560,
                            columnNumber: 15
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 559,
                        columnNumber: 13
                    }, this),
                    config.host_capabilities && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "mb-6 p-4 bg-gray-800/30 border border-gray-700/50 rounded-lg",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-start gap-3",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                    className: "w-5 h-5 text-gray-400 mt-0.5",
                                    fill: "none",
                                    stroke: "currentColor",
                                    viewBox: "0 0 24 24",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                        strokeLinecap: "round",
                                        strokeLinejoin: "round",
                                        strokeWidth: 2,
                                        d: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 579,
                                        columnNumber: 19
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                    lineNumber: 578,
                                    columnNumber: 17
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "w-full",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                            className: "text-gray-300 font-medium text-sm mb-3",
                                            children: "Detected Host Capabilities"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 582,
                                            columnNumber: 19
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "grid grid-cols-1 md:grid-cols-3 gap-4",
                                            children: [
                                                config.host_capabilities.max_ram && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "flex justify-between items-center",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-gray-500 text-sm",
                                                            children: "Max RAM:"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 586,
                                                            columnNumber: 25
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-gray-300 font-medium",
                                                            children: [
                                                                config.host_capabilities.max_ram,
                                                                " GB"
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 587,
                                                            columnNumber: 25
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 585,
                                                    columnNumber: 23
                                                }, this),
                                                config.host_capabilities.cpu_cores && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "flex justify-between items-center",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-gray-500 text-sm",
                                                            children: "CPU Cores:"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 592,
                                                            columnNumber: 25
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-gray-300 font-medium",
                                                            children: config.host_capabilities.cpu_cores
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 593,
                                                            columnNumber: 25
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 591,
                                                    columnNumber: 23
                                                }, this),
                                                config.host_capabilities.available_gpus && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "flex justify-between items-center",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-gray-500 text-sm",
                                                            children: "Available GPUs:"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 598,
                                                            columnNumber: 25
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-gray-300 font-medium",
                                                            children: config.host_capabilities.available_gpus.join(', ')
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 599,
                                                            columnNumber: 25
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 597,
                                                    columnNumber: 23
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 583,
                                            columnNumber: 19
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                    lineNumber: 581,
                                    columnNumber: 17
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                            lineNumber: 577,
                            columnNumber: 15
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 576,
                        columnNumber: 13
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: `bg-black rounded-lg p-4 overflow-x-auto border border-neutral-800 ${showRawJSON ? '' : 'hidden'}`,
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("pre", {
                            className: "text-xs text-green-400 font-mono whitespace-pre-wrap",
                            children: JSON.stringify(config, null, 2)
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                            lineNumber: 610,
                            columnNumber: 13
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 609,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: `space-y-6 ${showRawJSON ? 'hidden' : ''}`,
                        children: [
                            vramUsage && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "bg-gradient-to-br from-neutral-850/50 to-neutral-900/50 rounded-lg p-8 border border-neutral-700/60 shadow-inner",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "grid md:grid-cols-2 gap-10 items-center",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                                    className: "text-white font-semibold text-base mb-8 uppercase tracking-wider flex items-center gap-2",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                            className: "w-5 h-5 text-[#76b900]",
                                                            fill: "none",
                                                            stroke: "currentColor",
                                                            viewBox: "0 0 24 24",
                                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                                strokeLinecap: "round",
                                                                strokeLinejoin: "round",
                                                                strokeWidth: 2,
                                                                d: "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                lineNumber: 624,
                                                                columnNumber: 27
                                                            }, this)
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 623,
                                                            columnNumber: 25
                                                        }, this),
                                                        "VRAM Utilization Analysis"
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 622,
                                                    columnNumber: 23
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(VRAMUsageChart, {
                                                    usedVRAM: vramUsage.used,
                                                    totalVRAM: vramUsage.total,
                                                    numGPUs: vramUsage.numGPUs
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 628,
                                                    columnNumber: 23
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 621,
                                            columnNumber: 21
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "space-y-4",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "bg-black/20 rounded-lg p-5 border border-neutral-700/40",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h5", {
                                                            className: "text-sm font-medium text-gray-300 mb-3",
                                                            children: "Configuration Summary"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 636,
                                                            columnNumber: 25
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            className: "space-y-2.5 text-sm",
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex justify-between",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-gray-500",
                                                                            children: "Required VRAM:"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 639,
                                                                            columnNumber: 29
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-gray-200 font-medium",
                                                                            children: [
                                                                                vramUsage.used.toFixed(1),
                                                                                " GB"
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 640,
                                                                            columnNumber: 29
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 638,
                                                                    columnNumber: 27
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex justify-between",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-gray-500",
                                                                            children: "GPU Profile:"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 643,
                                                                            columnNumber: 29
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-gray-200 font-medium",
                                                                            children: config.parameters.vgpu_profile || config.parameters.vGPU_profile
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 644,
                                                                            columnNumber: 29
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 642,
                                                                    columnNumber: 27
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex justify-between",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-gray-500",
                                                                            children: "GPUs Required:"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 647,
                                                                            columnNumber: 29
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-gray-200 font-medium",
                                                                            children: vramUsage.numGPUs
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 648,
                                                                            columnNumber: 29
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 646,
                                                                    columnNumber: 27
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex justify-between",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-gray-500",
                                                                            children: "Total Capacity:"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 651,
                                                                            columnNumber: 29
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-[#76b900] font-medium",
                                                                            children: [
                                                                                vramUsage.total.toFixed(0),
                                                                                " GB"
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 652,
                                                                            columnNumber: 29
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 650,
                                                                    columnNumber: 27
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 637,
                                                            columnNumber: 25
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 635,
                                                    columnNumber: 23
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "text-sm text-gray-400 space-y-2",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                            className: "text-xs uppercase tracking-wider font-medium text-gray-500 mb-2",
                                                            children: "Utilization Guidelines"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 657,
                                                            columnNumber: 25
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("ul", {
                                                            className: "space-y-1.5 text-xs",
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                                                    className: "flex items-start gap-2",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-emerald-500 mt-0.5 text-lg",
                                                                            children: "●"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 660,
                                                                            columnNumber: 29
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            children: [
                                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                                                    className: "text-emerald-400",
                                                                                    children: "Comfortable (0-60%):"
                                                                                }, void 0, false, {
                                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                                    lineNumber: 661,
                                                                                    columnNumber: 35
                                                                                }, this),
                                                                                " Ideal for production with room for growth"
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 661,
                                                                            columnNumber: 29
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 659,
                                                                    columnNumber: 27
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                                                    className: "flex items-start gap-2",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-[#76b900] mt-0.5 text-lg",
                                                                            children: "●"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 664,
                                                                            columnNumber: 29
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            children: [
                                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                                                    className: "text-[#a3e635]",
                                                                                    children: "Moderate (60-90%):"
                                                                                }, void 0, false, {
                                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                                    lineNumber: 665,
                                                                                    columnNumber: 35
                                                                                }, this),
                                                                                " Efficient utilization with performance buffer"
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 665,
                                                                            columnNumber: 29
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 663,
                                                                    columnNumber: 27
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                                                    className: "flex items-start gap-2",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-red-500 mt-0.5 text-lg",
                                                                            children: "●"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 668,
                                                                            columnNumber: 29
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            children: [
                                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("strong", {
                                                                                    className: "text-red-400",
                                                                                    children: "Tight (90-100%):"
                                                                                }, void 0, false, {
                                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                                    lineNumber: 669,
                                                                                    columnNumber: 35
                                                                                }, this),
                                                                                " Consider larger GPU profile or additional units"
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 669,
                                                                            columnNumber: 29
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 667,
                                                                    columnNumber: 27
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 658,
                                                            columnNumber: 25
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 656,
                                                    columnNumber: 23
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 634,
                                            columnNumber: 21
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                    lineNumber: 620,
                                    columnNumber: 19
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 619,
                                columnNumber: 17
                            }, this),
                            keyParams.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                        className: "text-white font-medium text-sm mb-4 uppercase tracking-wider",
                                        children: "Key Parameters"
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 681,
                                        columnNumber: 19
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "bg-neutral-850/40 rounded-lg p-4 border border-neutral-700/60",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "grid gap-4 md:grid-cols-2",
                                            children: keyParams.map(([key, value], index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "flex items-center justify-between p-4 rounded-lg bg-neutral-800/70 border border-neutral-700/60 hover:bg-neutral-800 hover:border-[#76b900]/40 transition-all duration-200 group",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            className: "flex items-center gap-3",
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "text-gray-400 group-hover:text-[#76b900]/70 transition-colors",
                                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(ParameterIcon, {
                                                                        type: getIconType(key)
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                        lineNumber: 691,
                                                                        columnNumber: 31
                                                                    }, this)
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 690,
                                                                    columnNumber: 29
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex items-center gap-2",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "font-semibold text-gray-200",
                                                                            children: getParameterLabel(key)
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 694,
                                                                            columnNumber: 31
                                                                        }, this),
                                                                        parameterDefinitions[key] && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Tooltip, {
                                                                            content: parameterDefinitions[key],
                                                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                                                className: "w-4 h-4 text-gray-500 hover:text-gray-400 cursor-help",
                                                                                fill: "none",
                                                                                stroke: "currentColor",
                                                                                viewBox: "0 0 24 24",
                                                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                                                    strokeLinecap: "round",
                                                                                    strokeLinejoin: "round",
                                                                                    strokeWidth: 2,
                                                                                    d: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                                                                }, void 0, false, {
                                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                                    lineNumber: 700,
                                                                                    columnNumber: 37
                                                                                }, this)
                                                                            }, void 0, false, {
                                                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                                lineNumber: 699,
                                                                                columnNumber: 35
                                                                            }, this)
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 698,
                                                                            columnNumber: 33
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 693,
                                                                    columnNumber: 29
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 689,
                                                            columnNumber: 27
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-[#76b900] font-bold text-lg",
                                                            children: formatParameterValue(key, value)
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 706,
                                                            columnNumber: 27
                                                        }, this)
                                                    ]
                                                }, key, true, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 685,
                                                    columnNumber: 25
                                                }, this))
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 683,
                                            columnNumber: 21
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 682,
                                        columnNumber: 19
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 680,
                                columnNumber: 17
                            }, this),
                            advancedParams.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: ()=>setShowAdvancedDetails(!showAdvancedDetails),
                                        className: "flex items-center gap-2 text-gray-400 hover:text-[#76b900]/70 transition-all duration-150 ease-in-out mb-4 group",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                className: `w-4 h-4 transform transition-transform duration-150 ease-in-out ${showAdvancedDetails ? 'rotate-90' : ''}`,
                                                fill: "none",
                                                stroke: "currentColor",
                                                viewBox: "0 0 24 24",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                    strokeLinecap: "round",
                                                    strokeLinejoin: "round",
                                                    strokeWidth: 2,
                                                    d: "M9 5l7 7-7 7"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 724,
                                                    columnNumber: 23
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 723,
                                                columnNumber: 21
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                className: "text-sm font-medium uppercase tracking-wider",
                                                children: "Advanced Details"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 726,
                                                columnNumber: 21
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 719,
                                        columnNumber: 19
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: `transition-all duration-150 ease-in-out overflow-hidden ${showAdvancedDetails ? 'opacity-100 max-h-[2000px]' : 'opacity-0 max-h-0'}`,
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "bg-neutral-850/60 rounded-lg p-4 border border-neutral-700/60",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "grid gap-4 md:grid-cols-2",
                                                children: advancedParams.map(([key, value], index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "group",
                                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            className: "flex items-start gap-3 p-3 rounded-lg bg-neutral-800/60 border border-neutral-700/40 hover:border-[#76b900]/30 hover:bg-neutral-800/80 transition-all duration-200",
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "mt-0.5",
                                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(ParameterIcon, {
                                                                        type: getIconType(key),
                                                                        className: "w-4 h-4 text-gray-500"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                        lineNumber: 739,
                                                                        columnNumber: 33
                                                                    }, this)
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 738,
                                                                    columnNumber: 31
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex-1 min-w-0",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                            className: "flex items-center gap-1.5 mb-1",
                                                                            children: [
                                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                                    className: "text-xs text-gray-400 font-medium uppercase tracking-wider",
                                                                                    children: getParameterLabel(key)
                                                                                }, void 0, false, {
                                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                                    lineNumber: 743,
                                                                                    columnNumber: 35
                                                                                }, this),
                                                                                parameterDefinitions[key] && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Tooltip, {
                                                                                    content: parameterDefinitions[key],
                                                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                                                        className: "w-3 h-3 text-gray-600 hover:text-gray-500 cursor-help",
                                                                                        fill: "none",
                                                                                        stroke: "currentColor",
                                                                                        viewBox: "0 0 24 24",
                                                                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                                                            strokeLinecap: "round",
                                                                                            strokeLinejoin: "round",
                                                                                            strokeWidth: 2,
                                                                                            d: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                                                                        }, void 0, false, {
                                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                                            lineNumber: 749,
                                                                                            columnNumber: 41
                                                                                        }, this)
                                                                                    }, void 0, false, {
                                                                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                                        lineNumber: 748,
                                                                                        columnNumber: 39
                                                                                    }, this)
                                                                                }, void 0, false, {
                                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                                    lineNumber: 747,
                                                                                    columnNumber: 37
                                                                                }, this)
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 742,
                                                                            columnNumber: 33
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-sm font-medium text-gray-200 break-words",
                                                                            children: formatParameterValue(key, value)
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                            lineNumber: 754,
                                                                            columnNumber: 33
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                                    lineNumber: 741,
                                                                    columnNumber: 31
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 737,
                                                            columnNumber: 29
                                                        }, this)
                                                    }, key, false, {
                                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                        lineNumber: 733,
                                                        columnNumber: 27
                                                    }, this))
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 731,
                                                columnNumber: 23
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 730,
                                            columnNumber: 21
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                        lineNumber: 729,
                                        columnNumber: 19
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 718,
                                columnNumber: 17
                            }, this),
                            config.notes && config.notes.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "mt-6 p-4 bg-amber-950/20 border border-amber-900/50 rounded-lg",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex items-start gap-3",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                            className: "w-5 h-5 text-amber-400 mt-0.5 flex-shrink-0",
                                            fill: "none",
                                            stroke: "currentColor",
                                            viewBox: "0 0 24 24",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                strokeLinecap: "round",
                                                strokeLinejoin: "round",
                                                strokeWidth: 2,
                                                d: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 772,
                                                columnNumber: 23
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 771,
                                            columnNumber: 21
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                                    className: "text-amber-300 font-medium text-sm mb-2",
                                                    children: "Recommendations"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 775,
                                                    columnNumber: 23
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("ul", {
                                                    className: "space-y-1",
                                                    children: config.notes.map((note, index)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("li", {
                                                            className: "text-amber-200/80 text-sm",
                                                            children: [
                                                                "• ",
                                                                note
                                                            ]
                                                        }, index, true, {
                                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                            lineNumber: 778,
                                                            columnNumber: 27
                                                        }, this))
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                    lineNumber: 776,
                                                    columnNumber: 23
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 774,
                                            columnNumber: 21
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                    lineNumber: 770,
                                    columnNumber: 19
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 769,
                                columnNumber: 17
                            }, this),
                            !isRelevantConfig && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "mt-4 p-4 bg-yellow-950/20 border border-yellow-900/50 rounded-lg",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex items-center gap-2",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                            className: "w-5 h-5 text-yellow-400",
                                            fill: "none",
                                            stroke: "currentColor",
                                            viewBox: "0 0 24 24",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                strokeLinecap: "round",
                                                strokeLinejoin: "round",
                                                strokeWidth: 2,
                                                d: "M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                                lineNumber: 791,
                                                columnNumber: 23
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 790,
                                            columnNumber: 21
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "text-yellow-300 text-sm",
                                            children: "No specific vGPU configuration was recommended for this query."
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                            lineNumber: 793,
                                            columnNumber: 21
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                    lineNumber: 789,
                                    columnNumber: 19
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                                lineNumber: 788,
                                columnNumber: 17
                            }, this)
                        ]
                    }, void 0, true, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                        lineNumber: 616,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
                lineNumber: 547,
                columnNumber: 9
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/app/components/Chat/VGPUConfigCard.tsx",
        lineNumber: 478,
        columnNumber: 5
    }, this);
}
_s1(VGPUConfigCard, "H4ko9nCZzanO3EeojaaRY/CY6S4=");
_c3 = VGPUConfigCard;
var _c, _c1, _c2, _c3;
__turbopack_context__.k.register(_c, "Tooltip");
__turbopack_context__.k.register(_c1, "ParameterIcon");
__turbopack_context__.k.register(_c2, "VRAMUsageChart");
__turbopack_context__.k.register(_c3, "VGPUConfigCard");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/components/Chat/ApplyConfigurationForm.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "default": (()=>ApplyConfigurationForm)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
// Spinner component
const Spinner = ()=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex items-center justify-center",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "animate-spin rounded-full h-12 w-12 border-b-2 border-green-500"
        }, void 0, false, {
            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
            lineNumber: 23,
            columnNumber: 5
        }, this)
    }, void 0, false, {
        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
        lineNumber: 22,
        columnNumber: 3
    }, this);
_c = Spinner;
function ApplyConfigurationForm({ isOpen, onClose, configuration }) {
    _s();
    const [formData, setFormData] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({
        vmIpAddress: "",
        username: "",
        password: "",
        huggingFaceToken: ""
    });
    const [formErrors, setFormErrors] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({});
    const [showPassword, setShowPassword] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [showToken, setShowToken] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [isSubmitting, setIsSubmitting] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [showLogs, setShowLogs] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [configurationLogs, setConfigurationLogs] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [isConfigurationComplete, setIsConfigurationComplete] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [showDebugLogs, setShowDebugLogs] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [currentDisplayMessage, setCurrentDisplayMessage] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])("");
    // Validate IP address format
    const validateIpAddress = (ip)=>{
        const ipRegex = /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/;
        return ipRegex.test(ip);
    };
    // Validate form fields
    const validateForm = ()=>{
        const errors = {};
        if (!formData.vmIpAddress) {
            errors.vmIpAddress = "VM IP address is required";
        } else if (!validateIpAddress(formData.vmIpAddress)) {
            errors.vmIpAddress = "Invalid IP address format";
        }
        if (!formData.username) {
            errors.username = "Username is required";
        }
        if (!formData.password) {
            errors.password = "Password is required";
        }
        if (!formData.huggingFaceToken) {
            errors.huggingFaceToken = "Hugging Face token is required";
        }
        setFormErrors(errors);
        return Object.keys(errors).length === 0;
    };
    const handleInputChange = (field, value)=>{
        setFormData((prev)=>({
                ...prev,
                [field]: value
            }));
        // Clear error for this field when user starts typing (only for fields that exist in FormErrors)
        if (field in formErrors) {
            setFormErrors((prev)=>({
                    ...prev,
                    [field]: undefined
                }));
        }
    };
    const handleSubmit = async (e)=>{
        e.preventDefault();
        if (!validateForm()) {
            return;
        }
        setIsSubmitting(true);
        setShowLogs(false); // Hide logs initially
        setIsConfigurationComplete(false);
        setConfigurationLogs([
            "Starting configuration process..."
        ]);
        setCurrentDisplayMessage(""); // Initialize with empty string
        try {
            // Extract and normalize the configuration data
            let configData = {};
            if (configuration && configuration.parameters) {
                // The configuration comes from the vGPU generation which has parameters field
                configData = configuration.parameters;
            } else if (configuration) {
                // Direct configuration object
                configData = configuration;
            }
            const response = await fetch("/api/apply-configuration", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    vm_ip: formData.vmIpAddress,
                    username: formData.username,
                    password: formData.password,
                    configuration: configData,
                    hf_token: formData.huggingFaceToken,
                    description: configuration?.description || "vGPU configuration request from UI"
                })
            });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            // Read the streaming response
            const reader = response.body?.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            if (reader) {
                while(true){
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value, {
                        stream: true
                    });
                    buffer += chunk;
                    // Process complete lines
                    const lines = buffer.split("\n");
                    buffer = lines.pop() || ''; // Keep the last incomplete line in buffer
                    for (const line of lines){
                        if (line.startsWith("data: ")) {
                            try {
                                const data = JSON.parse(line.substring(6));
                                // Update display message if present
                                if (data.display_message) {
                                    setCurrentDisplayMessage(data.display_message);
                                }
                                // Update logs based on the progress
                                if (data.message) {
                                    // Split multi-line messages
                                    const messages = data.message.split('\n');
                                    for (const msg of messages){
                                        if (msg.trim()) {
                                            // Strip any timestamps that might be present (format: [HH:MM:SS AM/PM])
                                            const cleanMsg = msg.trim().replace(/^\[\d{1,2}:\d{2}:\d{2}\s*(AM|PM)?\]\s*/i, '');
                                            setConfigurationLogs((prev)=>[
                                                    ...prev,
                                                    cleanMsg
                                                ]);
                                        }
                                    }
                                }
                                // Handle command results
                                if (data.command_results) {
                                    for (const result of data.command_results){
                                        if (result.command) {
                                            setConfigurationLogs((prev)=>[
                                                    ...prev,
                                                    `$ ${result.command}`
                                                ]);
                                            if (result.output) {
                                                setConfigurationLogs((prev)=>[
                                                        ...prev,
                                                        result.output.trim()
                                                    ]);
                                            }
                                            if (result.error && !result.success) {
                                                setConfigurationLogs((prev)=>[
                                                        ...prev,
                                                        `Error: ${result.error}`
                                                    ]);
                                            }
                                        }
                                    }
                                }
                                // Check for completion or error
                                if (data.status === "completed") {
                                    // Don't add another success message, it's already in the logs
                                    setIsConfigurationComplete(true);
                                    setShowLogs(true); // Automatically show logs on completion
                                // Don't clear display message - let the last one persist
                                } else if (data.status === "error") {
                                    setConfigurationLogs((prev)=>[
                                            ...prev,
                                            `❌ Error: ${data.error || "Configuration failed"}`
                                        ]);
                                    setIsConfigurationComplete(true);
                                    setShowLogs(true); // Automatically show logs on error
                                // Don't clear display message - let the last one persist
                                }
                            } catch (parseError) {
                                console.error("Error parsing SSE data:", parseError);
                            }
                        }
                    }
                }
            }
        } catch (error) {
            console.error("Configuration error:", error);
            setConfigurationLogs((prev)=>[
                    ...prev,
                    `❌ Error: ${error instanceof Error ? error.message : "Failed to apply configuration"}`
                ]);
            setIsConfigurationComplete(true);
            setShowLogs(true); // Show logs on error
        // Don't clear display message here either
        } finally{
            setIsSubmitting(false);
        }
    };
    const handleRetry = ()=>{
        // Reset state but keep form data
        setIsConfigurationComplete(false);
        setConfigurationLogs([]);
        setShowLogs(false);
        setShowDebugLogs(false);
        setCurrentDisplayMessage("");
    // Form data is intentionally preserved
    };
    const handleClose = ()=>{
        // Reset form state
        setFormData({
            vmIpAddress: "",
            username: "",
            password: "",
            huggingFaceToken: ""
        });
        setFormErrors({});
        setShowPassword(false);
        setShowToken(false);
        setIsSubmitting(false);
        setShowLogs(false);
        setConfigurationLogs([]);
        setIsConfigurationComplete(false);
        setShowDebugLogs(false);
        setCurrentDisplayMessage("");
        onClose();
    };
    const handleExportLogs = ()=>{
        // Create log content without timestamps for cleaner export
        let logContent = configurationLogs.join('\n');
        // If debug logs are shown, add them to the export
        if (showDebugLogs) {
            const debugSection = "\n\n=== Debug Output ===\n" + configurationLogs.filter((log)=>{
                if (log.includes("===") || log.startsWith("✓")) return false;
                const includePatterns = [
                    "Starting configuration process",
                    "Connecting to",
                    "Connected successfully",
                    "Gathering system information",
                    "Hypervisor Layer",
                    "Checking GPU availability",
                    "GPU:",
                    "Starting setup phase",
                    "Authenticating with",
                    "Setting up Python",
                    "Installing",
                    "Cleaned up",
                    "Attempt",
                    "server started",
                    "Found",
                    "GPU memory detected",
                    "Post-launch cleanup",
                    "SSH connection closed",
                    "PID"
                ];
                return includePatterns.some((pattern)=>log.includes(pattern));
            }).join('\n');
            logContent += debugSection;
        }
        // Add header information
        const header = [
            '=== vGPU Configuration Logs ===',
            `Date: ${new Date().toLocaleString()}`,
            `VM IP: ${formData.vmIpAddress}`,
            `Username: ${formData.username}`,
            configuration?.parameters?.vGPU_profile ? `vGPU Profile: ${configuration.parameters.vGPU_profile}` : '',
            configuration?.parameters?.model_name ? `Model: ${configuration.parameters.model_name}` : '',
            '================================\n'
        ].filter(Boolean).join('\n');
        const fullContent = header + '\n' + logContent;
        // Create blob and download
        const blob = new Blob([
            fullContent
        ], {
            type: 'text/plain'
        });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `vgpu_config_logs_${new Date().toISOString().slice(0, 19).replace(/[:-]/g, '')}.txt`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };
    if (!isOpen) return null;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "bg-neutral-900 rounded-lg border border-neutral-700 w-full max-w-2xl max-h-[90vh] overflow-hidden flex flex-col",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex items-center justify-between p-6 border-b border-neutral-700",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                    className: "text-xl font-semibold text-white",
                                    children: "Apply Configuration"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 351,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                    className: "text-sm text-gray-400 mt-1",
                                    children: "Configure your VM with the recommended vGPU settings"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 352,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                            lineNumber: 350,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                            onClick: handleClose,
                            className: "text-gray-400 hover:text-white transition-colors",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                className: "h-6 w-6",
                                fill: "none",
                                stroke: "currentColor",
                                viewBox: "0 0 24 24",
                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                    strokeLinecap: "round",
                                    strokeLinejoin: "round",
                                    strokeWidth: 2,
                                    d: "M6 18L18 6M6 6l12 12"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 361,
                                    columnNumber: 15
                                }, this)
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                lineNumber: 360,
                                columnNumber: 13
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                            lineNumber: 356,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                    lineNumber: 349,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "flex-1 overflow-y-auto p-6",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("form", {
                            onSubmit: handleSubmit,
                            className: "space-y-6",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                            htmlFor: "vmIpAddress",
                                            className: "block text-sm font-medium text-gray-300 mb-2",
                                            children: "VM IP Address"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 371,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                            id: "vmIpAddress",
                                            type: "text",
                                            value: formData.vmIpAddress,
                                            onChange: (e)=>handleInputChange("vmIpAddress", e.target.value),
                                            placeholder: "Enter the IP address of your Virtual Machine (VM)",
                                            className: `w-full p-3 rounded-lg bg-neutral-800 border ${formErrors.vmIpAddress ? "border-red-500" : "border-neutral-600"} text-white placeholder-gray-500 focus:outline-none focus:border-green-500 transition-colors`
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 374,
                                            columnNumber: 15
                                        }, this),
                                        formErrors.vmIpAddress && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "mt-1 text-sm text-red-500",
                                            children: formErrors.vmIpAddress
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 385,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 370,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                            htmlFor: "username",
                                            className: "block text-sm font-medium text-gray-300 mb-2",
                                            children: "Username"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 391,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                            id: "username",
                                            type: "text",
                                            value: formData.username,
                                            onChange: (e)=>handleInputChange("username", e.target.value),
                                            placeholder: "Enter your VM username",
                                            className: `w-full p-3 rounded-lg bg-neutral-800 border ${formErrors.username ? "border-red-500" : "border-neutral-600"} text-white placeholder-gray-500 focus:outline-none focus:border-green-500 transition-colors`
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 394,
                                            columnNumber: 15
                                        }, this),
                                        formErrors.username && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "mt-1 text-sm text-red-500",
                                            children: formErrors.username
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 405,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 390,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                            htmlFor: "password",
                                            className: "block text-sm font-medium text-gray-300 mb-2",
                                            children: "Password"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 411,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "relative",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                    id: "password",
                                                    type: showPassword ? "text" : "password",
                                                    value: formData.password,
                                                    onChange: (e)=>handleInputChange("password", e.target.value),
                                                    placeholder: "Enter your VM password",
                                                    className: `w-full p-3 pr-12 rounded-lg bg-neutral-800 border ${formErrors.password ? "border-red-500" : "border-neutral-600"} text-white placeholder-gray-500 focus:outline-none focus:border-green-500 transition-colors`
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 415,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                    type: "button",
                                                    onClick: ()=>setShowPassword(!showPassword),
                                                    className: "absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors",
                                                    children: showPassword ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                        className: "h-5 w-5",
                                                        fill: "none",
                                                        stroke: "currentColor",
                                                        viewBox: "0 0 24 24",
                                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                            strokeLinecap: "round",
                                                            strokeLinejoin: "round",
                                                            strokeWidth: 2,
                                                            d: "M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                            lineNumber: 432,
                                                            columnNumber: 23
                                                        }, this)
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                        lineNumber: 431,
                                                        columnNumber: 21
                                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                        className: "h-5 w-5",
                                                        fill: "none",
                                                        stroke: "currentColor",
                                                        viewBox: "0 0 24 24",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                                strokeLinecap: "round",
                                                                strokeLinejoin: "round",
                                                                strokeWidth: 2,
                                                                d: "M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                                lineNumber: 436,
                                                                columnNumber: 23
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                                strokeLinecap: "round",
                                                                strokeLinejoin: "round",
                                                                strokeWidth: 2,
                                                                d: "M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                                lineNumber: 437,
                                                                columnNumber: 23
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                        lineNumber: 435,
                                                        columnNumber: 21
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 425,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 414,
                                            columnNumber: 15
                                        }, this),
                                        formErrors.password && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "mt-1 text-sm text-red-500",
                                            children: formErrors.password
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 443,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 410,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "flex items-center gap-2 mb-2",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                    htmlFor: "huggingFaceToken",
                                                    className: "text-sm font-medium text-gray-300",
                                                    children: "Hugging Face Token"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 450,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "group relative",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                            className: "h-4 w-4 text-gray-400 cursor-help",
                                                            fill: "none",
                                                            stroke: "currentColor",
                                                            viewBox: "0 0 24 24",
                                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                                strokeLinecap: "round",
                                                                strokeLinejoin: "round",
                                                                strokeWidth: 2,
                                                                d: "M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                                lineNumber: 455,
                                                                columnNumber: 21
                                                            }, this)
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                            lineNumber: 454,
                                                            columnNumber: 19
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            className: "absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-neutral-800 border border-neutral-600 rounded-lg text-sm text-gray-300 whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none",
                                                            children: "Used for model downloads from Hugging Face"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                            lineNumber: 457,
                                                            columnNumber: 19
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 453,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 449,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "relative",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                    id: "huggingFaceToken",
                                                    type: showToken ? "text" : "password",
                                                    value: formData.huggingFaceToken,
                                                    onChange: (e)=>handleInputChange("huggingFaceToken", e.target.value),
                                                    placeholder: "Enter your Hugging Face access token",
                                                    className: `w-full p-3 pr-12 rounded-lg bg-neutral-800 border ${formErrors.huggingFaceToken ? "border-red-500" : "border-neutral-600"} text-white placeholder-gray-500 focus:outline-none focus:border-green-500 transition-colors`
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 463,
                                                    columnNumber: 17
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                    type: "button",
                                                    onClick: ()=>setShowToken(!showToken),
                                                    className: "absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-white transition-colors",
                                                    children: showToken ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                        className: "h-5 w-5",
                                                        fill: "none",
                                                        stroke: "currentColor",
                                                        viewBox: "0 0 24 24",
                                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                            strokeLinecap: "round",
                                                            strokeLinejoin: "round",
                                                            strokeWidth: 2,
                                                            d: "M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                            lineNumber: 480,
                                                            columnNumber: 23
                                                        }, this)
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                        lineNumber: 479,
                                                        columnNumber: 21
                                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                        className: "h-5 w-5",
                                                        fill: "none",
                                                        stroke: "currentColor",
                                                        viewBox: "0 0 24 24",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                                strokeLinecap: "round",
                                                                strokeLinejoin: "round",
                                                                strokeWidth: 2,
                                                                d: "M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                                lineNumber: 484,
                                                                columnNumber: 23
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                                strokeLinecap: "round",
                                                                strokeLinejoin: "round",
                                                                strokeWidth: 2,
                                                                d: "M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                                lineNumber: 485,
                                                                columnNumber: 23
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                        lineNumber: 483,
                                                        columnNumber: 21
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 473,
                                                    columnNumber: 17
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 462,
                                            columnNumber: 15
                                        }, this),
                                        formErrors.huggingFaceToken && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "mt-1 text-sm text-red-500",
                                            children: formErrors.huggingFaceToken
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 491,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 448,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    type: "submit",
                                    disabled: isSubmitting,
                                    className: `w-full py-3 px-4 rounded-lg font-medium transition-all ${isSubmitting ? "bg-neutral-700 text-gray-400 cursor-not-allowed" : "bg-green-600 text-white hover:bg-green-700"}`,
                                    children: isSubmitting ? "Applying Configuration..." : isConfigurationComplete ? "Apply Configuration Again" : "Apply Configuration"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 496,
                                    columnNumber: 13
                                }, this),
                                isConfigurationComplete && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "mt-4 flex gap-3",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                            type: "button",
                                            onClick: handleRetry,
                                            className: "flex-1 py-3 px-4 rounded-lg font-medium bg-neutral-700 text-white hover:bg-neutral-600 transition-all",
                                            children: "Clear Logs & Retry"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 515,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                            type: "button",
                                            onClick: handleClose,
                                            className: "flex-1 py-3 px-4 rounded-lg font-medium bg-neutral-800 text-gray-300 hover:bg-neutral-700 transition-all",
                                            children: "Close"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 522,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 514,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                            lineNumber: 368,
                            columnNumber: 11
                        }, this),
                        isSubmitting && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "mt-6 border-t border-neutral-700 pt-6",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                className: "text-center",
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                        className: "text-lg font-medium text-white mb-4",
                                        children: "Applying Configuration"
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                        lineNumber: 537,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(Spinner, {}, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                        lineNumber: 538,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "text-sm text-gray-400 mt-4",
                                        children: "Please wait while we configure your VM..."
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                        lineNumber: 539,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "text-xs text-gray-500 mt-2",
                                        children: "This process typically takes 1-3 minutes"
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                        lineNumber: 542,
                                        columnNumber: 17
                                    }, this),
                                    currentDisplayMessage && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "mt-4 p-3 bg-neutral-800 rounded-lg border border-neutral-600",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-sm text-green-400 font-medium animate-pulse",
                                            children: currentDisplayMessage
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 547,
                                            columnNumber: 21
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                        lineNumber: 546,
                                        columnNumber: 19
                                    }, this),
                                    configurationLogs.length > 0 && !currentDisplayMessage && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                        className: "text-xs text-gray-400 mt-3 italic",
                                        children: configurationLogs[configurationLogs.length - 1]
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                        lineNumber: 553,
                                        columnNumber: 19
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                lineNumber: 536,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                            lineNumber: 535,
                            columnNumber: 13
                        }, this),
                        !isSubmitting && isConfigurationComplete && configurationLogs.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "mt-6 border-t border-neutral-700 pt-6",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex items-center justify-between mb-4",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                            className: "text-lg font-medium text-white",
                                            children: "Configuration Logs"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 565,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "flex items-center gap-2",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                    type: "button",
                                                    onClick: handleExportLogs,
                                                    className: "px-3 py-1 text-sm bg-neutral-700 hover:bg-neutral-600 text-white rounded-lg transition-colors flex items-center gap-2",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                            className: "h-4 w-4",
                                                            fill: "none",
                                                            stroke: "currentColor",
                                                            viewBox: "0 0 24 24",
                                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                                strokeLinecap: "round",
                                                                strokeLinejoin: "round",
                                                                strokeWidth: 2,
                                                                d: "M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                                lineNumber: 573,
                                                                columnNumber: 23
                                                            }, this)
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                            lineNumber: 572,
                                                            columnNumber: 21
                                                        }, this),
                                                        "Export Logs"
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 567,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                    type: "button",
                                                    onClick: ()=>setShowLogs(!showLogs),
                                                    className: "text-gray-400 hover:text-white transition-colors",
                                                    children: showLogs ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                        className: "h-5 w-5",
                                                        fill: "none",
                                                        stroke: "currentColor",
                                                        viewBox: "0 0 24 24",
                                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                            strokeLinecap: "round",
                                                            strokeLinejoin: "round",
                                                            strokeWidth: 2,
                                                            d: "M5 15l7-7 7 7"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                            lineNumber: 584,
                                                            columnNumber: 25
                                                        }, this)
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                        lineNumber: 583,
                                                        columnNumber: 23
                                                    }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                        className: "h-5 w-5",
                                                        fill: "none",
                                                        stroke: "currentColor",
                                                        viewBox: "0 0 24 24",
                                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                            strokeLinecap: "round",
                                                            strokeLinejoin: "round",
                                                            strokeWidth: 2,
                                                            d: "M19 9l-7 7-7-7"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                            lineNumber: 588,
                                                            columnNumber: 25
                                                        }, this)
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                        lineNumber: 587,
                                                        columnNumber: 23
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 577,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 566,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 564,
                                    columnNumber: 15
                                }, this),
                                showLogs && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "bg-black rounded-lg border border-neutral-700 p-4 max-h-64 overflow-y-auto",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "space-y-1 font-mono text-sm",
                                        children: (()=>{
                                            // Separate logs into categories
                                            const summaryLogs = [];
                                            const stepsLogs = [];
                                            const otherLogs = [];
                                            let inSummary = false;
                                            let inSteps = false;
                                            configurationLogs.forEach((log)=>{
                                                if (log.includes("=== Configuration Summary ===")) {
                                                    inSummary = true;
                                                    inSteps = false;
                                                    summaryLogs.push(log);
                                                } else if (log.includes("=== Steps Completed ===")) {
                                                    inSummary = false;
                                                    inSteps = true;
                                                    stepsLogs.push(log);
                                                } else if (inSummary) {
                                                    summaryLogs.push(log);
                                                } else if (inSteps) {
                                                    stepsLogs.push(log);
                                                } else {
                                                    // Filter out redundant messages
                                                    const skipMessages = [
                                                        "✅ Configuration applied successfully!",
                                                        "Configuration applied successfully.",
                                                        "PID .* no GPU usage entry found" // Skip PID messages that show no GPU usage
                                                    ];
                                                    const shouldSkip = skipMessages.some((pattern)=>{
                                                        if (pattern.includes(".*")) {
                                                            return new RegExp(pattern).test(log);
                                                        }
                                                        return log === pattern;
                                                    });
                                                    if (!shouldSkip) {
                                                        otherLogs.push(log);
                                                    }
                                                }
                                            });
                                            // Display summary first, then other logs, then steps
                                            const orderedLogs = [
                                                ...summaryLogs,
                                                ...otherLogs,
                                                ...stepsLogs
                                            ];
                                            // Filter out debug messages from main configuration logs
                                            const debugPatterns = [
                                                "Starting configuration process",
                                                "Connecting to",
                                                "Connected successfully",
                                                "Gathering system information",
                                                "Hypervisor Layer",
                                                "Checking GPU availability",
                                                "GPU:",
                                                "Starting setup phase",
                                                "Authenticating with",
                                                "Setting up Python",
                                                "Installing",
                                                "Cleaned up",
                                                "Attempt",
                                                "server started",
                                                "Found",
                                                "GPU memory detected",
                                                "Post-launch cleanup",
                                                "SSH connection closed"
                                            ];
                                            const filteredLogs = orderedLogs.filter((log)=>{
                                                // Keep summary and steps
                                                if (summaryLogs.includes(log) || stepsLogs.includes(log)) {
                                                    return true;
                                                }
                                                // Exclude debug messages
                                                return !debugPatterns.some((pattern)=>log.includes(pattern));
                                            });
                                            return filteredLogs.map((log, index)=>{
                                                const isSummaryHeader = log.includes("=== Configuration Summary ===") || log.includes("=== Steps Completed ===");
                                                const isStepItem = log.startsWith("✓");
                                                const isSummaryItem = summaryLogs.includes(log) && !isSummaryHeader;
                                                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: `
                              text-gray-300 
                              ${isSummaryHeader ? 'font-bold text-green-400 mt-3 mb-1' : ''} 
                              ${isStepItem ? 'ml-4 text-green-300' : ''}
                              ${isSummaryItem ? 'ml-4' : ''}
                            `,
                                                    children: log
                                                }, index, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 680,
                                                    columnNumber: 27
                                                }, this);
                                            });
                                        })()
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                        lineNumber: 597,
                                        columnNumber: 19
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 596,
                                    columnNumber: 17
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                            lineNumber: 563,
                            columnNumber: 13
                        }, this),
                        !isSubmitting && isConfigurationComplete && configurationLogs.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "mt-4",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex items-center justify-between mb-4",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                            className: "text-lg font-medium text-white",
                                            children: "Debug Output"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 704,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                            type: "button",
                                            onClick: ()=>setShowDebugLogs(!showDebugLogs),
                                            className: "text-gray-400 hover:text-white transition-colors flex items-center gap-2",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                    className: "text-sm",
                                                    children: "Show detailed steps"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 710,
                                                    columnNumber: 19
                                                }, this),
                                                showDebugLogs ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                    className: "h-5 w-5",
                                                    fill: "none",
                                                    stroke: "currentColor",
                                                    viewBox: "0 0 24 24",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                        strokeLinecap: "round",
                                                        strokeLinejoin: "round",
                                                        strokeWidth: 2,
                                                        d: "M5 15l7-7 7 7"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                        lineNumber: 713,
                                                        columnNumber: 23
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 712,
                                                    columnNumber: 21
                                                }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                    className: "h-5 w-5",
                                                    fill: "none",
                                                    stroke: "currentColor",
                                                    viewBox: "0 0 24 24",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                        strokeLinecap: "round",
                                                        strokeLinejoin: "round",
                                                        strokeWidth: 2,
                                                        d: "M19 9l-7 7-7-7"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                        lineNumber: 717,
                                                        columnNumber: 23
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 716,
                                                    columnNumber: 21
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                            lineNumber: 705,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 703,
                                    columnNumber: 15
                                }, this),
                                showDebugLogs && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "bg-black rounded-lg border border-neutral-700 p-4 max-h-64 overflow-y-auto",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "space-y-1 font-mono text-xs",
                                        children: (()=>{
                                            // Filter logs to show only intermediate/debug steps
                                            const debugLogs = configurationLogs.filter((log)=>{
                                                // Exclude summary sections
                                                if (log.includes("===") || log.startsWith("✓")) return false;
                                                // Include these types of messages
                                                const includePatterns = [
                                                    "Starting configuration process",
                                                    "Connecting to",
                                                    "Connected successfully",
                                                    "Gathering system information",
                                                    "Hypervisor Layer",
                                                    "Checking GPU availability",
                                                    "GPU:",
                                                    "Starting setup phase",
                                                    "Authenticating with",
                                                    "Setting up Python",
                                                    "Installing",
                                                    "Cleaned up",
                                                    "Attempt",
                                                    "server started",
                                                    "Found",
                                                    "GPU memory detected",
                                                    "Post-launch cleanup",
                                                    "SSH connection closed",
                                                    "PID"
                                                ];
                                                return includePatterns.some((pattern)=>log.includes(pattern));
                                            });
                                            return debugLogs.map((log, index)=>{
                                                // Color code different types of messages
                                                let className = "text-gray-400";
                                                if (log.includes("Error") || log.includes("failed")) {
                                                    className = "text-red-400";
                                                } else if (log.includes("successfully") || log.includes("✓")) {
                                                    className = "text-green-400";
                                                } else if (log.includes("Attempt") || log.includes("GPU memory")) {
                                                    className = "text-yellow-400";
                                                } else if (log.includes("Connecting") || log.includes("Starting")) {
                                                    className = "text-blue-400";
                                                }
                                                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: className,
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-gray-600",
                                                            children: "$"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                            lineNumber: 774,
                                                            columnNumber: 29
                                                        }, this),
                                                        " ",
                                                        log
                                                    ]
                                                }, index, true, {
                                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                                    lineNumber: 773,
                                                    columnNumber: 27
                                                }, this);
                                            });
                                        })()
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                        lineNumber: 725,
                                        columnNumber: 19
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                                    lineNumber: 724,
                                    columnNumber: 17
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                            lineNumber: 702,
                            columnNumber: 13
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
                    lineNumber: 367,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
            lineNumber: 347,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/src/app/components/Chat/ApplyConfigurationForm.tsx",
        lineNumber: 346,
        columnNumber: 5
    }, this);
}
_s(ApplyConfigurationForm, "VEHOBhrCQ4grdYxoJFBfLx7rYFU=");
_c1 = ApplyConfigurationForm;
var _c, _c1;
__turbopack_context__.k.register(_c, "Spinner");
__turbopack_context__.k.register(_c1, "ApplyConfigurationForm");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/components/Chat/VGPUConfigDrawer.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "default": (()=>VGPUConfigDrawer)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$VGPUConfigCard$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/components/Chat/VGPUConfigCard.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$ApplyConfigurationForm$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/components/Chat/ApplyConfigurationForm.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
function VGPUConfigDrawer({ config, isOpen, onClose }) {
    _s();
    const [isFullScreen, setIsFullScreen] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [isApplyFormOpen, setIsApplyFormOpen] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    // Close drawer on escape key
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "VGPUConfigDrawer.useEffect": ()=>{
            const handleEscape = {
                "VGPUConfigDrawer.useEffect.handleEscape": (e)=>{
                    if (e.key === "Escape" && isOpen) {
                        onClose();
                    }
                }
            }["VGPUConfigDrawer.useEffect.handleEscape"];
            document.addEventListener("keydown", handleEscape);
            return ({
                "VGPUConfigDrawer.useEffect": ()=>document.removeEventListener("keydown", handleEscape)
            })["VGPUConfigDrawer.useEffect"];
        }
    }["VGPUConfigDrawer.useEffect"], [
        isOpen,
        onClose
    ]);
    // Prevent body scroll when drawer is open
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "VGPUConfigDrawer.useEffect": ()=>{
            if (isOpen) {
                document.body.style.overflow = "hidden";
            } else {
                document.body.style.overflow = "unset";
            }
            return ({
                "VGPUConfigDrawer.useEffect": ()=>{
                    document.body.style.overflow = "unset";
                }
            })["VGPUConfigDrawer.useEffect"];
        }
    }["VGPUConfigDrawer.useEffect"], [
        isOpen
    ]);
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: `fixed inset-0 bg-black/50 backdrop-blur-sm transition-opacity duration-300 z-40 ${isOpen ? "opacity-100" : "opacity-0 pointer-events-none"}`,
                onClick: onClose
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                lineNumber: 58,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: `fixed inset-y-0 right-0 z-50 bg-neutral-950 shadow-2xl transition-all duration-300 ease-in-out ${isOpen ? "translate-x-0" : "translate-x-full"} ${isFullScreen ? "w-full" : "w-full md:w-[600px] lg:w-[700px] xl:w-[800px]"}`,
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "sticky top-0 z-10 bg-gradient-to-r from-[#76b900] to-[#5a8c00] px-6 py-4",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center justify-between",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex items-center gap-3",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                            className: "text-lg font-semibold text-white",
                                            children: "vGPU Configuration Details"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                            lineNumber: 77,
                                            columnNumber: 15
                                        }, this),
                                        isFullScreen && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "text-sm text-green-100 opacity-75",
                                            children: "Full Screen Mode"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                            lineNumber: 79,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                    lineNumber: 76,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex items-center gap-2",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                            onClick: ()=>setIsFullScreen(!isFullScreen),
                                            className: "p-2 hover:bg-white/10 rounded transition-colors group",
                                            title: isFullScreen ? "Exit full screen" : "Enter full screen",
                                            children: isFullScreen ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                className: "w-5 h-5 text-white group-hover:text-green-100",
                                                fill: "none",
                                                stroke: "currentColor",
                                                viewBox: "0 0 24 24",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                    strokeLinecap: "round",
                                                    strokeLinejoin: "round",
                                                    strokeWidth: 2,
                                                    d: "M6 18L18 6M6 6l12 12"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                                    lineNumber: 91,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                                lineNumber: 90,
                                                columnNumber: 19
                                            }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                className: "w-5 h-5 text-white group-hover:text-green-100",
                                                fill: "none",
                                                stroke: "currentColor",
                                                viewBox: "0 0 24 24",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                    strokeLinecap: "round",
                                                    strokeLinejoin: "round",
                                                    strokeWidth: 2,
                                                    d: "M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                                    lineNumber: 95,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                                lineNumber: 94,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                            lineNumber: 84,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                            onClick: onClose,
                                            className: "p-2 hover:bg-white/10 rounded transition-colors group",
                                            title: "Close drawer",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                className: "w-5 h-5 text-white group-hover:text-green-100",
                                                fill: "none",
                                                stroke: "currentColor",
                                                viewBox: "0 0 24 24",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                    strokeLinecap: "round",
                                                    strokeLinejoin: "round",
                                                    strokeWidth: 2,
                                                    d: "M6 18L18 6M6 6l12 12"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                                    lineNumber: 106,
                                                    columnNumber: 19
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                                lineNumber: 105,
                                                columnNumber: 17
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                            lineNumber: 100,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                    lineNumber: 82,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                            lineNumber: 75,
                            columnNumber: 11
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                        lineNumber: 74,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "h-full overflow-y-auto pb-20",
                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: `p-6 ${isFullScreen ? "max-w-6xl mx-auto" : ""}`,
                            children: [
                                config && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$VGPUConfigCard$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                                    config: config
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                    lineNumber: 116,
                                    columnNumber: 24
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "mt-6 flex flex-wrap gap-3",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                        onClick: ()=>setIsApplyFormOpen(true),
                                        className: "px-4 py-2 bg-[#76b900] hover:bg-[#5a8c00] text-white rounded-lg font-medium transition-colors",
                                        children: "Verify Configuration"
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                        lineNumber: 120,
                                        columnNumber: 15
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                                    lineNumber: 119,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                            lineNumber: 115,
                            columnNumber: 11
                        }, this)
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                        lineNumber: 114,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                lineNumber: 66,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$ApplyConfigurationForm$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                isOpen: isApplyFormOpen,
                onClose: ()=>setIsApplyFormOpen(false),
                configuration: config
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/VGPUConfigDrawer.tsx",
                lineNumber: 135,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true);
}
_s(VGPUConfigDrawer, "x1KdKob+lXQWv3k4/jRUi1qHVPw=");
_c = VGPUConfigDrawer;
var _c;
__turbopack_context__.k.register(_c, "VGPUConfigDrawer");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/components/Chat/WorkloadConfigWizard.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "default": (()=>WorkloadConfigWizard)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
function WorkloadConfigWizard({ isOpen, onClose, onSubmit }) {
    _s();
    const [config, setConfig] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({
        workloadType: "",
        specificModel: "",
        modelSize: "",
        batchSize: "",
        promptSize: "1024",
        responseSize: "256",
        embeddingModel: "",
        gpuInventory: {},
        precision: "",
        vectorDimension: "384",
        numberOfVectors: "10000",
        advancedConfig: {
            modelMemoryOverhead: 1.3,
            hypervisorReserveGb: 3.0,
            cudaMemoryOverhead: 1.2,
            vcpuPerGpu: 8,
            ramGbPerVcpu: 8
        }
    });
    const [currentStep, setCurrentStep] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(1);
    const totalSteps = 3;
    const [dynamicModels, setDynamicModels] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [isLoadingModels, setIsLoadingModels] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(true);
    const [showAdvancedConfig, setShowAdvancedConfig] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    // Fetch dynamic models from backend on mount
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "WorkloadConfigWizard.useEffect": ()=>{
            const fetchModels = {
                "WorkloadConfigWizard.useEffect.fetchModels": async ()=>{
                    try {
                        // Use Next.js API route to avoid CORS issues
                        const response = await fetch('/api/available-models');
                        if (response.ok) {
                            const data = await response.json();
                            if (data.models && data.models.length > 0) {
                                // Use modelTag as value to ensure uniqueness (full model ID like "org/model-name")
                                const formattedModels = data.models.map({
                                    "WorkloadConfigWizard.useEffect.fetchModels.formattedModels": (model)=>({
                                            value: model.modelTag.toLowerCase().replace(/\//g, '-').replace(/\./g, '-'),
                                            label: model.label,
                                            modelTag: model.modelTag
                                        })
                                }["WorkloadConfigWizard.useEffect.fetchModels.formattedModels"]);
                                setDynamicModels(formattedModels);
                                console.log(`✓ Successfully loaded ${formattedModels.length} models from HuggingFace`);
                            } else {
                                console.warn('No models returned from API');
                            }
                        } else {
                            console.warn('API returned non-OK status:', response.status);
                        }
                    } catch (error) {
                        console.error('Failed to fetch dynamic models:', error);
                        console.log('Using fallback model list');
                    // Fallback to hardcoded models will be used
                    } finally{
                        setIsLoadingModels(false);
                    }
                }
            }["WorkloadConfigWizard.useEffect.fetchModels"];
            if (isOpen) {
                fetchModels();
            }
        }
    }["WorkloadConfigWizard.useEffect"], [
        isOpen
    ]);
    const workloadTypes = [
        {
            value: "rag",
            label: "RAG (Retrieval-Augmented Generation)",
            desc: "Document search and generation workflows"
        },
        {
            value: "inference",
            label: "LLM Inference",
            desc: "Running predictions and serving trained models"
        }
    ];
    const modelSizes = [
        {
            value: "small",
            label: "Small (< 7B parameters)",
            desc: "Lightweight models, fast inference"
        },
        {
            value: "medium",
            label: "Medium (7B-30B parameters)",
            desc: "Balanced performance and speed"
        },
        {
            value: "large",
            label: "Large (40B-70B parameters)",
            desc: "High-quality results, more compute"
        },
        {
            value: "xlarge",
            label: "Extra Large (70B+ parameters)",
            desc: "Heavy compute, stronger reasoning models"
        }
    ];
    const embeddingModels = [
        {
            value: "nvidia/nvolveqa-embed-large-1B",
            label: "nvidia/nvolveqa-embed-large-1B",
            desc: "1B parameter embedding model"
        },
        {
            value: "text-embedding-ada-002-350M",
            label: "text-embedding-ada-002-350M",
            desc: "350M parameter OpenAI embedding model"
        },
        {
            value: "nvidia/nvolveqa-embed-base-400M",
            label: "nvidia/nvolveqa-embed-base-400M",
            desc: "400M parameter embedding model"
        },
        {
            value: "nvidia/nemo-embed-qa-200M",
            label: "nvidia/nemo-embed-qa-200M",
            desc: "200M parameter QA embedding model"
        },
        {
            value: "all-MiniLM-L6-v2-80M",
            label: "all-MiniLM-L6-v2-80M",
            desc: "80M parameter compact embedding model"
        },
        {
            value: "llama-3-2-nv-embedqa-1b-v2",
            label: "llama-3-2-nv-embedqa-1b-v2",
            desc: "Llama 3.2 based embedding model"
        }
    ];
    const performanceLevels = [
        {
            value: "basic",
            label: "Basic",
            desc: "Cost-optimized, adequate performance"
        },
        {
            value: "standard",
            label: "Standard",
            desc: "Good balance of cost and performance"
        },
        {
            value: "high",
            label: "High Performance",
            desc: "Optimized for speed and throughput"
        },
        {
            value: "maximum",
            label: "Maximum",
            desc: "Best possible performance, premium cost"
        }
    ];
    const availableGPUInventory = [
        {
            value: "l40s",
            label: "NVIDIA L40S",
            desc: "48GB GDDR6 with ECC, Ada Lovelace, 350W - ML training & inference + virtual workstations"
        },
        {
            value: "l40",
            label: "NVIDIA L40",
            desc: "48GB GDDR6 with ECC, Ada Lovelace - Virtual workstations & compute workloads"
        },
        {
            value: "l4",
            label: "NVIDIA L4",
            desc: "24GB GDDR6 with ECC, Ada Lovelace, 72W - AI inference, small model training & 3D graphics"
        },
        {
            value: "a40",
            label: "NVIDIA A40",
            desc: "48GB GDDR6 with ECC, Ampere, 300W - 3D design & mixed virtual workstation workloads"
        },
        {
            value: "DC",
            label: "NVIDIA RTX PRO 6000 Blackwell Server Edition (Refer as DC)",
            desc: "96GB GDDR7 with ECC, Blackwell, passive‑cooled dual‑slot PCIe Gen5 – Enterprise AI/graphics, scientific computing & virtual workstations"
        }
    ];
    // Fallback hardcoded models in case dynamic fetch fails
    const fallbackModels = [
        {
            value: "llama-3-8b",
            label: "Llama-3-8B",
            modelTag: "meta-llama/Meta-Llama-3-8B-Instruct"
        },
        {
            value: "llama-3-70b",
            label: "Llama-3-70B",
            modelTag: "meta-llama/Meta-Llama-3-70B-Instruct"
        },
        {
            value: "llama-3.1-8b",
            label: "Llama-3.1-8B",
            modelTag: "meta-llama/Llama-3.1-8B-Instruct"
        },
        {
            value: "llama-3.1-70b",
            label: "Llama-3.1-70B",
            modelTag: "meta-llama/Llama-3.3-70B-Instruct"
        },
        {
            value: "mistral-7b",
            label: "Mistral-7B",
            modelTag: "mistralai/Mistral-7B-Instruct-v0.3"
        },
        {
            value: "falcon-7b",
            label: "Falcon-7B",
            modelTag: "tiiuae/falcon-7b-instruct"
        },
        {
            value: "falcon-40b",
            label: "Falcon-40B",
            modelTag: "tiiuae/falcon-40b-instruct"
        },
        {
            value: "falcon-180b",
            label: "Falcon-180B",
            modelTag: "tiiuae/falcon-180B"
        },
        {
            value: "qwen-14b",
            label: "Qwen-14B",
            modelTag: "Qwen/Qwen3-14B"
        }
    ];
    // Use dynamic models if loaded, otherwise use fallback
    const specificModels = dynamicModels.length > 0 ? dynamicModels : fallbackModels;
    const precisionOptions = [
        {
            value: "fp16",
            label: "FP16",
            desc: "Half precision - Recommended balance of performance and accuracy"
        },
        {
            value: "int8",
            label: "INT-8",
            desc: "8-bit integer - Highest performance, some accuracy trade-off"
        }
    ];
    const handleInputChange = (field, value)=>{
        setConfig((prev)=>({
                ...prev,
                [field]: value
            }));
    };
    const handleAdvancedConfigChange = (field, value)=>{
        setConfig((prev)=>({
                ...prev,
                advancedConfig: {
                    ...prev.advancedConfig,
                    [field]: value
                }
            }));
    };
    const handleGPUInventoryChange = (gpuType, quantity)=>{
        setConfig((prev)=>{
            const newInventory = {
                ...prev.gpuInventory
            };
            if (quantity <= 0) {
                delete newInventory[gpuType];
            } else {
                newInventory[gpuType] = quantity;
            }
            return {
                ...prev,
                gpuInventory: newInventory
            };
        });
    };
    const getTotalGPUs = ()=>{
        return Object.values(config.gpuInventory).reduce((sum, count)=>{
            return sum + count;
        }, 0);
    };
    const getRecommendedEmbeddingModel = ()=>{
        // First check for specific model recommendations
        if (config.specificModel && config.specificModel !== 'unknown') {
            if (config.specificModel.includes('llama-3')) {
                return 'llama-3-2-nv-embedqa-1b-v2';
            }
            if (config.specificModel.includes('mistral')) {
                return 'nvidia/nemo-embed-qa-200M';
            }
            if (config.specificModel.includes('falcon-180b')) {
                return 'nvidia/nvolveqa-embed-large-1B';
            }
            if (config.specificModel.includes('falcon-40b')) {
                return 'nvidia/nvolveqa-embed-base-400M';
            }
            if (config.specificModel.includes('falcon-7b')) {
                return 'all-MiniLM-L6-v2-80M';
            }
            if (config.specificModel.includes('qwen')) {
                return 'text-embedding-ada-002-350M';
            }
        }
        // Fall back to model size category recommendations
        if (config.modelSize) {
            switch(config.modelSize){
                case 'small':
                    return 'all-MiniLM-L6-v2-80M';
                case 'medium':
                    return 'nvidia/nvolveqa-embed-base-400M';
                case 'large':
                    return 'nvidia/nvolveqa-embed-large-1B';
                case 'xlarge':
                    return 'llama-3-2-nv-embedqa-1b-v2';
                default:
                    return 'nvidia/nvolveqa-embed-large-1B';
            }
        }
        // Default recommendation
        return 'nvidia/nvolveqa-embed-large-1B';
    };
    const generateQuery = ()=>{
        const parts = [];
        // Base query structure
        parts.push(`I need a vGPU configuration for`);
        // Workload type
        if (config.workloadType) {
            const workloadLabel = workloadTypes.find((w)=>w.value === config.workloadType)?.label || config.workloadType;
            parts.push(`${workloadLabel.trim()}`);
        }
        // Model size
        if (config.modelSize) {
            const sizeLabel = modelSizes.find((s)=>s.value === config.modelSize)?.label || config.modelSize;
            parts.push(`with ${sizeLabel.toLowerCase()}`);
        }
        // GPU Inventory - Enhanced with specific quantities
        if (config.gpuInventory && Object.keys(config.gpuInventory).length > 0) {
            const gpuLabels = Object.entries(config.gpuInventory).filter(([_, quantity])=>quantity > 0).map(([gpu, quantity])=>{
                const gpuInfo = availableGPUInventory.find((g)=>g.value === gpu);
                return `${quantity}x ${gpuInfo?.label || gpu}`;
            });
            parts.push(`using available GPU inventory: ${gpuLabels.join(', ')}`);
        } else {
            // Recommended GPU (L40S) if no GPU is selected
            parts.push(`using available GPU inventory: 1x NVIDIA L40S`);
        }
        // Specific Model
        if (config.specificModel && config.specificModel !== 'unknown') {
            const modelLabel = specificModels.find((m)=>m.value === config.specificModel)?.label || config.specificModel;
            parts.push(`running ${modelLabel}`);
        }
        // Performance requirements
        if (config.workloadType === 'rag' && config.embeddingModel) {
            const modelLabel = embeddingModels.find((m)=>m.value === config.embeddingModel)?.label || config.embeddingModel;
            parts.push(`using embedding model ${modelLabel}`);
        } else if (config.workloadType === 'rag') {
            // Use recommended embedding model based on selection
            const recommendedModel = getRecommendedEmbeddingModel();
            const modelLabel = embeddingModels.find((m)=>m.value === recommendedModel)?.label || recommendedModel;
            parts.push(`using embedding model ${modelLabel}`);
        }
        // Performance requirements
        const requirements = [];
        if (config.promptSize) {
            requirements.push(`prompt size of ${config.promptSize} tokens`);
        }
        if (config.responseSize) {
            requirements.push(`response size of ${config.responseSize} tokens`);
        }
        if (config.batchSize) {
            requirements.push(`batch size of ${config.batchSize}`);
        }
        if (requirements.length > 0) {
            parts.push(`with ${requirements.join(', ')}`);
        }
        // Precision
        if (config.precision) {
            const precisionLabel = precisionOptions.find((p)=>p.value === config.precision)?.label || config.precision;
            parts.push(`with ${precisionLabel} precision`);
        } else {
            // Recommended precision
            parts.push(`with FP16 precision`);
        }
        // Add retrieval configuration for RAG workloads
        if (config.workloadType === 'rag' && (config.vectorDimension || config.numberOfVectors)) {
            const retrievalParts = [];
            if (config.vectorDimension) {
                retrievalParts.push(`${config.vectorDimension}d vectors`);
            }
            if (config.numberOfVectors) {
                retrievalParts.push(`${config.numberOfVectors} total vectors`);
            }
            if (retrievalParts.length > 0) {
                parts.push(`with retrieval configuration: ${retrievalParts.join(', ')}`);
            }
        }
        const naturalLanguageQuery = parts.join(' ') + '.';
        // EMBED THE STRUCTURED CONFIG DATA AS JSON
        // This preserves all the original user selections
        const structuredConfig = {
            workloadType: config.workloadType,
            specificModel: config.specificModel,
            modelTag: config.specificModel ? specificModels.find((m)=>m.value === config.specificModel)?.modelTag : null,
            modelSize: config.modelSize,
            batchSize: config.batchSize,
            promptSize: config.promptSize ? parseInt(config.promptSize) : 1024,
            responseSize: config.responseSize ? parseInt(config.responseSize) : 256,
            embeddingModel: config.workloadType === 'rag' ? config.embeddingModel || getRecommendedEmbeddingModel() : null,
            gpuInventory: config.gpuInventory,
            precision: config.precision || 'fp16',
            // Add retrieval config for RAG
            ...config.workloadType === 'rag' && {
                vectorDimension: config.vectorDimension ? parseInt(config.vectorDimension) : null,
                numberOfVectors: config.numberOfVectors ? parseInt(config.numberOfVectors) : null
            },
            // Add computed values for easier backend processing
            selectedGPU: Object.keys(config.gpuInventory)[0] || 'l40s',
            gpuCount: Object.values(config.gpuInventory)[0] || 1,
            // Include advanced configuration
            advancedConfig: config.advancedConfig
        };
        // Embed as HTML comment that won't be visible to user but can be parsed in backend
        return naturalLanguageQuery + `\n<!--VGPU_CONFIG:${JSON.stringify(structuredConfig)}-->`;
    };
    const handleSubmit = ()=>{
        const query = generateQuery();
        onSubmit(query);
        onClose();
        // Reset form
        setConfig({
            workloadType: "",
            specificModel: "",
            modelSize: "",
            batchSize: "",
            promptSize: "1024",
            responseSize: "256",
            embeddingModel: "",
            gpuInventory: {},
            precision: "",
            vectorDimension: "384",
            numberOfVectors: "10000",
            advancedConfig: {
                modelMemoryOverhead: 1.3,
                hypervisorReserveGb: 3.0,
                cudaMemoryOverhead: 1.2,
                vcpuPerGpu: 8,
                ramGbPerVcpu: 8
            }
        });
        setCurrentStep(1);
    };
    const canProceed = ()=>{
        switch(currentStep){
            case 1:
                return config.workloadType !== "";
            case 2:
                // If "unknown" is selected, user must also select a model size
                if (config.specificModel === 'unknown') {
                    return config.modelSize !== '';
                }
                // Otherwise, just need a specific model selected
                return config.specificModel !== '';
            case 3:
                return true; // Additional requirements are optional
            default:
                return false;
        }
    };
    if (!isOpen) return null;
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50",
        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "bg-neutral-900 rounded-lg border border-neutral-700 w-full max-w-2xl max-h-[90vh] overflow-y-auto",
            children: [
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "bg-gradient-to-r from-green-600 to-green-700 text-white p-6 rounded-t-lg",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center justify-between",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h2", {
                                            className: "text-xl font-bold",
                                            children: "AI Workload Configuration Wizard"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 426,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-green-100 text-sm mt-1",
                                            children: "Configure your AI workload to get personalized vGPU recommendations"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 427,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 425,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    onClick: onClose,
                                    className: "text-white hover:text-green-200 text-xl",
                                    children: "✕"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 431,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                            lineNumber: 424,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "mt-4",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex items-center justify-between text-sm",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            children: [
                                                "Step ",
                                                currentStep,
                                                " of ",
                                                totalSteps
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 442,
                                            columnNumber: 15
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            children: [
                                                Math.round(currentStep / totalSteps * 100),
                                                "% Complete"
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 443,
                                            columnNumber: 15
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 441,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "w-full bg-green-800 rounded-full h-2 mt-2",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "bg-white rounded-full h-2 transition-all duration-300",
                                        style: {
                                            width: `${currentStep / totalSteps * 100}%`
                                        }
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                        lineNumber: 446,
                                        columnNumber: 15
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 445,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                            lineNumber: 440,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                    lineNumber: 423,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "p-6",
                    children: [
                        currentStep === 1 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "space-y-6",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                        className: "text-lg font-semibold text-white mb-4",
                                        children: "What type of AI workload do you need?"
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                        lineNumber: 460,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "grid grid-cols-1 md:grid-cols-2 gap-3",
                                        children: workloadTypes.map((type)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                onClick: ()=>handleInputChange("workloadType", type.value),
                                                className: `p-4 rounded-lg border text-left transition-all ${config.workloadType === type.value ? "border-green-500 bg-green-900/20 text-white" : "border-neutral-600 bg-neutral-800 text-gray-300 hover:border-green-600"}`,
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "font-medium",
                                                        children: type.label
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 472,
                                                        columnNumber: 23
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "text-sm text-gray-400 mt-1",
                                                        children: type.desc
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 473,
                                                        columnNumber: 23
                                                    }, this)
                                                ]
                                            }, type.value, true, {
                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                lineNumber: 463,
                                                columnNumber: 21
                                            }, this))
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                        lineNumber: 461,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                lineNumber: 459,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                            lineNumber: 458,
                            columnNumber: 13
                        }, this),
                        currentStep === 2 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "space-y-6",
                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                children: [
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                        className: "text-lg font-semibold text-white mb-4",
                                        children: "Model Size & Performance"
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                        lineNumber: 485,
                                        columnNumber: 17
                                    }, this),
                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "space-y-4",
                                        children: [
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                        className: "block text-sm font-medium text-gray-300 mb-2",
                                                        children: [
                                                            "Specific Model (if known)",
                                                            isLoadingModels && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                className: "ml-2 text-sm text-green-500 animate-pulse",
                                                                children: "Loading models..."
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                lineNumber: 490,
                                                                columnNumber: 43
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 488,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                        value: config.specificModel,
                                                        onChange: (e)=>handleInputChange("specificModel", e.target.value),
                                                        className: "w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white mb-4",
                                                        disabled: isLoadingModels,
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: "",
                                                                disabled: true,
                                                                children: isLoadingModels ? "Loading models from HuggingFace..." : "Select a specific model"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                lineNumber: 498,
                                                                columnNumber: 23
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: "unknown",
                                                                children: "Unknown / Not Sure"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                lineNumber: 501,
                                                                columnNumber: 23
                                                            }, this),
                                                            specificModels.map((model)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                    value: model.value,
                                                                    children: model.label
                                                                }, model.value, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 503,
                                                                    columnNumber: 25
                                                                }, this))
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 492,
                                                        columnNumber: 21
                                                    }, this),
                                                    !isLoadingModels && dynamicModels.length > 0 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                        className: "text-xs text-green-500 mb-2",
                                                        children: [
                                                            "✓ ",
                                                            dynamicModels.length,
                                                            " models loaded from HuggingFace"
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 507,
                                                        columnNumber: 23
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                lineNumber: 487,
                                                columnNumber: 19
                                            }, this),
                                            config.specificModel === 'unknown' && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                        className: "block text-sm font-medium text-gray-300 mb-2",
                                                        children: "Model Size Category"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 514,
                                                        columnNumber: 23
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "grid grid-cols-1 md:grid-cols-2 gap-3",
                                                        children: modelSizes.map((size)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                                onClick: ()=>handleInputChange("modelSize", size.value),
                                                                className: `p-3 rounded-lg border text-left transition-all ${config.modelSize === size.value ? "border-green-500 bg-green-900/20 text-white" : "border-neutral-600 bg-neutral-800 text-gray-300 hover:border-green-600"}`,
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                        className: "font-medium",
                                                                        children: size.label
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                        lineNumber: 526,
                                                                        columnNumber: 29
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                        className: "text-sm text-gray-400",
                                                                        children: size.desc
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                        lineNumber: 527,
                                                                        columnNumber: 29
                                                                    }, this)
                                                                ]
                                                            }, size.value, true, {
                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                lineNumber: 517,
                                                                columnNumber: 27
                                                            }, this))
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 515,
                                                        columnNumber: 23
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                lineNumber: 513,
                                                columnNumber: 21
                                            }, this),
                                            config.workloadType === 'rag' && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                        className: "block text-sm font-medium text-gray-300 mb-2",
                                                        children: "Embedding Model"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 537,
                                                        columnNumber: 23
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                        value: config.embeddingModel,
                                                        onChange: (e)=>handleInputChange("embeddingModel", e.target.value),
                                                        className: "w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: "",
                                                                children: [
                                                                    "Recommended (",
                                                                    getRecommendedEmbeddingModel(),
                                                                    ")"
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                lineNumber: 543,
                                                                columnNumber: 25
                                                            }, this),
                                                            embeddingModels.map((model)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                    value: model.value,
                                                                    children: model.label
                                                                }, model.value, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 545,
                                                                    columnNumber: 27
                                                                }, this))
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 538,
                                                        columnNumber: 23
                                                    }, this),
                                                    config.embeddingModel && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                        className: "text-sm text-gray-400 mt-2",
                                                        children: embeddingModels.find((m)=>m.value === config.embeddingModel)?.desc
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 549,
                                                        columnNumber: 25
                                                    }, this),
                                                    !config.embeddingModel && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                        className: "text-sm text-gray-400 mt-2",
                                                        children: embeddingModels.find((m)=>m.value === getRecommendedEmbeddingModel())?.desc
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 554,
                                                        columnNumber: 25
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                lineNumber: 536,
                                                columnNumber: 21
                                            }, this),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "mt-6 grid grid-cols-1 md:grid-cols-2 gap-4",
                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                            className: "block text-sm font-medium text-gray-300 mb-2",
                                                            children: "Precision"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 563,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                            value: config.precision,
                                                            onChange: (e)=>handleInputChange("precision", e.target.value),
                                                            className: "w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white",
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                    value: "",
                                                                    children: "Recommended (FP16)"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 569,
                                                                    columnNumber: 25
                                                                }, this),
                                                                precisionOptions.map((option)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                        value: option.value,
                                                                        children: option.label
                                                                    }, option.value, false, {
                                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                        lineNumber: 571,
                                                                        columnNumber: 27
                                                                    }, this))
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 564,
                                                            columnNumber: 23
                                                        }, this),
                                                        config.precision && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                            className: "text-sm text-gray-400 mt-2",
                                                            children: precisionOptions.find((p)=>p.value === config.precision)?.desc
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 575,
                                                            columnNumber: 25
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 562,
                                                    columnNumber: 21
                                                }, this)
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                lineNumber: 561,
                                                columnNumber: 19
                                            }, this),
                                            config.workloadType === 'rag' && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                className: "mt-6 pt-6 border-t border-neutral-700",
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                                        className: "text-md font-semibold text-white mb-4",
                                                        children: "Retrieval Configuration"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 585,
                                                        columnNumber: 23
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                        className: "text-sm text-gray-400 mb-4",
                                                        children: "Configure vector database settings for RAG retrieval"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 586,
                                                        columnNumber: 23
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: "grid grid-cols-1 md:grid-cols-2 gap-4",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                                        className: "block text-sm font-medium text-gray-300 mb-2",
                                                                        children: "Vector Dimension"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                        lineNumber: 592,
                                                                        columnNumber: 27
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                                        value: config.vectorDimension || "",
                                                                        onChange: (e)=>handleInputChange("vectorDimension", e.target.value),
                                                                        className: "w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white",
                                                                        children: [
                                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                                value: "",
                                                                                children: "Select dimension"
                                                                            }, void 0, false, {
                                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                                lineNumber: 598,
                                                                                columnNumber: 29
                                                                            }, this),
                                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                                value: "384",
                                                                                children: "384 (Compact)"
                                                                            }, void 0, false, {
                                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                                lineNumber: 599,
                                                                                columnNumber: 29
                                                                            }, this),
                                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                                value: "768",
                                                                                children: "768 (Standard)"
                                                                            }, void 0, false, {
                                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                                lineNumber: 600,
                                                                                columnNumber: 29
                                                                            }, this),
                                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                                value: "1024",
                                                                                children: "1024 (Large)"
                                                                            }, void 0, false, {
                                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                                lineNumber: 601,
                                                                                columnNumber: 29
                                                                            }, this)
                                                                        ]
                                                                    }, void 0, true, {
                                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                        lineNumber: 593,
                                                                        columnNumber: 27
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                                        className: "text-sm text-gray-400 mt-1",
                                                                        children: "Must match your embedding model's output dimension"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                        lineNumber: 603,
                                                                        columnNumber: 27
                                                                    }, this)
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                lineNumber: 591,
                                                                columnNumber: 25
                                                            }, this),
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                children: [
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                                        className: "block text-sm font-medium text-gray-300 mb-2",
                                                                        children: "Number of Vectors"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                        lineNumber: 609,
                                                                        columnNumber: 27
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                                        type: "number",
                                                                        value: config.numberOfVectors || "",
                                                                        onChange: (e)=>handleInputChange("numberOfVectors", e.target.value),
                                                                        placeholder: "e.g., 1000000",
                                                                        min: "1000",
                                                                        step: "1000",
                                                                        className: "w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white placeholder-gray-500"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                        lineNumber: 610,
                                                                        columnNumber: 27
                                                                    }, this),
                                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                                        className: "text-sm text-gray-400 mt-1",
                                                                        children: "Total vectors in your knowledge base"
                                                                    }, void 0, false, {
                                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                        lineNumber: 619,
                                                                        columnNumber: 27
                                                                    }, this)
                                                                ]
                                                            }, void 0, true, {
                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                lineNumber: 608,
                                                                columnNumber: 25
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 590,
                                                        columnNumber: 23
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                lineNumber: 584,
                                                columnNumber: 21
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                        lineNumber: 486,
                                        columnNumber: 17
                                    }, this)
                                ]
                            }, void 0, true, {
                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                lineNumber: 484,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                            lineNumber: 483,
                            columnNumber: 13
                        }, this),
                        currentStep === 3 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "space-y-6",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                    className: "text-lg font-semibold text-white mb-4",
                                    children: "Additional Requirements (Optional)"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 634,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "grid grid-cols-1 md:grid-cols-2 gap-4",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                    className: "block text-sm font-medium text-gray-300 mb-2",
                                                    children: "Prompt Size (tokens)"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 638,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                    type: "number",
                                                    value: config.promptSize,
                                                    onChange: (e)=>handleInputChange("promptSize", e.target.value),
                                                    placeholder: "e.g., 1024",
                                                    min: "256",
                                                    max: "32768",
                                                    step: "256",
                                                    className: "w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white placeholder-gray-500"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 639,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                    className: "text-sm text-gray-400 mt-1",
                                                    children: "Maximum input prompt length in tokens"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 649,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 637,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                    className: "block text-sm font-medium text-gray-300 mb-2",
                                                    children: "Response Size (tokens)"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 655,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                    type: "number",
                                                    value: config.responseSize,
                                                    onChange: (e)=>handleInputChange("responseSize", e.target.value),
                                                    placeholder: "e.g., 256",
                                                    min: "128",
                                                    max: "8192",
                                                    step: "128",
                                                    className: "w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white placeholder-gray-500"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 656,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                    className: "text-sm text-gray-400 mt-1",
                                                    children: "Maximum response length in tokens"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 666,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 654,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 636,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "mt-6 pt-6 border-t border-neutral-700",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h4", {
                                            className: "text-md font-semibold text-white mb-4",
                                            children: "GPU Selection"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 674,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                            className: "text-sm text-gray-400 mb-4",
                                            children: "Select the GPU you want to use. If you don't select a GPU, the recommended NVIDIA L40S will be used."
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 675,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "grid grid-cols-1 md:grid-cols-2 gap-4",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                children: [
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                        className: "block text-sm font-medium text-gray-300 mb-2",
                                                        children: "GPU Model"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 681,
                                                        columnNumber: 21
                                                    }, this),
                                                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("select", {
                                                        value: Object.keys(config.gpuInventory)[0] || "",
                                                        onChange: (e)=>{
                                                            // Clear existing inventory and set the new one
                                                            setConfig((prev)=>({
                                                                    ...prev,
                                                                    gpuInventory: e.target.value ? {
                                                                        [e.target.value]: 1
                                                                    } : {}
                                                                }));
                                                        },
                                                        className: "w-full p-3 rounded-lg bg-neutral-800 border border-neutral-600 text-white",
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                value: "",
                                                                children: "Recommended (NVIDIA L40S)"
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                lineNumber: 693,
                                                                columnNumber: 23
                                                            }, this),
                                                            availableGPUInventory.map((gpu)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("option", {
                                                                    value: gpu.value,
                                                                    children: gpu.label
                                                                }, gpu.value, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 695,
                                                                    columnNumber: 25
                                                                }, this))
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 682,
                                                        columnNumber: 21
                                                    }, this)
                                                ]
                                            }, void 0, true, {
                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                lineNumber: 680,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 679,
                                            columnNumber: 17
                                        }, this),
                                        Object.keys(config.gpuInventory)[0] && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "mt-3 p-3 bg-neutral-800 border border-neutral-600 rounded-lg",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                className: "text-sm text-gray-400",
                                                children: availableGPUInventory.find((g)=>g.value === Object.keys(config.gpuInventory)[0])?.desc
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                lineNumber: 706,
                                                columnNumber: 21
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 705,
                                            columnNumber: 19
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 673,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "mt-6 pt-6 border-t border-neutral-700",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                            type: "button",
                                            onClick: ()=>setShowAdvancedConfig(!showAdvancedConfig),
                                            className: "w-full flex items-center justify-between p-4 bg-neutral-800 hover:bg-neutral-750 rounded-lg transition-colors",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "flex items-center gap-2",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-md font-semibold text-white",
                                                            children: "Advanced Configuration"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 721,
                                                            columnNumber: 21
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                            className: "text-xs text-gray-400 bg-neutral-700 px-2 py-1 rounded",
                                                            children: "Optional"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 722,
                                                            columnNumber: 21
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 720,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                    className: `w-5 h-5 text-gray-400 transition-transform ${showAdvancedConfig ? 'rotate-180' : ''}`,
                                                    fill: "none",
                                                    stroke: "currentColor",
                                                    viewBox: "0 0 24 24",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                        strokeLinecap: "round",
                                                        strokeLinejoin: "round",
                                                        strokeWidth: 2,
                                                        d: "M19 9l-7 7-7-7"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                        lineNumber: 730,
                                                        columnNumber: 21
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 724,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 715,
                                            columnNumber: 17
                                        }, this),
                                        showAdvancedConfig && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                            className: "mt-4 p-4 bg-neutral-800 rounded-lg border border-neutral-700",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                    className: "text-sm text-gray-400 mb-6",
                                                    children: "Fine-tune calculator accuracy with advanced parameters. The defaults are suitable for most use cases."
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 736,
                                                    columnNumber: 21
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: "space-y-6",
                                                    children: [
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex justify-between items-center mb-2",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                                            className: "text-sm font-medium text-gray-300",
                                                                            children: "Model Memory Overhead"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 744,
                                                                            columnNumber: 27
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-sm text-green-500 font-mono",
                                                                            children: [
                                                                                config.advancedConfig.modelMemoryOverhead.toFixed(2),
                                                                                "x"
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 747,
                                                                            columnNumber: 27
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 743,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                                    type: "range",
                                                                    min: "1.0",
                                                                    max: "2.0",
                                                                    step: "0.1",
                                                                    value: config.advancedConfig.modelMemoryOverhead,
                                                                    onChange: (e)=>handleAdvancedConfigChange("modelMemoryOverhead", parseFloat(e.target.value)),
                                                                    className: "w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 751,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                                    className: "text-xs text-gray-400 mt-1",
                                                                    children: "Multiplier for model weight memory footprint (1.0-2.0)"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 762,
                                                                    columnNumber: 25
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 742,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex justify-between items-center mb-2",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                                            className: "text-sm font-medium text-gray-300",
                                                                            children: "Hypervisor Reserve (GB)"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 770,
                                                                            columnNumber: 27
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-sm text-green-500 font-mono",
                                                                            children: [
                                                                                config.advancedConfig.hypervisorReserveGb.toFixed(1),
                                                                                " GB"
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 773,
                                                                            columnNumber: 27
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 769,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                                    type: "range",
                                                                    min: "0.0",
                                                                    max: "10.0",
                                                                    step: "0.5",
                                                                    value: config.advancedConfig.hypervisorReserveGb,
                                                                    onChange: (e)=>handleAdvancedConfigChange("hypervisorReserveGb", parseFloat(e.target.value)),
                                                                    className: "w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 777,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                                    className: "text-xs text-gray-400 mt-1",
                                                                    children: "GPU memory reserved for hypervisor layer (0.0-10.0 GB)"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 788,
                                                                    columnNumber: 25
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 768,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex justify-between items-center mb-2",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                                            className: "text-sm font-medium text-gray-300",
                                                                            children: "CUDA Memory Overhead"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 796,
                                                                            columnNumber: 27
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-sm text-green-500 font-mono",
                                                                            children: [
                                                                                config.advancedConfig.cudaMemoryOverhead.toFixed(2),
                                                                                "x"
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 799,
                                                                            columnNumber: 27
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 795,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                                    type: "range",
                                                                    min: "1.0",
                                                                    max: "1.5",
                                                                    step: "0.05",
                                                                    value: config.advancedConfig.cudaMemoryOverhead,
                                                                    onChange: (e)=>handleAdvancedConfigChange("cudaMemoryOverhead", parseFloat(e.target.value)),
                                                                    className: "w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 803,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                                    className: "text-xs text-gray-400 mt-1",
                                                                    children: "CUDA runtime memory overhead multiplier (1.0-1.5)"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 814,
                                                                    columnNumber: 25
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 794,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex justify-between items-center mb-2",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                                            className: "text-sm font-medium text-gray-300",
                                                                            children: "vCPUs per GPU"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 822,
                                                                            columnNumber: 27
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-sm text-green-500 font-mono",
                                                                            children: config.advancedConfig.vcpuPerGpu
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 825,
                                                                            columnNumber: 27
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 821,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                                    type: "range",
                                                                    min: "1",
                                                                    max: "32",
                                                                    step: "1",
                                                                    value: config.advancedConfig.vcpuPerGpu,
                                                                    onChange: (e)=>handleAdvancedConfigChange("vcpuPerGpu", parseInt(e.target.value)),
                                                                    className: "w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 829,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                                    className: "text-xs text-gray-400 mt-1",
                                                                    children: "Number of vCPUs to allocate per GPU (1-32)"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 840,
                                                                    columnNumber: 25
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 820,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                            children: [
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                    className: "flex justify-between items-center mb-2",
                                                                    children: [
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("label", {
                                                                            className: "text-sm font-medium text-gray-300",
                                                                            children: "RAM per vCPU (GB)"
                                                                        }, void 0, false, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 848,
                                                                            columnNumber: 27
                                                                        }, this),
                                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                                            className: "text-sm text-green-500 font-mono",
                                                                            children: [
                                                                                config.advancedConfig.ramGbPerVcpu,
                                                                                " GB"
                                                                            ]
                                                                        }, void 0, true, {
                                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                            lineNumber: 851,
                                                                            columnNumber: 27
                                                                        }, this)
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 847,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("input", {
                                                                    type: "range",
                                                                    min: "2",
                                                                    max: "32",
                                                                    step: "1",
                                                                    value: config.advancedConfig.ramGbPerVcpu,
                                                                    onChange: (e)=>handleAdvancedConfigChange("ramGbPerVcpu", parseInt(e.target.value)),
                                                                    className: "w-full h-2 bg-neutral-700 rounded-lg appearance-none cursor-pointer"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 855,
                                                                    columnNumber: 25
                                                                }, this),
                                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                                                                    className: "text-xs text-gray-400 mt-1",
                                                                    children: "GB of system RAM to allocate per vCPU (2-32 GB)"
                                                                }, void 0, false, {
                                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                                    lineNumber: 866,
                                                                    columnNumber: 25
                                                                }, this)
                                                            ]
                                                        }, void 0, true, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 846,
                                                            columnNumber: 23
                                                        }, this),
                                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                            type: "button",
                                                            onClick: ()=>setConfig((prev)=>({
                                                                        ...prev,
                                                                        advancedConfig: {
                                                                            modelMemoryOverhead: 1.3,
                                                                            hypervisorReserveGb: 3.0,
                                                                            cudaMemoryOverhead: 1.2,
                                                                            vcpuPerGpu: 8,
                                                                            ramGbPerVcpu: 8
                                                                        }
                                                                    })),
                                                            className: "w-full px-4 py-2 bg-neutral-700 text-white rounded-lg hover:bg-neutral-600 transition-colors",
                                                            children: "Reset to Defaults"
                                                        }, void 0, false, {
                                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                            lineNumber: 872,
                                                            columnNumber: 23
                                                        }, this)
                                                    ]
                                                }, void 0, true, {
                                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                                    lineNumber: 740,
                                                    columnNumber: 21
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                            lineNumber: 735,
                                            columnNumber: 19
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 714,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                            lineNumber: 633,
                            columnNumber: 13
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                    lineNumber: 455,
                    columnNumber: 9
                }, this),
                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "p-6 border-t border-neutral-700 flex justify-between",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex space-x-3",
                            children: currentStep > 1 && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                onClick: ()=>setCurrentStep(currentStep - 1),
                                className: "px-4 py-2 bg-neutral-700 text-white rounded-lg hover:bg-neutral-600 transition-colors",
                                children: "← Previous"
                            }, void 0, false, {
                                fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                lineNumber: 902,
                                columnNumber: 15
                            }, this)
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                            lineNumber: 900,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex space-x-3",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    onClick: onClose,
                                    className: "px-4 py-2 bg-neutral-700 text-white rounded-lg hover:bg-neutral-600 transition-colors",
                                    children: "Cancel"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 912,
                                    columnNumber: 13
                                }, this),
                                currentStep < totalSteps ? /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    onClick: ()=>setCurrentStep(currentStep + 1),
                                    disabled: !canProceed(),
                                    className: `px-4 py-2 rounded-lg transition-colors ${canProceed() ? "bg-green-600 text-white hover:bg-green-700" : "bg-neutral-600 text-gray-400 cursor-not-allowed"}`,
                                    children: "Next →"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 920,
                                    columnNumber: 15
                                }, this) : /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                    onClick: handleSubmit,
                                    className: "px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors font-medium",
                                    children: "Get Recommendations"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                                    lineNumber: 932,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                            lineNumber: 911,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
                    lineNumber: 899,
                    columnNumber: 9
                }, this)
            ]
        }, void 0, true, {
            fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
            lineNumber: 421,
            columnNumber: 7
        }, this)
    }, void 0, false, {
        fileName: "[project]/src/app/components/Chat/WorkloadConfigWizard.tsx",
        lineNumber: 420,
        columnNumber: 5
    }, this);
}
_s(WorkloadConfigWizard, "xY6eYMAjGuvrxeubN7PhRy1mWFA=");
_c = WorkloadConfigWizard;
var _c;
__turbopack_context__.k.register(_c, "WorkloadConfigWizard");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/hooks/useChatStream.ts [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "useChatStream": (()=>useChatStream)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var _s = __turbopack_context__.k.signature();
;
const useChatStream = ()=>{
    _s();
    const [streamState, setStreamState] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])({
        content: "",
        citations: [],
        error: null,
        isTyping: false
    });
    const [abortController, setAbortController] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(new AbortController());
    const resetAbortController = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "useChatStream.useCallback[resetAbortController]": ()=>{
            const controller = new AbortController();
            setAbortController(controller);
            return controller;
        }
    }["useChatStream.useCallback[resetAbortController]"], []);
    const stopStream = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "useChatStream.useCallback[stopStream]": ()=>{
            abortController.abort();
            setStreamState({
                "useChatStream.useCallback[stopStream]": (prev)=>({
                        ...prev,
                        isTyping: false
                    })
            }["useChatStream.useCallback[stopStream]"]);
        }
    }["useChatStream.useCallback[stopStream]"], [
        abortController
    ]);
    const processStream = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "useChatStream.useCallback[processStream]": async (response, assistantMessageId, setMessages, confidenceScoreThreshold)=>{
            const reader = response.body?.getReader();
            if (!reader) throw new Error("No response body");
            const decoder = new TextDecoder();
            let buffer = "";
            let content = "";
            let latestCitations = [];
            // Log the threshold we're using for debugging
            console.log(`Starting stream with confidence threshold: ${confidenceScoreThreshold}, type: ${typeof confidenceScoreThreshold}`);
            try {
                while(true){
                    const { done, value } = await reader.read();
                    if (done) break;
                    const chunk = decoder.decode(value);
                    buffer += chunk;
                    const lines = buffer.split("\n");
                    buffer = lines.pop() || "";
                    for (const line of lines){
                        if (line.trim() === "" || !line.startsWith("data: ")) continue;
                        try {
                            const data = JSON.parse(line.slice(5));
                            console.log("Stream data type:", typeof data, "structure:", Object.keys(data).join(", "));
                            if (data.choices?.[0]?.message?.content?.includes("Error from rag server")) {
                                throw new Error("RAG server error");
                            }
                            // Handle delta content
                            const deltaContent = data.choices?.[0]?.delta?.content;
                            if (deltaContent) {
                                content += deltaContent;
                            }
                            // Check for citations in different possible locations in the response
                            let citationsData = null;
                            // Try to find citations data in various possible locations
                            if (data.citations?.results) {
                                citationsData = data.citations.results;
                            } else if (data.sources?.results) {
                                citationsData = data.sources.results;
                            } else if (Array.isArray(data.citations)) {
                                citationsData = data.citations;
                            } else if (Array.isArray(data.sources)) {
                                citationsData = data.sources;
                            } else if (data.choices?.[0]?.message?.citations) {
                                citationsData = Array.isArray(data.choices[0].message.citations) ? data.choices[0].message.citations : data.choices[0].message.citations.results || [];
                            } else if (data.choices?.[0]?.message?.sources) {
                                citationsData = Array.isArray(data.choices[0].message.sources) ? data.choices[0].message.sources : data.choices[0].message.sources.results || [];
                            }
                            // Update citations with filtering based on confidence score
                            if (citationsData && citationsData.length > 0) {
                                // Map the sources to our Citation type, preserving the score
                                const sourcesWithScores = citationsData.map({
                                    "useChatStream.useCallback[processStream].sourcesWithScores": (source)=>{
                                        // Get score from different possible locations
                                        const score = source.score !== undefined ? source.score : source.confidence_score !== undefined ? source.confidence_score : source.similarity_score !== undefined ? source.similarity_score : source.relevance_score !== undefined ? source.relevance_score : undefined;
                                        const sourceTitle = source.document_name || source.source || source.title || source.filename || "Unknown source";
                                        console.log(`Source "${sourceTitle}" has score: ${score}`);
                                        return {
                                            text: source.content || source.text || source.snippet || "",
                                            source: sourceTitle,
                                            document_type: source.document_type || "text",
                                            score: score
                                        };
                                    }
                                }["useChatStream.useCallback[processStream].sourcesWithScores"]);
                                console.log("All citation scores:", sourcesWithScores.map({
                                    "useChatStream.useCallback[processStream]": (c)=>`${c.source}: ${c.score !== undefined ? c.score : 'N/A'}`
                                }["useChatStream.useCallback[processStream]"]).join(', '));
                                // Only apply filtering if threshold is provided and valid
                                const validThreshold = confidenceScoreThreshold !== undefined && !isNaN(parseFloat(String(confidenceScoreThreshold)));
                                if (validThreshold) {
                                    // Parse the threshold as a number
                                    let normalizedThreshold = parseFloat(String(confidenceScoreThreshold));
                                    // Ensure threshold is within 0-1 range (UI now uses the same 0-1 scale as the API)
                                    normalizedThreshold = Math.max(0, Math.min(1, normalizedThreshold));
                                    console.log(`Using threshold: ${normalizedThreshold} (original: ${confidenceScoreThreshold})`);
                                    latestCitations = sourcesWithScores.filter({
                                        "useChatStream.useCallback[processStream]": (citation)=>{
                                            // If score is undefined, include the citation (don't filter it out)
                                            if (citation.score === undefined) {
                                                console.log(`Citation "${citation.source}" has no score, including it anyway`);
                                                return true;
                                            }
                                            // Ensure score is a number
                                            const score = typeof citation.score === 'string' ? parseFloat(citation.score) : citation.score;
                                            // Both citation scores from API and UI threshold are on a 0-1 scale
                                            // so we can compare them directly
                                            const passesThreshold = score >= normalizedThreshold;
                                            console.log(`Citation "${citation.source}" with score ${score} passes threshold ${normalizedThreshold}? ${passesThreshold}`);
                                            return passesThreshold;
                                        }
                                    }["useChatStream.useCallback[processStream]"]);
                                } else {
                                    console.log("No valid confidence threshold set, including all citations");
                                    latestCitations = sourcesWithScores;
                                }
                                console.log(`Filtered citations: ${latestCitations.length} / ${sourcesWithScores.length} with threshold ${confidenceScoreThreshold}`);
                                console.log("Remaining citations:", latestCitations.map({
                                    "useChatStream.useCallback[processStream]": (c)=>c.source
                                }["useChatStream.useCallback[processStream]"]).join(', '));
                            }
                            // Update message state
                            setMessages({
                                "useChatStream.useCallback[processStream]": (prev)=>prev.map({
                                        "useChatStream.useCallback[processStream]": (msg)=>msg.id === assistantMessageId ? {
                                                ...msg,
                                                content,
                                                citations: latestCitations.length > 0 ? latestCitations : msg.citations
                                            } : msg
                                    }["useChatStream.useCallback[processStream]"])
                            }["useChatStream.useCallback[processStream]"]);
                            // Handle stream completion
                            if (data.choices?.[0]?.finish_reason === "stop") {
                                setStreamState({
                                    "useChatStream.useCallback[processStream]": (prev)=>({
                                            ...prev,
                                            content,
                                            citations: latestCitations,
                                            isTyping: false
                                        })
                                }["useChatStream.useCallback[processStream]"]);
                                break;
                            }
                        } catch (parseError) {
                            console.error("Error parsing stream data:", parseError);
                            if (!(parseError instanceof SyntaxError)) {
                                throw parseError;
                            }
                        }
                    }
                }
            } catch (error) {
                console.error("Stream processing error:", error);
                setStreamState({
                    "useChatStream.useCallback[processStream]": (prev)=>({
                            ...prev,
                            error: "Sorry, there was an error processing your request.",
                            isTyping: false
                        })
                }["useChatStream.useCallback[processStream]"]);
                throw error;
            } finally{
                reader.releaseLock();
            }
        }
    }["useChatStream.useCallback[processStream]"], []);
    const startStream = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "useChatStream.useCallback[startStream]": ()=>{
            const controller = resetAbortController();
            setStreamState({
                "useChatStream.useCallback[startStream]": (prev)=>({
                        ...prev,
                        isTyping: true,
                        error: null
                    })
            }["useChatStream.useCallback[startStream]"]);
            return controller;
        }
    }["useChatStream.useCallback[startStream]"], [
        resetAbortController
    ]);
    const resetStream = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useCallback"])({
        "useChatStream.useCallback[resetStream]": ()=>{
            setStreamState({
                content: "",
                citations: [],
                error: null,
                isTyping: false
            });
        }
    }["useChatStream.useCallback[resetStream]"], []);
    return {
        streamState,
        processStream,
        startStream,
        resetStream,
        stopStream,
        isStreaming: streamState.isTyping
    };
};
_s(useChatStream, "6iDk92HevmCGtz1peSfYAoxUCgs=");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/components/Chat/Chat.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "default": (()=>Chat)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/index.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$RightSidebar$2f$RightSidebar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/components/RightSidebar/RightSidebar.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$VGPUConfigDrawer$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/components/Chat/VGPUConfigDrawer.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$WorkloadConfigWizard$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/components/Chat/WorkloadConfigWizard.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$uuid$2f$dist$2f$esm$2d$browser$2f$v4$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__v4$3e$__ = __turbopack_context__.i("[project]/node_modules/uuid/dist/esm-browser/v4.js [app-client] (ecmascript) <export default as v4>");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$marked$2f$lib$2f$marked$2e$esm$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/marked/lib/marked.esm.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$hooks$2f$useChatStream$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/hooks/useChatStream.ts [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SettingsContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/context/SettingsContext.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SidebarContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/context/SidebarContext.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
;
;
;
;
;
;
function Chat() {
    _s();
    const { activePanel, toggleSidebar, setActiveCitations } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SidebarContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useSidebar"])();
    const [messages, setMessages] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])([]);
    const [isWizardOpen, setIsWizardOpen] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const [drawerConfig, setDrawerConfig] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(null);
    const [isDrawerOpen, setIsDrawerOpen] = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useState"])(false);
    const { streamState, processStream, startStream, resetStream, stopStream } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$hooks$2f$useChatStream$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useChatStream"])();
    const { temperature, topP, vdbTopK, rerankerTopK, confidenceScoreThreshold, useGuardrails, includeCitations } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SettingsContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useSettings"])();
    const messagesEndRef = (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useRef"])(null);
    const handleToggleSidebar = (panel, citations)=>{
        if (panel === "citations" && citations) {
            setActiveCitations(citations);
            if (!activePanel || activePanel !== "citations") {
                toggleSidebar(panel);
            }
        } else {
            toggleSidebar(panel);
        }
    };
    const scrollToBottom = ()=>{
        messagesEndRef.current?.scrollIntoView({
            behavior: "smooth"
        });
    };
    (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$index$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useEffect"])({
        "Chat.useEffect": ()=>{
            scrollToBottom();
        }
    }["Chat.useEffect"], [
        messages
    ]);
    const handleSubmit = async (message)=>{
        if (!message.trim()) return;
        resetStream();
        const controller = startStream();
        const userMessage = createUserMessage(message);
        const assistantMessage = createAssistantMessage();
        setMessages((prev)=>[
                ...prev,
                userMessage,
                assistantMessage
            ]);
        // Debug confidence score threshold being used
        console.log(`Submitting with confidence threshold: ${confidenceScoreThreshold} (value type: ${typeof confidenceScoreThreshold})`);
        try {
            const response = await fetch("/api/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(createRequestBody(userMessage)),
                signal: controller.signal
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            await processStream(response, assistantMessage.id, setMessages, confidenceScoreThreshold);
        } catch (error) {
            if (error instanceof Error && error.name === "AbortError") {
                console.log("Stream aborted");
                return;
            }
            console.error("Error generating response:", error);
            handleError(assistantMessage.id);
        }
    };
    const isVGPUConfig = (content)=>{
        try {
            const parsed = JSON.parse(content.trim());
            return parsed.title === "generate_vgpu_config" && parsed.parameters;
        } catch  {
            return false;
        }
    };
    const renderMessageContent = (content, isTyping)=>{
        if (isTyping) {
            return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center space-x-3",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                        className: "animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-[#76b900]"
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/Chat.tsx",
                        lineNumber: 127,
                        columnNumber: 11
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-gray-400",
                        children: "Generating configuration..."
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Chat/Chat.tsx",
                        lineNumber: 128,
                        columnNumber: 11
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/components/Chat/Chat.tsx",
                lineNumber: 126,
                columnNumber: 9
            }, this);
        }
        // Check if content is a vGPU configuration JSON
        if (isVGPUConfig(content)) {
            try {
                const vgpuConfig = JSON.parse(content.trim());
                // Return a preview card that opens the drawer
                return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "bg-neutral-800 border border-[#76b900]/30 rounded-lg p-4 cursor-pointer hover:bg-neutral-750 hover:border-[#76b900]/50 transition-all duration-200",
                    onClick: ()=>{
                        setDrawerConfig(vgpuConfig);
                        setIsDrawerOpen(true);
                    },
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center justify-between mb-3",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex items-center gap-2",
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                            className: "w-5 h-5 text-[#76b900]",
                                            fill: "none",
                                            stroke: "currentColor",
                                            viewBox: "0 0 24 24",
                                            children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                strokeLinecap: "round",
                                                strokeLinejoin: "round",
                                                strokeWidth: 2,
                                                d: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                lineNumber: 149,
                                                columnNumber: 19
                                            }, this)
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                            lineNumber: 148,
                                            columnNumber: 17
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("h3", {
                                            className: "text-white font-semibold",
                                            children: "vGPU Configuration Ready"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                            lineNumber: 151,
                                            columnNumber: 17
                                        }, this)
                                    ]
                                }, void 0, true, {
                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                    lineNumber: 147,
                                    columnNumber: 15
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-xs text-gray-400",
                                    children: "Click to view details →"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                    lineNumber: 153,
                                    columnNumber: 15
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                            lineNumber: 146,
                            columnNumber: 13
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("p", {
                            className: "text-sm text-gray-300 mb-3",
                            children: vgpuConfig.description
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                            lineNumber: 155,
                            columnNumber: 13
                        }, this),
                        (vgpuConfig.parameters.vgpu_profile || vgpuConfig.parameters.vGPU_profile) && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex items-center gap-4 text-sm",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-gray-400",
                                    children: "Profile:"
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                    lineNumber: 158,
                                    columnNumber: 17
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                    className: "text-[#76b900] font-medium",
                                    children: vgpuConfig.parameters.vgpu_profile || vgpuConfig.parameters.vGPU_profile
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                    lineNumber: 159,
                                    columnNumber: 17
                                }, this),
                                vgpuConfig.parameters.gpu_memory_size && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["Fragment"], {
                                    children: [
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "text-gray-400",
                                            children: "•"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                            lineNumber: 162,
                                            columnNumber: 21
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "text-gray-400",
                                            children: "Memory:"
                                        }, void 0, false, {
                                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                            lineNumber: 163,
                                            columnNumber: 21
                                        }, this),
                                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                            className: "text-[#76b900] font-medium",
                                            children: [
                                                vgpuConfig.parameters.gpu_memory_size,
                                                " GB"
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                            lineNumber: 164,
                                            columnNumber: 21
                                        }, this)
                                    ]
                                }, void 0, true)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                            lineNumber: 157,
                            columnNumber: 15
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                    lineNumber: 139,
                    columnNumber: 11
                }, this);
            } catch (error) {
                console.error("Error parsing vGPU config:", error);
            // Fall back to regular markdown rendering
            }
        }
        return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
            className: "prose prose-invert max-w-none text-sm",
            dangerouslySetInnerHTML: {
                __html: __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$marked$2f$lib$2f$marked$2e$esm$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["marked"].parse(content, {
                    async: false,
                    breaks: true,
                    gfm: true
                })
            }
        }, void 0, false, {
            fileName: "[project]/src/app/components/Chat/Chat.tsx",
            lineNumber: 178,
            columnNumber: 7
        }, this);
    };
    const createUserMessage = (content)=>({
            id: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$uuid$2f$dist$2f$esm$2d$browser$2f$v4$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__v4$3e$__["v4"])(),
            role: "user",
            content,
            timestamp: new Date().toISOString()
        });
    const createAssistantMessage = ()=>({
            id: (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$uuid$2f$dist$2f$esm$2d$browser$2f$v4$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__$3c$export__default__as__v4$3e$__["v4"])(),
            role: "assistant",
            content: "",
            timestamp: new Date().toISOString()
        });
    const createRequestBody = (userMessage)=>{
        // Create base request body - always use the vGPU knowledge base
        const requestBody = {
            messages: messages.concat(userMessage).map((msg)=>({
                    role: msg.role,
                    content: msg.content
                })),
            collection_name: "vgpu_knowledge_base",
            temperature,
            top_p: topP,
            reranker_top_k: rerankerTopK,
            vdb_top_k: vdbTopK,
            confidence_threshold: confidenceScoreThreshold,
            use_knowledge_base: true,
            enable_citations: includeCitations,
            enable_guardrails: useGuardrails
        };
        // Only include model parameters if the environment variables are set
        if (__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_MODEL_NAME) {
            requestBody.model = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_MODEL_NAME;
        }
        if (__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_EMBEDDING_MODEL) {
            requestBody.embedding_model = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_EMBEDDING_MODEL;
        }
        if (__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_RERANKER_MODEL) {
            requestBody.reranker_model = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_RERANKER_MODEL;
        }
        return requestBody;
    };
    const handleError = (messageId)=>{
        setMessages((prev)=>prev.map((msg)=>msg.id === messageId ? {
                    ...msg,
                    content: "Sorry, there was an error processing your request."
                } : msg));
    };
    const handleWizardSubmit = async (generatedQuery)=>{
        // Process query silently without showing it as a user message
        if (!generatedQuery.trim()) return;
        resetStream();
        const controller = startStream();
        // Clear previous messages and only show the new configuration
        setMessages([]);
        // Only create assistant message (no user message shown)
        const assistantMessage = createAssistantMessage();
        setMessages([
            assistantMessage
        ]);
        // Debug confidence score threshold being used
        console.log(`Submitting wizard query with confidence threshold: ${confidenceScoreThreshold}`);
        try {
            // Create the request with the query but don't show it in chat
            const silentUserMessage = createUserMessage(generatedQuery);
            const requestBody = {
                messages: [
                    silentUserMessage
                ].map((msg)=>({
                        role: msg.role,
                        content: msg.content
                    })),
                collection_name: "vgpu_knowledge_base",
                temperature,
                top_p: topP,
                reranker_top_k: rerankerTopK,
                vdb_top_k: vdbTopK,
                confidence_threshold: confidenceScoreThreshold,
                use_knowledge_base: true,
                enable_citations: includeCitations,
                enable_guardrails: useGuardrails
            };
            // Include model parameters if set
            if (__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_MODEL_NAME) {
                requestBody.model = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_MODEL_NAME;
            }
            if (__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_EMBEDDING_MODEL) {
                requestBody.embedding_model = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_EMBEDDING_MODEL;
            }
            if (__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_RERANKER_MODEL) {
                requestBody.reranker_model = __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_RERANKER_MODEL;
            }
            const response = await fetch("/api/generate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(requestBody),
                signal: controller.signal
            });
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            await processStream(response, assistantMessage.id, setMessages, confidenceScoreThreshold);
        } catch (error) {
            if (error instanceof Error && error.name === "AbortError") {
                console.log("Stream aborted");
                return;
            }
            console.error("Error generating response:", error);
            handleError(assistantMessage.id);
        }
    };
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex h-[calc(100vh-56px)] bg-[#121212]",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: `flex flex-1 transition-all duration-300 ${!!activePanel ? "mr-[400px]" : ""}`,
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                    className: "relative flex-1",
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$RightSidebar$2f$RightSidebar$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                            lineNumber: 328,
                            columnNumber: 11
                        }, this),
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                            className: "flex h-full flex-col",
                            children: [
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex-1 overflow-y-auto p-4",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "mx-auto max-w-3xl space-y-6",
                                        children: [
                                            messages.map((msg)=>/*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                    className: `flex ${msg.role === "user" ? "justify-end" : "justify-start"}`,
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                        className: `max-w-2xl rounded-lg p-4 ${msg.role === "user" ? "bg-neutral-800 text-white" : "bg-neutral-800 text-white"}`,
                                                        children: [
                                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                className: "text-sm",
                                                                children: msg.content ? renderMessageContent(msg.content, false) : msg.role === "assistant" && streamState.isTyping ? renderMessageContent("", true) : ""
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                                lineNumber: 346,
                                                                columnNumber: 23
                                                            }, this),
                                                            msg.citations && /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                                className: "mt-2 text-xs text-gray-400",
                                                                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                                                    onClick: ()=>handleToggleSidebar("citations", msg.citations),
                                                                    className: "text-[var(--nv-green)] hover:underline",
                                                                    children: [
                                                                        msg.citations.length,
                                                                        " Citations"
                                                                    ]
                                                                }, void 0, true, {
                                                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                                    lineNumber: 355,
                                                                    columnNumber: 27
                                                                }, this)
                                                            }, void 0, false, {
                                                                fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                                lineNumber: 354,
                                                                columnNumber: 25
                                                            }, this)
                                                        ]
                                                    }, void 0, true, {
                                                        fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                        lineNumber: 339,
                                                        columnNumber: 21
                                                    }, this)
                                                }, msg.id, false, {
                                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                    lineNumber: 333,
                                                    columnNumber: 19
                                                }, this)),
                                            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                                ref: messagesEndRef
                                            }, void 0, false, {
                                                fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                lineNumber: 368,
                                                columnNumber: 17
                                            }, this)
                                        ]
                                    }, void 0, true, {
                                        fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                        lineNumber: 331,
                                        columnNumber: 15
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                    lineNumber: 330,
                                    columnNumber: 13
                                }, this),
                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                    className: "flex-shrink-0 border-t border-neutral-800",
                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                                        className: "p-4",
                                        children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                                            onClick: ()=>setIsWizardOpen(true),
                                            className: "w-full bg-gradient-to-r from-green-600 to-green-700 text-white p-4 rounded-lg shadow-lg hover:from-green-700 hover:to-green-800 transition-all duration-200 hover:scale-[1.02] flex items-center justify-center space-x-3",
                                            title: "Open Workload Configuration Wizard",
                                            children: [
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("svg", {
                                                    className: "w-6 h-6",
                                                    fill: "none",
                                                    stroke: "currentColor",
                                                    viewBox: "0 0 24 24",
                                                    children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("path", {
                                                        strokeLinecap: "round",
                                                        strokeLinejoin: "round",
                                                        strokeWidth: 2,
                                                        d: "M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z"
                                                    }, void 0, false, {
                                                        fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                        lineNumber: 380,
                                                        columnNumber: 21
                                                    }, this)
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                    lineNumber: 379,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                    className: "text-lg font-bold",
                                                    children: "vGPU"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                    lineNumber: 382,
                                                    columnNumber: 19
                                                }, this),
                                                /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                                                    className: "font-medium",
                                                    children: "Initialize Sizing Job"
                                                }, void 0, false, {
                                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                                    lineNumber: 383,
                                                    columnNumber: 19
                                                }, this)
                                            ]
                                        }, void 0, true, {
                                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                            lineNumber: 374,
                                            columnNumber: 17
                                        }, this)
                                    }, void 0, false, {
                                        fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                        lineNumber: 373,
                                        columnNumber: 15
                                    }, this)
                                }, void 0, false, {
                                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                                    lineNumber: 372,
                                    columnNumber: 13
                                }, this)
                            ]
                        }, void 0, true, {
                            fileName: "[project]/src/app/components/Chat/Chat.tsx",
                            lineNumber: 329,
                            columnNumber: 11
                        }, this)
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/Chat/Chat.tsx",
                    lineNumber: 327,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/Chat.tsx",
                lineNumber: 322,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$WorkloadConfigWizard$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                isOpen: isWizardOpen,
                onClose: ()=>setIsWizardOpen(false),
                onSubmit: handleWizardSubmit
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/Chat.tsx",
                lineNumber: 392,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$VGPUConfigDrawer$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                config: drawerConfig,
                isOpen: isDrawerOpen,
                onClose: ()=>setIsDrawerOpen(false)
            }, void 0, false, {
                fileName: "[project]/src/app/components/Chat/Chat.tsx",
                lineNumber: 399,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/app/components/Chat/Chat.tsx",
        lineNumber: 321,
        columnNumber: 5
    }, this);
}
_s(Chat, "SHz/FT5dgAohBjN1tDehPO6FUCQ=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SidebarContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useSidebar"],
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$hooks$2f$useChatStream$2e$ts__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useChatStream"],
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SettingsContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useSettings"]
    ];
});
_c = Chat;
var _c;
__turbopack_context__.k.register(_c, "Chat");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/components/Header/Header.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "default": (()=>Header)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/build/polyfills/process.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$image$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/image.js [app-client] (ecmascript)");
"use client";
;
;
function Header({ onToggleSidebar, activePanel }) {
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex h-14 items-center justify-between border-b border-neutral-800 bg-black px-4",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center gap-2",
                children: [
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$image$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                        src: "/nvidia-logo.svg",
                        alt: "NVIDIA Logo",
                        width: 128,
                        height: 24
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Header/Header.tsx",
                        lineNumber: 29,
                        columnNumber: 9
                    }, this),
                    /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                        className: "text-lg font-semibold text-white",
                        children: "AI vWS Sizing Advisor"
                    }, void 0, false, {
                        fileName: "[project]/src/app/components/Header/Header.tsx",
                        lineNumber: 35,
                        columnNumber: 9
                    }, this)
                ]
            }, void 0, true, {
                fileName: "[project]/src/app/components/Header/Header.tsx",
                lineNumber: 28,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "absolute left-1/2 -translate-x-1/2 transform"
            }, void 0, false, {
                fileName: "[project]/src/app/components/Header/Header.tsx",
                lineNumber: 38,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("span", {
                className: "rounded-lg border border-neutral-800 bg-neutral-900 px-8 py-1 text-sm text-neutral-100",
                children: __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$build$2f$polyfills$2f$process$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"].env.NEXT_PUBLIC_MODEL_NAME || "Model not found"
            }, void 0, false, {
                fileName: "[project]/src/app/components/Header/Header.tsx",
                lineNumber: 39,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex items-center gap-4",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("button", {
                    onClick: ()=>onToggleSidebar("citations"),
                    className: `flex items-center gap-2 text-sm ${activePanel === "citations" ? "text-white" : "text-gray-400"} transition-colors hover:text-white`,
                    children: [
                        /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$image$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                            src: "/citations.svg",
                            alt: "Citations Icon",
                            width: 16,
                            height: 16
                        }, void 0, false, {
                            fileName: "[project]/src/app/components/Header/Header.tsx",
                            lineNumber: 50,
                            columnNumber: 11
                        }, this),
                        "Citations"
                    ]
                }, void 0, true, {
                    fileName: "[project]/src/app/components/Header/Header.tsx",
                    lineNumber: 44,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/components/Header/Header.tsx",
                lineNumber: 43,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/app/components/Header/Header.tsx",
        lineNumber: 27,
        columnNumber: 5
    }, this);
}
_c = Header;
var _c;
__turbopack_context__.k.register(_c, "Header");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
"[project]/src/app/page.tsx [app-client] (ecmascript)": ((__turbopack_context__) => {
"use strict";

var { g: global, __dirname, k: __turbopack_refresh__, m: module } = __turbopack_context__;
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
    "default": (()=>Home)
});
var __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/node_modules/next/dist/compiled/react/jsx-dev-runtime.js [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$Chat$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/components/Chat/Chat.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Header$2f$Header$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/components/Header/Header.tsx [app-client] (ecmascript)");
var __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SidebarContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__ = __turbopack_context__.i("[project]/src/app/context/SidebarContext.tsx [app-client] (ecmascript)");
;
var _s = __turbopack_context__.k.signature();
"use client";
;
;
;
function Home() {
    _s();
    const { activePanel, toggleSidebar } = (0, __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SidebarContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useSidebar"])();
    return /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
        className: "flex h-screen flex-col",
        children: [
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Header$2f$Header$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {
                onToggleSidebar: toggleSidebar,
                activePanel: activePanel === "citations" ? "citations" : null
            }, void 0, false, {
                fileName: "[project]/src/app/page.tsx",
                lineNumber: 27,
                columnNumber: 7
            }, this),
            /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])("div", {
                className: "flex-1",
                children: /*#__PURE__*/ (0, __TURBOPACK__imported__module__$5b$project$5d2f$node_modules$2f$next$2f$dist$2f$compiled$2f$react$2f$jsx$2d$dev$2d$runtime$2e$js__$5b$app$2d$client$5d$__$28$ecmascript$29$__["jsxDEV"])(__TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$components$2f$Chat$2f$Chat$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["default"], {}, void 0, false, {
                    fileName: "[project]/src/app/page.tsx",
                    lineNumber: 29,
                    columnNumber: 9
                }, this)
            }, void 0, false, {
                fileName: "[project]/src/app/page.tsx",
                lineNumber: 28,
                columnNumber: 7
            }, this)
        ]
    }, void 0, true, {
        fileName: "[project]/src/app/page.tsx",
        lineNumber: 26,
        columnNumber: 5
    }, this);
}
_s(Home, "NHHpy7zT8rb7om/Q/yJjIowb1uk=", false, function() {
    return [
        __TURBOPACK__imported__module__$5b$project$5d2f$src$2f$app$2f$context$2f$SidebarContext$2e$tsx__$5b$app$2d$client$5d$__$28$ecmascript$29$__["useSidebar"]
    ];
});
_c = Home;
var _c;
__turbopack_context__.k.register(_c, "Home");
if (typeof globalThis.$RefreshHelpers$ === 'object' && globalThis.$RefreshHelpers !== null) {
    __turbopack_context__.k.registerExports(module, globalThis.$RefreshHelpers$);
}
}}),
}]);

//# sourceMappingURL=src_app_55c4c5a6._.js.map