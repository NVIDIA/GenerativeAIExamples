# Evaluating the Medical Device Training Assistant

## Introduction

Evaluation is crucial for retrieval augmented generation (RAG) pipelines because it ensures the accuracy and relevance of the information that is retrieved as well as the generated content.

There are three components needed for evaluating the performance of a RAG pipeline:

- Ground truth data to evaluate. We will assume the ground truth data comes in the form of question-answer pairs, so the GT answer can be compared with the retrieved answer and context.
- A running chain server from the IFU RAG at port 8081. We assume there are IFU documents uploaded via the web UI to the Knowledge Base, and use the documents shown in the Knowledge Base for evaluation of the RAG performance. We will send each question from the GT question-answer pairs document to the IFU RAG, receive an answer back from the IFU RAG, and compare the received answer to the ground truth answer.
- Automated metrics (RAGAS) to measure performance of both the context retrieval and response generation.


This tool provides a set of notebooks that demonstrate how to address these requirements in an automated fashion for the default developer RAG example.

### Automated Metrics

[RAGAS](https://github.com/explodinggradients/ragas) is an automated metrics tool for measuring performance of both the retriever and generator.
This tool uses a LangChain wrapper to connect to NVIDIA API Catalog endpoints to run RAGAS evaluation on our example RAG pipeline.


## Prerequisites

The assumption is that you have already started a RAG application, and the chain server is running on port 8081. 

Navigate to the Knowledge Base tab on the web browser, and see which document(s) are currently uploaded. The document name(s) shown under `File Uploaded` in the middle of the browser is what the RAG will be retrieving answers from during evaluation. Make sure to add and remove documents using the `Add File` and `Delete` buttons on the web UI until the list under `File Uploaded` shows you exactly the document(s) that you want for evaluating the RAG's capability to produce a desired answer.

## Build and Start the Containers

1. Export the `NVIDIA_API_KEY` variable in terminal.

   Add the API for the model endpoint:

   ```text
   export NVIDIA_API_KEY="nvapi-<...>"
   ```
2. Edit the `compose.env` file and set directory paths for
    - `DATA_DIR`: This is a directory which we assume contains the the GT QA pairs txt or json file
    - `OUTPUT_DIR`: This is the directory to write the output files to from the evaluation process. Make sure this directory exists.
    - `GT_QA_DOC`: This is the name of the txt or json document that has the GT QA pairs for evaluation purposes. If this is a txt file, the GT QA pairs will also be written in json format in `OUTPUT_DIR`.
    
      If this is a txt document, we will assume this document has content in the following format with a empty line first:

       ```
      
      Example 1:
      Question: This is the first question
      Answer: Answer begins here...
      and continues in multiple lines if needed
      and ends before the next line containing "Example n:"...
      Example 2:
       ...
       ```
      If this is a json document, we will assume this document has content in the following format:

       ```
      [
        {
          "question": "This is the first question",
          "gt_answer": "This is the first answer"
        },
        {
          "question": "This is the second question",
          "gt_answer": "This is the second answer"
        },
        ...
      ]
       ``` 
       
  
3. Evaluate a RAG pipeline:

   ```console
   # Build the docker image and run
   docker compose --env-file compose.env up --build
   ```

   ```console
   # After the first time running, if no changes to the Docker image were made, no need to build again
   docker compose --env-file compose.env up
   ```

   Please note it is expected that the terminal appears to be hanging 
   ```output
   [+] Running 1/0
   ✔ Container rag-evaluator Created                    0.0s 
   Attaching to rag-evaluator
   ```
   To verify that the evaluation is ongoing, you could use `docker logs chain-server` to see the request logs.

   The amount of time to wait will depend on the number of queries in your ground truth QA pairs document.

   *Example Output after completion*

   ```output
   rag-evaluator  | Querying the RAG with question number 61 / 61
   Evaluating: 100%|██████████| 366/366 [01:40<00:00,  3.63it/s]
   rag-evaluator  | INFO:__main__:Results written to /output/eval_result.json and /output/eval_result.parquet
   rag-evaluator  | {'answer_similarity': 0.8609, 'faithfulness': 0.7904, 'context_precision': 0.9180, 'context_relevancy': 0.2990, 'answer_relevancy': 0.8383, 'context_recall': 0.7638}
   ```

## Results and Conclusion

The `OUTPUT_DIR` path has two newly created files.

- A JSON file, `eval_result.json`, with aggregated PERF metrics like the following example:

  ```json
  {
  "answer_similarity": 0.8509608317248247,
  "faithfulness": 0.8244930388373011,
  "context_precision": 0.8852459015508195,
  "context_relevancy": 0.25839891301287393,
  "answer_relevancy": 0.5291339338274769,
  "context_recall": 0.7854511153691482,
  "ragas_score": 0.4850903699042371
  }
  ```

- A parquet file, `eval_result.parquet`, with PERF metrics for each Q&A pair.


## Troubleshooting
If you see a lot of errors similar to
```
rag-evaluator  | ERROR:asyncio:Task was destroyed but it is pending!
rag-evaluator  | task: <Task pending name='Task-36' coro=<as_completed.<locals>.sema_coro() running at /usr/local/lib/python3.10/site-packages/ragas/executor.py:37> wait_for=<Future pending cb=[Task.task_wakeup()]> cb=[as_completed.<locals>._on_completion() at /usr/local/lib/python3.10/asyncio/tasks.py:558]>
```
This might be due to the `NVIDIA_API_KEY` variable not being exported prior to running the `docker compose` command.