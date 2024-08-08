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

import yaml
import os
from abc import ABC,abstractmethod
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

API_CATALOG_KEY = os.getenv("API_CATALOG_KEY", "")
NIM_INFER_URL = os.getenv("NIM_INFER_URL", "https://integrate.api.nvidia.com/v1")

class APIRequest(ABC):
    def __init__(self, config_path):
        self.config_path = config_path
        self.config = {}
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
        return 
    
    def get_model_settings(self,api_model):
        model_settings = self.config.get(api_model,None)
        if model_settings == None:
            logging.info(f"No config for {api_model}, load the default")
            model_settings=self.config.get('default')

        return model_settings
    def update_yaml(self,api_model,parameters):
        self.config.update({api_model:parameters})
        with open(self.config_path, 'w') as file:
            yaml.dump(self.config, file, default_flow_style=False, sort_keys=False)

    def get_model_configuration(self,api_model):
        model_config = self.get_model_settings(api_model)
        # system_prompt = model_config.get('system_prompt','')    
        return model_config
    
    @abstractmethod
    def send_request(self,api_model,oai_message,temperature,top_p,max_tokens,base_url=''):
        pass

    def generate_response(self,api_model,chat_messages,system_prompt=None,initial_prompt=None,temperature=None, top_p=None,max_tokens=None,few_shot_exampls=None,base_url='',context=''):
        # Step 1: Get model config based on configuration yaml file.
        model_config = self.get_model_settings(api_model)

        # Step 2: Get the parameters for LLM based on different model.
        temperature = temperature if temperature!=None else model_config.get("temperature",0.0)
        top_p = top_p if top_p!=None else model_config.get("top_p",0.7)
        max_tokens = max_tokens if max_tokens!=None else model_config.get("max_tokens",1024)

        # Step 3: Prepare the messages to be sent to API catalog
        #         System prompt
        #         few shot examples.
        oai_message = []
        system_prompt_message = system_prompt if system_prompt!=None else model_config.get('system_prompt','')
        if context:
            system_prompt_message += f"\nUse the following pieces of retrieved context to answer the question. \n {context}"
        fewshow_examples = few_shot_exampls if few_shot_exampls else model_config.get('few_shot_examples',[])
        if system_prompt_message !='':
            oai_message.append({'role': 'system', 'content': system_prompt_message})
        if fewshow_examples:
            for example in few_shot_exampls:
                oai_message.append(example)
        
        for item in chat_messages:
            if item[0] == None and item[1] == initial_prompt:
                continue
            oai_message.append({'role': 'user', 'content': item[0]})
            if item[1] != '' and item[1] !=None:
                # add pure assitant response to chat history.
                assistant_msg = item[1]
                oai_message.append({'role': 'assistant', 'content': assistant_msg})
        
        request_body = {
            "model":api_model,
            "messages":oai_message,
            "temperature":temperature,
            "top_p":top_p,
            "max_tokens":max_tokens,
            "stream":True
        }
        logging.info(request_body)

        # Step 4: Send the requests using OpenAI Compatible API
        return self.send_request(api_model,oai_message,temperature,top_p,max_tokens,base_url)
        

    