import gradio as gr
import requests
import json, os
from pymongo import MongoClient
from langgraph_sdk import get_client
from datetime import datetime

import asyncio  # Import asyncio to run the async function


# MongoDB connection setup
agents_host = os.environ["AGENTS_HOST"]
images_host = os.environ["IMAGES_HOST"]
mongodb_user = os.environ["MONGO_INITDB_ROOT_USERNAME"]
mongodb_password = os.environ["MONGO_INITDB_ROOT_PASSWORD"]
mongodb_port = os.environ["MONGO_PORT"]
client = MongoClient(f'mongodb://{mongodb_user}:{mongodb_password}@mongodb:{mongodb_port}/')  # Adjust as needed
db = client['tme_urls_db']  # Replace with your database name


questions_list = [
    "What is the Max-scale time-to-train records set on the NVIDIA platform and H100 Tensor Core GPUs in the case of Recommendation (DLRMv2) benchmark?",
    "What is the Max-scale time-to-train records set on the NVIDIA platform and H100 Tensor Core GPUs in the case of Object detection, heavyweight (Mask R-CNN)?",
    "What is the difference in performance between NVIDIA A100 and NVIDIA H100 (v2.1) on RetinaNet benchmark?",
    "What is the difference in performance between NVIDIA A100 and NVIDIA H100 (v3.0) on BERT benchmark?",
    "What are the takeaways of MLPerf Training v3.0 takeaways?",
    "What are the two high-level stages of the neural architecture search AI agent?",
    "How many neural architecture candidates are screened before performing bayesian optimization?",
    "What is the dimension of output channel filters for stage 1 conv layer?",
    "What are the hyperparameters of stage 2 Fused-IRB layer?",
    "What does NAS search return?",
    "What is H100 v3.0 inference speed-up on RetinaNet?",
    "What's the performance difference between NVIDIA T4 and NVIDIA L4 on RNN-T benchmark?",
    "While performing network division on multiple nodes, what NVIDIA component connects a front-end node and DGX A100?",
    "Did Jetson Orin NX show any speedup when compared to Jetson Xavier NX on 3D-Unet benchmark?",
    "Where can we observe a speedup with Jetson AGX Orin v3.0 Performance on RetinaNet, offline, single stream or multi-stream?",
    "What components does an IBConnection have?",
    "What is the difference between closed division on a single node and network division on Multiple nodes?",
    "What is the performance of the network division compared to the closed division on BERT (high accuracy) benchmark?",
    "How much throughput can InfiniBand HDR sustain?"
]

answers_list = [
"1.61min",
"1.47 min",
"~2.25x",
"~3x",
"""The NVIDIA AI platform delivered record-setting performance in MLPerf Training v3.0, highlighting the exceptional capabilities of the NVIDIA H100 GPU and the NVIDIA AI platform for the full breadth of workloads—from training mature networks like ResNet-50 and BERT to training cutting-edge LLMs like GPT-3 175B. The NVIDIA joint submission with CoreWeave using their publicly available NVIDIA HGX H100 infrastructure showcased that the NVIDIA platform and the H100 GPU deliver great performance at very large scale on publicly-available cloud infrastructure. 

The NVIDIA platform delivers the highest performance, and greatest versatility, and is available everywhere. All software used for NVIDIA MLPerf submissions is available from the MLPerf repository, so you can reproduce these results. All NVIDIA AI software used to achieve these results is also available in the enterprise-grade software suite, NVIDIA AI Enterprise.""",
    """At a high level, the neural architecture search (NAS) AI agent is split into two stages:

Categorizing all possible network architectures by the inference latency.
Using a subset of these networks that fit within the latency budget and optimizing them for accuracy.""",
"~20K",
"[24, 32, 8]",
"[#Filters, Kernel, E, SE, Act, #Layers]",
    "At the end of the NAS search, the returned ranked candidates is a list of these best-performing encodings, which are in turn the best-performing GPUNets.",

"54%",
"2.7x",
"NVIDIA Quantum InfiniBand",
"Yes (bonus, by 2x)",
"Offline",
"IBConfigs, IBDevice and IBResources",
"Open this image: https://developer-blogs.nvidia.com/wp-content/uploads/2023/06/closed-network-nodes-1.png",
"90%",
"200 Gbits/sec"]

gt_urls = [
    "https://developer.nvidia.com/blog/breaking-mlperf-training-records-with-nvidia-h100-gpus/",
    "https://developer.nvidia.com/blog/breaking-mlperf-training-records-with-nvidia-h100-gpus/",
    "https://developer.nvidia.com/blog/breaking-mlperf-training-records-with-nvidia-h100-gpus/",
    "https://developer.nvidia.com/blog/breaking-mlperf-training-records-with-nvidia-h100-gpus/",
    "https://developer.nvidia.com/blog/breaking-mlperf-training-records-with-nvidia-h100-gpus/",
    "https://developer.nvidia.com/blog/beating-sota-inference-performance-on-nvidia-gpus-with-gpunet/",
    "https://developer.nvidia.com/blog/beating-sota-inference-performance-on-nvidia-gpus-with-gpunet/",
    "https://developer.nvidia.com/blog/beating-sota-inference-performance-on-nvidia-gpus-with-gpunet/",
    "https://developer.nvidia.com/blog/beating-sota-inference-performance-on-nvidia-gpus-with-gpunet/",
    "https://developer.nvidia.com/blog/beating-sota-inference-performance-on-nvidia-gpus-with-gpunet/",
    "https://developer.nvidia.com/blog/setting-new-records-in-mlperf-inference-v3-0-with-full-stack-optimizations-for-ai/",
    "https://developer.nvidia.com/blog/setting-new-records-in-mlperf-inference-v3-0-with-full-stack-optimizations-for-ai/",
    "https://developer.nvidia.com/blog/setting-new-records-in-mlperf-inference-v3-0-with-full-stack-optimizations-for-ai/",
    "https://developer.nvidia.com/blog/setting-new-records-in-mlperf-inference-v3-0-with-full-stack-optimizations-for-ai/",
    "https://developer.nvidia.com/blog/setting-new-records-in-mlperf-inference-v3-0-with-full-stack-optimizations-for-ai/",
    "https://developer.nvidia.com/blog/new-mlperf-inference-network-division-showcases-infiniband-and-gpudirect-rdma-capabilities/",
    "https://developer.nvidia.com/blog/new-mlperf-inference-network-division-showcases-infiniband-and-gpudirect-rdma-capabilities/",
    "https://developer.nvidia.com/blog/new-mlperf-inference-network-division-showcases-infiniband-and-gpudirect-rdma-capabilities/",
    "https://developer.nvidia.com/blog/new-mlperf-inference-network-division-showcases-infiniband-and-gpudirect-rdma-capabilities/",
]

# Function to ingest documents into MongoDB collection
def ingest_docs(urls_list, collection_name, backend_llm):
    url = "http://ingest-service:8000/ingest-docs/invoke"  # This URL is fine for Docker Compose internal networking

    payload = {
        "input": {
            "urls_list": urls_list,
            "collection_name": collection_name,
            "backend_llm": backend_llm
        },
        "config": {},
        "kwargs": {}
    }

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return "Documents successfully ingested into the collection!"
        else:
            return f"Error: {response.status_code}, {response.text}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


# Function to load available collection names dynamically
def get_collection_names():
    try:
        collections = db.list_collection_names()
        # Exclude the 'images' collection
        filtered_collections = [collection for collection in collections if collection != 'images']
        return filtered_collections
    except Exception as e:
        return f"An error occurred while fetching collection names: {str(e)}"


# Function to load document URLs and document IDs for a selected collection
def get_document_urls_and_ids(collection_name):
    try:
        collection = db[collection_name]
        # Fetch both the document_id (_id), URL, and backend_llm fields from MongoDB
        documents = collection.find({}, {"_id": 1, "url": 1, "backend_llm": 1})  # Adjust "url" based on your document structure
        # Set the default value for backend_llm to 'openai' if it is not present
        return {str(doc["_id"]): doc.get("backend_llm", "openai") + " " + doc["url"] for doc in documents}
    except Exception as e:
        return {}  # Return an empty dictionary in case of error


def document_sdg(collection_name, document_id, vision_model):
    url = "http://ingest-service:8000/document-sdg/invoke"  # Assuming QA service runs on same container

    payload = {
        "input": {
            "document_id": document_id,
            "collection_name": collection_name,
            "vision_model": vision_model
        },
        "config": {},
        "kwargs": {}
    }

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            return response.json()  # Return the JSON response from the service
        else:
            return f"Error: {response.status_code}, {response.text}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


# Function to query the document QA service
def document_qa(collection_name, document_id, question):
    url = "http://ingest-service:8000/document-qa/invoke"  # Assuming QA service runs on same container

    payload = {
        "input": {
            "document_id": document_id,
            "collection_name": collection_name,
            "question": question
        },
        "config": {},
        "kwargs": {}
    }

    headers = {
        'accept': 'application/json',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            print(response.json())
            return response.json()  # Return the JSON response from the service
        else:
            return f"Error: {response.status_code}, {response.text}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


def get_run(run_id):
    """Function to get run statistics from the API."""
    try:
        headers = {"x-api-key": os.environ["LANGSMITH_API_KEY"]}

        response = requests.get(
            f"https://api.smith.langchain.com/api/v1/runs/{run_id}",
            headers=headers
        )

        # Check if the request was successful
        if response.status_code == 200:
            # Return the content of the response (e.g., JSON)
            return response.json()  # or response.text for plain text responses
        else:
            # Return the status code and error text for non-200 responses
            return {
                "status_code": response.status_code,
                "error_message": response.text
            }

    except Exception as e:
        # Handle exceptions such as connection errors
        return {"error": str(e)}

def extract_token_usage_and_cost(statistics, run_id):
    # Initialize a dictionary to store the results
    result = {
        "total_tokens": None,
        "prompt_tokens": None,
        "completion_tokens": None,
        "total_cost": None,
        "prompt_cost": None,
        "completion_cost": None,
        "latency_seconds": None,
        "latency_milliseconds": None,
        "run_id": None
    }

    # Extract token and cost details
    result["total_tokens"] = statistics.get("total_tokens")
    result["prompt_tokens"] = statistics.get("prompt_tokens")
    result["completion_tokens"] = statistics.get("completion_tokens")
    result["total_cost"] = statistics.get("total_cost")
    result["prompt_cost"] = statistics.get("prompt_cost")
    result["completion_cost"] = statistics.get("completion_cost")
    result["run_id"] = run_id

    # Extract latency if both start_time and end_time are available
    start_time = statistics.get("start_time")
    end_time = statistics.get("end_time")

    if start_time and end_time:
        # Convert start_time and end_time to datetime objects
        start_time_dt = datetime.fromisoformat(start_time)
        end_time_dt = datetime.fromisoformat(end_time)

        # Calculate latency in seconds and milliseconds
        latency = end_time_dt - start_time_dt
        result["latency_seconds"] = latency.total_seconds()
        result["latency_milliseconds"] = latency.total_seconds() * 1000

    return result

def format_statistics(statistics):
    """Format the statistics into a readable string format with bold text and newlines."""
    return (
        f""" - **Total Tokens**: {statistics['total_tokens']}
         - **Prompt Tokens**: {statistics['prompt_tokens']}
         - **Completion Tokens**: {statistics['completion_tokens']}
         - **Total Cost**: ${statistics['total_cost']}
         - **Prompt Cost**: ${statistics['prompt_cost']}
         - **Completion Cost**: ${statistics['completion_cost']}
         - **Latency (seconds)**: {statistics['latency_seconds']}
         - **Latency (milliseconds)**: {statistics['latency_milliseconds']}"""
    )



async def run_stream_service(collection_name, document_id, question, vision_model):
    # Get the client from langgraph_sdk
    agents_host = os.environ["AGENTS_HOST"]
    agents_port = os.environ["AGENTS_PORT"]
    client = get_client(url=f"http://{agents_host}:{agents_port}")
    thread = await client.threads.create()

    assistant_id = "agent"

    input = {
        "messages": [
            {
                "role": "user",
                "content": question
            }
        ]
    }

    final_answer = None
    collected_chunks = []  # To collect all chunks for logging
    run_ids = []

    if document_id:
        config = {
            "configurable": {
                "collection_name": collection_name,
                "document_id": document_id,
                "vision_model": vision_model  # Add vision_model to the config
            }
        }
    else:
        config = {
            "configurable": {
                "collection_name": collection_name,
                "vision_model": vision_model  # Add vision_model to the config
            }
        }

    try:
        # Stream response chunks and get the final answer
        async for chunk in client.runs.stream(
            thread_id=thread["thread_id"],
            assistant_id=assistant_id,
            input=input,
            config=config,
            stream_mode="values"
        ):
            collected_chunks.append({
                "event": chunk.event,  # The event type
                "data": chunk.data,    # The actual data
            })

            # Extract the run_id if available
            if chunk.event == "metadata":
                run_id = chunk.data.get("run_id")
                run_ids.append(run_id)

            # Capture the final answer from the last chunk with event "values"
            if chunk.event == "values":
                final_answer = chunk.data  # Keep updating with the latest "values" event

    except Exception as e:
        return "An error occurred", f"An error occurred: {str(e)}"

    # Return the final answer and run_id after streaming
    final_response = final_answer['messages'][-1]['content'] if final_answer else "No final answer received"
    run_id = run_ids[0] if run_ids else None  # Use the first run_id, if available
    return final_response, run_id



def compute_statistics(run_id):
    if run_id:
        run_statistics = get_run(run_id)
        extracted_info = extract_token_usage_and_cost(run_statistics, run_id)
        formatted_statistics = format_statistics(extracted_info)
        return formatted_statistics
    else:
        return "No run_id was received."


# def update_answer_dropdown(question_index):
#     # Function to fill the answer field based on selected question index
#     return answers_list[question_index]

def update_answer_and_url(question):
    question_index = questions_list.index(question)
    return answers_list[question_index], gt_urls[question_index]

# Create the Gradio interface with three tabs
with gr.Blocks() as interface:
    with gr.Tab("Ingest Documents"):
        gr.Markdown("## Ingest Documents to MongoDB Collection")

        urls_input = gr.Textbox(label="Enter the URLs (comma separated)",
                                placeholder="https://example.com/doc1, https://example.com/doc2")
        collection_input = gr.Textbox(label="Enter the MongoDB Collection Name", placeholder="collection_name")

        # Add the dropdown for selecting between 'openai' and 'nvidia'
        model_dropdown = gr.Dropdown(label="Select Model", choices=["openai", "nvidia"], value="openai")

        submit_button = gr.Button("Ingest Documents")
        output_text = gr.Textbox(label="Response")

        # Modify the click function to also capture the selected model from the dropdown
        submit_button.click(fn=lambda urls, coll, model: ingest_docs(urls.split(','), coll, model),
                            inputs=[urls_input, collection_input, model_dropdown], outputs=output_text)


    with gr.Tab("Agent Stream Service"):
        gr.Markdown("## Call the New Agent Stream Service")

        collection_dropdown_stream = gr.Dropdown(label="Select Collection", choices=[], interactive=True)
        document_dropdown_stream = gr.Dropdown(label="Select Document URL", choices=[])
        question_input_stream = gr.Textbox(label="Enter your question", placeholder="Type your question here...")


        # Add a dropdown for vision model selection

        vision_model_dropdown = gr.Dropdown(
            label="Select Vision Model",
            choices=["openai", "nvidia"],
            value="openai",  # Optionally set a default value to ensure something is selected
            interactive=True
        )


        stream_button = gr.Button("Run Stream Service")
        stream_output_answer = gr.Markdown(label="Final Answer")  # Separate markdown box for the answer
        # gr.Markdown("---")
        # stream_output_stats = gr.Markdown(label="Statistics")  # Separate markdown box for statistics


        def update_collection_dropdown_stream():
            return gr.update(choices=get_collection_names())


        def update_document_dropdown_stream(collection_name):
            documents = get_document_urls_and_ids(collection_name)
            return gr.update(choices=[(url, doc_id) for doc_id, url in documents.items()], value=None)


        collection_dropdown_stream.change(fn=update_document_dropdown_stream, inputs=collection_dropdown_stream,
                                          outputs=document_dropdown_stream)


        # Click function for the streaming service with chained statistic computation
        async def run_and_compute_statistics(collection_name, document_id, question, vision_model):
            final_answer, run_id = await run_stream_service(collection_name, document_id, question, vision_model)

            # Introduce a delay of 3 seconds (adjust as needed)
            await asyncio.sleep(3)  # Delay execution by 3 seconds

            # Now compute the statistics after the delay
            statistics = compute_statistics(run_id)

            # return final_answer, statistics
            return final_answer


        # Trigger both the streaming service and stats calculation when the button is clicked
        stream_button.click(
            fn=run_and_compute_statistics,
            inputs=[collection_dropdown_stream, document_dropdown_stream, question_input_stream, vision_model_dropdown],
            # Added vision_model_dropdown
            outputs=[stream_output_answer]  # Display final answer and stats separately
        )

        interface.load(fn=update_collection_dropdown_stream, outputs=collection_dropdown_stream)

    with gr.Tab("Agent Multi Documents QA"):
        gr.Markdown("## Call the New Agent Stream Service for multidocuments")

        collection_dropdown_stream = gr.Dropdown(label="Select Collection", choices=[], interactive=True)
        question_input_stream = gr.Textbox(label="Enter your question", placeholder="Type your question here...")

        # Add a dropdown for vision model selection
        vision_model_dropdown = gr.Dropdown(
            label="Select Vision Model",
            choices=["openai", "nvidia"],
            value="openai",  # Optionally set a default value to ensure something is selected
            interactive=True
        )

        stream_button = gr.Button("Run Stream Service")
        stream_output_answer = gr.Markdown()  # Remove the label argument
        # gr.Markdown("---")
        # stream_output_stats = gr.Markdown()  # Remove the label argument


        def update_collection_dropdown_stream():
            return gr.update(choices=get_collection_names())  # Ensure get_collection_names() returns a list


        # async def run_and_compute_statistics(collection_name, question, vision_model):
        #     # Return the vision model to the output field for testing
        #     return f"Vision Model: {vision_model}", ""


        async def run_and_compute_statistics(collection_name, question, vision_model):
            # print(f"Collection Name: {collection_name}")
            # print(f"Question: {question}")
            # print(f"Vision Model: {vision_model}")

            final_answer, run_id = await run_stream_service(collection_name, None, question, vision_model)

            # Introduce a delay of 3 seconds (adjust as needed)
            await asyncio.sleep(3)  # Delay execution by 3 seconds

            # Now compute the statistics after the delay
            statistics = compute_statistics(run_id)

            # return final_answer, statistics
            return final_answer

        # Trigger both the streaming service and stats calculation when the button is clicked
        stream_button.click(
            fn=run_and_compute_statistics,
            inputs=[collection_dropdown_stream, question_input_stream, vision_model_dropdown],
            # Added vision_model_dropdown
            outputs=[stream_output_answer]  # Display final answer and stats separately
        )

        interface.load(fn=update_collection_dropdown_stream, outputs=collection_dropdown_stream)


    with gr.Tab("Agent Multi Documents QA Evaluation"):
        gr.Markdown("## Call the New Agent Stream Service for multidocuments")

        collection_dropdown_stream = gr.Dropdown(label="Select Collection", choices=[], interactive=True)
        # vision_model_dropdown = gr.Dropdown(label="Select Vision Model", choices=["openai", "nvidia"])
        vision_model_dropdown = gr.Dropdown(
            label="Select Vision Model",
            choices=["openai", "nvidia"],
            value="openai",  # Optionally set a default value to ensure something is selected
            interactive=True
        )
        question_dropdown_stream = gr.Dropdown(label="Select Question", choices=questions_list, value=questions_list[0], interactive=True)
        answer_box = gr.Textbox(label="Ground Truth Answer", value=answers_list[0], interactive=False)  # Answer box is not editable
        url_box = gr.Textbox(label="Ground Truth Url", value=gt_urls[0], interactive=False)  # Answer box is not editable

        stream_button = gr.Button("Run QA Agent")
        stream_output_answer = gr.Markdown(value="")  # Remove the label argument
        # gr.Markdown("---")
        # stream_output_stats = gr.Markdown(value="")  # Remove the label argument

        # Function to update the dropdown when clicked

        def update_collection_dropdown_stream():
            return gr.update(choices=get_collection_names())  # Ensure get_collection_names() returns a list

        # Click function for the streaming service with chained statistic computation
        async def run_and_compute_statistics(collection_name, question, vision_model):
            print(collection_name, question, vision_model)
            final_answer, run_id = await run_stream_service(collection_name, None, question, vision_model)

            # Introduce a delay of 3 seconds (adjust as needed)
            await asyncio.sleep(3)

            # Now compute the statistics after the delay
            statistics = compute_statistics(run_id)

            # return final_answer, statistics
            return final_answer
        # When a question is selected, automatically fill the answer box

        question_dropdown_stream.change(
            fn=update_answer_and_url,
            inputs=[question_dropdown_stream],
            outputs=[answer_box, url_box]
        )

        # question_dropdown_stream.change(
        #     fn=lambda question: update_answer_dropdown(questions_list.index(question)),
        #     inputs=[question_dropdown_stream],
        #     outputs=[answer_box]
        # )

        def update_placeholders():
            return "Processing your request...", "Computing statistics..."

        stream_button.click(
            fn=update_placeholders,
            inputs=[],
            outputs=[stream_output_answer],
            queue=False  # Ensure this update happens immediately without waiting
        )
        # Trigger both the streaming service and stats calculation when the button is clicked
        stream_button.click(
            fn=run_and_compute_statistics,
            inputs=[collection_dropdown_stream, question_dropdown_stream, vision_model_dropdown],
            outputs=[stream_output_answer]
        )

        # Load the collections when the interface loads
        interface.load(fn=update_collection_dropdown_stream, outputs=collection_dropdown_stream)


    with gr.Tab("QA Synthetic generation"):
        gr.Markdown("## Generate Synthetic questions / answers pairs from Documents")

        collection_dropdown = gr.Dropdown(label="Select Collection", choices=[], interactive=True)
        document_dropdown = gr.Dropdown(label="Select Document URL", choices=[])

        # Add a dropdown for vision model selection
        # vision_model_dropdown = gr.Dropdown(label="Select Vision Model", choices=["openai", "nvidia"])

        vision_model_dropdown = gr.Dropdown(
            label="Select Vision Model",
            choices=["openai", "nvidia"],
            value="openai",  # Optionally set a default value to ensure something is selected
            interactive=True
        )

        generate_button = gr.Button("Generate SDG QA Pair")

        # _qa_output = gr.Textbox(label="Response")  # Removed the 'label' argument
        qa_output = gr.Markdown(label="Response")  # Removed the 'label' argument


        def update_collection_dropdown():
            return gr.update(choices=get_collection_names())


        def update_document_dropdown(collection_name):
            documents = get_document_urls_and_ids(collection_name)
            return gr.update(choices=[(url, doc_id) for doc_id, url in documents.items()], value=None)


        collection_dropdown.change(
            fn=update_document_dropdown, inputs=collection_dropdown, outputs=document_dropdown
        )


        def format_qa_output(result):
            qa_pairs = result['output']['sdgqa_pairs'][0]
            question = qa_pairs['question']['question']
            answer = qa_pairs['answer']['answer']
            return f"### Question:\n{question}\n\n### Answer:\n{answer}"


        # Trigger both the streaming service and stats calculation when the button is clicked
        generate_button.click(
            fn=lambda *args: format_qa_output(document_sdg(*args)),
            inputs=[collection_dropdown, document_dropdown, vision_model_dropdown],  # Added vision_model_dropdown
            outputs=qa_output  # Display question and answer
        )

        interface.load(fn=update_collection_dropdown, outputs=collection_dropdown)


# Launch the Gradio interface
interface.launch(server_name="0.0.0.0", server_port=7860)

