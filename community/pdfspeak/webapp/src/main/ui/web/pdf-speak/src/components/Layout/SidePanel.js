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

import React from 'react';
import { Tooltip } from 'react-tooltip';

const SidePanel = ({ pdfUrl, isExpanded, setIsExpanded }) => {
    return (
        <div className={`transition-all duration-300 relative ${
            isExpanded ? 'w-[500px]' : 'w-[50px]'
        }`}>
            <>
                <button 
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="absolute top-4 -left-3 z-10 bg-green-500 border rounded p-2 shadow-md hover:bg-green-600"
                    // className='p-3 rounded-full bg-gray-200 hover:bg-gray-300 dark:bg-gray-700 dark:hover:bg-gray-600 transition-colors shadow-lg z-50'
                    data-tooltip-id="pdf-view-tooltip"
                >
                    {isExpanded ? '→' : '←'}
                </button>
                
                <Tooltip 
                    id="pdf-view-tooltip"
                    place="left"
                    content={isExpanded ? "Close PDF view" : "Show annotated PDF"}
                    className="text-sm"
                />
            </>
            
            {isExpanded && (
                <div className="h-full border-l bg-white">
                    {pdfUrl ? (
                        <iframe
                            src={pdfUrl}
                            className="w-full h-[calc(100vh-120px)]"
                            title="PDF Viewer"
                        />
                    ) : (
                        <div className="p-8 text-gray-500">
                            Upload a PDF and ask questions to view highlighted references!
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};


export default SidePanel;