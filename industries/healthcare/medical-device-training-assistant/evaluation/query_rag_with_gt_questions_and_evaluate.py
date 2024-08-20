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

import os
import json
import requests
import mimetypes
import typing
import statistics

import argparse
import logging

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
from datasets import Dataset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# assume that the chain server from our IFU RAG is running at port 8081
url_generate = f"http://chain-server:8081/generate"
url_doc_search = f"http://chain-server:8081/search"


def read_gt_qa_pairs_into_json(gt_qa_pairs_doc):
    # assume gt_qa_pairs_doc is a txt file that has format:
    # ......
    # Example n:
    # Question: How do your perform xyz?
    # Answer: [Start the ground truth answer] ...
    # ... (any number of lines in the ground truth answer)
    # ...
    # Example n+1:
    # ......

    assert os.path.exists(gt_qa_pairs_doc), "Check your specification for arg gt_qa_pairs_doc (txt)"

    gt_to_write = []
    curr_item = {}

    in_answer = False
    with open(gt_qa_pairs_doc, "rb") as file:
        for line in file:
            line = line.rstrip().decode("utf-8")
            if line.startswith("Example"):
                in_answer = False
                if curr_item != {}:
                    gt_to_write.append(curr_item)
                    curr_item = {}
                #print(line)
                
            elif line.startswith("Question: "):
                line = line[len("Question: "):]
                #print(line)
                assert curr_item == {}
                curr_item["question"] = line
            elif line.startswith("Answer: "):
                in_answer = True
                line = line[len("Answer: "):]
                #print(line)
                curr_item["gt_answer"] = line
            else:
                if in_answer:
                    curr_item["gt_answer"] += "\n"
                    curr_item["gt_answer"] += line
        if curr_item != {}:
            gt_to_write.append(curr_item)
    file.close()
    return gt_to_write

def write_to_json(list_of_dict, output_filename):
    assert list_of_dict != [], "List of dict to be written in json cannot be empty!"
    with open(output_filename, "w", encoding="utf-8") as f:
        json.dump(list_of_dict, f, indent=2)
    
def query_rag_for_each_question(data):
    # assume data is a list of dicts
    # each dict contains two keys "question" and "gt_answer"
    print("There are {} pairs of GT question answers".format(len(data)))
    counter = 0 
    new_data=[]
    for entry in data:
        counter += 1
        print("Querying the RAG with question number {} / {}".format(counter,len(data)))
        entry_to_query = {
            "messages":[
                {
                    "role":"user",
                    "content":entry["question"]
                }
            ],
            "use_knowledge_base": True,
            "temperature": 0.2,
            "top_p": 0.7,
            "max_tokens": 256,
            "stop":["string"]
        }
        # populate the "answer" field with the answer from RAG
        entry["answer"] = ""
        try:
            with requests.post(url_generate, stream=True, json=entry_to_query) as r:
                for chunk in r.iter_lines():
                    raw_resp = chunk.decode("UTF-8")
                    if not raw_resp:
                        continue
                    resp_dict = None
                    try:
                        resp_dict = json.loads(raw_resp[6:])
                        resp_choices = resp_dict.get("choices", [])
                        if len(resp_choices):
                            resp_str = resp_choices[0].get("message", {}).get("content", "")
                            entry["answer"] += resp_str
                    except Exception as e:
                        print(f"Exception Occured: {e}")
        except Exception as e:
            print(f"Exception Occured: {e}")
            entry["answer"] = "Answer couldn't be generated."
        # populate the "context" field from the RAG
        entry_doc_search = {
                "query": entry["question"],
                "top_k": 1
            }
        response = requests.post(url_doc_search, json=entry_doc_search).json()
        context_list =typing.cast(typing.List[typing.Dict[str, typing.Union[str, float]]], response)
        contexts = [context.get("content") for context in context_list['chunks']]
        try:
            entry["contexts"] = [contexts[0]]
        except Exception as e:
            print(f"Exception Occured: {e}")
            entry["contexts"] = ""
        new_data.append(entry)
    return new_data     

def eval_with_ragas_metrics(evaluate_data, ev_result_path, llm_model="meta/llama3-70b-instruct", embedding_model = "ai-embed-qa-4"):
    """
    This function evaluates a language model's performance using a dataset and metrics.
    It sets the NVAPI_KEY, initializes a ChatNVIDIA model and LangchainLLM object, loads the
    evaluation dataset, prepares data samples, creates a Dataset object, sets the language model
    for each metric, and evaluates the model with the specified metrics, printing the results.
    """
    llm_params = {
        "temperature": 0.2,
        "max_tokens": 1024,
    }
    nvidia_api_key = os.environ["NVIDIA_API_KEY"]
    llm_params["nvidia_api_key"] = nvidia_api_key
    llm_params["model"] = llm_model
    llm = ChatNVIDIA(**llm_params)
    nvpl_llm = LangchainLLMWrapper(langchain_llm=llm)
    embeddings = NVIDIAEmbeddings(model=embedding_model, model_type="passage")
    nvpl_embeddings = LangchainEmbeddingsWrapper(embeddings)
    
    eval_questions = []
    eval_answers = []
    ground_truth = []
    vdb_contexts = []
    for entry in evaluate_data:
        eval_questions.append(entry["question"])
        eval_answers.append(entry["answer"])
        vdb_contexts.append(entry["contexts"])
        ground_truth.append(entry["gt_answer"])
        

    data_samples = {
        'question': eval_questions,
        'answer': eval_answers,
        'contexts': vdb_contexts,
        'ground_truth': ground_truth,
    }
    dataset = Dataset.from_dict(data_samples)

    result = evaluate(
        dataset,
        llm=nvpl_llm,
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
    print(result)
    df = result.to_pandas()
    def calculate_ragas_score(row):
        values = row[['faithfulness', 'context_relevancy', 'answer_relevancy', 'context_recall']].values
        return statistics.harmonic_mean(values)
    df['ragas_score'] = df.apply(calculate_ragas_score, axis=1)
    df.to_parquet(ev_result_path + '.parquet')
    result['ragas_score'] = statistics.harmonic_mean(
        [result['faithfulness'], result['context_relevancy'], result['answer_relevancy'], result['context_recall']]
    )
    with open(ev_result_path + '.json', "w", encoding="utf-8") as json_file:
        json.dump(result, json_file, indent=2)

    logger.info(f"Results written to {ev_result_path}.json and {ev_result_path}.parquet")


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--gt_qa_pairs_doc", type=str, nargs="?", default="", help="A .txt or .json document that should contain ground truth question-answer pairs. See README for required format.",
    )
    parser.add_argument(
        "--output_dir", type=str, nargs="?", default="", help="Specify the output directory for the evaluation results and optional json files",
    )
    parser.add_argument(
        "--eval_result_name", type=str, nargs="?", default="", help="Specify the output file name of the evaluation files.",
    )
    
    
    args = parser.parse_args()
    if args.gt_qa_pairs_doc.endswith(".txt"):
        # consume the txt document of ground truth question-answer pairs into json format
        gt_qa_pairs = read_gt_qa_pairs_into_json(args.gt_qa_pairs_doc)
        # write question-answer pairs in json format to file
        write_to_json(gt_qa_pairs, output_filename = os.path.join(args.output_dir, 'ground_truth_qa_pairs.json'))
    elif args.gt_qa_pairs_doc.endswith(".json"):
        with open(args.gt_qa_pairs_doc) as f:
            gt_qa_pairs = json.load(f)
    else:
        raise Exception("The --gt_qa_pairs_doc arg must be either a .txt or .json file")
    
    # for each question in the gt qa pairs, query the IFU RAG for an answer and retrieved context
    queried_data = query_rag_for_each_question(gt_qa_pairs)
    # write each item in queried data that has these fields: {question, gt_answer, answer, contexts} in json format to file
    write_to_json(queried_data, output_filename = os.path.join(args.output_dir, 'data_to_evaluate.json'))
    # with each {question, gt_answer, answer, contexts}, we can evaluate the RAG performance according to the RAGAS metrics
    eval_with_ragas_metrics(queried_data, os.path.join(args.output_dir, args.eval_result_name), llm_model="meta/llama3-70b-instruct", embedding_model = "ai-embed-qa-4")

