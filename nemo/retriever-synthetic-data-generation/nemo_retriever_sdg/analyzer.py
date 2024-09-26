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
from dataclasses import dataclass
import json

import pandas as pd

from .dataset import Corpus

@dataclass
class Report:
    report: dict

    def __add__(self, other: 'Report') -> 'Report':
        new_report = dict(self.report)
        new_report.update(other.report)
        return Report(new_report)    

    def write_json(self, output_path: str):
        with open(output_path, "w") as f:
            json.dump(self.report, f)

class Analyzer(ABC):
    @abstractmethod
    def analyze(self, corpus: Corpus) -> Report:
        pass

class DummyAnalyzer(Analyzer):
    def analyze(self, corpus: Corpus) -> dict:
        return Report({})


class QuestionLengthAnalyzer(Analyzer):
    def analyze(self, corpus: Corpus) -> dict:
        synthetic_qlen_list =[]
        original_qlen_list = []
        for example in corpus.data["data"]:
            for qa in example["paragraphs"][0]["qas"]:
                if "synthetic" in qa and qa["synthetic"]:
                    # * Synthetic questions
                    synthetic_qlen_list.append(len(qa["question"]))
                else:
                    # * Original questions
                    original_qlen_list.append(len(qa["question"]))

        return Report({"synthetic_question_length": pd.Series(synthetic_qlen_list).describe().to_dict(),
                       "original_question_length": pd.Series(original_qlen_list).describe().to_dict()})

class LexicalDivergenceAnalyzer(Analyzer):
    def analyze(self, corpus: Corpus) -> dict:
        synthetic_ldiv_list =[]
        original_ldiv_list = []
        for example in corpus.data["data"]:
            for qa in example["paragraphs"][0]["qas"]:
                if "lexical_divergence" not in qa:
                    continue
                if "synthetic" in qa and qa["synthetic"]:
                    # * Synthetic questions
                    synthetic_ldiv_list.append(qa["lexical_divergence"])
                else:
                    # * Original questions
                    original_ldiv_list.append(qa["lexical_divergence"])

        return Report({"synthetic_lexical_divergence": pd.Series(synthetic_ldiv_list).describe().to_dict(),
                       "original_lexical_divergence": pd.Series(original_ldiv_list).describe().to_dict()})
    

# TODO
# Retriever model analyzer?
# Difficulty judgement