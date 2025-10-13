# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""The definition of the Llama Index chain server."""
import importlib
import json
import logging
import os
import shutil
from inspect import getmembers, isclass
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4

import bleach
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field, constr, validator
from pymilvus.exceptions import MilvusException, MilvusUnavailableException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from RAG.src.chain_server.tracing import llamaindex_instrumentation_wrapper

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())
logger = logging.getLogger(__name__)

# create the FastAPI server
app = FastAPI()

# Allow access in browser from RAG UI and Storybook (development)
origins = ["*"]
app.add_middleware(
    CORSMiddleware, allow_origins=origins, allow_credentials=False, allow_methods=["*"], allow_headers=["*"],
)

EXAMPLE_DIR = "RAG/examples/"


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
    use_knowledge_base: bool = Field(..., description="Whether to use a knowledge base")
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
    # seed: int = Field(42, description="If specified, our system will make a best effort to sample deterministically, such that repeated requests with the same seed and parameters should return the same result.")
    # bad: List[str] = Field(None, description="A word or list of words not to use. The words are case sensitive.")
    stop: List[constr(max_length=256, pattern=r'[\s\S]*')] = Field(
        description="A string or a list of strings where the API will stop generating further tokens. The returned text will not contain the stop sequence.",
        max_items=256,
        default=[],
    )
    # stream: bool = Field(True, description="If set, partial message deltas will be sent. Tokens will be sent as data-only server-sent events (SSE) as they become available (JSON responses are prefixed by data:), with the stream terminated by a data: [DONE] message.")

    @validator('use_knowledge_base')
    def sanitize_use_kb(cls, v):
        """ Feild validator function to santize user populated feilds from HTML"""
        v = bleach.clean(str(v), strip=True)
        try:
            return {"True": True, "False": False}[v]
        except KeyError:
            raise ValueError("use_knowledge_base must be a boolean value")

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


class DocumentSearch(BaseModel):
    """Definition of the DocumentSearch API data type."""

    query: str = Field(
        description="The content or keywords to search for within documents.",
        max_length=131072,
        pattern=r'[\s\S]*',
        default="",
    )
    top_k: int = Field(
        description="The maximum number of documents to return in the response.",
        default=4,
        ge=0,
        le=25,
        format="int64",
    )


class DocumentChunk(BaseModel):
    """Represents a chunk of a document."""

    content: str = Field(
        description="The content of the document chunk.", max_length=131072, pattern=r'[\s\S]*', default=""
    )
    filename: str = Field(
        description="The name of the file the chunk belongs to.", max_length=4096, pattern=r'[\s\S]*', default=""
    )
    score: float = Field(..., description="The relevance score of the chunk.")


class DocumentSearchResponse(BaseModel):
    """Represents a response from a document search."""

    chunks: List[DocumentChunk] = Field(..., description="List of document chunks.", max_items=256)


class DocumentsResponse(BaseModel):
    """Represents the response containing a list of documents."""

    documents: List[constr(max_length=131072, pattern=r'[\s\S]*')] = Field(
        description="List of filenames.", max_items=1000000, default=[]
    )


class HealthResponse(BaseModel):
    message: str = Field(max_length=4096, pattern=r'[\s\S]*', default="")


@app.on_event("startup")
def import_example() -> None:
    """
    Import the example class from the specified example file.
    The example directory is expected to have a python file where the example class is defined.
    """

    # path of the example directory, to check for chain implementation
    file_location = os.path.join(EXAMPLE_DIR, os.environ.get("EXAMPLE_PATH", "basic_rag/llamaindex"))

    # Walk through the directory to find the RAG chains and store it's class
    for root, dirs, files in os.walk(file_location):
        for file in files:
            if not file.endswith(".py"):
                continue

            # Import the specified file dynamically
            spec = importlib.util.spec_from_file_location(name="example", location=os.path.join(root, file))
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Scan each class in the file to find one with the 3 implemented methods: ingest_docs, rag_chain and llm_chain
            for name, _ in getmembers(module, isclass):
                try:
                    cls = getattr(module, name)
                    if set(["ingest_docs", "llm_chain", "rag_chain"]).issubset(set(dir(cls))):
                        if name == "BaseExample":
                            continue
                        # Try creating example class instance, store it in app.example if successful
                        example = cls()
                        app.example = cls
                        return
                except:
                    raise ValueError(f"Class {name} is not implemented and could not be instantiated.")

    raise NotImplementedError(f"Could not find a valid example class in {EXAMPLE_DIR}")


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors(), exclude={"input"})},
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal server error occurred"}}},
        }
    },
)
def health_check():
    """
    Perform a Health Check

    Returns 200 when service is up. This does not check the health of downstream services.
    """

    response_message = "Service is up."
    return HealthResponse(message=response_message)


@app.post(
    "/documents",
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal server error occurred"}}},
        }
    },
)
@llamaindex_instrumentation_wrapper
async def upload_document(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """Upload a document to the vector store."""

    if not file.filename:
        return JSONResponse(content={"message": "No files provided"}, status_code=200)

    try:
        upload_folder = "/tmp-data/uploaded_files"
        upload_file = os.path.basename(file.filename)
        if not upload_file:
            raise RuntimeError("Error parsing uploaded filename.")
        file_path = os.path.join(upload_folder, upload_file)
        uploads_dir = Path(upload_folder)
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Copy uploaded file to upload_dir directory and pass that file path to chain server
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        app.example().ingest_docs(file_path, upload_file)

        return JSONResponse(content={"message": "File uploaded successfully"}, status_code=200)

    except Exception as e:
        logger.error(
            "Error from POST /documents endpoint. Ingestion of file: "
            + file.filename
            + " failed with error: "
            + str(e)
        )
        return JSONResponse(content={"message": str(e)}, status_code=500)


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
@llamaindex_instrumentation_wrapper
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
    llm_settings = {key: value for key, value in vars(prompt).items() if key not in ['messages', 'use_knowledge_base']}
    try:
        example = app.example()
        generator = None
        # call rag_chain if use_knowledge_base is enabled
        if prompt.use_knowledge_base:
            logger.info("Knowledge base is enabled. Using rag chain for response generation.")
            generator = example.rag_chain(query=last_user_message, chat_history=chat_history, **llm_settings)

        else:
            generator = example.llm_chain(query=last_user_message, chat_history=chat_history, **llm_settings)

        def response_generator():
            """Convert generator streaming response into `data: ChainResponse` format for chunk 
            """
            # unique response id for every query
            resp_id = str(uuid4())
            if generator:
                logger.debug(f"Generated response chunks\n")
                # Create ChainResponse object for every token generated
                for chunk in generator:
                    chain_response = ChainResponse()
                    response_choice = ChainResponseChoices(index=0, message=Message(role="assistant", content=chunk))
                    chain_response.id = resp_id
                    chain_response.choices.append(response_choice)
                    logger.debug(response_choice)
                    # Send generator with tokens in ChainResponse format
                    yield "data: " + str(chain_response.json()) + "\n\n"
                chain_response = ChainResponse()

                # [DONE] indicate end of response from server
                response_choice = ChainResponseChoices(finish_reason="[DONE]")
                chain_response.id = resp_id
                chain_response.choices.append(response_choice)
                logger.debug(response_choice)
                yield "data: " + str(chain_response.json()) + "\n\n"
            else:
                chain_response = ChainResponse()
                yield "data: " + str(chain_response.json()) + "\n\n"

        return StreamingResponse(response_generator(), media_type="text/event-stream")

    except (MilvusException, MilvusUnavailableException) as e:
        exception_msg = "Error from milvus server. Please ensure you have ingested some documents. Please check chain-server logs for more details."
        chain_response = ChainResponse()
        response_choice = ChainResponseChoices(
            index=0, message=Message(role="assistant", content=exception_msg), finish_reason="[DONE]"
        )
        chain_response.choices.append(response_choice)
        logger.error(
            f"Error from Milvus database in /generate endpoint. Please ensure you have ingested some documents. Error details: {e}"
        )
        return StreamingResponse(
            iter(["data: " + str(chain_response.json()) + "\n\n"]), media_type="text/event-stream", status_code=500
        )

    except Exception as e:
        exception_msg = "Error from chain server. Please check chain-server logs for more details."
        chain_response = ChainResponse()
        response_choice = ChainResponseChoices(
            index=0, message=Message(role="assistant", content=exception_msg), finish_reason="[DONE]"
        )
        chain_response.choices.append(response_choice)
        logger.error(f"Error from /generate endpoint. Error details: {e}")
        return StreamingResponse(
            iter(["data: " + str(chain_response.json()) + "\n\n"]), media_type="text/event-stream", status_code=500
        )


@app.post(
    "/search",
    response_model=DocumentSearchResponse,
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal server error occurred"}}},
        }
    },
)
@llamaindex_instrumentation_wrapper
async def document_search(request: Request, data: DocumentSearch) -> Dict[str, List[Dict[str, Any]]]:
    """Search for the most relevant documents for the given search parameters."""

    try:
        example = app.example()
        if hasattr(example, "document_search") and callable(example.document_search):
            search_result = example.document_search(data.query, data.top_k)
            chunks = []
            # Format top_k result in response format
            for entry in search_result:
                content = entry.get("content", "")  # Default to empty string if "content" key doesn't exist
                source = entry.get("source", "")  # Default to empty string if "source" key doesn't exist
                score = entry.get("score", 0.0)  # Default to 0.0 if "score" key doesn't exist
                chunk = DocumentChunk(content=content, filename=source, document_id="", score=score)
                chunks.append(chunk)
            return DocumentSearchResponse(chunks=chunks)
        raise NotImplementedError("Example class has not implemented the document_search method.")

    except Exception as e:
        logger.error(f"Error from POST /search endpoint. Error details: {e}")
        return JSONResponse(content={"message": "Error occurred while searching documents."}, status_code=500)


@app.get(
    "/documents",
    response_model=DocumentsResponse,
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal server error occurred"}}},
        }
    },
)
@llamaindex_instrumentation_wrapper
async def get_documents(request: Request) -> DocumentsResponse:
    """Get list of document ingested in vectorstore."""
    try:
        example = app.example()
        if hasattr(example, "get_documents") and callable(example.get_documents):
            documents = example.get_documents()
            return DocumentsResponse(documents=documents)
        else:
            raise NotImplementedError("Example class has not implemented the get_documents method.")

    except Exception as e:
        logger.error(f"Error from GET /documents endpoint. Error details: {e}")
        return JSONResponse(content={"message": "Error occurred while fetching documents."}, status_code=500)


@app.delete(
    "/documents",
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {"application/json": {"example": {"detail": "Internal server error occurred"}}},
        }
    },
)
@llamaindex_instrumentation_wrapper
async def delete_document(request: Request, filename: str) -> JSONResponse:
    """Delete a document from vectorstore."""
    try:
        example = app.example()
        if hasattr(example, "delete_documents") and callable(example.delete_documents):
            status = example.delete_documents([filename])
            if not status:
                raise Exception(f"Error in deleting document {filename}")
            return JSONResponse(content={"message": f"Document {filename} deleted successfully"}, status_code=200)

        raise NotImplementedError("Example class has not implemented the delete_document method.")

    except Exception as e:
        logger.error(f"Error from DELETE /documents endpoint. Error details: {e}")
        return JSONResponse(content={"message": f"Error deleting document {filename}"}, status_code=500)
