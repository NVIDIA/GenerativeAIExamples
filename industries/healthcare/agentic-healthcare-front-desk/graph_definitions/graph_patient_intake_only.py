from dotenv import load_dotenv
import os

from langchain_nvidia_ai_endpoints import ChatNVIDIA


import datetime

from enum import Enum

from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
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

specialized_llm_model = "meta/llama-3.1-70b-instruct"
env_var_file = "vars.env"


#########################
### get env variables ###
#########################
load_dotenv(env_var_file)  # This line brings all environment variables from vars.env into os.environ
print("Your NVIDIA_API_KEY is set to: ", os.environ['NVIDIA_API_KEY'])

assert os.environ['NVIDIA_API_KEY'] is not None, "Make sure you have your NVIDIA_API_KEY exported as a environment variable!"

NVIDIA_API_KEY=os.getenv("NVIDIA_API_KEY", None)
RIVA_API_URI = os.getenv("RIVA_API_URI", None)
RIVA_ASR_FUNCTION_ID = os.getenv("RIVA_ASR_FUNCTION_ID", None)
RIVA_TTS_FUNCTION_ID = os.getenv("RIVA_TTS_FUNCTION_ID", None)

### define which llm to use
specialized_assistant_llm = ChatNVIDIA(model=specialized_llm_model) # base_url=base_url

########################
### Define the tools ###
########################
# In this tool we illustrate how you can define 
# the different data fields that are needed for 
# patient intake and the agentic llm will gather each field. 
# Here we are only printing each of the fields for illustration
# of the tool, however in your own use case, you would likely want 
# to make API calls to transmit the gathered data fields back
# to your own database.
@tool
def print_gathered_patient_info(
    patient_name: str,
    patient_dob: datetime.date,
    allergies_medication: List[str],
    current_symptoms: str,
    current_symptoms_duration: datetime.timedelta,
    pharmacy_location: str
):
    """This function prints out and transmits the gathered information for each patient intake field:
     patient_name is the patient name,
     patient_dob is the patient date of birth,
     allergies_medication is a list of allergies in medication for the patient,
     current_symptoms is a description of the current symptoms for the patient,
     current_symptoms_duration is the time duration of current symptoms,
     pharmacy_location is the patient pharmacy location. """
    
    print(patient_name)
    print(patient_dob)
    print(allergies_medication)
    print(current_symptoms)
    print(current_symptoms_duration)
    print(pharmacy_location)

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
    

# Patient Intake assistant
with open('/app/graph_definitions/system_prompts/patient_intake_system_prompt.txt', 'r') as file:
    prompt = file.read()

patient_intake_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", prompt),
        ("placeholder", "{messages}"),
    ]
)

patient_intake_tools = [print_gathered_patient_info]
patient_intake_runnable = patient_intake_prompt | specialized_assistant_llm.bind_tools(patient_intake_tools)


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

# Define nodes: these do the work
builder.add_node("patient_intake_assistant", Assistant(patient_intake_runnable))
builder.add_node("tools", create_tool_node_with_fallback(patient_intake_tools))
# Define edges: these determine how the control flow moves
builder.add_edge(START, "patient_intake_assistant")
builder.add_conditional_edges(
    "patient_intake_assistant",
    tools_condition,
)
builder.add_edge("tools", "patient_intake_assistant")


# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
intake_graph = builder.compile(checkpointer=memory)

if save_graph_to_png:
    
    with open("/images/appgraph_patient_intake.png", "wb") as png:
        png.write(intake_graph.get_graph(xray=True).draw_mermaid_png())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860,
                        help = "Specify the port number for the simple voice UI to run at.")
                            
    args = parser.parse_args()
    server_port = args.port
    launch_demo_ui(intake_graph, server_port, NVIDIA_API_KEY, RIVA_ASR_FUNCTION_ID, RIVA_TTS_FUNCTION_ID, RIVA_API_URI)
    