from dotenv import load_dotenv
import os

from langchain_nvidia_ai_endpoints import ChatNVIDIA


from typing import  Optional
import sqlite3
import pandas as pd

import datetime

from enum import Enum

import shutil

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

llm_model = "meta/llama-3.1-70b-instruct"
env_var_file = "vars.env"

local_file_constant = "sample_db/test_db.sqlite"
local_file_current = "sample_db/test_db_tmp_copy.sqlite"



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
assistant_llm = ChatNVIDIA(model=llm_model) # base_url=base_url)

########################
### Define the tools ###
########################

class ApptType(Enum):
    adult_physicals = "Adult physicals"
    pediatric_physicals = "Pediatric physicals"
    follow_up_appointments = "Follow-up appointments"
    sick_visits = "Sick visits"
    flu_shots = "Flu shots"
    other_vaccinations = "Other vaccinations"
    allergy_shots = "Allergy shots"
    b12_injections = "B12 injections"
    diabetes_management = "Diabetes management"
    hypertension_management = "Hypertension management"
    asthma_management = "Asthma management"
    chronic_pain_management  = "Chronic pain management"
    initial_mental_health = "Initial mental health consultations"
    follow_up_mental_health = "Follow-up mental health appointments"
    therapy_session = "Therapy sessions"
    blood_draws = "Blood draws"
    urine_tests = "Urine tests"
    ekgs = "EKGs"
    biopsies = "Biopsies"
    medication_management = "Medication management"
    wart_removals = "Wart removals"
    skin_tag_removals = "Skin tag removals"
    ear_wax_removals = "Ear wax removals"

@tool
def find_available_appointments(
    appointment_type: ApptType,
    start_date: Optional[datetime.date] = None,
    end_date: Optional[datetime.date] = None,
) -> list:
    """Look for available new appointments."""
    
    
    shutil.copyfile(local_file_constant, local_file_current)

    conn = sqlite3.connect(local_file_current)
    
    query_datetime = "SELECT * from appointment_schedule WHERE appointment_type = \"{}\" AND patient IS NULL ".format(appointment_type.value)


    #start_date, end_date = datetime.date.fromisoformat(start_date), datetime.date.fromisoformat(end_date)
    if start_date:
        query_datetime += " AND datetime >= \"{}\"".format(start_date)

    if end_date:
        query_datetime += " AND datetime <= \"{}\"".format(end_date + datetime.timedelta(hours=24) )
    print(query_datetime)
    
    available_appts = pd.read_sql(
        query_datetime, conn
    )

    print(available_appts)
    conn.close()
    return list(available_appts['datetime'])

@tool
def book_appointment(
    appointment_datetime: datetime.datetime,
    appointment_type: ApptType,
)-> pd.DataFrame:
    """Book new appointments."""
    
    conn = sqlite3.connect(local_file_current)

    booking_query = "UPDATE appointment_schedule SET patient = \"current_patient\" WHERE datetime = \"{}\" AND appointment_type = \"{}\"".format(appointment_datetime, appointment_type.value)
    
    cur = conn.cursor()    
    cur.execute(booking_query)

    find_patient_appt_query = "SELECT * from appointment_schedule where patient = \"current_patient\""

    current_patient_entries = pd.read_sql(find_patient_appt_query, conn, index_col="index")

    cur.close()
    conn.close()
        
    
    return current_patient_entries


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

with open('/app/graph_definitions/system_prompts/appointment_system_prompt.txt', 'r') as file:
    guidelines_for_scheduling_appointment = file.read()

appointment_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for healthcare appointment scheduling. Your purpose is to help patients with looking up and making appointments."
            "Use the provided tools as necessary."
            "\nCurrent date and time: {time}."
            "\nGuidelines for scheduling appointments: {guidelines_for_scheduling_appointment}."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.datetime.now(), guidelines_for_scheduling_appointment=guidelines_for_scheduling_appointment)

appointment_tools = [find_available_appointments, book_appointment]
# appointment_assistant_runnable = appointment_assistant_prompt | llm
appointment_runnable = appointment_prompt | assistant_llm.bind_tools(
    appointment_tools 
)




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

# Appointment assistant
# Define nodes: these do the work
builder.add_node("appointment_assistant", Assistant(appointment_runnable))
builder.add_node("tools", create_tool_node_with_fallback(appointment_tools))
# Define edges: these determine how the control flow moves
builder.add_edge(START, "appointment_assistant")
builder.add_conditional_edges(
    "appointment_assistant",
    tools_condition,
)
builder.add_edge("tools", "appointment_assistant")

# Compile graph
memory = MemorySaver()
appt_graph = builder.compile(
    checkpointer=memory,    
)

if save_graph_to_png:
    
    with open("/graph_images/appgraph_appointment.png", "wb") as png:
        png.write(appt_graph.get_graph(xray=True).draw_mermaid_png())

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860,
                        help = "Specify the port number for the simple voice UI to run at.")
                            
    args = parser.parse_args()
    server_port = args.port
    launch_demo_ui(appt_graph, server_port, NVIDIA_API_KEY, RIVA_ASR_FUNCTION_ID, RIVA_TTS_FUNCTION_ID, RIVA_API_URI)
    


