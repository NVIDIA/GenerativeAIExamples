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

import os

import hydra
from hydra.utils import instantiate
from omegaconf import DictConfig

from nemo_retriever_sdg import Corpus, Filters, Report, EvaluatorConfig

@hydra.main(version_base=None, config_path="conf", config_name="config.yaml")
def main(cfg: DictConfig) -> None:
    # Do not overwrite existing output directory
    if os.path.exists(cfg.output_dir):
        raise ValueError(f"Output directory {cfg.output_dir} already exists. Please remove it or specify a new directory.")

    # if(cfg.qa_generator.qa_generations_file is None):
    #     cfg.qa_generator.qa_generations_file = cfg.output_dir.rstrip("/") + "_qa_generations_file.jsonl"
    
    # ** Create instances
    # * Pre-processors
    pre_processors = []
    for pre_processor in cfg.pre_processors:
        # The user can customize the pre_processor by adding a class in the config file
        pre_processors.append(instantiate(pre_processor))
        
    # * QA Generator
    qa_generator = instantiate(cfg.qa_generator)

    # * Post-processors
    post_processors = []
    for post_processor in cfg.post_processors:
        # The user can customize the post_processor by adding a class in the config file
        post_processors.append(instantiate(post_processor))

    # * Filters
    # Filters will add {filter_name}__is_keep fields to the data
    filters = Filters()
    for filter in cfg.filters:
        # The user can customize the filter by adding a class in the config file
        filters.add(instantiate(filter))

    # * Analyzers
    analyzers = []
    for analyzer in cfg.analyzers:
        # The user can customize the analyzer by adding a class in the config file
        analyzers.append(instantiate(analyzer))

    # ** Load dataset
    corpus = Corpus.load_data(cfg.input_file,
                              cfg.input_format)

    # ** Run the pipeline
    for pre_processor in pre_processors:
        corpus = pre_processor.process(corpus)

    corpus = qa_generator.generate_qa_pairs(corpus)

    for post_processor in post_processors:
        corpus = post_processor.process(corpus)

    # Apply filters and create two corpora:
    #   (1) one with all examples
    #   (2) one with filtered examples
    corpus_all, corpus_filtered = filters.apply_filters(corpus)

    # ** Save the dataset
    squad_output_dir = os.path.join(cfg.output_dir, "squad")
    beir_output_all_dir = os.path.join(cfg.output_dir, "beir", "all")
    beir_output_filtered_dir = os.path.join(cfg.output_dir, "beir", "filtered")

    if not os.path.exists(cfg.output_dir):
        os.makedirs(squad_output_dir)
        os.makedirs(beir_output_all_dir)
        os.makedirs(beir_output_filtered_dir)

    # 1) SQuAD format
    corpus_all.to_json(os.path.join(squad_output_dir, "synthetic_data__all.json"))
    corpus_filtered.to_json(os.path.join(squad_output_dir, "synthetic_data__filtered.json"))

    # 2) BEIR format (directory)
    # if input_format is not SQuAD, this step will not create original directory
    corpus_all.to_beir(beir_output_all_dir, cfg.input_format=="squad")
    corpus_filtered.to_beir(beir_output_filtered_dir, cfg.input_format=="squad")

    # * Analyze the dataset
    for name, cur_corpus in [("all", corpus_all), ("filtered", corpus_filtered)]:
        report = Report({})
        for analyzer in analyzers:
            report += analyzer.analyze(cur_corpus)
        report.write_json(os.path.join(cfg.output_dir, f"report__{name}.json"))

    # * Evaluate retriever models
    if hasattr(cfg, "evaluators") and len(cfg.evaluators) > 0:
        for filter_type, cur_corpus in [("all", corpus_all), ("filtered", corpus_filtered)]:
            eval_dirpath = os.path.join(cfg.output_dir, "eval", filter_type)
            if not os.path.exists(eval_dirpath):
                os.makedirs(eval_dirpath)
            for evaluator in cfg.evaluators:
                # Currently, only supports BEIR evaluator
                evaluator = instantiate(evaluator)
                evaluator_cfg = EvaluatorConfig(cfg, eval_dirpath)
                evaluator.evaluate(evaluator_cfg,
                                   filter_type,
                                   cfg.use_original if hasattr(cfg, "use_original") else False)

if __name__ == "__main__":
    main()