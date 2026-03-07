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
        this._config = null;

        // "serverIp" is used for X-LLM-IP. Keep as-is for backward compat.
        this._serverIp = localStorage.getItem('serverIp') || '';

        // Default to same host serving the frontend (avoids "localhost" on Windows clients).
        this._defaultHost = window.location.hostname || 'localhost';
        this._ragServerUrl = `http://${this._defaultHost}:8001`;

        console.log('Default host:', this._defaultHost);
        console.log('Initial RAG server URL:', this._ragServerUrl);
    }

    set serverIp(ip) {
        this._serverIp = ip;
        localStorage.setItem('serverIp', ip);
    }

    get serverIp() {
        return this._serverIp;
    }

    _safeUrl(url) {
        try {
            return new URL(url);
        } catch {
            return null;
        }
    }

    _deriveHostFromConfig(config) {
        // Prefer explicit ip/host fields, otherwise derive from api.base_url, otherwise frontend host.
        const fromApi = this._safeUrl(config?.api?.base_url);
        if (config?.api?.ip) return config.api.ip;
        if (config?.api?.host) return config.api.host;
        if (fromApi?.hostname) return fromApi.hostname;
        return this._defaultHost;
    }

    _deriveRagUrl(config) {
        const fromApi = this._safeUrl(config?.api?.base_url);
        if (fromApi) return fromApi.origin;

        const host = this._deriveHostFromConfig(config);
        const port = config?.api?.port || process.env.REACT_APP_API_PORT || '8001';
        return `http://${host}:${port}`;
    }

    _deriveLlmProxyUrl(config) {
        // Prefer explicit llm_proxy.ip/host, otherwise derive from llm.base_url host, otherwise frontend host.
        const fromLlm = this._safeUrl(config?.llm?.base_url);
        const host =
            config?.llm_proxy?.ip ||
            config?.llm_proxy?.host ||
            fromLlm?.hostname ||
            this._defaultHost;

        const port =
            process.env.REACT_APP_LLM_PROXY_PORT ||
            config?.llm_proxy?.port ||
            '8002';

        return `http://${host}:${port}`;
    }

    _shouldSendXLLMIPHeader() {
        // Only send if user provided/stored a value.
        // This avoids sending an empty/invalid X-LLM-IP header.
        return Boolean(this._serverIp && this._serverIp.trim());
    }

    get api() {
        const self = this;
        return {
            get proxy() {
                // RAG backend URL (FastAPI on 8001)
                return self._ragServerUrl;
            },
            get llmServer() {
                // LLM proxy URL (Express on 8002)
                const url = self._deriveLlmProxyUrl(self._config || {});
                return {
                    url,
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        ...(self._shouldSendXLLMIPHeader()
                            ? { 'X-LLM-IP': self._serverIp }
                            : {}),
                    },
                };
            },
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

            // Cache it
            this.configs[configName] = config;

            // Keep a reference to app_config for runtime URL derivation
            if (configName === 'app_config') {
                this._config = config;

                // Update RAG server URL based on app_config (avoid "localhost" on Windows)
                this._ragServerUrl = this._deriveRagUrl(config);

                console.log('Loaded app_config.yaml');
                console.log('Resolved RAG server URL:', this._ragServerUrl);
                console.log('Resolved LLM proxy URL:', this._deriveLlmProxyUrl(config));
            }

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