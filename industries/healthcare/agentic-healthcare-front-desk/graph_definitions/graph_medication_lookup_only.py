from dotenv import load_dotenv
import os

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from fhirclient import client
from fhirclient.models.patient import Patient
from fhirclient.models.medication import Medication
from fhirclient.models.medicationrequest import MedicationRequest
from fhirclient.models.appointment import Appointment

from typing import  Optional
import sqlite3
import pandas as pd

import datetime

from enum import Enum

import shutil

from langchain_community.tools.tavily_search import TavilySearchResults

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.runnables import RunnableLambda
from langchain_core.messages import ToolMessage


from langgraph.graph.message import AnyMessage, add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START

import sys 
from typing import Any, Dict, List, Tuple, Literal, Callable, Annotated, Literal, Optional
from typing_extensions import TypedDict

import argparse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from utils.ui import launch_demo_ui

#################
### variables ###
#################
patient_id = '14867dba-fb11-4df3-9829-8e8e081b39e6' # test patient id from looking through https://launch.smarthealthit.org/
save_graph_to_png = True
env_var_file = "vars.env"


#########################
### get env variables ###
#########################
load_dotenv(env_var_file)  # This line brings all environment variables from vars.env into os.environ
print("Your NVIDIA_API_KEY is set to: ", os.environ['NVIDIA_API_KEY'])
print("Your TAVILY_API_KEY is set to: ", os.environ['TAVILY_API_KEY'])

assert os.environ['NVIDIA_API_KEY'] is not None, "Make sure you have your NVIDIA_API_KEY exported as a environment variable!"
assert os.environ['TAVILY_API_KEY'] is not None, "Make sure you have your TAVILY_API_KEY exported as a environment variable!"
NVIDIA_API_KEY=os.getenv("NVIDIA_API_KEY", None)
RIVA_API_URI = os.getenv("RIVA_API_URI", None)

RIVA_ASR_FUNCTION_ID = os.getenv("RIVA_ASR_FUNCTION_ID", None)
RIVA_TTS_FUNCTION_ID = os.getenv("RIVA_TTS_FUNCTION_ID", None)

assert os.environ['LLM_MODEL'] is not None, "Make sure you have your LLM_MODEL exported as a environment variable!"
llm_model = os.getenv("LLM_MODEL", None)

assert os.environ['BASE_URL'] is not None, "Make sure you have your BASE_URL exported as a environment variable!"
base_url = os.getenv("BASE_URL", None)

### define which llm to use
assistant_llm = ChatNVIDIA(model=llm_model, base_url=base_url)

########################
### Define the tools ###
########################

settings = {
    'app_id': 'my_web_app',
    'api_base': 'https://r4.smarthealthit.org'
}

smart = client.FHIRClient(settings=settings)

@tool
def get_patient_dob() -> str:
    """Retrieve the patient's date of birth."""
    patient = Patient.read(patient_id, smart.server)
    return patient.birthDate.isostring

@tool
def get_patient_medications() -> list:
    """Retrieve the patient's list of medications."""
    def _med_name(med):
        if med.coding:
            name = next((coding.display for coding in med.coding if coding.system == 'http://www.nlm.nih.gov/research/umls/rxnorm'), None)
            if name:
                return name
        if med.text and med.text:
            return med.text
        return "Unnamed Medication(TM)"
  
    def _get_medication_by_ref(ref, smart):
        med_id = ref.split("/")[1]
        return Medication.read(med_id, smart.server).code
    
    def _get_med_name(prescription, client=None):
        if prescription.medicationCodeableConcept is not None:
            med = prescription.medicationCodeableConcept
            return _med_name(med)
        elif prescription.medicationReference is not None and client is not None:
            med = _get_medication_by_ref(prescription.medicationReference.reference, client)
            return _med_name(med)
        else:
            return 'Error: medication not found'
    
    # test patient id from looking through https://launch.smarthealthit.org/
    bundle = MedicationRequest.where({'patient': patient_id}).perform(smart.server)
    prescriptions = [be.resource for be in bundle.entry] if bundle is not None and bundle.entry is not None else None
  
    return [_get_med_name(p, smart) for p in prescriptions]


medication_instruction_search_tool = TavilySearchResults(
    description="Search online for instructions related the patient's requested medication. Do not use to give medical advice."
)

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}

# Medication assistant
with open('/app/graph_definitions/system_prompts/medication_lookup_system_prompt.txt', 'r') as file:
    prompt = file.read()
medication_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", prompt),
        ("placeholder", "{messages}"),
    ]
)

medication_tools = [get_patient_medications, get_patient_dob, medication_instruction_search_tool] # to add later
medication_runnable = medication_prompt | assistant_llm.bind_tools(medication_tools)



builder = StateGraph(State)

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


# Medication assistant
builder.add_node("medication_assistant", Assistant(medication_runnable))
builder.add_node("tools", create_tool_node_with_fallback(medication_tools))


# Define edges: these determine how the control flow moves
builder.add_edge(START, "medication_assistant")
builder.add_conditional_edges(
    "medication_assistant",
    tools_condition,
)
builder.add_edge("tools", "medication_assistant")


memory = MemorySaver()
medication_lookup_graph = builder.compile(checkpointer=memory)

if save_graph_to_png:
    
    with open("/graph_images/appgraph_medication_lookup.png", "wb") as png:
        png.write(medication_lookup_graph.get_graph(xray=True).draw_mermaid_png())
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860,
                        help = "Specify the port number for the simple voice UI to run at.")
                            
    args = parser.parse_args()
    server_port = args.port
    launch_demo_ui(medication_lookup_graph, server_port, NVIDIA_API_KEY, RIVA_ASR_FUNCTION_ID, RIVA_TTS_FUNCTION_ID, RIVA_API_URI)
    



