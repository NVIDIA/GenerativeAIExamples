import os
import json
from typing_extensions import TypedDict
from langchain_openai import ChatOpenAI
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from nv_mm_document_qa.model_full_collection import BestDocuments, Answer
from nv_mm_document_qa.mongodb_utils import get_document_summaries_markdown

from langchain.schema.runnable.history import RunnableWithMessageHistory
from langchain.schema.runnable import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain.callbacks.tracers import LangChainTracer
from langchain.chains.openai_functions import (
    create_structured_output_chain,
)


# llm = ChatOpenAI(model="gpt-4-1106-preview", temperature=0, max_tokens=3000)
llm = ChatOpenAI(model="gpt-4o", temperature=0, max_tokens=3000)

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