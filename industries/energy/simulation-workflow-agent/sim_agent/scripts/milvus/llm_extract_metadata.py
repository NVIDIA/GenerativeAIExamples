# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

from openai import OpenAI
import os
import re
import json
nvidia_api=os.getenv("NVIDIA_API_KEY")
client = OpenAI(
  base_url = "https://integrate.api.nvidia.com/v1",
  api_key = nvidia_api
)

system_prompt = """
You are an expert in extracting metadata as preprocessing to a vector store. 
You will be given one page from a user manual of oil and gas production software and each page will contain instruction on how to use the software called OPEN POROUS MEDIA(OPM).
This manual is used by expert reservoir engineers to perform simulations on the software in order to optimize the production of oil and gas from the reservoir.
You will need to extract the metadata from the page in order to create a vector store of the software.
The vector store will be used to answer user queries about the software.

<RULES>
1.Pay attention to anything useful, including for example keywords, descriptions, code snippets, fields and their meanings, etc.
2.You will also add possible user queries associated with the keyword
3. you should also extract any anything inside  that looks useful for an reservoir engineer to use the software. for example code snippet, yaml looking blocks...etc
4.The output metadata should be in a list of JSON format
5. If more than one keyword is present in the txt file, you will need to extract the metadata for each keyword and add them to the JSON output.
6. You will return ONLY a list of JSON objects, no other text or formatting.
</RULES>
now process the  input_txt_file: {input_txt_file}
"""
def response(input_txt_file):
  prompt = system_prompt.format(input_txt_file=input_txt_file)
  completion = client.chat.completions.create(
     model="nvidia/llama-3.3-nemotron-super-49b-v1.5",
    messages=[{"role":"user","content":prompt}],
    temperature=1,
    top_p=0.95,
    max_tokens=16384,
    extra_body={"chat_template_kwargs":{"enable_thinking":True},"reasoning_budget":16384},
    stream=True
  )
  response = ""
  for chunk in completion:
    if not chunk.choices:
      continue
    reasoning = getattr(chunk.choices[0].delta, "reasoning_content", None)
    if reasoning:
      response += reasoning
    if chunk.choices[0].delta.content is not None:
      response += chunk.choices[0].delta.content
  return response

def strip_thinking_tags(raw_response: str) -> list[dict]:
  """Strip <think>...</think> tags and extract the JSON list; return a list of Python dicts."""
  # Remove thinking block (may span many lines)
  text = re.sub(r"<think>.*?</think>", "", raw_response, flags=re.DOTALL)
  # Remove markdown code fences
  text = text.replace("```json", "").replace("```", "").strip()
  # Find JSON array: first '[' to matching ']'
  start = text.find("[")
  if start == -1:
    return []
  depth = 0
  for i in range(start, len(text)):
    if text[i] == "[":
      depth += 1
    elif text[i] == "]":
      depth -= 1
      if depth == 0:
        return json.loads(text[start : i + 1])
  return []

if __name__ == "__main__":
  input_txt_file = input("Enter the path to the txt file: ")
  response_json = response(input_txt_file)
  output_json = strip_thinking_tags(response_json)
  print(output_json)