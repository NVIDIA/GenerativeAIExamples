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
"""The definition of the NVIDIA RAG Ingestion server."""
import asyncio
import logging
import os
import json
import shutil
from inspect import getmembers
from inspect import isclass
from pathlib import Path
from typing import List, Dict, Any
from uuid import uuid4

from fastapi import UploadFile, Request, File, FastAPI, Form, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from pydantic import Field
from pydantic import constr
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY
from nv_ingest_client.util.file_processing.extract import EXTENSION_TO_DOCUMENT_TYPE

from src.chains import UnstructuredRAG
from .main import NVIngestIngestor

logging.basicConfig(level=os.environ.get('LOGLEVEL', 'INFO').upper())
logger = logging.getLogger(__name__)

tags_metadata = [
    {
        "name": "Health APIs",
        "description": "APIs for checking and monitoring server liveliness and readiness.",
    },
    {"name": "Ingestion APIs", "description": "APIs for uploading, deletion and listing documents."},
    {"name": "Vector DB APIs", "description": "APIs for managing collections in vector database."}
]

# create the FastAPI server
app = FastAPI(root_path=f"/v1", title="APIs for NVIDIA RAG Ingestion Server",
    description="This API schema describes all the Ingestion endpoints exposed for NVIDIA RAG server Blueprint",
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

# Support for UnstructuredRAG.ingest_docs()
UNSTRUCTURED_RAG_CHAIN = UnstructuredRAG() # Support to be DEPRECATED in future
ENABLE_NV_INGEST = True # Configurable flag to enable/disable nv-ingest

# Initialize the NVIngestIngestor class
NV_INGEST_INGESTOR = NVIngestIngestor()

class HealthResponse(BaseModel):
    message: str = Field(max_length=4096, pattern=r'[\s\S]*', default="")


class ExtractionOptions(BaseModel):
    """Options for extracting different content types from documents."""
    extract_text: bool = Field(os.getenv("APP_NVINGEST_EXTRACTTEXT", "True").lower() in ["true", "True"], description="Enable text extraction from the document.")
    extract_tables: bool = Field(os.getenv("APP_NVINGEST_EXTRACTTABLES", "True").lower() in ["true", "True"], description="Enable table extraction from the document.")
    extract_charts: bool = Field(os.getenv("APP_NVINGEST_EXTRACTCHARTS", "True").lower() in ["true", "True"], description="Enable chart extraction from the document.")
    extract_images: bool = Field(os.getenv("APP_NVINGEST_EXTRACTIMAGES", "False").lower() in ["true", "True"], description="Enable image extraction from the document.")
    extract_method: str = Field(os.getenv("APP_NVINGEST_EXTRACTMETHOD", "pdfium"), description="Extract method 'pdfium', 'nemoretriever_parse', 'haystack', 'llama_parse', 'tika', 'unstructured_io'")
    text_depth: str = Field(os.getenv("APP_NVINGEST_TEXTDEPTH", "page"), description="Extract text by 'page' or 'document'")


class SplitOptions(BaseModel):
    """Options for splitting the document into smaller chunks."""
    chunk_size: int = Field(1024, description="Number of units per split.")
    chunk_overlap: int = Field(150, description="Number of overlapping units between consecutive splits.")


class DocumentUploadRequest(BaseModel):
    """Request model for uploading and processing documents."""

    vdb_endpoint: str = Field(
        os.getenv("APP_VECTORSTORE_URL", "http://localhost:19530"),
        description="URL of the vector database endpoint.",
        exclude=True # WAR to hide it from openapi schema
    )

    collection_name: str = Field(
        "multimodal_data",
        description="Name of the collection in the vector database."
    )

    extraction_options: ExtractionOptions = Field(
        default_factory=ExtractionOptions,
        description="Options to control what types of content are extracted from the document."
    )

    split_options: SplitOptions = Field(
        default_factory=SplitOptions,
        description="Options for splitting documents into smaller parts before embedding."
    )

    # Reserved for future use
    # embedding_model: str = Field(
    #     os.getenv("APP_EMBEDDINGS_MODELNAME", ""),
    #     description="Identifier for the embedding model to be used."
    # )

    # embedding_endpoint: str = Field(
    #     os.getenv("APP_EMBEDDINGS_SERVERURL", ""),
    #     description="URL of the embedding service endpoint."
    # )

class UploadedDocument(BaseModel):
    """Model representing an individual uploaded document."""
    # Reserved for future use
    # document_id: str = Field("", description="Unique identifier for the document.")
    document_name: str = Field("", description="Name of the document.")
    # Reserved for future use
    # size_bytes: int = Field(0, description="Size of the document in bytes.")

class DocumentListResponse(BaseModel):
    """Response model for uploading a document."""
    message: str = Field("", description="Message indicating the status of the request.")
    total_documents: int = Field(0, description="Total number of documents uploaded.")
    documents: List[UploadedDocument] = Field([], description="List of uploaded documents.")

class UploadedCollection(BaseModel):
    """Model representing an individual uploaded document."""
    collection_name: str = Field("", description="Name of the collection.")
    num_entities: int = Field(0, description="Number of rows or entities in the collection.")

class CollectionListResponse(BaseModel):
    """Response model for uploading a document."""
    message: str = Field("", description="Message indicating the status of the request.")
    total_collections: int = Field(0, description="Total number of collections uploaded.")
    collections: List[UploadedCollection] = Field([], description="List of uploaded collections.")

class CollectionResponse(BaseModel):
    """Response model for creation or deletion of collections in Milvus."""

    message: str = Field(..., description="Status message of the process.")
    successful: List[str] = Field(default_factory=list, description="List of successfully created or deleted collections.")
    failed: List[str] = Field(default_factory=list, description="List of collections that failed to be created or deleted.")
    total_success: int = Field(0, description="Total number of collections successfully created or deleted.")
    total_failed: int = Field(0, description="Total number of collections that failed to be created or deleted.")


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    try:
        body = await request.json()
        logger.warning("Invalid incoming Request Body:", body)
    except Exception as e:
        print("Failed to read request body:", e)
    return JSONResponse(
        status_code=HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors(), exclude={"input"})},
    )

async def validate_files(files: List[UploadFile] = File(...)) -> List[UploadFile]:
    """Validate the files to be uploaded."""
    non_supported_files = []
    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ["." + supported_ext for supported_ext in EXTENSION_TO_DOCUMENT_TYPE.keys()]:
            non_supported_files.append(file.filename)
    if non_supported_files:
        raise HTTPException(status_code=400, detail=f"Invalid file types: {non_supported_files}")
    return files

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
async def health_check():
    """
    Perform a Health Check

    Returns 200 when service is up. This does not check the health of downstream services.
    """

    response_message = "Ingestion Service is up."
    return HealthResponse(message=response_message)


async def parse_json_data(
    data: str = Form(
        ...,
        description="JSON data in string format containing metadata about the documents which needs to be uploaded.",
        examples=[json.dumps({
            # "vdb_endpoint": "http://milvus:19530", # WAR to hide it from openapi schema
            "collection_name": "multimodal_data",
            "extraction_options": {
                "extract_text": True,
                "extract_tables": True,
                "extract_charts": True,
                "extract_images": False,
                "extract_method": "pdfium",
                "text_depth": "page"
            },
            "split_options": {
                "chunk_size": 1024,
                "chunk_overlap": 150
            }
        }
        )],
        media_type="application/json"
    )
) -> DocumentUploadRequest:
    try:
        json_data = json.loads(data)
        return DocumentUploadRequest(**json_data)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail="Invalid JSON format") from e
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post(
    "/documents",
    tags=["Ingestion APIs"],
    response_model=DocumentListResponse,
    responses={
        499: {
            "description": "Client Closed Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The client cancelled the request"
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        },
    }
)
async def upload_document(documents: List[UploadFile] = File(...),
    request: DocumentUploadRequest = Depends(parse_json_data)) -> DocumentListResponse:
    """Upload a document to the vector store."""

    if not len(documents):
        raise Exception("No files provided for uploading.")

    # Validate the files
    await validate_files(documents)

    # Store all provided file paths
    all_file_paths = []
    temp_dirs = []

    try:
        base_upload_folder = Path("/tmp-data/uploaded_files")
        base_upload_folder.mkdir(parents=True, exist_ok=True)

        for file in documents:
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

            # Create a unique directory for each file
            unique_dir = base_upload_folder #/ str(uuid4())
            unique_dir.mkdir(parents=True, exist_ok=True)
            temp_dirs.append(unique_dir)

            file_path = unique_dir / upload_file
            if not (hasattr(NV_INGEST_INGESTOR, "get_documents") and callable(NV_INGEST_INGESTOR.get_documents)):
                raise NotImplementedError("Example class has not implemented get_documents method.")

            response = NV_INGEST_INGESTOR.get_documents(request.collection_name, request.vdb_endpoint)
            if upload_file in [doc.get("document_name") for doc in response['documents']]:
                logger.error(f"Document {upload_file} already exists. Upload failed. Please call PATCH /documents endpoint to delete and replace this file.")
                raise Exception(f"Document {upload_file} already exists. Upload failed. Please call PATCH /documents endpoint to delete and replace this file.")

            all_file_paths.append(str(file_path))

            # Copy uploaded file to upload_dir directory and pass that file path to rag server
            with open(file_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            if not ENABLE_NV_INGEST:
                UNSTRUCTURED_RAG_CHAIN.ingest_docs(str(file_path), upload_file, request.collection_name, request.vdb_endpoint)

        if ENABLE_NV_INGEST:
            response_dict = await NV_INGEST_INGESTOR.ingest_docs(
                filepaths=all_file_paths,
                vdb_endpoint=request.vdb_endpoint, # WAR to hide it from openapi schema
                **request.model_dump()
            )
            return DocumentListResponse(**response_dict)

        return JSONResponse(content="Documents uploaded successfully!", status_code=200)

    except asyncio.CancelledError as e:
        logger.warning(f"Request cancelled while uploading document {e}")
        return JSONResponse(content={"message": "Request was cancelled by the client"}, status_code=499)
    except Exception as e:
        logger.error(f"Error from POST /documents endpoint. Ingestion of file failed with error: {e}")
        return JSONResponse(content={"message": f"Ingestion of files failed with error: {e}"}, status_code=500)
    finally:
        # Ensure all temporary directories are deleted in case of errors
        logger.info(f"Cleaning up files in {all_file_paths}")
        for file in all_file_paths:
            try:
                os.remove(file)
                logger.info(f"Deleted temporary file: {file}")
            except FileNotFoundError:
                logger.warning(f"File not found: {file}")
            except Exception as e:
                logger.error(f"Error deleting {file}: {e}")


@app.patch(
    "/documents",
    tags=["Ingestion APIs"],
    response_model=DocumentListResponse,
    responses={
        499: {
            "description": "Client Closed Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The client cancelled the request"
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        },
    }
)
async def delete_and_upload_document(documents: List[UploadFile] = File(...),
    request: DocumentUploadRequest = Depends(parse_json_data)) -> DocumentListResponse:

    """Upload a document to the vector store. If the document already exists, it will be replaced."""

    try:
        for file in documents:
            file_name = os.path.basename(file.filename)

            # Delete the existing document
            if not (hasattr(NV_INGEST_INGESTOR, "delete_documents") and callable(NV_INGEST_INGESTOR.delete_documents)):
                raise NotImplementedError("Example class has not implemented delete_documents method.")
            response = NV_INGEST_INGESTOR.delete_documents([file_name], document_ids=[], collection_name=request.collection_name, vdb_endpoint=request.vdb_endpoint)
            if response["total_documents"] == 0:
                logger.info("Unable to remove %s from collection. Either the document does not exist or there is an error while removing. Proceeding with ingestion.", file_name)
            else:
                logger.info("Successfully removed %s from collection %s.", file_name, request.collection_name)

        response = await upload_document(documents=documents, request=request)
        return response

    except asyncio.CancelledError as e:
        logger.error(f"Request cancelled while deleting and uploading document")
        return JSONResponse(content={"message": "Request was cancelled by the client"}, status_code=499)
    except Exception as e:
        logger.error("Error from PATCH /documents endpoint. Ingestion failed with error.")
        return JSONResponse(content={"message": f"Ingestion of files failed with error. {e}"}, status_code=500)


@app.get(
    "/documents",
    tags=["Ingestion APIs"],
    response_model=DocumentListResponse,
    responses={
        499: {
            "description": "Client Closed Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The client cancelled the request"
                    }
                }
            },
        },
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
async def get_documents(
    _: Request,
    collection_name: str = os.getenv("COLLECTION_NAME", ""),
    vdb_endpoint: str = Query(default=os.getenv("APP_VECTORSTORE_URL"), include_in_schema=False)
) -> DocumentListResponse:
    """Get list of document ingested in vectorstore."""
    try:
        if hasattr(NV_INGEST_INGESTOR, "get_documents") and callable(NV_INGEST_INGESTOR.get_documents):
            documents = NV_INGEST_INGESTOR.get_documents(collection_name, vdb_endpoint)
            return DocumentListResponse(**documents)
        raise NotImplementedError("Example class has not implemented the get_documents method.")

    except asyncio.CancelledError as e:
        logger.warning(f"Request cancelled while fetching documents. {str(e)}")
        return JSONResponse(content={"message": "Request was cancelled by the client."}, status_code=499)
    except Exception as e:
        logger.error("Error from GET /documents endpoint. Error details: %s", e)
        return JSONResponse(content={"message": f"Error occurred while fetching documents: {e}"}, status_code=500)


@app.delete(
    "/documents",
    tags=["Ingestion APIs"],
    response_model=DocumentListResponse,
    responses={
        499: {
            "description": "Client Closed Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The client cancelled the request"
                    }
                }
            },
        },
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
async def delete_documents(_: Request, document_names: List[str] = [], collection_name: str = os.getenv("COLLECTION_NAME"), vdb_endpoint: str = Query(default=os.getenv("APP_VECTORSTORE_URL"), include_in_schema=False)) -> DocumentListResponse:
    """Delete a document from vectorstore."""
    try:
        if hasattr(NV_INGEST_INGESTOR, "delete_documents") and callable(NV_INGEST_INGESTOR.delete_documents):
            response = NV_INGEST_INGESTOR.delete_documents(document_names=document_names, document_ids=[], collection_name=collection_name, vdb_endpoint=vdb_endpoint)
            return DocumentListResponse(**response)

        raise NotImplementedError("Example class has not implemented the delete_document method.")

    except asyncio.CancelledError as e:
        logger.warning(f"Request cancelled while deleting document:, {document_names}, {str(e)}")
        return JSONResponse(content={"message": "Request was cancelled by the client."}, status_code=499)
    except Exception as e:
        logger.error("Error from DELETE /documents endpoint. Error details: %s", e)
        return JSONResponse(content={"message": f"Error deleting document {document_names}: {e}"}, status_code=500)


@app.get(
    "/collections",
    tags=["Vector DB APIs"],
    response_model=CollectionListResponse,
    responses={
        499: {
            "description": "Client Closed Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The client cancelled the request"
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        },
    },
)
async def get_collections(vdb_endpoint: str = Query(default=os.getenv("APP_VECTORSTORE_URL"), include_in_schema=False)) -> CollectionListResponse:
    """
    Endpoint to get a list of collection names from the Milvus server.
    Returns a list of collection names.
    """
    try:
        if hasattr(NV_INGEST_INGESTOR, "get_collections") and callable(NV_INGEST_INGESTOR.get_collections):
            response = NV_INGEST_INGESTOR.get_collections(vdb_endpoint)
            return CollectionListResponse(**response)
        raise NotImplementedError("Example class has not implemented the get_collections method.")

    except asyncio.CancelledError as e:
        logger.warning(f"Request cancelled while fetching collections. {str(e)}")
        return JSONResponse(content={"message": "Request was cancelled by the client."}, status_code=499)
    except Exception as e:
        logger.error("Error from GET /collections endpoint. Error details: %s", e)
        return JSONResponse(content={"message": f"Error occurred while fetching collections. Error: {e}"}, status_code=500)


@app.post(
    "/collections",
    tags=["Vector DB APIs"],
    response_model=CollectionResponse,
    responses={
        499: {
            "description": "Client Closed Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The client cancelled the request"
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        },
    },
)
async def create_collections(
    vdb_endpoint: str = Query(default=os.getenv("APP_VECTORSTORE_URL"), include_in_schema=False),
    collection_names: List[str] = [os.getenv("COLLECTION_NAME")],
    collection_type: str = "text",
    embedding_dimension: int = 2048
) -> CollectionResponse:
    """
    Endpoint to create a collection from the Milvus server.
    Returns status message.
    """
    try:
        if hasattr(NV_INGEST_INGESTOR, "create_collections") and callable(NV_INGEST_INGESTOR.create_collections):
            response = NV_INGEST_INGESTOR.create_collections(collection_names, vdb_endpoint, embedding_dimension, collection_type)
            return CollectionResponse(**response)
        raise NotImplementedError("Example class has not implemented the create_collections method.")

    except asyncio.CancelledError as e:
        logger.warning(f"Request cancelled while fetching collections. {str(e)}")
        return JSONResponse(content={"message": "Request was cancelled by the client."}, status_code=499)
    except Exception as e:
        logger.error("Error from POST /collections endpoint. Error details: %s", e)
        return JSONResponse(content={"message": f"Error occurred while creating collections. Error: {e}"}, status_code=500)


@app.delete(
    "/collections",
    tags=["Vector DB APIs"],
    response_model=CollectionResponse,
    responses={
        499: {
            "description": "Client Closed Request",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "The client cancelled the request"
                    }
                }
            },
        },
        500: {
            "description": "Internal Server Error",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Internal server error occurred"
                    }
                }
            },
        },
    },
)
async def delete_collections(vdb_endpoint: str = Query(default=os.getenv("APP_VECTORSTORE_URL"), include_in_schema=False), collection_names: List[str] = [os.getenv("COLLECTION_NAME")]) -> CollectionResponse:
    """
    Endpoint to delete a collection from the Milvus server.
    Returns status message.
    """
    try:
        if hasattr(NV_INGEST_INGESTOR, "delete_collections") and callable(NV_INGEST_INGESTOR.delete_collections):
            response = NV_INGEST_INGESTOR.delete_collections(collection_names, vdb_endpoint)
            return CollectionResponse(**response)
        raise NotImplementedError("Example class has not implemented the delete_collections method.")

    except asyncio.CancelledError as e:
        logger.warning(f"Request cancelled while fetching collections. {str(e)}")
        return JSONResponse(content={"message": "Request was cancelled by the client."}, status_code=499)
    except Exception as e:
        logger.error("Error from DELETE /collections endpoint. Error details: %s", e)
        return JSONResponse(content={"message": f"Error occurred while deleting collections. Error: {e}"}, status_code=500)
