import os, json
import logging
from pathlib import Path
from datetime import datetime
from langchain_core.tools import tool
from typing_extensions import TypedDict
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, StateGraph, START
from langgraph.prebuilt import tools_condition
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import ToolNode
# from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.runnables import ensure_config
from langgraph.prebuilt import InjectedState
from langchain.schema.output_parser import StrOutputParser
import requests, base64
from typing_extensions import Annotated


from typing import Annotated, Optional

from langgraph.graph.message import AnyMessage, add_messages

from langchain_openai import ChatOpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate
from nv_mm_document_qa.chain import chain as fciannella_tme_document_qa_chain
from nv_mm_document_qa.mongodb_utils import get_base64_image
from nv_mm_document_qa.chain_full_collection import chain_document_expert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("../app.log"),
        logging.StreamHandler()
    ]
)

# from fciannella_tme_ingest_docs.openai_parse_image import call_openai_api_for_image
nvidia_ngc_api_key = os.environ["NVIDIA_API_KEY"]

from openai import OpenAI

client = OpenAI()

system_template = """
Please describe this image in detail.
"""

def call_image_processing_api(backend_llm, image_base64, system_template, question):

    llm_openai = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=4095,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    llm_nvidia = ChatNVIDIA(
        model="meta/llama-3.2-90b-vision-instruct",
        temperature=0,
        max_tokens=4095,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )

    if backend_llm == "nvidia":
        llm = llm_nvidia
    elif backend_llm == "openai":
        llm = llm_openai
    else:
        llm = None

    system_message = SystemMessage(content=system_template)

    _question = f"Can you answer this question from the provided image: {question}"

    # print(image_base64)

    human_message = HumanMessage(
        content=[
            {"type": "text", "text": _question},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{image_base64}"},
            },
        ]
    )

    messages = [system_message, human_message]

    response = llm.invoke(
        messages
    )

    return response.content

@tool
def find_best_document_id(
        question: Optional[str] = None,
    ) -> dict:
    """
    Use this tool when you only have the collection name and the question at your disposal, but not the document_id. This tool will allow you to find the best document_id for the user question inside the specified collection.
    Args:
        question (Optional[str]): The question that the user is asking
    Returns:
        str: The document_id that is the best for the answer asked by the user inside the collection. This is an md5 hash prefixed by a string names openai_ or nvidia_, which determine the name of the vision model that's been used.
    """

    config = ensure_config()

    configuration = config.get("configurable", {})
    collection_name = configuration.get("collection_name", None)
    best_documents = chain_document_expert.invoke(({"collection_name": collection_name, "question": question}))
    document_id = best_documents["documents"][0]["id"]
    return {"document_id": document_id, "collection_name": collection_name}

@tool
def query_document(
        question: Optional[str] = None,
        document_id: Optional[str] = None,
) -> dict:
    """
    Search an answer to the question in the document. The document is a mix of images and text, and the images are just described. When you query the document, and you think that the answer is in an image, then use the query_image tool to dig deeper into the image.

    Args:
        question (Optional[str]): The question that the user is asking
        document_id: (Optional[str]): The document_id that has been selected or configured by the user in the form of an md5 hash,  prefixed by a string names openai_ or nvidia_, which determine the name of the vision model that's been used.
    Returns:
        str: The response whether there is an answer or not
    """
    config = ensure_config()

    configuration = config.get("configurable", {})
    collection_name = configuration.get("collection_name", None)
    input_data = {"question": question, "collection_name": collection_name, "document_id": document_id}
    image_instance = fciannella_tme_document_qa_chain.invoke(input_data)

    if image_instance.image_hash:
        image_hash = image_instance.image_hash
    else:
        image_hash = None

    if image_instance.image_description:
        image_description = image_instance.image_description
    else:
        image_description = None
    answer = image_instance.answer.answer

    return {"image_hash": image_hash, "description": image_description, "answer": answer, "document_id": document_id }


@tool
def query_image(
        question: Optional[str] = None,
        image_id: Optional[str] = None,
        document_id: Optional[str] = None,
) -> dict:
    """
    Queries an image each time the description of the image hints at the possibility that the answer to the question is in the image. Use this tool when you think that the answer could be in an image.

    Args:
        question (Optional[str]): The question that the user is asking
        image_id (Optional[str]): The image identifier in form of an md5 hash
        vision_model: (Optional[str]): The backend model to use
        document_id: (Optional[str]): The document_id that has been selected or configured by the user in the form of am md5 hash  prefixed by a string names openai_ or nvidia_, which determine the name of the vision model that's been used.
    Returns:
        str: The response whether there is an answer or not
    """
    config = ensure_config()

    configuration = config.get("configurable", {})
    # collection_name = configuration.get("collection_name", None)
    images_collection_name = "images"
    vision_model = configuration.get("vision_model", None)
    image_base64 = get_base64_image(images_collection_name, image_id)

    system_template = f"""You are a helpful assistant specialized in analyzing images. You are able to find answer to questions into images, may these be charts, diagrams, or any type of image. If you don't know the answer, try to give a possible answer, don't give up!"""

    response = call_image_processing_api(vision_model, image_base64, system_template, question)
    return {"answer": response, "document_id": document_id}


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        # print("State - Placeholder")
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)


class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    document_id: str
    collection_name: str
    images_host: str


class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        max_iterations = 20
        iteration_count = 0
        result = None
        doc_id = None
        while iteration_count < max_iterations:
            configuration = config.get("configurable", {})
            collection_name = configuration.get("collection_name", None)
            vision_model = configuration.get("vision_model", None)
            images_host = os.environ["IMAGES_HOST"]
            if "document_id" in configuration.keys():
                document_id = configuration.get("document_id", None)
                state = {**state, "collection_name": collection_name, "document_id": document_id, "images_host": images_host}
                doc_id = ""
            elif "document_id" in state.keys() and state["document_id"] != None:
                doc_id = state["document_id"]
                state = {**state, "collection_name": collection_name, "document_id": doc_id, "images_host": images_host}
                pass
            else:
                doc_id = None
                state = {**state, "collection_name": collection_name, "document_id": None, "images_host": images_host}

            result = self.runnable.invoke(state)
            # If the LLM happens to return an empty response, we will re-prompt it
            # for an actual response.
            if not result.tool_calls and (
                    not result.content
                    or isinstance(result.content, list)
                    and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                if result.tool_calls:
                    if result.tool_calls[0]["name"] == "query_document":
                        doc_id = result.tool_calls[0]["args"]["document_id"]
                        logging.info(f"This is the doc id after querying the document: {doc_id}")
                        state = {**state, "document_id": doc_id, "collection_name": collection_name, "images_host": images_host}
                break
        return {"messages": result, "document_id": doc_id}


primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            """You are an assistant who is able to find the answer of a complex question inside a document.
            The answer to a question could be also in the images present in the document.
            At first check into the text of the image (it's a description after a tag in the form of an md5 hash, representing the identifier of the image). If you think that an image could have the actual answer, based on its description, then you must dig deeper into the image using the corresponding query_image tool. 
            Each time you find a possible answer inside the description of an image, then you need to use the query_image tool to find the actual final answer.
            Also each time you are asked to do a comparison, involving a difference between values on a plot, you should always use the query_image tool to find the answer.
            When depends on numeric values taken from an image, please also use the query_image tool to verify the correctedness of the answer.
            Provide the final output in markdown and if the answer was in an image then use this url format for the image and show it to the user: http://{images_host}:6001/image/{collection_name}/{document_id}/image_id"""
        ),
        ("placeholder", "{messages}"),
    ]
)

_tools = [
    query_document,
    query_image,
    find_best_document_id,
]

llm = ChatOpenAI(model="gpt-4o")

part_1_assistant_runnable = primary_assistant_prompt | llm.bind_tools(_tools)

builder = StateGraph(State)

# Define nodes: these do the work
builder.add_node("assistant", Assistant(part_1_assistant_runnable))
builder.add_node("tools", create_tool_node_with_fallback(_tools))
# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")

agent_graph = builder.compile()


def main():
    tutorial_questions = [
        # "Explain the significance of the trade-off between latency and accuracy as depicted in the graph of neural network models' performance on ImageNet.",
        # "What is the difference in performance between NVIDIA A100 and NVIDIA H100 (v2.1) on RetinaNet benchmark?",
        "What is the difference in performance between NVIDIA A100 and NVIDIA H100 (v3.0) on BERT benchmark?"
    ]

    # config = {
    #     "configurable": {
    #         "collection_name": "blogs",
    #         "document_id": "openai_7cc79c984147e038cf95de3a543524cf",
    #         "vision_model": "openai"
    #     }
    # }

    config = {
        "configurable": {
            "collection_name": "nvidia-docs",
            "vision_model": "nvidia"
        }
    }

    _printed = set()
    for question in tutorial_questions:
        events = agent_graph.stream(
            {"messages": ("user", question)}, config, stream_mode="values"
        )
        for event in events:
            _print_event(event, _printed)


if __name__ == "__main__":
    main()
