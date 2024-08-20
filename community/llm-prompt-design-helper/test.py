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

from api_request import APIRequest
import os
# set up the base_url and api_key first
os.environ['API_CATALOG_KEY'] = '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'
os.environ['NIM_INFER_URL'] ="https://integrate.api.nvidia.com/v1"
# load your dataset and parse the test set 
input_texts = [
    "What is the capital of France?",
    "What is 2 + 2?",
]

output_texts =[]
model_to_evaluates = [
    "meta/llama3-70b-instruct"
]

inference_api = APIRequest("./config.yaml")

for model in model_to_evaluates:
    output_texts.append({"model":model,"outputs":[]})
    model_outputs = output_texts[-1]["outputs"]
    for text in input_texts:
        output_generator = inference_api.send_request(model,[[text,None]])
        output_text = ""
        for next_token in output_generator:
            output_text += next_token
        model_outputs.append(output_text)
print(output_texts)
