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
    model="nvdev/meta/llama-3.3-70b-instruct", api_key=os.getenv("NVIDIA_API_KEY")
)
embeddings = NVIDIAEmbeddings(
    model="nvdev/nvidia/llama-3.2-nv-embedqa-1b-v2",
    api_key=os.getenv("NVIDIA_API_KEY"),
    truncate="NONE",
)

glean_api_key = os.getenv("GLEAN_API_KEY")
base_url = os.getenv("GLEAN_API_BASE_URL") 
chroma_db_path = "."

logger = logging.getLogger("gradio_log")


class InfoBotState(BaseModel):
    messages: List[Tuple[str, str]] = None
    glean_query: Optional[str] = None
    glean_results: Optional[List[str]] = None
    db: Optional[Any] = None
    answer_candidate: Optional[str] = None


def call_glean(state: InfoBotState):
    """Call the Glean Search API with a user query and it will return relevant results"""
    logger.info("Calling Glean")
    response = glean_search(
        query=state.glean_query, api_key=glean_api_key, base_url=base_url
    )
    state.glean_results = documents_from_glean_response(response)
    return state


def add_embeddings(state: InfoBotState):
    """Update the vector DB with glean search results"""
    logger.info("Adding Embeddings")
    db = Chroma.from_texts(
        state.glean_results, embedding=embeddings, persist_directory=chroma_db_path
    )
    state.db = db
    return state


def answer_candidates(state: InfoBotState):
    """Use RAG to get most likely answer"""
    logger.info("RAG on Embeddings")
    most_recent_message: Tuple[str, str] = state.messages[-1]
    role, query = most_recent_message
    retriever = state.db.as_retriever(search_kwargs={"k": 1})
    docs = retriever.invoke(query)
    state.answer_candidate = docs[0].page_content
    return state


def create_glean_query(state: InfoBotState):
    """parses the user message and creates an appropriate glean query"""
    logger.info("Glean Query from User Message")
    most_recent_message: Tuple[str, str] = state.messages[-1]
    role, query = most_recent_message

    llm = PROMPT_GLEAN_QUERY | model
    response = llm.invoke({"query": query})

    state.glean_query = response.content

    return state


def call_bot(state: InfoBotState):
    """the main agent responsible for taking all the context and answering the question"""
    logger.info("Generate final answer")

    llm = PROMPT_ANSWER | model

    response = llm.invoke(
        {
            "messages": state.messages,
            "glean_query": state.glean_query,
            "glean_search_result_documents": state.glean_results,
            "answer_candidate": state.answer_candidate,
        }
    )
    state.messages.append(("agent", response.content))
    return state


# Define the graph

graph = StateGraph(InfoBotState)
graph.add_node("call_bot", call_bot)
graph.add_node("call_glean", call_glean)
graph.add_node("answer_candidates", answer_candidates)
graph.add_node("create_glean_query", create_glean_query)
graph.add_node("add_embeddings", add_embeddings)

graph.add_edge(START, "create_glean_query")
graph.add_edge("create_glean_query", "call_glean")
graph.add_edge("call_glean", "add_embeddings")
graph.add_edge("add_embeddings", "answer_candidates")
graph.add_edge("answer_candidates", "call_bot")
graph.add_edge("call_bot", END)
agent = graph.compile()


if __name__ == "__main__":
    msg = "do I need to take PTO if I am sick"
    history = []
    history.append(("user", msg))
    messages = history
    response = agent.invoke({"messages": messages})
    logger.info(response["messages"][-1][1])
