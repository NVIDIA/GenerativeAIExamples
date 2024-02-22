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
from langchain.utils.math import cosine_similarity
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
import logging
from numpy import ndarray
import numpy as np
from openai_function_calling import Function, Parameter
import pandas as pd
from pandas import DataFrame
from pydantic import BaseModel
import random


Embeddings = list[list[float]]


class Product(BaseModel):
    """Product"""

    name: str
    description: str
    url: str
    price: float
    image: str
    ratings: list[int]


Products = list[Product]


class SubCategory(BaseModel):
    """Subcategory"""

    name: str
    description: str
    products: Products


class Category(BaseModel):
    """Category"""

    name: str
    description: str
    subcategories: list[SubCategory]


class Department(BaseModel):
    """Department"""

    name: str
    description: str
    categories: list[Category]


class Catalog:
    """Catalog"""

    def __init__(self, filename: str) -> None:
        self.df: DataFrame = self.load_data(filename)
        self.products: Products = self.create_products(self.df)
        self.products_prompts: list[str] = [
            self.product_to_prompt(p) for p in self.products
        ]
        self.embeddings: Embeddings = NVIDIAEmbeddings(
            model="nvolveqa_40k", model_type="passage"
        ).embed_documents(self.products_prompts)

    def load_data(self, filename: str) -> DataFrame:
        """Load data"""
        # load data
        df = pd.read_csv(filename)
        df.columns = [i.lower() for i in df.columns]

        # process data
        df = df.astype({"price": np.float32})
        logging.info("Data loaded and has shape %s", df.shape)
        return df

    def create_products(self, df: DataFrame) -> Products:
        """create products"""
        products = []
        for _, row in df.iterrows():
            product = Product(
                name=row["name"],
                description=row["description"],
                url=row["url"],
                price=row["price"],
                image=row["image"],
                ratings=[random.randint(4, 5) for _ in range(random.randint(10, 50))],
            )
            products.append(product)
        return products

    def product_to_prompt(self, p: Product) -> str:
        """Converts a product to context"""
        prompt_template = """Name: {name}
        Description: {description}
        URL: {url}
        Price: {price}
        Rating: {rating}"""
        prompt = prompt_template.format(
            name=p.name,
            description=p.description,
            url=p.url,
            price=p.price,
            rating=round(sum(p.ratings) / len(p.ratings), 2),
        )
        return prompt

    def products_to_context(self, products: Products) -> str:
        """Converts a list of products to context"""
        prompts = [self.product_to_prompt(p) for p in products]
        context = "\n".join(prompts)
        return context

    def search(self, query: str) -> Products:
        """
        This function can be used for searching and retrieval.
        But it can be made as generic and wide as possible/needed.
        """
        query = query.lower().strip()
        logging.info("query has been identified as: %s", query)

        query_embedding = NVIDIAEmbeddings(
            model="nvolveqa_40k", model_type="query"
        ).embed_query(query)
        similarity_scores: ndarray = cosine_similarity(
            [query_embedding], self.embeddings
        )[0]
        top_k = 2
        indices = list(np.argpartition(similarity_scores, -top_k)[-top_k:])
        products: Products = [self.products[index] for index in indices]
        return products


search_function = Function(
    name="search",
    description="Search for products",
    parameters=[
        Parameter(
            name="query",
            type="string",
            description="Query string to search for items",
        ),
    ],
    required_parameters=["query"],
)
