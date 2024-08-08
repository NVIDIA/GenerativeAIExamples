# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from .api_request import API_CATALOG_KEY,APIRequest,NIM_INFER_URL
from langchain_nvidia_ai_endpoints import ChatNVIDIA

class ChatNVDIAClient(APIRequest):
    def __init__(self, config_path):
        super().__init__(config_path)
        
    def send_request(self,api_model,oai_message,temperature,top_p,max_tokens,base_url=''):
        # default NIM_INFER_URL = "https://integrate.api.nvidia.com/v1"

        base_url_infer = NIM_INFER_URL
        api_key = API_CATALOG_KEY
        if base_url !='':
            base_url_infer = base_url

        client = ChatNVIDIA(base_url= base_url_infer, api_key= api_key,model=api_model, temperature=temperature, max_tokens=max_tokens, top_p=top_p)
        try:
            completion = client.stream(oai_message,timeout=10.0)
            
            # Step 5: Yield the output of delta content
            for chunk in completion:
                if chunk.content is not None:
                    next_token= chunk.content
                    yield next_token
                else:
                    pass
        except Exception as e:
            yield "Request is Error:\n" + str(e)