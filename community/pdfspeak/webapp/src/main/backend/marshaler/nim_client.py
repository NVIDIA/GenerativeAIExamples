# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import os
from openai import OpenAI
import re
from dotenv import load_dotenv

def clean_response(response):
    cleaned_response = re.sub(r'^\W+', '', response)
    return cleaned_response

def request_nvidia_llama(messages, pdf_context):
    load_dotenv()
    NV_API_KEY = os.getenv("NV_API_KEY")
    print(NV_API_KEY)
    client = OpenAI(
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=NV_API_KEY
    )
    
    if pdf_context != "":
        messages.append({"role": "system", "content": f"Consider this to be the document uploaded as the context for the question: {pdf_context['text']}"})
    
    messages.append({"role": "system", "content": "Answer the last question of this conversation in as little words as possible. Extra explanation is not necessary unless asked in the question."})

    try:
        response = client.chat.completions.create(
            model="nvidia/llama-3.1-nemotron-70b-instruct",
            messages=messages,
            temperature=0.5,
            top_p=1,
            max_tokens=1024,
            stream=False
        )
        return clean_response(response.choices[0].message.content.strip())
    except Exception as e:
        print(f"Error: {e}")
        return "NVIDIA API temporarily down :( Please try again in a while."
