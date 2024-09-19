# Copyright (c) 2024, NVIDIA CORPORATION.  All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from abc import ABC, abstractmethod
import hashlib
import re
import secrets
from typing import Union

from omegaconf import DictConfig
from openai import OpenAI
from tqdm import tqdm
import json
import os

from .dataset import Corpus

def get_random_hash():
    """Generate random hash for synthetic question IDs
    """
    # Generate a random string
    random_string = secrets.token_hex(16)  # Generates a secure, random string of 16 bytes hex-encoded

    # Hash the random string using SHA-256
    hash_object = hashlib.sha256(random_string.encode())  # Encode the string to bytes
    hex_dig = hash_object.hexdigest()
    return hex_dig


class QAGenerator(ABC):
    @abstractmethod
    def generate_qa_pairs(self, corpus: Corpus) -> Corpus:
        pass

class DummyQAGenerator(QAGenerator):
    def generate_qa_pairs(self, corpus: Corpus) -> Corpus:
        return corpus

class SimpleQAGenerator(QAGenerator):
    """
    See https://build.nvidia.com/mistralai/mixtral-8x7b-instruct for details to get access information
    """
    def __init__(self,
                 generate_config: DictConfig,
                 api_key: str,
                 model: str = "mistralai/mixtral-8x7b-instruct-v0.1",              
                 base_url: str = "https://integrate.api.nvidia.com/v1",
                 max_examples: int = 10,
                 prompt_builder_config: DictConfig = None, 
                 qa_generations_file: str = None
                 ):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key)
        self.model = model
        self.max_examples = max_examples
        self.generate_config = generate_config
        self.system_prompt = None
        self.prompt_builder = None
        self.qa_generations_file = qa_generations_file

        if(self.qa_generations_file):
            if(not os.path.isfile(self.qa_generations_file)):
                print(f"Creating new QA Generations file: {self.qa_generations_file}")
            else:
                print(f"Reusing QA Generations from file: {self.qa_generations_file}")


    def generate(self,
                 document: str,
                 system_prompt: str = None,
                 user_prompt_template: str = None,
                 temperature: float = 0.5,
                 top_p: float = 1,
                 max_tokens: int = 1024,
                 stream: bool = True,
                 parse_response: bool = True,
                 num_questions: int = 3,
                 squad_format: bool = True) -> Union[None, str]:

        # import pdb; pdb.set_trace()
        if self.system_prompt is None:
            print("Updating system prompt...")
            if system_prompt:
                self.system_prompt = system_prompt
            else:
                self.system_prompt = """
You are a data annotator trying to generate three qestions and corresponding answers based on Input Document.

- The generated questions must be answerable from Input Document.
- Avoid duplicate questions and ask different questions.
- Generate an answer to each question as well.

Example:

Input Document:
AV Sync 

Use of an AV Receiver with HDMI for video may result in audio lagging behind video.  First try 
using the receiver AV sync settings to calibrate.  If this does not work, use the AV sync slider 
utility in Settings  > Display & sound > Advanced settings > Audio video sync to calibrate for 
any audio delay.  The AV sync slider allows you to advance audio by 1 second (in small 
increments of 10ms) to synchronize the audio and video. 
Note that this tool is effective only when SHIELD is connected to your AV Receiver over HDMI 
(i.e. audio/video over HDMI); it is not meant to be used when a headset is plugged into SHIELD 
Controller/SHIELD Remote or USB audio device or Bluetooth audio device. 
If video lags behind audio (i.e. audio is ahead of video) then use your AV receiver’s settings to 
delay audio.
ADJUST FOR OVERSCAN

For TVs that don't provide their own overscan settings, use this setting to adjust the picture size to fit the screen.

Go to Settings > Device Preferences > Display & Sound > Advanced Settings > Adjust for overscan to resize the picture on your TV or display.  Use the UP and DOWN d-pad buttons on your remote to maximize the picture on your TV.  Make sure the green triangles are completely visible to avoid overscan.

Generated Questions:
- Q. How do I adjust the display so that my picture does not go out of the screen?
- Q. Why is AV Sync not working when I'm plugging my SHIELD into my bluetooth earphone?
- Q. How many seconds can I delay audio by in AV Sync?"""

        if user_prompt_template is None:
            self.user_prompt_template = """Generate {num_questions} qestions and corresponding answers based on Input Document.

Input Document:
{document}


Generated Questions:
"""
        else:
            self.user_prompt_template = user_prompt_template
            
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user",
                 "content": self.system_prompt + "\n\n" + self.user_prompt_template.format(document=document, num_questions=num_questions)}],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=stream)

        generation = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                generation += chunk.choices[0].delta.content

        if parse_response:
            return self.parse_response(generation, 
                                       squad_format=squad_format)
        else:
            return generation
    
    def parse_response(self,
                       response: str,
                       squad_format: bool = True):
        qa_pairs = []
        qa_list = response.split("Question")[1:]
        try:
            for qa in qa_list:
                qas = qa.split("Answer")
                q = qas[0].split(":")[1].strip()
                if re.search("Explanation", qas[1]):
                    a = qas[1].split("Explanation")[0].split(":")[1].strip()
                    explanation = qas[1].split("Explanation")[1].strip()  # Not used
                else:
                    a = qas[1].split(":")[1].strip()
                if squad_format:
                    qa_pairs.append({"question": q,
                                     "id": get_random_hash(),
                                     "synthetic": True,
                                     "answers": [
                                         {"text": a,
                                          "answer_start": -1,
                                          "synthetic": True}
                                     ]})
                else:
                    qa_pairs.append({"question": q,
                                     "answer": a})
        except Exception as e:
            print(f"error: {e}")
        return qa_pairs

    def generate_qa_pairs(self, corpus: Corpus) -> Corpus:
        # - Create a deep copy here to avoid overwriting the original object
        count = 0
        progress_bar = tqdm(total=self.max_examples)
        previous_generations = []
        if(self.qa_generations_file):
            if(os.path.isfile(self.qa_generations_file)):
                with open(self.qa_generations_file) as f:
                    previous_generations = [json.loads(line) for line in f]
                    print(f"Skipping {len(previous_generations)} generations and loading from QA generations file")
            # else:
            #     previous_generations = []
        for idx, example in enumerate(tqdm(corpus.data["data"])):
            if(idx<len(previous_generations)):
                assert example["paragraphs"][0]["context"] == previous_generations[idx]["paragraphs"][0]["context"], "Example in the cache file does not match the original data. Possibly broken cache file."
                example=previous_generations[idx]
                print(f"Skipped Example #{idx}")
                count += 1
                if count >= self.max_examples:
                    break
                continue
            try:
                response = self.generate(document=example["paragraphs"][0]["context"], **self.generate_config)
            except Exception:
                response = None

            if response is not None:
                example["paragraphs"][0]["qas"] += response
                if(self.qa_generations_file):
                    with open(self.qa_generations_file, "a") as f:
                        f.write(f"{json.dumps(example)}\n")
                count += 1
                if count >= self.max_examples:
                    break
        progress_bar.update(self.max_examples - count)
        progress_bar.close()
        return corpus
     
    def _update_system_prompt(self, prompt: str):
        self.system_prompt = prompt