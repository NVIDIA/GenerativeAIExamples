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

import json
import logging
import os
import statistics

from datasets import Dataset
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
from ragas import evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_relevancy,
    answer_similarity,
    context_precision,
    context_recall,
    context_relevancy,
    faithfulness,
)

LLAMA_PROMPT_TEMPLATE = (
    "<s>[INST] <<SYS>>"
    "{system_prompt}"
    "<</SYS>>"
    ""
    "Example 1:"
    "[Question]"
    "When did Queen Elizabeth II die?"
    "[The Start of the Reference Context]"
    """On 8 September 2022, Buckingham Palace released a statement which read: "Following further evaluation this morning, the Queen's doctors are concerned for Her Majesty's health and have recommended she remain under medical supervision. The Queen remains comfortable and at Balmoral."[257][258] Her immediate family rushed to Balmoral to be by her side.[259][260] She died peacefully at 15:10 BST at the age of 96, with two of her children, Charles and Anne, by her side;[261][262] Charles immediately succeeded as monarch. Her death was announced to the public at 18:30,[263][264] setting in motion Operation London Bridge and, because she died in Scotland, Operation Unicorn.[265][266] Elizabeth was the first monarch to die in Scotland since James V in 1542.[267] Her death certificate recorded her cause of death as old age"""
    "[The End of Reference Context]"
    "[The Start of the Reference Answer]"
    "Queen Elizabeth II died on September 8, 2022."
    "[The End of Reference Answer]"
    "[The Start of the Assistant's Answer]"
    "She died on September 8, 2022"
    "[The End of Assistant's Answer]"
    '"Rating": 5, "Explanation": "The answer is helpful, relevant, accurate, and concise. It matches the information provided in the reference context and answer."'
    ""
    "Example 2:"
    "[Question]"
    "When did Queen Elizabeth II die?"
    "[The Start of the Reference Context]"
    """On 8 September 2022, Buckingham Palace released a statement which read: "Following further evaluation this morning, the Queen's doctors are concerned for Her Majesty's health and have recommended she remain under medical supervision. The Queen remains comfortable and at Balmoral."[257][258] Her immediate family rushed to Balmoral to be by her side.[259][260] She died peacefully at 15:10 BST at the age of 96, with two of her children, Charles and Anne, by her side;[261][262] Charles immediately succeeded as monarch. Her death was announced to the public at 18:30,[263][264] setting in motion Operation London Bridge and, because she died in Scotland, Operation Unicorn.[265][266] Elizabeth was the first monarch to die in Scotland since James V in 1542.[267] Her death certificate recorded her cause of death as old age"""
    "[The End of Reference Context]"
    "[The Start of the Reference Answer]"
    "Queen Elizabeth II died on September 8, 2022."
    "[The End of Reference Answer]"
    "[The Start of the Assistant's Answer]"
    "Queen Elizabeth II was the longest reigning monarch of the United Kingdom and the Commonwealth."
    "[The End of Assistant's Answer]"
    '"Rating": 1, "Explanation": "The answer is not helpful or relevant. It does not answer the question and instead goes off topic."'
    ""
    "Follow the exact same format as above. Put Rating first and Explanation second. Rating must be between 1 and 5. What is the rating and explanation for the following assistant's answer"
    "Rating and Explanation should be in JSON format"
    "[Question]"
    "{question}"
    "[The Start of the Reference Context]"
    "{ctx_ref}"
    "[The End of Reference Context]"
    "[The Start of the Reference Answer]"
    "{answer_ref}"
    "[The End of Reference Answer]"
    "[The Start of the Assistant's Answer]"
    "{answer}"
    "[The End of Assistant's Answer][/INST]"
)
SYS_PROMPT = """
    You are an impartial judge that evaluates the quality of an assistant's answer to the question provided.
    You evaluation takes into account helpfullness, relevancy, accuracy, and level of detail of the answer.
    You must use both the reference context and reference answer to guide your evaluation.
    """

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def calculate_ragas_score(row):
    values = row[['faithfulness', 'context_relevancy', 'answer_relevancy', 'context_recall']].values
    return statistics.harmonic_mean(values)


def eval_ragas(ev_file_path, ev_result_path, llm_model='ai-mixtral-8x7b-instruct'):
    """
    This function evaluates a language model's performance using a dataset and metrics.
    It sets the NVAPI_KEY, initializes a ChatNVIDIA model and LangchainLLM object, loads the
    evaluation dataset, prepares data samples, creates a Dataset object, sets the language model
    for each metric, and evaluates the model with the specified metrics, printing the results.
    """
    llm_params = {
        "temperature": 0.1,
        "max_tokens": 200,
        "top_p": 1.0,
        "stream": False,
    }
    nvidia_api_key = os.environ["NVIDIA_API_KEY"]
    llm_params["nvidia_api_key"] = nvidia_api_key
    llm_params["model"] = llm_model
    llm = ChatNVIDIA(**llm_params)
    nvpl_llm = LangchainLLMWrapper(langchain_llm=llm)
    embeddings = NVIDIAEmbeddings(model="ai-embed-qa-4", model_type="passage", truncate="END")
    nvpl_embeddings = LangchainEmbeddingsWrapper(embeddings)
    try:
        with open(ev_file_path, "r", encoding="utf-8") as file:
            json_data = json.load(file)
    except Exception as e:
        logger.info(f"Error Occured while loading file : {e}")
    eval_questions = []
    eval_answers = []
    ground_truth = []
    vdb_contexts = []
    for entry in json_data:
        eval_questions.append(entry["question"])
        eval_answers.append(entry["generated_answer"])
        vdb_contexts.append(entry["retrieved_context"])
        ground_truth.append(entry["ground_truth_answer"])

    data_samples = {
        'question': eval_questions,
        'answer': eval_answers,
        'contexts': vdb_contexts,
        'ground_truth': ground_truth,
    }
    dataset = Dataset.from_dict(data_samples)

    result = evaluate(
        dataset,
        llm=llm,
        embeddings=nvpl_embeddings,
        metrics=[
            answer_similarity,
            faithfulness,
            context_precision,
            context_relevancy,
            answer_relevancy,
            context_recall,
        ],
    )
    df = result.to_pandas()
    df['ragas_score'] = df.apply(calculate_ragas_score, axis=1)
    df.to_parquet(ev_result_path + '.parquet')
    result['ragas_score'] = statistics.harmonic_mean(
        [result['faithfulness'], result['context_relevancy'], result['answer_relevancy'], result['context_recall']]
    )
    with open(ev_result_path + '.json', "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=2)

    logger.info(f"Results written to {ev_result_path}.json and {ev_result_path}.parquet")


def eval_llm_judge(ev_file_path, ev_result_path, llm_model='ai-mixtral-8x7b-instruct'):
    """
    The function utilizes pre-trained Judge LLM to assess the coherence and relevance of a generated answer
    for a given question and context. It returns a Likert rating between 1 and 5, indicating the quality of
    the answer and an explanation supporting the same, returns the mean of likert rating, dumping the same in JSON format.
    """
    llm_params = {
        "temperature": 0.1,
        "max_tokens": 200,
        "top_p": 1.0,
        "stream": False,
    }
    nvidia_api_key = os.environ["NVIDIA_API_KEY"]
    llm_params["nvidia_api_key"] = nvidia_api_key
    llm_params["model"] = llm_model

    llm = ChatNVIDIA()
    # Read the JSON file
    try:
        with open(ev_file_path, "r", encoding="utf-8") as file:
            data = json.load(file)
    except Exception as e:
        logger.info(f"Error Occured while loading file : {e}")

    llama_ratings = []
    llama_explanations = []
    for d in data:
        try:
            context = LLAMA_PROMPT_TEMPLATE.format(
                system_prompt=SYS_PROMPT,
                question=d["question"],
                ctx_ref=d["ground_truth_context"],
                answer_ref=d["ground_truth_answer"],
                answer=d["answer"],
            )

            response = llm.invoke(context)
            response_body = json.loads(response.content)
            rating = response_body["Rating"]
            explanantion = response_body["Explanantion"]
            llama_ratings.append(rating)
            llama_explanations.append(explanantion)
            logger.info(f"progress: {len(llama_explanations)}/{len(data)}")
        except Exception as e:
            logger.info(f"Exception Occured: {e}")
            llama_ratings.append(None)

    logger.info(f"Number of judgements: {len(llama_ratings)}")

    llama_ratings = [1 if r == 0 else r for r in llama_ratings]  # Change 0 ratings to 1
    llama_ratings_filtered = [r for r in llama_ratings if r]  # Remove empty ratings

    mean = round(statistics.mean(llama_ratings_filtered), 1)
    logger.info(f"Number of ratings: {len(llama_ratings_filtered)}")
    logger.info(f"Mean rating: {mean}")

    results = list(
        zip(
            llama_ratings,
            llama_explanations,
            [d["question"] for d in data],
            [d["answer"] for d in data],
            [d["ground_truth_answer"] for d in data],
            [d["ground_truth_context"] for d in data],
        )
    )

    with open(ev_result_path, "w", encoding="utf-8") as json_file:
        json.dump(results, json_file, indent=2)

    logger.info(f"Results written to {ev_result_path}")
