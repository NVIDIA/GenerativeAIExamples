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

import argparse
import logging

from evaluator import eval_llm_judge, eval_ragas
from llm_answer_generator import generate_answers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument("--base_url", type=str, help="Specify the base URL to be used.")
    parser.add_argument(
        "--generate_answer",
        type=bool,
        nargs="?",
        default=False,
        help="Specify if 'answer' generation by RAG pipeline is required.",
    )
    parser.add_argument(
        "--evaluate", type=bool, nargs="?", default=True, help="Specify if evaluation is required.",
    )
    parser.add_argument(
        "--docs", type=str, nargs="?", default="", help="Specify the folder path for dataset.",
    )
    parser.add_argument(
        "--ga_input",
        type=str,
        nargs="?",
        default="",
        help="Specify the .json file with QnA pair for generating answers by RAG pipeline.",
    )
    parser.add_argument(
        "--ga_output",
        type=str,
        nargs="?",
        default="",
        help="Specify the .JSON file path for generated answers along with QnA.",
    )
    parser.add_argument(
        "--ev_input",
        type=str,
        nargs="?",
        default="",
        help="Specify the .JSON file path with 'question','gt_answer','gt_context','answer',and 'contexts'.",
    )
    parser.add_argument(
        "--ev_result", type=str, nargs="?", default="", help="Specify the file path to store evaluation results.",
    )
    parser.add_argument(
        "--metrics",
        type=str,
        nargs="?",
        default="judge_llm",
        choices=["ragas", "judge_llm"],
        help="Specify evaluation metrics between ragas and judge-llm.",
    )
    parser.add_argument(
        "--judge_llm_model",
        type=str,
        nargs="?",
        default="ai-mixtral-8x7b-instruct",
        help="Specify the LLM model to be used as judge llm for evaluation from ChatNVIDIA catalog.",
    )
    args = parser.parse_args()

    if args.generate_answer:
        generate_answers(
            base_url=args.base_url,
            dataset_folder_path=args.docs,
            qa_generation_file_path=args.ga_input,
            eval_file_path=args.ga_output,
        )

    logger.info("\nANSWERS GENERATED\n")
    if args.evaluate:
        if args.metrics == "ragas":
            eval_ragas(
                ev_file_path=args.ev_input, ev_result_path=args.ev_result, llm_model=args.judge_llm_model,
            )
            logger.info("\nRAG EVALUATED WITH RAGAS METRICS\n")
        elif args.metrics == "judge_llm":
            eval_llm_judge(
                ev_file_path=args.ev_input, ev_result_path=args.ev_result, llm_model=args.judge_llm_model,
            )
            logger.info("\nRAG EVALUATED WITH JUDGE LLM\n")
