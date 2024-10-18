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
main_llm_model = "meta/llama-3.1-70b-instruct"
specialized_llm_model = "meta/llama-3.1-70b-instruct"
env_var_file = "vars.env"

local_file_constant = "sample_db/test_db.sqlite"
local_file_current = "sample_db/test_db_tmp_copy.sqlite"



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

### define which llm to use
main_assistant_llm = ChatNVIDIA(model=main_llm_model)#, base_url=base_url 
specialized_assistant_llm = ChatNVIDIA(model=specialized_llm_model)#, base_url=base_url

def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state."""
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    user_info: str
    dialog_state: Annotated[
        list[
            Literal[
                "assistant",
                "medication_assistant",
                "appointment_assistant",
            ]
        ],
        update_dialog_stack,
    ]

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


medication_instruction_search_tool = TavilySearchResults(
    description="Search online for instructions related the patient's requested medication. Do not use to give medical advice."
)

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
    
class CompleteOrEscalate(BaseModel):
    """A tool to mark the current task as completed and/or to escalate control of the dialog to the main assistant,
    who can re-route the dialog based on the user's needs."""

    cancel: bool = True
    reason: str

    class Config:
        schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User changed their mind about the current task.",
            },
            "example 2": {
                "cancel": True,
                "reason": "I have fully completed the task.",
            },
            "example 3": {
                "cancel": False,
                "reason": "I need to search the user's emails or calendar for more information.",
            },
        }


# Medication assistant
with open('/app/graph_definitions/system_prompts/medication_lookup_system_prompt.txt', 'r') as file:
    prompt = file.read()
medication_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", prompt),
        ("placeholder", "{messages}"),
    ]
)

medication_safe_tools = [get_patient_medications, get_patient_dob, medication_instruction_search_tool] # to add later
medication_sensitive_tools = [] # to add later
medication_tools = medication_safe_tools + medication_sensitive_tools
medication_runnable = medication_prompt | specialized_assistant_llm.bind_tools(
    medication_tools + [CompleteOrEscalate]
)

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

appointment_safe_tools = [find_available_appointments, book_appointment]
appointment_sensitive_tools = []
appointment_tools = appointment_safe_tools + appointment_sensitive_tools
# appointment_assistant_runnable = appointment_assistant_prompt | llm
appointment_runnable = appointment_prompt | specialized_assistant_llm.bind_tools(
    appointment_tools + [CompleteOrEscalate]
)


# Patient Intake assistant
with open('/app/graph_definitions/system_prompts/patient_intake_system_prompt.txt', 'r') as file:
    intake_system_prompt = file.read()
patient_intake_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", intake_system_prompt),
        ("placeholder", "{messages}"),
    ]
)
patient_intake_safe_tools = [print_gathered_patient_info]
patient_intake_sensitive_tools = []
patient_intake_tools = patient_intake_safe_tools + patient_intake_sensitive_tools
patient_intake_runnable = patient_intake_prompt | specialized_assistant_llm.bind_tools(
    patient_intake_tools + [CompleteOrEscalate]
)
class ToPatientIntakeAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle patient intake."""
    patient_name: str = Field(description="The patient's name.")
    patient_dob: datetime.date = Field(description="The patient's date of birth.")
    allergies_medication: List[str] = Field(description="A list of allergies in medication for the patient.")
    current_symptoms: str = Field(description="A description of the current symptoms for the patient.")
    current_symptoms_duration: datetime.timedelta = Field(description="The time duration of current symptoms.")
    pharmacy_location: str = Field(description="The patient's pharmacy location.")
    request: str = Field(
        description="Any necessary information the patient intake assistant should clarify before proceeding."
    )

# Primary Assistant
class ToFindMedicationInfoAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle medication."""

    request: str = Field(
        description="Any necessary information the medication assistant should clarify before proceeding."
    )


class ToFindAppointmentInfoAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle appointment type suggestion and appointment bookings."""

    start_date: datetime.date = Field(description="The start date of the search window for appointments.")
    end_date: datetime.date = Field(description="The end date of the the search window for appointments.")
    appointment_datetime: datetime.datetime = Field(description="The intended date and time of appointment the customer wants to book.")
    appointment_type: ApptType = Field(description="The type of appointment.")
    request: str = Field(
        description="Any additional information or requests from the user regarding their symptoms that will help determine the type of appointment."
    )

    class Config:
        schema_extra = {
            "example": {
                # "start_date": "2023-07-01",
                # "end_date": "2023-07-05",
                # "appointment_type": "Adult physicals",
                "request": "I have chest pain when I exercise, I want to see someone.",
            }
        }

# The top-level assistant performs general Q&A and delegates specialized tasks to other assistants.
# The task delegation is a simple form of semantic routing / does simple intent detection
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful customer support assistant for healthcare patients and administrators. "
            "Your primary role is to determine what the customer needs help with, whether they want to inquire about medication, make appointments, or register as a new patient. "
            "If a customer requests to see the list of current medications for a patient, describe their symptoms for making an appointment, mention they want to register as a patient, "
            "delegate the task to the appropriate specialized assistant by invoking the corresponding tool. You are not able to retrieve these information or make these types of changes yourself."
            " Only the specialized assistants are given permission to do this for the user."
            "The user is not aware of the different specialized assistants, so do not mention them; just quietly delegate through function calls. "
            "Provide detailed information to the customer, and always double-check the database before concluding that information is unavailable. "
            " When searching, be persistent. Expand your query bounds if the first search returns no results. "
            " If a search comes up empty, expand your search before giving up."
            "\nCurrent time: {time}.",
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.datetime.now())

primary_assistant_tools = [
    #TavilySearchResults(max_results=1),
]

assistant_runnable = primary_assistant_prompt | main_assistant_llm.bind_tools(
    primary_assistant_tools
    + [
        ToFindMedicationInfoAssistant,
        ToFindAppointmentInfoAssistant,
        ToPatientIntakeAssistant,
    ]
)

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: State) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node


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

# This node will be shared for exiting all specialized assistants
def pop_dialog_state(state: State) -> dict:
    """Pop the dialog stack and return to the main assistant.

    This lets the full graph explicitly track the dialog flow and delegate control
    to specific sub-graphs.
    """
    messages = []
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }

# Medication assistant
builder.add_node(
    "enter_medication_assistant",
    create_entry_node("Medication Finding and Info Assistant", "medication_assistant"),
)
builder.add_node("medication_assistant", Assistant(medication_runnable))
builder.add_edge("enter_medication_assistant", "medication_assistant")
builder.add_node(
    "medication_sensitive_tools",
    create_tool_node_with_fallback(medication_sensitive_tools),
)
builder.add_node(
    "medication_safe_tools",
    create_tool_node_with_fallback(medication_safe_tools),
)

def route_medication_assistant(
    state: State,
) -> Literal[
    "medication_sensitive_tools",
    "medication_safe_tools",
    "leave_skill",
    "__end__",
]:
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in medication_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "medication_safe_tools"
    return "medication_sensitive_tools"

builder.add_edge("medication_sensitive_tools", "medication_assistant")
builder.add_edge("medication_safe_tools", "medication_assistant")
builder.add_conditional_edges("medication_assistant", route_medication_assistant)

# Appointment assistant
builder.add_node(
    "enter_appointment_assistant",
    create_entry_node("Appointment Type and Scheduling Assistant", "appointment_assistant"),
)
builder.add_node("appointment_assistant", Assistant(appointment_runnable))
builder.add_edge("enter_appointment_assistant", "appointment_assistant")
builder.add_node(
    "appointment_safe_tools",
    create_tool_node_with_fallback(appointment_safe_tools),
)
builder.add_node(
    "appointment_sensitive_tools",
    create_tool_node_with_fallback(appointment_sensitive_tools),
)
def route_appointment_assist(
    state: State,
) -> Literal[
    "appointment_safe_tools",
    "appointment_sensitive_tools",
    "leave_skill",
    "__end__",
]:
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in appointment_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "appointment_safe_tools"
    return "appointment_sensitive_tools"

builder.add_edge("appointment_sensitive_tools", "appointment_assistant")
builder.add_edge("appointment_safe_tools", "appointment_assistant")
builder.add_conditional_edges("appointment_assistant", route_appointment_assist)



# Patient intake assistant
builder.add_node(
    "enter_patient_intake_assistant",
    create_entry_node("Patient Intake Assistant", "patient_intake_assistant"),
)
builder.add_node("patient_intake_assistant", Assistant(patient_intake_runnable))
builder.add_edge("enter_patient_intake_assistant", "patient_intake_assistant")
builder.add_node(
    "patient_intake_sensitive_tools",
    create_tool_node_with_fallback(patient_intake_sensitive_tools),
)
builder.add_node(
    "patient_intake_safe_tools",
    create_tool_node_with_fallback(patient_intake_safe_tools),
)

def route_patient_intake_assistant(
    state: State,
) -> Literal[
    "patient_intake_sensitive_tools",
    "patient_intake_safe_tools",
    "leave_skill",
    "__end__",
]:
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in patient_intake_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "patient_intake_safe_tools"
    return "patient_intake_sensitive_tools"

builder.add_edge("patient_intake_sensitive_tools", "patient_intake_assistant")
builder.add_edge("patient_intake_safe_tools", "patient_intake_assistant")
builder.add_conditional_edges("patient_intake_assistant", route_patient_intake_assistant)
    
    
# Primary assistant
builder.add_node("primary_assistant", Assistant(assistant_runnable))
builder.add_node(
    "primary_assistant_tools", create_tool_node_with_fallback(primary_assistant_tools)
)

def route_primary_assistant(
    state: State,
) -> Literal[
    "primary_assistant_tools",
    "enter_medication_assistant",
    "enter_appointment_assistant",
    "__end__",
]:
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        if tool_calls[0]["name"] == ToFindAppointmentInfoAssistant.__name__:
            return "enter_appointment_assistant"
        elif tool_calls[0]["name"] == ToFindMedicationInfoAssistant.__name__:
            return "enter_medication_assistant"
        elif tool_calls[0]["name"] == ToPatientIntakeAssistant.__name__:
            return "enter_patient_intake_assistant"
        return "primary_assistant_tools"
    raise ValueError("Invalid route")

# The assistant can route to one of the delegated assistants,
# directly use a tool, or directly respond to the user
builder.add_conditional_edges(
    "primary_assistant",
    route_primary_assistant,
    {
        "enter_medication_assistant": "enter_medication_assistant",
        "enter_appointment_assistant": "enter_appointment_assistant",
        "enter_patient_intake_assistant": "enter_patient_intake_assistant",
        "primary_assistant_tools": "primary_assistant_tools",
        END: END,
    },
)
builder.add_edge("primary_assistant_tools", "primary_assistant")

builder.add_node("leave_skill", pop_dialog_state)
builder.add_edge("leave_skill", "primary_assistant")

# Each delegated workflow can directly respond to the user
# When the user responds, we want to return to the currently active workflow
def route_to_workflow(
    state: State,
) -> Literal[
    "primary_assistant",
    "medication_assistant",
    "appointment_assistant",
    "patient_intake_assistant",
]:
    """If we are in a delegated state, route directly to the appropriate assistant."""
    dialog_state = state.get("dialog_state")
    if not dialog_state:
        return "primary_assistant"
    return dialog_state[-1]

#builder.add_conditional_edges("fetch_user_info", route_to_workflow)

builder.add_conditional_edges(START, route_to_workflow)
# Compile graph
memory = MemorySaver()
full_graph = builder.compile(
    checkpointer=memory,
    # To enable interrupts before sensitive tools and
    # let the user approve or deny the use of sensitive tools,
    # enable this interrupt_before param and also check for snapshot.next
    # as demonstrated by https://langchain-ai.github.io/langgraph/tutorials/customer-support/customer-support
    #interrupt_before=[
    #    "medication_sensitive_tools",
    #    "appointment_sensitive_tools",
    #],
)

if save_graph_to_png:
    
    with open("/graph_images/appgraph.png", "wb") as png:
        png.write(full_graph.get_graph(xray=True).draw_mermaid_png())
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=7860,
                        help = "Specify the port number for the simple voice UI to run at.")
                            
    args = parser.parse_args()
    server_port = args.port
    launch_demo_ui(full_graph, server_port, NVIDIA_API_KEY, RIVA_ASR_FUNCTION_ID, RIVA_TTS_FUNCTION_ID, RIVA_API_URI)
    



