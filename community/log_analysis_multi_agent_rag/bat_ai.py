
from langgraph.graph import END, StateGraph, START
from graphnodes import Nodes
from graphedges import Edge
from typing_extensions import TypedDict
from typing import List
class GraphState(TypedDict):
    """
    A current Graph State
    Attributes:
        path: log file path
        question: The current question being processed.
            This can be a user-inputted query.
        generation: The current LLM (Large Language Model) generation.
            This is used to keep track of the different stages of the language model's output.
        documents: A list of relevant documents that have been retrieved.
            These documents are used as input for the LLM to generate a response
    question: str
    sub_questions:  List[str]
    generation: str
    documents: List[str]
    """
    path : str
    question: str
    generation: str
    documents: List[str]


bat_ai = StateGraph(GraphState)

# Define the nodes
bat_ai.add_node("retrieve", Nodes.retrieve)  
bat_ai.add_node("rerank", Nodes.rerank)  
bat_ai.add_node("grade_documents", Nodes.grade_documents)  
bat_ai.add_node("generate", Nodes.generate) 
bat_ai.add_node("transform_query", Nodes.transform_query)  

# Build graph
bat_ai.add_edge(START, "retrieve")
bat_ai.add_edge("retrieve", "rerank")
bat_ai.add_edge("rerank", "grade_documents")
bat_ai.add_conditional_edges(
    "grade_documents",
    Edge.decide_to_generate,
    {
        "transform_query": "transform_query",
        "generate": "generate",
    },
)
bat_ai.add_edge("transform_query", "retrieve")
bat_ai.add_conditional_edges(
    "generate",
    Edge.grade_generation_vs_documents_and_question,
    {
        "not supported": "generate",
        "useful": END,
        "not useful": "transform_query",
    },
)

app = bat_ai.compile()