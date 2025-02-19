import os
from langchain_chroma import Chroma
from typing import List, Tuple, Optional, Any
from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel
from glean_example.src.glean_utils.utils import (
    glean_search,
    documents_from_glean_response,
)
from glean_example.src.prompts import PROMPT_GLEAN_QUERY, PROMPT_ANSWER
from langchain_nvidia_ai_endpoints import ChatNVIDIA, NVIDIAEmbeddings
import logging

model = ChatNVIDIA(
    model="meta/llama-3.3-70b-instruct", api_key=os.getenv("NVIDIA_API_KEY")
)
embeddings = NVIDIAEmbeddings(
    model="nvidia/llama-3.2-nv-embedqa-1b-v2",
    api_key=os.getenv("NVIDIA_API_KEY"),
    truncate="NONE",
)

glean_api_key = os.getenv("GLEAN_API_KEY")
base_url = os.getenv("GLEAN_API_BASE_URL") 
chroma_db_path = "."

logger = logging.getLogger("gradio_log")


class InfoBotState(BaseModel):
    messages: List[Tuple[str, str]] = None
    glean_query_required: Optional[bool] = None
    glean_results: Optional[List[str]] = None
    db: Optional[Any] = None
    answer_candidate: Optional[str] = None

def determine_user_intent(state: InfoBotState):
    """parses the user message and determines whether or not to call glean"""

    # in this example the intent mapping is straight forward, either: 
    #  - determining the question requires context and routing to glean
    #  - or answering with the LLMs foundational world knowledge
    # in practice, this initial step could be an agent responsible for many actions such as
    #  - parsing multi-modal inputs
    #  - asking the user clarifying questions
    #  - running the promopt through custom guardrails, eg screening for sensitive HR topics
    
    logger.info("Thinking about question")
    most_recent_message: Tuple[str, str] = state.messages[-1]
    role, query = most_recent_message

    llm = PROMPT_GLEAN_QUERY | model
    response = llm.invoke({"query": query})

    if "Yes" in response.content:
        logger.info("I will need to check Glean to answer")
        state.glean_query_required = True
    
    if "No" in response.content:
        state.glean_query_required = False

    return state

def enrich_user(state: InfoBotState):
    """
    
    adds user information to the query, eg enriching 'who is my boss' to 

    'who is my boss, the user is Jane Doe with username jdoe'
    
    """

    # this is a mock example, a production deployment could source the user
    # from the application (eg parsing the current oauth session) 
    # and pass to glean appropriately

    user, msg = state.messages[-1]
    new_msg = f"{msg} \n \n the user asking the question is Jane Doe with username jdoe"
    state.messages[-1] = (user, new_msg)
    return state

def route_glean(state: InfoBotState):
    if state.glean_query_required:
        return "enrich_user"

    if not state.glean_query_required:
        return "summarize_answer"

def call_glean(state: InfoBotState):
    """Call the Glean Search API with a user query and it will return relevant results"""
    logger.info("Calling Glean")
    most_recent_message: Tuple[str, str] = state.messages[-1]
    role, query = most_recent_message
    response = glean_search(
        query=query, api_key=glean_api_key, base_url=base_url
    )
    state.glean_results = documents_from_glean_response(response)
    return state


def add_embeddings(state: InfoBotState):
    """Update the vector DB with glean search results"""
    logger.info("Understanding search results... adding embeddings")
    db = Chroma.from_texts(
        state.glean_results, embedding=embeddings, persist_directory=chroma_db_path
    )
    state.db = db
    return state


def answer_candidates(state: InfoBotState):
    """Use RAG to get most likely answer"""
    logger.info("Understanding search results... querying embeddings")
    most_recent_message: Tuple[str, str] = state.messages[-1]
    role, query = most_recent_message
    retriever = state.db.as_retriever(search_kwargs={"k": 1})
    docs = retriever.invoke(query)
    state.answer_candidate = docs[0].page_content
    return state


def summarize_answer(state: InfoBotState):
    """the main agent responsible for taking all the context and answering the question"""
    logger.info("Generating final answer")

    llm = PROMPT_ANSWER | model

    response = llm.invoke(
        {
            "messages": state.messages,
            "glean_search_result_documents": state.glean_results,
            "answer_candidate": state.answer_candidate,
        }
    )
    state.messages.append(("agent", response.content))
    return state


# Define the graph

graph = StateGraph(InfoBotState)
graph.add_node("determine_user_intent", determine_user_intent)
graph.add_node("enrich_user", enrich_user)
graph.add_node("call_glean", call_glean)
graph.add_node("add_embeddings", add_embeddings)
graph.add_node("answer_candidates", answer_candidates)
graph.add_node("summarize_answer", summarize_answer)
graph.add_edge(START, "determine_user_intent")
graph.add_conditional_edges(
    "determine_user_intent",
    route_glean, 
    {"enrich_user": "enrich_user", "summarize_answer": "summarize_answer"}
)
graph.add_edge("enrich_user", "call_glean")
graph.add_edge("call_glean", "add_embeddings")
graph.add_edge("add_embeddings", "answer_candidates")
graph.add_edge("answer_candidates", "summarize_answer")
graph.add_edge("summarize_answer", END)
agent = graph.compile()


if __name__ == "__main__":
    msg = "do I need to take PTO if I am sick"
    history = []
    history.append(("user", msg))
    messages = history
    response = agent.invoke({"messages": messages})
    logger.info(response["messages"][-1][1])
