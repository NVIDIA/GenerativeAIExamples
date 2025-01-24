from langchain.schema.runnable import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_openai import ChatOpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from pydantic import BaseModel
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.schema.output_parser import StrOutputParser
from langchain.schema.runnable.history import RunnableWithMessageHistory
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough, RunnableLambda
from typing_extensions import TypedDict
from nv_mm_document_qa.mongodb_utils import load_document_by_id
from nv_mm_document_qa.model_images import Image
from nv_mm_document_qa.model_metadata import DocumentMetadata
import os, json

import logging
from uuid import uuid4

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("../app.log"),
        logging.StreamHandler()
    ]
)

unique_id = uuid4().hex[0:8]

nvidia_ngc_api_key = os.environ["NVIDIA_API_KEY"]
text_model_provider = os.environ["TEXT_MODEL_PROVIDER"]
nvidia_text_model = os.environ["NVIDIA_TEXT_MODEL"]

llm_openai = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_tokens=3500,
)

llm_nvidia = ChatNVIDIA(
    model=nvidia_text_model,
    temperature=0,
    max_tokens=4095,
    top_p=1,
    frequency_penalty=0,
    presence_penalty=0,
)

logging.info(f"We are using the following text model: {text_model_provider}")

if text_model_provider == "nvidia":
    llm = llm_nvidia
    # print("I am using the NVIDIA Model")
elif text_model_provider == "openai":
    llm = llm_openai
    # print("I am using the OpenAI Model")
else:
    llm = None

system_template_metadata = """You are a helpful assistant specialized in extracting metadata from a document."""

prompt_metadata = ChatPromptTemplate.from_messages(
    [
        ("system", system_template_metadata),
        ("human", """Here is the content of a document: {document_text}. \n\n Can you extract metadata as in summary and the list of entities?"""),
    ]
)

def get_context(input_data: dict) -> dict:
    # _input_data = json.loads(input_data)
    collection_name = input_data.get("collection_name")
    document_id = input_data.get("document_id")
    question = input_data.get("question")

    document = load_document_by_id(collection_name, document_id)
    document_text = document["text"]
    # print(document_text)
    return {"document_text": document_text, "question": question, "collection_name": collection_name, "document_id": document_id}

system_template = """You are a helpful assistant specialized in answering questions from a document. You are given the text of the document with the caveat that the images have been replaced with a description of the image. 

Here is an example of how an image shows in the document:

![image 3e3a6a0d4feb34ba5b04abf81839fea3][The image depicts a wireframe model of a high-speed train on a set of tracks. The wireframe is rendered in a light blue color against a black background, giving it a futuristic and technical appearance. The train is shown in a perspective view, with the front of the train closer to the viewer and the rest of the train extending into the distance. The wireframe outlines the shape and structure of the train, including the wheels, axles, and the track it runs on. The intricate details of the train's design are visible, highlighting the engineering and mechanical components. The overall effect is a detailed and transparent representation of a high-speed train, emphasizing its sleek and aerodynamic design.]

the 3e3a6a0d4feb34ba5b04abf81839fea3 represent a hash of the image

In general it has the form:

![image <hash>][<image description>]

At times the answer to a question can be in an image inside the document.
"""


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_template),
        ("human", """Here is the content of a document: {document_text}. \n\n Can you answer this question: {question}"""),
    ]
)

chain = (
    RunnableLambda(get_context) | prompt | llm.with_structured_output(Image)
    # | StrOutputParser()
)

chain_metadata = (
    RunnableLambda(get_context) | prompt_metadata | llm.with_structured_output(DocumentMetadata)
)

# result = chain.invoke({'question': 'Please describe the relative performance per accelerator', 'collection_name': 'nvidia_eval_blogs', 'document_id': 'openai_84be51268785ee2fd0def64161801cd5'})
# print(result)

# result = chain_metadata.invoke({'question': 'How much throughput can InfiniBand HDR sustain?', 'collection_name': 'nvidia_eval_blogs', 'document_id': 'openai_af9f13e35d0bf08bb8e864e2461cc1d7'})
# print(result)
