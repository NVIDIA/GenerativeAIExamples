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

import copy

import nltk

from .dataset import Corpus
from .processor import Processor


class DivergenceCalculator(Processor):
    def __init__(self):
        pass

    def process(self,
                corpus: Corpus) -> Corpus:
        """Directly add scores to the corpus"""
        annotated_corpus = copy.deepcopy(corpus)
        for example in annotated_corpus.data["data"]:
            context = example["paragraphs"][0]["context"]
            for qa in example["paragraphs"][0]["qas"]:
                question = qa["question"]
                # TODO: Will update the field name
                qa["lexical_divergence"] = self.calculate_lexical_divergence(context, question)
                # qa["syntactic_divergence"] = self.calculate_syntactic_divergence(context, question)
        return annotated_corpus

    def calculate_lexical_divergence(self,
                                     sent1,
                                     sent2,
                                     n: int = 1):
        """Lexical divergence (PINC score)"""
        sum_ = 0
        index = 0
        for i in range(1, n + 1):
            s = set(nltk.ngrams(sent1, i,pad_left = False, pad_right = False)) 
            p = set(nltk.ngrams(sent2, i,pad_left = False, pad_right = False))
            if s and p:
                index += 1
                intersection = s.intersection(p)
                sum_ += 1 - len(intersection) / len(p)

        if index == 0:
            return 0

        return sum_ / index
    
    def calculate_syntactic_divergence(self,
                                       sent1,
                                       sent2):
        """Syntactic divergence
        https://github.com/jasonyux/FastKASSIM 
        """
        pass
        # similarity = fkassim.FastKassim(fkassim.FastKassim.FTK).compute_similarity(query, passage)
        # return 1. - similarity