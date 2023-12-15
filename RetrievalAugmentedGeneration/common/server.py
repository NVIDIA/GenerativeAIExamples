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

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field
from pymilvus.exceptions import MilvusException, MilvusUnavailableException

from RetrievalAugmentedGeneration.common import utils
from RetrievalAugmentedGeneration.examples.developer_rag import chains

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# create the FastAPI server
app = FastAPI()
# prestage the embedding model
_ = utils.get_embedding_model()
# set the global service context for Llama Index
utils.set_service_context()


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


@app.post("/uploadDocument")
async def upload_document(file: UploadFile = File(...)) -> JSONResponse:
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

        chains.ingest_docs(file_path, upload_file)

        return JSONResponse(
            content={"message": "File uploaded successfully"}, status_code=200
        )

    except Exception as e:
        logger.error("Error from /uploadDocument endpoint. Ingestion of file: " + file.filename + " failed with error: " + str(e))
        return JSONResponse(
            content={"message": f"Ingestion of file: " + file.filename + " failed with error: " + str(e)}, status_code=500
        )


@app.post("/generate")
async def generate_answer(prompt: Prompt) -> StreamingResponse:
    """Generate and stream the response to the provided prompt."""

    try:
        if prompt.use_knowledge_base:
            logger.info("Knowledge base is enabled. Using rag chain for response generation.")
            generator = chains.rag_chain(prompt.question, prompt.num_tokens)
            return StreamingResponse(generator, media_type="text/event-stream")

        generator = chains.llm_chain(prompt.context, prompt.question, prompt.num_tokens)
        return StreamingResponse(generator, media_type="text/event-stream")

    except (MilvusException, MilvusUnavailableException) as e:
        logger.error(f"Error from Milvus database in /generate endpoint. Please ensure you have ingested some documents. Error details: {e}")
        return StreamingResponse(iter(["Error from milvus server. Please ensure you have ingested some documents. Please check chain-server logs for more details."]), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error from /generate endpoint. Error details: {e}")
        return StreamingResponse(iter(["Error from chain server. Please check chain-server logs for more details."]), media_type="text/event-stream")


@app.post("/documentSearch")
def document_search(data: DocumentSearch) -> List[Dict[str, Any]]:
    """Search for the most relevant documents for the given search parameters."""

    try:
        retriever = utils.get_doc_retriever(num_nodes=data.num_docs)
        nodes = retriever.retrieve(data.content)
        output = []
        for node in nodes:
            file_name = nodes[0].metadata["filename"]
            decoded_filename = base64.b64decode(file_name.encode("utf-8")).decode("utf-8")
            entry = {"score": node.score, "source": decoded_filename, "content": node.text}
            output.append(entry)

        return output

    except Exception as e:
        logger.error(f"Error from /documentSearch endpoint. Error details: {e}")
        return []