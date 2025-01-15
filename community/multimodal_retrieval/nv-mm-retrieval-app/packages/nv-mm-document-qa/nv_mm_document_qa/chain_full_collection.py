import os
from langchain_openai import ChatOpenAI
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from nv_mm_document_qa.model_full_collection import BestDocuments, Answer
from nv_mm_document_qa.mongodb_utils import get_document_summaries_markdown
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough, RunnableLambda
import logging

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

nvidia_vision_model = os.environ["NVIDIA_VISION_MODEL"]

if text_model_provider == "nvidia":
    llm = llm_nvidia
    # print("I am using the NVIDIA Model")
elif text_model_provider == "openai":
    llm = llm_openai
    # print("I am using the OpenAI Model")
else:
    llm = None

prompt_document_expert = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            f""" # Extract Best Document Identifier from list of summaries, based on a question coming from the user. You are an expert in getting insights of a document, based on its summaries and you are able to figure the best matches to the question in terms of the summary of the document.
            Provide no more than 3 of these documents.
            ## Format of the Input
            - The input is a markdown file containing second level headers (##) with the chapter index in the form ## Document <document_id> where document_id is an integer pointing to the index of the document. After the document heading there is the summary of the document which is relevant to understand the content of the document.
            ## Format of the output
            - The output is going to be the list of the best documents indices and a few of the corresponding summaries that help to answer the question coming from the user.
            ## Content
            - Here is the input you can work on:

                {{documents_context}}
                """,
        ),
        (
            "human",
            "Can you tell me what are the most relevant document ids for this question: {question}"
        ),
        ("human", "Tip: Make sure to answer in the correct format"),
    ]
)

def get_context(input_data: dict) -> dict:

    collection_name = input_data.get("collection_name")
    question = input_data.get("question")

    documents_context = get_document_summaries_markdown(collection_name)

    # print(context)
    return {"documents_context": documents_context,
            "collection_name": collection_name,
            "question": question}



chain_document_expert = (
    RunnableLambda(get_context) | prompt_document_expert | llm.with_structured_output(BestDocuments) | (lambda x: x.dict())
)

# result = chain_document_expert.invoke({"collection_name": "nvidia_eval_blogs", "question": "What are the performance optimizations that are used by NVIDIA when it comes to network division?"})
# # print([doc.dict() for doc in result])
# print(result)