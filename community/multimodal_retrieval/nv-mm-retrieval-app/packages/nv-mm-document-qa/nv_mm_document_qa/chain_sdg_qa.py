import os
import logging
from langchain_openai import ChatOpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough, RunnableLambda
from nv_mm_document_qa.model_sdg_qa import SDGQA
from nv_mm_document_qa.mongodb_utils import load_document_by_id

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("../app.log"),
        logging.StreamHandler()
    ]
)

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
    max_tokens=3500,
)

if text_model_provider == "nvidia":
    llm = llm_nvidia
    # print("I am using the NVIDIA Model")
elif text_model_provider == "openai":
    llm = llm_openai
    # print("I am using the OpenAI Model")
else:
    llm = None

logging.info(f"We are using the following text model: {text_model_provider}")

system_template = """
*You are an expert educator specializing in creating challenging and insightful questions for developers in the field of Tec43chincal Documentation.*

*Your task is to generate a set of complex synthetic questions based on the following technical document written in markdown format. 

*When creating the question, you need to think in terms of pinpointed questions and concise answers, meaning that you don't want to make the question too generic*

*The questions should:*

- *Incorporate information from both the main text and the detailed image descriptions.*
- *Make sure that you use at least one image when generating the question.*
- *Cover a range of cognitive levels, including analysis, evaluation, and synthesis.*
- *Encourage critical thinking and the application of concepts in novel situations.*
- *Be clear, concise, and unambiguous.*

*For each question, provide:*

1. *The question itself.* No image should be mentioned in the question, although the question must be generated including information from the description of an image.
2. *A detailed answer or solution, including explanations of the reasoning process and any necessary calculations. The image that has been used to generate the question should be provided with its identifier (an md5 hash). The text should include the image as in a markdown file, showing the image with the link http://localhost:6001/image/{collection_name}/{document_id}/image_id* (you need to replace image_id in the url with the identifier of the image that comes from the document, which is the md5 of the image).

Generate no more than one Question / Answer pairs.

*Here is the technical document:*

{document_text}
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_template)
    ]
)

def get_context(input_data: dict) -> dict:
    global llm
    # _input_data = json.loads(input_data)
    collection_name = input_data.get("collection_name")
    document_id = input_data.get("document_id")
    vision_model = input_data.get("vision_model")

    if vision_model == "openai":
        llm = ChatOpenAI(model="gpt-4o", temperature=0.71, max_tokens=3000)
    else:
        print("Using the nvidia model!")
        llm = ChatNVIDIA(
            model="meta/llama-3.2-90b-vision-instruct",
            temperature=0,
            max_tokens=4095,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

    document = load_document_by_id(collection_name, document_id)
    document_text = document["text"]
    # print(document_text)
    return {"document_text": document_text, "collection_name": collection_name, "document_id": document_id, "vision_model": vision_model}



chain = (
    RunnableLambda(get_context) | prompt | llm.with_structured_output(SDGQA) | (lambda x: x.dict())
)

# result = chain.invoke({"document_id": "openai_7cc79c984147e038cf95de3a543524cf", "collection_name": "blogs"})
# print(result)