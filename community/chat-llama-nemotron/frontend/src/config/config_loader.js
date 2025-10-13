// SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0
//
// Copyright (c) 2023-2025, NVIDIA CORPORATION.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.


import yaml from 'js-yaml';

class ConfigLoader {
    constructor() {
        if (ConfigLoader.instance) {
            return ConfigLoader.instance;
        }
        ConfigLoader.instance = this;
        
        this.configs = {};
        this._serverIp = localStorage.getItem('serverIp') || '';
        
        // Initialize RAG server URL
        const ip = window.appConfig?.api?.ip || 'localhost';
        const port = process.env.REACT_APP_API_PORT || window.appConfig?.api?.port || '8001';
        this._ragServerUrl = `http://${ip}:${port}`;
        console.log('RAG server URL:', this._ragServerUrl);
    }

    set serverIp(ip) {
        this._serverIp = ip;
        localStorage.setItem('serverIp', ip);
    }

    get serverIp() {
        return this._serverIp;
    }

    get api() {
        const self = this;
        return {
            get proxy() {
                return self._ragServerUrl;
            },
            get llmServer() {
                const ip = window.appConfig?.llm_proxy?.ip || 'localhost';
                const port = process.env.REACT_APP_LLM_PROXY_PORT || window.appConfig?.llm_proxy?.port || '8002';
                const url = `http://${ip}:${port}`;
                return {
                    url,
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-LLM-IP': self._serverIp
                    }
                };
            }
        };
    }

    async loadConfig(configName) {
        // Return cached config if available
        if (this.configs[configName]) {
            return this.configs[configName];
        }

        try {
            const publicPath = `/config/${configName}.yaml`;
            const response = await fetch(publicPath);
            
            if (!response.ok) {
                throw new Error(`Failed to load config: ${configName}`);
            }
            
            const yamlText = await response.text();
            const config = yaml.load(yamlText);
            
            if (!config) {
                throw new Error('YAML parsing resulted in null or undefined');
            }
            
            this.configs[configName] = config;
            return config;
        } catch (error) {
            console.error(`Error loading config ${configName}:`, error);
            throw error;
        }
    }

    async getAppConfig() {
        return this.loadConfig('app_config');
    }
}

// Create a singleton instance
const configLoader = new ConfigLoader();
export default configLoader; 