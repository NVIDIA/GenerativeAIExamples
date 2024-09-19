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

from dataclasses import dataclass
from typing import Union

from omegaconf import DictConfig
from openai import OpenAI
from tqdm import tqdm

from .dataset import Corpus
from .processor import Processor

class DummyRewriter(Processor):
    def process(self, corpus: Corpus) -> Corpus:
        return corpus


class ParaphraseQuestionRewriter(Processor):
    """Rewrite the question using paraphrasing techniques."""
    def __init__(self,
                 generate_config: DictConfig,
                 api_key: str,
                 model: str = "mistralai/mixtral-8x7b-instruct-v0.1",                 
                 base_url: str = "https://integrate.api.nvidia.com/v1"):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key)
        self.model = model
        self.generate_config = generate_config

    def process(self, corpus: Corpus) -> Corpus:
        for example in tqdm(corpus.data["data"]):
            for qa in example["paragraphs"][0]["qas"]:
                if "synthetic" in qa and qa["synthetic"]:
                    # * Synthetic questions
                    rephrased_question = self.generate(
                        document=example["paragraphs"][0]["context"],
                        question=qa["question"],
                        **self.generate_config)
                    if rephrased_question is not None:
                        qa["question"] = rephrased_question
        return corpus

    def generate(self,
                 question: str,
                 document: str = None,
                 system_prompt: str = None,
                 user_prompt_template: str = None,
                 temperature: float = 0.5,
                 top_p: float = 1,
                 max_tokens: int = 1024,
                 stream: bool = True) -> Union[None, str]:

        if system_prompt is None:
            system_prompt = """
You are a writer trying to rewrite the given qestions to make it shorter and more challenging. 

- You will be given a question and a document.
- Generate an rephrased answer to the question.
- Make sure the question can be answered by the document.
- Try to make the question more challenging, reducing the lexical overlap between the question and the document.
- Shoter questions are preferred. Try not to elaborate on the question."""

        if user_prompt_template is None:
            user_prompt_template = """Rewrite the question while making sure to keep the question answerable by the document.

Input Document:
{document}

Question:
{question}

Rephrased Question:"""
        if document is None:
            user_prompt = user_prompt_template.format(question=question)
        else:
            user_prompt = user_prompt_template.format(document=document, question=question)

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "user",
                 "content": system_prompt + "\n\n" + user_prompt}],
            temperature=temperature,
            top_p=top_p,
            max_tokens=max_tokens,
            stream=stream)

        generation = ""
        for chunk in completion:
            if chunk.choices[0].delta.content is not None:
                generation += chunk.choices[0].delta.content
        return generation

