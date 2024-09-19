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
import copy
import json
from typing import Tuple

import numpy as np
from sentence_transformers import SentenceTransformer
from omegaconf import DictConfig
from openai import OpenAI

from .dataset import Corpus
import itertools

class Filter(ABC):
    @abstractmethod
    def filter(self, corpus: Corpus) -> Corpus:
        pass

class Filters:
    def __init__(self):
        self.filters = []

    def add(self, filter: Filter):
        self.filters.append(filter)

    def apply_filters(self, corpus: Corpus) -> Tuple[Corpus, Corpus]:
        # Apply filters to the corpus one by one
        # Note: Apply all filters to all examples for consistent analysis, which may computationally expensive
        for filter in self.filters:
            corpus = filter.filter(corpus)        

        # The input corpus will not be reused but create deep copies just in case
        corpus_all = copy.deepcopy(corpus)
        corpus_filtered = copy.deepcopy(corpus)

        for example in corpus_filtered.data["data"]:
            if example["paragraphs"][0]["qas"]:
                filtered_qas = []
                for qa in example["paragraphs"][0]["qas"]:
                    qa["is_keep"] = True
                    for filter in self.filters:
                        if (f"{filter.prefix}__keep" in qa) and (
                            not qa[f"{filter.prefix}__keep"]):
                            qa["is_keep"] = False
                            break
                    if qa["is_keep"]:
                        filtered_qas.append(qa)
                example["paragraphs"][0]["qas"] = filtered_qas
        return corpus_all, corpus_filtered

class EasinessFilter(Filter):
    def __init__(self, filter_cfg: DictConfig):
        self.prefix = "easiness"
        if "embedding_model" in filter_cfg:
            # Use HF embedding model for Easiness Filter
            self.embedding_model = filter_cfg.embedding_model
            self.filter_threshold = filter_cfg.filter_threshold
            self.model = SentenceTransformer(self.embedding_model)
        elif "nim_model" in filter_cfg:
            # Use build.nvidia.com NIM for Easiness Filter
            self.base_url = filter_cfg.base_url
            self.api_key = filter_cfg.api_key
            self.nim_model = filter_cfg.nim_model
            self.percentile = filter_cfg.percentile
            if filter_cfg.truncate:
                self.truncate = filter_cfg.truncate
            else:
                self.trunacte = "NONE"
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        self.batch_size = filter_cfg.batch_size
        
    def filter(self,
               corpus: Corpus) -> Corpus:
        """Directly add scores to the corpus"""
        passages = []
        questions = []
        annotated_corpus = copy.deepcopy(corpus)
        for example in annotated_corpus.data["data"]:
            context = example["paragraphs"][0]["context"]
            if example["paragraphs"][0]["qas"]:
                for qa in example["paragraphs"][0]["qas"]:
                    question = qa["question"]
                    passages.append(context)
                    questions.append(question)
                    
        similarity = []
        n_batches = len(passages)//self.batch_size
        
        for idx in range(n_batches):
            passages_batch = passages[idx * self.batch_size : (idx+1) * self.batch_size]
            questions_batch = questions[idx * self.batch_size : (idx + 1)* self.batch_size]
            if hasattr(self, "nim_model"):
                similarity.append(self.calc_similarity_nim(passages_batch, questions_batch))
            elif hasattr(self, "embedding_model"):
                similarity.append(self.calc_similarity_hf(passages_batch, questions_batch))
                
        if n_batches * self.batch_size < len(passages): 
            passages_remain = passages[n_batches * self.batch_size:] 
            questions_remain = questions[n_batches * self.batch_size:]
            if hasattr(self, "nim_model"):
                similarity.append(self.calc_similarity_nim(passages_remain, questions_remain))
            elif hasattr(self, "embedding_model"):
                similarity.append(self.calc_similarity_hf(passages_remain, questions_remain))

        similarity_ = list(itertools.chain.from_iterable(similarity))
        if hasattr(self, "embedding_model"):
            filter_threshold = self.filter_threshold
        elif hasattr(self, "nim_model"): 
            filter_threshold = np.percentile(similarity_, self.percentile)

        qc = 0
        for example in annotated_corpus.data["data"]:
            if example["paragraphs"][0]["qas"]:
                for qa in example["paragraphs"][0]["qas"]:
                    qa[f"{self.prefix}__cossim"] = similarity_[qc]
                    if qa[f"{self.prefix}__cossim"] <= filter_threshold:
                        # if the cosine similarity is less than the threshold, keep the data
                        qa[f"{self.prefix}__keep"] = True # keep the data
                    else:
                        qa[f"{self.prefix}__keep"] = False # filter out the data
                    qc += 1
        return annotated_corpus

    def calc_similarity_hf(self, context, question):
        # Otain embeddings from hf model
        doc_embed = self.model.encode(context) # returns normalized embeddings
        q_embed = self.model.encode(question)  # returns normalized embeddings
        sim = np.diag(np.dot(doc_embed, q_embed.T))
        return sim
    
    def get_nim_embedding(self, text, input_type):
        # Obtain embeddings from nim model
        if isinstance(text, list):
            input_ = text
        elif isinstance(text, str):
            input_ = [text]
            
        try:
            response = self.client.embeddings.create(
                    input= input_,
                    model= self.nim_model,
                    encoding_format="float",
                    extra_body={"input_type": input_type, "truncate": self.truncate}
            )
        except Exception as e:
            print (f'Error: {e}')
            response = None
            
        if response:
            if isinstance(text, list): 
                embeddings = [r.embedding for r in response.data]
            elif isinstance(text, str):
                embeddings = response.data[0].embedding
            return embeddings
        else:
            return [] 
    
    def calc_similarity_nim(self, context, question):
        #cosine similarity 
        doc_embed = self.get_nim_embedding(text=context, 
                                          input_type='passage')
        q_embed = self.get_nim_embedding(text=question,
                                        input_type='query')
        if isinstance(context, list) and isinstance(question, list):
            if doc_embed and q_embed:
                sim = np.diag(np.dot(np.array(doc_embed), np.array(q_embed).T))
            else:
                sim = np.zeros(len(context)) # keep the question
        else: 
            if doc_embed and q_embed:
                sim = np.dot(doc_embed, q_embed)
            else:
                sim = 0.
            
        return list(sim)


class AnswerabilityFilter(Filter):
    def __init__(self, filter_cfg: DictConfig):
        self.prefix = "answerability"
        self.base_url = filter_cfg.base_url
        self.api_key = filter_cfg.api_key
        self.model_name = filter_cfg.model_name
        self.system_prompt = filter_cfg.system_prompt
        self.user_prompt_template = filter_cfg.user_prompt_template
        self.num_criteria = filter_cfg.num_criteria

    def filter(self,
               corpus: Corpus) -> Corpus:
        """Directly add scores to the corpus"""
        annotated_corpus = copy.deepcopy(corpus)
        for example in annotated_corpus.data["data"]:
            context = example["paragraphs"][0]["context"]
            if example["paragraphs"][0]["qas"]:
                for qa in example["paragraphs"][0]["qas"]:
                    question = qa["question"]
                    filter_result, score = self.llm_as_judge(context, question)
                    qa[f"{self.prefix}__keep"] = filter_result
                    qa[f"{self.prefix}__llm_as_judge_score"] = score
        return annotated_corpus

    def llm_as_judge(self,
                     context: str,
                     question: str):
        client = OpenAI(
            base_url = self.base_url,
            api_key = self.api_key
        )
        
        user_query = self.system_prompt + "\n\n" 
        user_query += self.user_prompt_template.format(context=context,
                                                                question=question)

        try:                                              
            completion = client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": user_query}],
                temperature=0.5,
                top_p=1,
                max_tokens=1024,
                stream=True
            )

            generation = ""
            for chunk in completion:
                if chunk.choices[0].delta.content is not None:
                    generation += chunk.choices[0].delta.content
        except Exception as e:
            print(f"API call error {e}")
            return None, None  # is_keep, generation
    
        is_keep = True # default is to keep
        try:
            json_ans = json.loads(generation)
            for i in range(self.num_criteria):
                if json_ans[f"criterion_{i+1}"] != "Y":
                    # filter out data if any of the criteria fails
                    is_keep = False  # filter out
                    break
        except Exception as e:
            print (f"Parse error {e}")
            # if there is an error, return None
            is_keep = None
    
        return is_keep, generation
    