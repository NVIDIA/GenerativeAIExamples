# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import openai
from openai import OpenAI
import os
from pydantic import BaseModel

from nvretail.cart import Cart
from nvretail.catalog import Catalog, Products
from nvretail.generate import FunctionMetadata, Messages, ProductAdvisor


# Setup Product Advisor
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

client = OpenAI()
cart = Cart()
catalog = Catalog("/app/data/gear-store.csv")
PRODUCT_ADVISOR = ProductAdvisor(client=client, cart=cart, catalog=catalog)

##########################################
# Setup logging and app
##########################################
LEVEL = "INFO"
logging.basicConfig(
    format=(
        '{"level": "%(levelname)s", "file_path": "%(pathname)s", "line_number": %(lineno)d, '
        '"time": "%(asctime)s%(msecs)03d", "message": "%(message)s"}'
    ),
    level=logging.getLevelName(LEVEL),
    datefmt="%H:%M:%S.",
    force=True,
)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/reset")
async def reset() -> dict:
    """Reset the shopping cart."""
    PRODUCT_ADVISOR.cart.reset()
    logging.info("Reset the shopping cart.")
    return {"status": "Reset the shopping cart."}


@app.get("/cart")
async def get_cart() -> dict:
    """View the items in the shopping cart."""
    return PRODUCT_ADVISOR.cart.items


class ResponseData(BaseModel):
    """Response Data"""

    messages: Messages
    products: Products
    fn_metadata: FunctionMetadata


@app.post("/chat")
async def chat_response(messages: Messages) -> ResponseData:
    """Chat endpoint."""
    messages, fn_metadata, products = PRODUCT_ADVISOR.chat(messages)

    response_data = ResponseData(
        messages=messages, products=products, fn_metadata=fn_metadata
    )

    return response_data
