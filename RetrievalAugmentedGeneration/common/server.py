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
import base64
import os
import shutil
import logging
from pathlib import Path
from typing import Any, Dict, List
import importlib
from inspect import getmembers, isclass

from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from pymilvus.exceptions import MilvusException, MilvusUnavailableException
from RetrievalAugmentedGeneration.common import utils, tracing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# create the FastAPI server
app = FastAPI()

EXAMPLE_DIR = "RetrievalAugmentedGeneration/example"

class Prompt(BaseModel):
    """Definition of the Prompt API data type."""

    question: str = Field(description="The input query/prompt to the pipeline.")
    context: str = Field(description="Additional context for the question (optional)")
    use_knowledge_base: bool = Field(description="Whether to use a knowledge base", default=True)
    num_tokens: int = Field(description="The maximum number of tokens in the response.", default=50)


class DocumentSearch(BaseModel):
    """Definition of the DocumentSearch API data type."""

    content: str = Field(description="The content or keywords to search for within documents.")
    num_docs: int = Field(description="The maximum number of documents to return in the response.", default=4)


@app.on_event("startup")
def import_example() -> None:
    """
    Import the example class from the specified example file.
    The example directory is expected to have a python file where the example class is defined.
    """

    for root, dirs, files in os.walk(EXAMPLE_DIR):
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
                        example = cls()
                        app.example = cls
                        return
                except:
                    raise ValueError(f"Class {name} is not implemented and could not be instantiated.")

    raise NotImplementedError(f"Could not find a valid example class in {EXAMPLE_DIR}")


@app.post("/uploadDocument")
@tracing.instrumentation_wrapper
async def upload_document(request: Request, file: UploadFile = File(...)) -> JSONResponse:
    """Upload a document to the vector store."""
    if not file.filename:
        return JSONResponse(content={"message": "No files provided"}, status_code=200)

    try:
        upload_folder = "uploaded_files"
        upload_file = os.path.basename(file.filename)
        if not upload_file:
            raise RuntimeError("Error parsing uploaded filename.")
        file_path = os.path.join(upload_folder, upload_file)
        uploads_dir = Path(upload_folder)
        uploads_dir.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        app.example().ingest_docs(file_path, upload_file)

        return JSONResponse(
            content={"message": "File uploaded successfully"}, status_code=200
        )

    except Exception as e:
        logger.error("Error from /uploadDocument endpoint. Ingestion of file: " + file.filename + " failed with error: " + str(e))
        return JSONResponse(
            content={"message": str(e)}, status_code=500
        )


@app.post("/generate")
@tracing.instrumentation_wrapper
async def generate_answer(request: Request, prompt: Prompt) -> StreamingResponse:
    """Generate and stream the response to the provided prompt."""

    try:
        example = app.example()
        if prompt.use_knowledge_base:
            logger.info("Knowledge base is enabled. Using rag chain for response generation.")
            generator = example.rag_chain(prompt.question, prompt.num_tokens)
            return StreamingResponse(generator, media_type="text/event-stream")

        generator = example.llm_chain(prompt.context, prompt.question, prompt.num_tokens)
        return StreamingResponse(generator, media_type="text/event-stream")

    except (MilvusException, MilvusUnavailableException) as e:
        logger.error(f"Error from Milvus database in /generate endpoint. Please ensure you have ingested some documents. Error details: {e}")
        return StreamingResponse(iter(["Error from milvus server. Please ensure you have ingested some documents. Please check chain-server logs for more details."]), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error from /generate endpoint. Error details: {e}")
        return StreamingResponse(iter(["Error from chain server. Please check chain-server logs for more details."]), media_type="text/event-stream")


@app.post("/documentSearch")
@tracing.instrumentation_wrapper
async def document_search(request: Request,data: DocumentSearch) -> List[Dict[str, Any]]:
    """Search for the most relevant documents for the given search parameters."""

    try:
        example = app.example()
        if hasattr(example, "document_search") and callable(example.document_search):
            return example.document_search(data.content, data.num_docs)

        raise NotImplementedError("Example class has not implemented the document_search method.")

    except Exception as e:
        logger.error(f"Error from /documentSearch endpoint. Error details: {e}")
        return []