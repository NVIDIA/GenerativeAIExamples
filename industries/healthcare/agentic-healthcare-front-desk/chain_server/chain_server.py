import uvicorn
import argparse


from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from pydantic import BaseModel, Field, constr, validator
import bleach
from typing import List, Generator

import uuid
from uuid import uuid4
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

parser = argparse.ArgumentParser()
parser.add_argument("--assistant", choices=["full", "intake", "appointment", "medication"],
                    help = "Specify full for the full graph with main assistant routing to specialist assistants. "
                    "Specify intake for the patient intake assistant only. "
                    "Specify appointment for the appointemnt making assistant only."
                    "Specify medication for the medication lookup assistant only")
parser.add_argument("--port", type=int, default=8081,
                    help = "Specify the port number for the chain server to run at.")
                        
args = parser.parse_args()
if args.assistant == "full":
    from graph_definitions.graph import full_graph
    assistant_graph = full_graph
elif args.assistant == "intake":
    from graph_definitions.graph_patient_intake_only import intake_graph
    assistant_graph = intake_graph
elif args.assistant == "appointment":
    from graph_definitions.graph_appointment_making_only import appt_graph
    assistant_graph = appt_graph
elif args.assistant == "medication":
    from graph_definitions.graph_medication_lookup_only import medication_lookup_graph
    assistant_graph = medication_lookup_graph
else:
    raise Exception("We must specify one of the three options for assistant: full, intake or appointment.")

port = args.port

# create the FastAPI server
app = FastAPI()

# Allow access in browser from RAG UI and Storybook (development)
origins = ["*"]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
)

class Message(BaseModel):
    """Definition of the Chat Message type."""

    role: str = Field(
        description="Role for a message AI, User and System", default="user", max_length=256, pattern=r'[\s\S]*'
    )
    content: str = Field(
        description="The input query/prompt to the pipeline.",
        default="I am going to Paris, what should I see?",
        max_length=131072,
        pattern=r'[\s\S]*',
    )

    @validator('role')
    def validate_role(cls, value):
        """ Field validator function to validate values of the field role"""
        value = bleach.clean(value, strip=True)
        valid_roles = {'user', 'assistant', 'system'}
        if value.lower() not in valid_roles:
            raise ValueError("Role must be one of 'user', 'assistant', or 'system'")
        return value.lower()

    @validator('content')
    def sanitize_content(cls, v):
        """ Feild validator function to santize user populated feilds from HTML"""
        return bleach.clean(v, strip=True)

class Prompt(BaseModel):
    """Definition of the Prompt API data type."""

    messages: List[Message] = Field(
        ...,
        description="A list of messages comprising the conversation so far. The roles of the messages must be alternating between user and assistant. The last input message should have role user. A message with the the system role is optional, and must be the very first message if it is present.",
        max_items=50000,
    )
    temperature: float = Field(
        0.2,
        description="The sampling temperature to use for text generation. The higher the temperature value is, the less deterministic the output text will be. It is not recommended to modify both temperature and top_p in the same call.",
        ge=0.1,
        le=1.0,
    )
    top_p: float = Field(
        0.7,
        description="The top-p sampling mass used for text generation. The top-p value determines the probability mass that is sampled at sampling time. For example, if top_p = 0.2, only the most likely tokens (summing to 0.2 cumulative probability) will be sampled. It is not recommended to modify both temperature and top_p in the same call.",
        ge=0.1,
        le=1.0,
    )
    max_tokens: int = Field(
        1024,
        description="The maximum number of tokens to generate in any given call. Note that the model is not aware of this value, and generation will simply stop at the number of tokens specified.",
        ge=0,
        le=1024,
        format="int64",
    )

    stop: List[constr(max_length=256, pattern=r'[\s\S]*')] = Field(
        description="A string or a list of strings where the API will stop generating further tokens. The returned text will not contain the stop sequence.",
        max_items=256,
        default=[],
    )
    # stream: bool = Field(True, description="If set, partial message deltas will be sent. Tokens will be sent as data-only server-sent events (SSE) as they become available (JSON responses are prefixed by data:), with the stream terminated by a data: [DONE] message.")

    @validator('temperature')
    def sanitize_temperature(cls, v):
        """ Feild validator function to santize user populated feilds from HTML"""
        return float(bleach.clean(str(v), strip=True))

    @validator('top_p')
    def sanitize_top_p(cls, v):
        """ Feild validator function to santize user populated feilds from HTML"""
        return float(bleach.clean(str(v), strip=True))
    
class ChainResponseChoices(BaseModel):
    """ Definition of Chain response choices"""

    index: int = Field(default=0, ge=0, le=256, format="int64")
    message: Message = Field(default=Message(role="assistant", content=""))
    finish_reason: str = Field(default="", max_length=4096, pattern=r'[\s\S]*')

class ChainResponse(BaseModel):
    """Definition of Chain APIs resopnse data type"""

    id: str = Field(default="", max_length=100000, pattern=r'[\s\S]*')
    choices: List[ChainResponseChoices] = Field(default=[], max_items=256)

class HealthResponse(BaseModel):
    message: str = Field(max_length=4096, pattern=r'[\s\S]*', default="")
class HealthCheck(BaseModel):
    status: str = "OK"

def get_new_thread_id():
    return str(uuid.uuid4())
thread_id = get_new_thread_id()

langgraph_config = {
    "configurable": {
        # Checkpoints are accessed by thread_id
        "thread_id": thread_id,
    }
}

def _print_event(event: dict, _printed: set, max_length=1500):
    return_print = ""
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
        return_print += "Currently in: "
        return_print += current_state[-1]
        return_print += "\n"
    message = event.get("messages")
    latest_msg_chatbot = ""
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr()
            msg_repr_chatbot = str(message.content)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
                msg_repr_chatbot = msg_repr_chatbot[:max_length] + " ... (truncated)"
            return_print += msg_repr
            latest_msg_chatbot = msg_repr_chatbot
            print(msg_repr)
            _printed.add(message.id)
    return_print += "\n"
    return return_print, latest_msg_chatbot

def example_llm_chain(query: str, chat_history: List["Message"], **kwargs) -> Generator[str, None, None]:
        """Execute a Retrieval Augmented Generation chain using the components defined above."""
        
        print("thread_id", langgraph_config["configurable"]["thread_id"])
        
        _printed = set()
        events = assistant_graph.stream(
            {"messages": ("user", query)}, langgraph_config, stream_mode="values"
        )
        latest_response = ""
        for event in events:
            return_print, latest_msg =  _print_event(event, _printed)
            if latest_msg != "":
                latest_response = latest_msg
        yield latest_response
        

@app.post(
    "/generate",
    response_model=ChainResponse,
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal server error occurred"}}},
        }
    },
)
async def generate_answer(request: Request, prompt: Prompt) -> StreamingResponse:
    """Generate and stream the response to the provided prompt."""

    chat_history = prompt.messages
    # The last user message will be the query for the rag or llm chain
    last_user_message = next((message.content for message in reversed(chat_history) if message.role == 'user'), None)

    # Find and remove the last user message if present
    for i in reversed(range(len(chat_history))):
        if chat_history[i].role == 'user':
            del chat_history[i]
            break  # Remove only the last user message

    # All the other information from the prompt like the temperature, top_p etc., are llm_settings
    llm_settings = {key: value for key, value in vars(prompt).items() if key not in ['messages']}
    try:
        generator = None
        # call llm_chain since we're not doing knowledge base
        generator = example_llm_chain(query=last_user_message, chat_history=chat_history, **llm_settings)

        def response_generator():
            """Convert generator streaming response into `data: ChainResponse` format for chunk 
            """
            # unique response id for every query
            resp_id = str(uuid4())
            if generator:
                # Create ChainResponse object for every token generated
                for chunk in generator:
                    chain_response = ChainResponse()
                    response_choice = ChainResponseChoices(index=0, message=Message(role="assistant", content=chunk))
                    chain_response.id = resp_id
                    chain_response.choices.append(response_choice)
                    
                    # Send generator with tokens in ChainResponse format
                    yield "data: " + str(chain_response.json()) + "\n\n"
                chain_response = ChainResponse()

                # [DONE] indicate end of response from server
                response_choice = ChainResponseChoices(finish_reason="[DONE]")
                chain_response.id = resp_id
                chain_response.choices.append(response_choice)
                
                yield "data: " + str(chain_response.json()) + "\n\n"
            else:
                chain_response = ChainResponse()
                yield "data: " + str(chain_response.json()) + "\n\n"

        return StreamingResponse(response_generator(), media_type="text/event-stream")

    except Exception as e:
        exception_msg = "Error from chain server. Please check chain-server logs for more details."
        chain_response = ChainResponse()
        response_choice = ChainResponseChoices(
            index=0, message=Message(role="assistant", content=exception_msg), finish_reason="[DONE]"
        )
        chain_response.choices.append(response_choice)
        return StreamingResponse(
            iter(["data: " + str(chain_response.json()) + "\n\n"]), media_type="text/event-stream", status_code=500
        )
    
@app.get("/health", 
         tags=["healthcheck"], 
         summary="Perform a Health Check", 
         response_description="Return HTTP Status Code 200 (OK)", 
         status_code=status.HTTP_200_OK, 
         response_model=HealthCheck)
def get_health() -> HealthCheck:
    return HealthCheck(status="OK")


if __name__ == "__main__":
    

    uvicorn.run(app, host="0.0.0.0", port=port)