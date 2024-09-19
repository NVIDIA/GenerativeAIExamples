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
import os
from warnings import warn

from beir.retrieval import models
from beir.datasets.data_loader import GenericDataLoader
from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.dense import DenseRetrievalExactSearch as DRES
from omegaconf import DictConfig
import pandas as pd


@dataclass
class EvaluatorConfig:
    cfg: DictConfig
    eval_dirpath: str

@dataclass
class EvaluatorResult:
    results: dict

class Evaluator(ABC):
    @abstractmethod
    def evaluate(self,
                 cfg: EvaluatorConfig,
                 use_original: bool = False) -> EvaluatorResult:
        pass


class BEIREvaluator(Evaluator):
    def __init__(self,
                 model_names: list[str],
                 score_function: str = "cos_sim",
                 batch_size: int = 16):
        self.model_names = model_names
        self.score_function = score_function
        self.batch_size = batch_size
    
    def __get_topk_rel_doc_flags(self,
                                 results: dict,
                                 qrels: dict,
                                 topk: int = 5) -> pd.Series:
        """Return list[bool] = True if at least one relevant document is in the topk retrieved documents"""
        topk_rel_list = []
        topk_qid_list = []
        for qid, qrel_dict in qrels.items():
            topk_qid_list.append(qid)
            topk_doc_ids = pd.Series(results[qid]).sort_values(ascending=False).head(topk).index.tolist()
            rel_doc_ids = list(qrel_dict.keys())
            if len(set(topk_doc_ids) & set(rel_doc_ids)) >= 1:
                topk_rel_list.append(True)
            else:
                topk_rel_list.append(False)

        topk_s = pd.Series(topk_rel_list)
        topk_s.index = topk_qid_list

        return topk_s

    def evaluate(self,
                 cfg: EvaluatorConfig,
                 filter_type: str, # "all" or "filtered"
                 use_original: bool = False) -> EvaluatorResult:
        type_model_results_dict = {"original": {}, "synthetic": {}}
        type_model_eval_dict = {"original": {}, "synthetic": {}}
        type_topk_rel_doc_flags = {"original": {}, "synthetic": {}}

        beir_output_dir = os.path.join(cfg.cfg.output_dir, "beir")

        for type in ["original", "synthetic"] if use_original else ["synthetic"]:
            data_folder = os.path.join(beir_output_dir, filter_type, type)  # beir/all/synthetic
            if os.path.exists(data_folder):
                corpus, queries, qrels = GenericDataLoader(data_folder=data_folder).load(split="test")
    
                for model_name in self.model_names:
                    # if ".nemo" in model_name:
                    #     model = DRES(NeMoModel(model_name), batch_size=args.batch_size)
                    # else:
                    model = DRES(models.SentenceBERT(model_name), batch_size=self.batch_size)
                    retriever = EvaluateRetrieval(model, score_function=self.score_function) # dot or "cos_sim" for cosine similarity
                    results = retriever.retrieve(corpus, queries)
                    type_model_results_dict[type][model_name] = results
                    ndcg, map, recall, precision = retriever.evaluate(qrels, results, retriever.k_values)
                    type_model_eval_dict[type][model_name] = {"ndcg": ndcg,
                                                            "map": map,
                                                            "recall": recall,
                                                            "precision": precision}
                    topk_rel_doc_flags = self.__get_topk_rel_doc_flags(results, qrels)
                    type_topk_rel_doc_flags[type][model_name] = topk_rel_doc_flags
            else:
                warn("Data folder does not exist: {}".format(data_folder))

        if use_original:
            recall5_df = pd.DataFrame([{"model_name": x,
                                        "original": type_model_eval_dict["original"][x]["recall"]["Recall@5"],
                                        "synthetic": type_model_eval_dict["synthetic"][x]["recall"]["Recall@5"]} for x in type_model_eval_dict["synthetic"]])
        else:
            # Only synthetic
            recall5_df = pd.DataFrame([{"model_name": x,
                                        "synthetic": type_model_eval_dict["synthetic"][x]["recall"]["Recall@5"]} for x in type_model_eval_dict["synthetic"]])
            
        recall5_df.to_csv(os.path.join(cfg.eval_dirpath, "beir_evaluator__recall5.csv"), index=False)

        with open(os.path.join(cfg.eval_dirpath, "beir_evaluator__type_model_eval_dict.json"), "w") as f:
            json.dump(type_model_eval_dict, f, indent=4)

        """
        pd.DataFrame(type_topk_rel_doc_flags["original"])
            sentence-transformers/gtr-t5-large  msmarco-distilbert-base-tas-b  intfloat/e5-large-unsupervised
        157                                True                           True                            True
        190                                True                           True                           False
        140                                True                           True                            True
        54                                 True                           True                            True
        147                                True                           True                           False
        ..                                  ...                            ...                             ...
        14                                False                           True                            True
        143                                True                           True                            True
        49                                 True                          False                            True
        74                                False                          False                           False
        154                                True                          False                           False
        """
        pd.DataFrame(type_topk_rel_doc_flags["synthetic"]).to_csv(os.path.join(cfg.eval_dirpath, "beir_evaluator__synthetic_topk_rel_doc_flags.csv"))
        if use_original:
            pd.DataFrame(type_topk_rel_doc_flags["original"]).to_csv(os.path.join(cfg.eval_dirpath, "beir_evaluator__original_topk_rel_doc_flags.csv"))
        """
        3    70
        0    34
        2    21
        1    12
        """
        pd.DataFrame(type_topk_rel_doc_flags["synthetic"]).sum(axis=1).value_counts().to_csv(os.path.join(cfg.eval_dirpath, "beir_evaluator__synthetic_topk_rel_doc_flags_counts.csv"))
        if use_original:
            pd.DataFrame(type_topk_rel_doc_flags["original"]).sum(axis=1).value_counts().to_csv(os.path.join(cfg.eval_dirpath, "beir_evaluator__original_topk_rel_doc_flags_counts.csv"))
