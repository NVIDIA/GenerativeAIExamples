# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
"""The definition of the NVIDIA RAG server which acts as the main orchestrator."""
import importlib
import logging
import os
import shutil
import time
from contextlib import asynccontextmanager
from inspect import getmembers
from inspect import isclass
from pathlib import Path
from typing import Any, Literal, Optional
from typing import Dict
from typing import List
from uuid import uuid4

import bleach
from fastapi import FastAPI
from fastapi import File
from fastapi import Request
from fastapi import UploadFile
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from pydantic import Field
from pydantic import constr
from pydantic import validator
from pymilvus.exceptions import MilvusException
from pymilvus.exceptions import MilvusUnavailableException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())
logger = logging.getLogger(__name__)

tags_metadata = [
    {
        "name": "Health APIs",
        "description": "APIs for checking and monitoring server liveliness and readiness.",
    },
    {"name": "Ingestion APIs", "description": "APIs for ingestion, deletion and listing documents."},
    {"name": "Retrieval APIs", "description": "APIs for retrieving document chunks for a query."},
    {"name": "RAG APIs", "description": "APIs for retrieval followed by generation."},
]

# create the FastAPI server
app = FastAPI(title="APIs for NVIDIA RAG Server",
    description="This API schema describes all the retriever endpoints exposed for NVIDIA RAG server Blueprint",
    version="1.0.0",
        docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata,
)

# Allow access in browser from RAG UI and Storybook (development)
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


EXAMPLE_DIR = "./"


class Message(BaseModel):
    """Definition of the Chat Message type."""

    role: Literal["user", "assistant", "system", None] = Field(
        description="Role for a message: either 'user' or 'assistant' or 'system",
        default="user"
    )
    content: str = Field(
        description="The input query/prompt to the pipeline.",
        default="I am going to Paris, what should I see?",
        max_length=131072,
        pattern=r'[\s\S]*',
    )

    @validator('role')
    @classmethod
    def validate_role(cls, value):
        """ Field validator function to validate values of the field role"""
        if value:
            value = bleach.clean(value, strip=True)
            valid_roles = {'user', 'assistant', 'system'}
            if value is not None and value.lower() not in valid_roles:
                raise ValueError("Role must be one of 'user', 'assistant', or 'system'")
            return value.lower()

    @validator('content')
    @classmethod
    def sanitize_content(cls, v):
        """ Feild validator function to santize user populated feilds from HTML"""
        return bleach.clean(v, strip=True)


class Prompt(BaseModel):
    """Definition of the Prompt API data type."""

    messages: List[Message] = Field(
        ...,
        description="A list of messages comprising the conversation so far. "
        "The roles of the messages must be alternating between user and assistant. "
        "The last input message should have role user. "
        "A message with the the system role is optional, and must be the very first message if it is present.",
        max_items=50000,
    )
    use_knowledge_base: bool = Field(default=True, description="Whether to use a knowledge base")
    temperature: float = Field(
        0.2,
        description="The sampling temperature to use for text generation. "
        "The higher the temperature value is, the less deterministic the output text will be. "
        "It is not recommended to modify both temperature and top_p in the same call.",
        ge=0.1,
        le=1.0,
    )
    top_p: float = Field(
        0.7,
        description="The top-p sampling mass used for text generation. "
        "The top-p value determines the probability mass that is sampled at sampling time. "
        "For example, if top_p = 0.2, only the most likely tokens "
        "(summing to 0.2 cumulative probability) will be sampled. "
        "It is not recommended to modify both temperature and top_p in the same call.",
        ge=0.1,
        le=1.0,
    )
    max_tokens: int = Field(
        1024,
        description="The maximum number of tokens to generate in any given call. "
        "Note that the model is not aware of this value, "
        " and generation will simply stop at the number of tokens specified.",
        ge=0,
        le=1024,
        format="int64",
    )
    top_k: int = Field(
        description="The maximum number of documents to return in the response.",
        default=int(os.getenv("APP_RETRIEVER_TOPK", 4)),
        ge=0,
        le=25,
        format="int64",
    )
    collection_name: str = Field(
        description="Name of collection to be used for inference.",
        default=os.getenv("COLLECTION_NAME", ""),
        max_length=4096,
        pattern=r'[\s\S]*',
    )
    model: str = Field(
        description="Name of NIM LLM model  to be used for inference.",
        default=os.getenv("APP_LLM_MODELNAME", ""),
        max_length=4096,
        pattern=r'[\s\S]*',
    )

    # seed: int = Field(42, description="If specified, our system will make a best effort to sample deterministically,
    #       such that repeated requests with the same seed and parameters should return the same result.")
    # bad: List[str] = Field(None, description="A word or list of words not to use. The words are case sensitive.")
    stop: List[constr(max_length=256)] = Field(
        description="A string or a list of strings where the API will stop generating further tokens."
        "The returned text will not contain the stop sequence.",
        max_items=256,
        default=[],
    )
    # stream: bool = Field(True, description="If set, partial message deltas will be sent.
    #           Tokens will be sent as data-only server-sent events (SSE) as they become available
    #           (JSON responses are prefixed by data:), with the stream terminated by a data: [DONE] message.")

    @validator('use_knowledge_base')
    @classmethod
    def sanitize_use_kb(cls, v):
        """ Feild validator function to santize user populated feilds from HTML"""
        v = bleach.clean(str(v), strip=True)
        try:
            return {"True": True, "False": False}[v]
        except KeyError as e:
            raise ValueError("use_knowledge_base must be a boolean value") from e

    @validator('temperature')
    @classmethod
    def sanitize_temperature(cls, v):
        """ Feild validator function to santize user populated feilds from HTML"""
        return float(bleach.clean(str(v), strip=True))

    @validator('top_p')
    @classmethod
    def sanitize_top_p(cls, v):
        """ Feild validator function to santize user populated feilds from HTML"""
        return float(bleach.clean(str(v), strip=True))


def _string_to_prompt(data: str) -> Prompt:
    return Prompt(messages=[Message(content=data, role='user')],
                use_knowledge_base=True,
                collection_name=os.getenv("COLLECTION_NAME", "nvidia_api_catalog"))

class ChainResponseChoices(BaseModel):
    """ Definition of Chain response choices"""

    index: int = Field(default=0, ge=0, le=256, format="int64")
    # Should deprecate in long term, and move to message for OpenAI API compatibility
    message: Message = Field(default=Message(role="assistant", content=""))
    delta: Message = Field(default=Message(role=None, content=""))
    finish_reason: Optional[str] = Field(default=None, max_length=4096, pattern=r'[\s\S]*')



class ChainResponse(BaseModel):
    """Definition of Chain APIs resopnse data type"""

    id: str = Field(default="", max_length=100000, pattern=r'[\s\S]*')
    choices: List[ChainResponseChoices] = Field(default=[], max_items=256)
    model: str = Field(default="", max_length=4096, pattern=r'[\s\S]*')
    object: str = Field(default="", max_length=4096, pattern=r'[\s\S]*')
    created: int = Field(default=0, ge=0, le=9999999999, format="int64")


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
        default=int(os.getenv("APP_RETRIEVER_TOPK", 4)),
        ge=0,
        le=25,
        format="int64",
    )
    collection_name: str = Field(
        description="Name of collection to be used for searching document.",
        default=os.getenv("COLLECTION_NAME", ""),
        max_length=4096,
        pattern=r'[\s\S]*',
    )


class DocumentChunk(BaseModel):
    """Represents a chunk of a document."""

    content: str = Field(description="The content of the document chunk.",
                         max_length=131072,
                         pattern=r'[\s\S]*',
                         default="")
    filename: str = Field(description="The name of the file the chunk belongs to.",
                          max_length=4096,
                          pattern=r'[\s\S]*',
                          default="")
    score: float = Field(..., description="The relevance score of the chunk.")


class DocumentSearchResponse(BaseModel):
    """Represents a response from a document search."""

    chunks: List[DocumentChunk] = Field(..., description="List of document chunks.", max_items=256)


class DocumentsResponse(BaseModel):
    """Represents the response containing a list of documents."""

    documents: List[constr(max_length=131072)] = Field(description="List of filenames.", max_items=1000000, default=[])


class HealthResponse(BaseModel):
    message: str = Field(max_length=4096, pattern=r'[\s\S]*', default="")


@app.on_event("startup")
def import_example() -> None:
    """
    Import the example class from the specified example file.
    """

    # Path of the example directory
    example_path = os.environ.get("EXAMPLE_PATH", "src/")
    file_location = os.path.join(EXAMPLE_DIR, example_path)

    # Walk through the directory to find Python files
    for root, _, files in os.walk(file_location):
        for file in files:
            if not file.endswith(".py") or file == "__init__.py":
                continue

            file_path = os.path.join(root, file)

            try:
                # Generate the module name relative to the package
                relative_module = os.path.relpath(file_path, EXAMPLE_DIR).replace("/", ".").replace(".py", "")
                print(f"Attempting to import module: {relative_module}")

                # Import the module dynamically
                module = importlib.import_module(relative_module)

                # Look for classes implementing the required methods
                for name, cls in getmembers(module, isclass):
                    if name == "BaseExample":
                        continue

                    # Ensure the class implements required methods
                    if set(["ingest_docs", "rag_chain", "llm_chain"]).issubset(set(dir(cls))):
                        instance = cls
                        app.example = instance
                        print(f"Successfully loaded class: {name}")
                        return

            except Exception as e:
                print(f"Failed to import {file_path}: {e}")
                continue

    # Raise an error if no valid class is found
    raise NotImplementedError(f"Could not find a valid example class in {file_location}")


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors(), exclude={"input"})},
    )


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health APIs"],
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
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
    tags=["Ingestion APIs"],
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        }
    },
)
async def upload_document(
    request: Request,  # pylint: disable=unused-argument
    collection_name: str = os.getenv("COLLECTION_NAME", ""),
    replace_existing: bool = True,
    file: UploadFile = File(...)
) -> JSONResponse:
    """Upload a document to the vector store."""

    if not file.filename:
        return JSONResponse(content={"message": "No files provided"}, status_code=200)

    try:
        upload_folder = "/tmp-data/uploaded_files"
        upload_file = os.path.basename(file.filename)

        # Check for unsupported file formats (.rst, .rtf, etc.)
        not_supported_formats = ('.rst', '.rtf', '.org')
        if upload_file.endswith(not_supported_formats):
            logger.info("Detected a .rst or .rtf file, you need to install Pandoc manually in Docker.")
            # Provide instructions to install Pandoc in Dockerfile
            dockerfile_instructions = """
            # Install pandoc from the tarball to support ingestion .rst, .rtf & .org files
            RUN curl -L https://github.com/jgm/pandoc/releases/download/3.6/pandoc-3.6-linux-amd64.tar.gz -o /tmp/pandoc.tar.gz && \
            tar -xzf /tmp/pandoc.tar.gz -C /tmp && \
            mv /tmp/pandoc-3.6/bin/pandoc /usr/local/bin/ && \
            rm -rf /tmp/pandoc.tar.gz /tmp/pandoc-3.6
            """
            logger.info(dockerfile_instructions)
            raise Exception(f"File format for {upload_file} is not supported.")

        if not upload_file:
            raise RuntimeError("Error parsing uploaded filename.")
        file_path = os.path.join(upload_folder, upload_file)
        uploads_dir = Path(upload_folder)
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Check if the file already exists
        if os.path.exists(file_path):
            if replace_existing:
                logger.info("Document %s already exists replacing document", file.filename)
                example = app.example()
                if hasattr(example, "delete_documents") and callable(example.delete_documents):
                    status = example.delete_documents([file.filename], collection_name)
                    if not status:
                        logger.warning("Unable to remove %s from collection", file.filename)
            else:
                raise RuntimeError(f"The document '{file.filename}' already exists. To overwrite it, enable the 'replace_existing' option to delete and re-ingest the file.")

        # Copy uploaded file to upload_dir directory and pass that file path to rag server
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        app.example().ingest_docs(file_path, upload_file, collection_name)

        return JSONResponse(content={"message": "File uploaded successfully"}, status_code=200)

    except Exception as e:
        logger.error("Error from POST /documents endpoint. Ingestion of file: %s failed with error: %s",
                     file.filename,
                     e)
        return JSONResponse(content={"message": str(e)}, status_code=500)


@app.post(
    "/generate",
    tags=["RAG APIs"],
    response_model=ChainResponse,
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        }
    },
)
async def generate_answer(_: Request, prompt: Prompt) -> StreamingResponse:
    """Generate and stream the response to the provided prompt."""

    try:
        chat_history = prompt.messages
        collection_name = prompt.collection_name
        # The last user message will be the query for the rag or llm chain
        last_user_message = next((message.content for message in reversed(chat_history) if message.role == 'user'),
                                 None)

        # Find and remove the last user message if present
        for i in reversed(range(len(chat_history))):
            if chat_history[i].role == 'user':
                del chat_history[i]
                break  # Remove only the last user message

        # All the other information from the prompt like the temperature, top_p etc., are llm_settings
        llm_settings = {
            key: value
            for key, value in vars(prompt).items() if key not in ['messages', 'use_knowledge_base', 'collection_name']
        }

        # pylint: disable=unreachable
        example = app.example()
        generator = None
        # call rag_chain if use_knowledge_base is enabled
        if prompt.use_knowledge_base:
            logger.info("Knowledge base is enabled. Using rag chain for response generation.")
            generator = example.rag_chain(query=last_user_message,
                                          chat_history=chat_history,
                                          top_n=prompt.top_k,
                                          collection_name=collection_name,
                                          **llm_settings)

        else:
            generator = example.llm_chain(query=last_user_message, chat_history=chat_history, **llm_settings)

        def response_generator():
            """Convert generator streaming response into `data: ChainResponse` format for chunk"""
            # unique response id for every query
            resp_id = str(uuid4())
            if generator:
                logger.debug("Generated response chunks\n")
                # Create ChainResponse object for every token generated
                for chunk in generator:
                    chain_response = ChainResponse()
                    response_choice = ChainResponseChoices(
                        index=0,
                        message=Message(role="assistant", content=chunk),
                        delta=Message(role=None, content=chunk),
                        finish_reason=None

                    )
                    chain_response.id = resp_id
                    chain_response.choices.append(response_choice)  # pylint: disable=E1101
                    chain_response.model = prompt.model
                    chain_response.object = "chat.completion.chunk"
                    chain_response.created = int(time.time())
                    logger.debug(response_choice)
                    # Send generator with tokens in ChainResponse format
                    yield "data: " + str(chain_response.json()) + "\n\n"
                chain_response = ChainResponse()

                # [DONE] indicate end of response from server
                response_choice = ChainResponseChoices(
                    finish_reason="stop",
                )
                chain_response.id = resp_id
                chain_response.choices.append(response_choice)  # pylint: disable=E1101
                chain_response.model = prompt.model
                chain_response.object = "chat.completion.chunk"
                chain_response.created = int(time.time())
                logger.debug(response_choice)
                yield "data: " + str(chain_response.json()) + "\n\n"
            else:
                chain_response = ChainResponse()
                yield "data: " + str(chain_response.json()) + "\n\n"

        return StreamingResponse(response_generator(), media_type="text/event-stream")
        # pylint: enable=unreachable

    except (MilvusException, MilvusUnavailableException) as e:
        exception_msg = ("Error from milvus server. Please ensure you have ingested some documents. "
                         "Please check rag-server logs for more details.")
        chain_response = ChainResponse()
        response_choice = ChainResponseChoices(index=0,
                                               message=Message(role="assistant", content=exception_msg),
                                               delta=Message(role="assistant", content=exception_msg),
                                               finish_reason="stop")
        chain_response.choices.append(response_choice)  # pylint: disable=E1101
        chain_response.model = prompt.model
        chain_response.object = "chat.completion.chunk"
        chain_response.created = int(time.time())
        logger.error(
            "Error from Milvus database in /generate endpoint. Please ensure you have ingested some documents. " +
            "Error details: %s",
            e)
        return StreamingResponse(iter(["data: " + str(chain_response.json()) + "\n\n"]),
                                 media_type="text/event-stream",
                                 status_code=500)

    except Exception as e:
        exception_msg = "Error from rag server. Please check rag-server logs for more details."
        chain_response = ChainResponse()
        response_choice = ChainResponseChoices(index=0,
                                               message=Message(role="assistant", content=exception_msg),
                                               delta=Message(role="assistant", content=exception_msg),
                                               finish_reason="stop")
        chain_response.choices.append(response_choice)  # pylint: disable=E1101
        chain_response.model = prompt.model
        chain_response.object = "chat.completion.chunk"
        chain_response.created = int(time.time())
        logger.error("Error from /generate endpoint. Error details: %s", e)
        return StreamingResponse(iter(["data: " + str(chain_response.json()) + "\n\n"]),
                                 media_type="text/event-stream",
                                 status_code=500)

# Alias function to /generate endpoint OpenAI API compatibility
@app.post(
    "/v1/chat/completions",
    tags=["RAG APIs"],
    response_model=ChainResponse,
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        }
    },
)
async def v1_chat_completions(_: Request, prompt: Prompt) -> StreamingResponse:
    """ Just an alias function to /generate endpoint which is openai compatible """

    response = await generate_answer(_, prompt)
    return response


@app.post(
    "/search",
    tags=["Retrieval APIs"],
    response_model=DocumentSearchResponse,
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        }
    },
)
async def document_search(_: Request, data: DocumentSearch) -> Dict[str, List[Dict[str, Any]]]:
    """Search for the most relevant documents for the given search parameters."""

    try:
        example = app.example()
        if hasattr(example, "document_search") and callable(example.document_search):
            search_result = example.document_search(data.query, data.top_k, data.collection_name)
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
        logger.error("Error from POST /search endpoint. Error details: %s", e)
        return JSONResponse(content={"message": "Error occurred while searching documents."}, status_code=500)


@app.get(
    "/documents",
    tags=["Ingestion APIs"],
    response_model=DocumentsResponse,
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        }
    },
)
async def get_documents(_: Request, collection_name: str = os.getenv("COLLECTION_NAME", "")) -> DocumentsResponse:
    """Get list of document ingested in vectorstore."""
    try:
        example = app.example()
        if hasattr(example, "get_documents") and callable(example.get_documents):
            documents = example.get_documents(collection_name)
            return DocumentsResponse(documents=documents)

        raise NotImplementedError("Example class has not implemented the get_documents method.")

    except Exception as e:
        logger.error("Error from GET /documents endpoint. Error details: %s", e)
        return JSONResponse(content={"message": "Error occurred while fetching documents."}, status_code=500)


@app.delete(
    "/documents",
    tags=["Ingestion APIs"],
    responses={
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        }
    },
)
async def delete_document(_: Request, filename: str, collection_name: str = os.getenv("COLLECTION_NAME",
                                                                                      "")) -> JSONResponse:
    """Delete a document from vectorstore."""
    try:
        example = app.example()
        if hasattr(example, "delete_documents") and callable(example.delete_documents):
            status = example.delete_documents([filename], collection_name)
            if not status:
                raise Exception(f"Error in deleting document {filename}")  # pylint: disable=W0719
            return JSONResponse(content={"message": f"Document {filename} deleted successfully"}, status_code=200)

        raise NotImplementedError("Example class has not implemented the delete_document method.")

    except Exception as e:
        logger.error("Error from DELETE /documents endpoint. Error details: %s", e)
        return JSONResponse(content={"message": f"Error deleting document {filename}"}, status_code=500)


@app.get("/collections", tags=["Ingestion APIs"], response_model=List[str])
async def get_collections():
    """
    Endpoint to get a list of collection names from the Milvus server.
    Returns a list of collection names.
    """
    from .utils import get_collection
    collections = get_collection()
    return collections
