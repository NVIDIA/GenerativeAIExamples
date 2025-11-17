# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import json
import logging
import os
from typing import Optional

from pydantic import Field, BaseModel

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig
from nat.builder.framework_enum import LLMFrameworkEnum

logger = logging.getLogger(__name__)

class GenerateSqlQueryAndRetrieveToolConfig(FunctionBaseConfig, name="generate_sql_query_and_retrieve_tool"):
    """
    NeMo Agent Toolkit function to generate SQL queries and retrieve data.
    
    Supports multiple database types through flexible connection configuration.
    """
    # Runtime configuration parameters
    llm_name: str = Field(description="The name of the LLM to use for the function.")
    embedding_name: str = Field(description="The name of the embedding to use for the function.")
    
    # Vector store configuration
    vector_store_type: str = Field(
        default="chromadb",
        description="Type of vector store: 'chromadb' or 'elasticsearch'"
    )
    vector_store_path: Optional[str] = Field(
        default=None,
        description="Path to ChromaDB vector store (required if vector_store_type='chromadb')"
    )
    elasticsearch_url: Optional[str] = Field(
        default=None,
        description="Elasticsearch URL (required if vector_store_type='elasticsearch', e.g., 'http://localhost:9200')"
    )
    elasticsearch_index_name: str = Field(
        default="vanna_vectors",
        description="Elasticsearch index name (used if vector_store_type='elasticsearch')"
    )
    elasticsearch_username: Optional[str] = Field(
        default=None,
        description="Elasticsearch username for basic auth (optional)"
    )
    elasticsearch_password: Optional[str] = Field(
        default=None,
        description="Elasticsearch password for basic auth (optional)"
    )
    elasticsearch_api_key: Optional[str] = Field(
        default=None,
        description="Elasticsearch API key for authentication (optional)"
    )
    
    # Database configuration
    db_connection_string_or_path: str = Field(
        description=(
            "Database connection (path for SQLite, connection string for others). Format depends on db_type:\n"
            "- sqlite: Path to .db file (e.g., './database.db')\n"
            "- postgres: Connection string (e.g., 'postgresql://user:pass@host:port/db')\n"
            "- sql: SQLAlchemy connection string (e.g., 'mysql+pymysql://user:pass@host/db')"
        )
    )
    db_type: str = Field(
        default="sqlite",
        description="Type of database: 'sqlite', 'postgres', or 'sql' (generic SQL via SQLAlchemy)"
    )
    
    # Output configuration
    output_folder: str = Field(description="The path to the output folder to use for the function.")
    vanna_training_data_path: str = Field(description="The path to the YAML file containing Vanna training data.")

@register_function(config_type=GenerateSqlQueryAndRetrieveToolConfig, framework_wrappers=[LLMFrameworkEnum.LANGCHAIN])
async def generate_sql_query_and_retrieve_tool(
    config: GenerateSqlQueryAndRetrieveToolConfig, builder: Builder
):
    """
    Generate a SQL query for a given question and retrieve the data from the database.
    """
    class GenerateSqlQueryInputSchema(BaseModel):
        input_question_in_english: str = Field(description="User's question in plain English to generate SQL query for")

    # Create Vanna instance
    vanna_llm_config = builder.get_llm_config(config.llm_name)
    vanna_embedder_config = builder.get_embedder_config(config.embedding_name)
    
    from langchain_core.prompts.chat import ChatPromptTemplate
    
    llm = await builder.get_llm(config.llm_name, wrapper_type=LLMFrameworkEnum.LANGCHAIN)

    system_prompt = """
    You are an intelligent SQL query assistant that analyzes database query results and provides appropriate responses.

    Your responsibilities:
    1. Analyze the SQL query results and determine the best response format.
    2. For data extraction queries (multiple rows/complex data): recommend saving to JSON file and provide summary.
    3. For simple queries (single values, counts, yes/no, simple lookups): provide DIRECT answers without file storage.
    4. Always be helpful and provide context about the results.

    Guidelines:

    - If results contain multiple rows or complex data AND the query is for data analysis/processing: recommend saving to file
    - If results are simple (single value, count, or small lookup): provide only the direct answer even if a file was created for the results.
    - Always mention the SQL query that was executed.
    - Important: Do not use template variables or placeholders in your response. Provide actual values and descriptions.
    
    Be conversational and helpful. Explain what was found.
    """
    # CRITICAL INSTRUCTION: If the question asks for unit numbers or IDs (e.g., "what are their unit numbers"):
    # - Provide the COMPLETE list of ALL unit numbers from the data
    # - Never say "not shown in sample" or "additional values" 
    # - Extract all unit_number values from the complete dataset, not just the sample
    # - If you see unit numbers 40, 82, 174, 184 in the data, list ALL of them explicitly
    # """
    
    user_prompt = """
    Original Question: {original_question}
    
    SQL Query Executed: {sql_query}
    
    Query Results:
    - Number of rows: {num_rows}
    - Number of columns: {num_columns}
    - Columns: {columns}
    - Sample data (first few rows): {sample_data}
    
    Output directory: {output_dir}
    """
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", user_prompt)])
    output_message = prompt | llm
    
    from .vanna_manager import VannaManager
    
    # Create a VannaManager instance with full configuration
    # This will trigger immediate Vanna instance creation and training during initialization
    vanna_manager = VannaManager.create_with_config(
        vanna_llm_config=vanna_llm_config,
        vanna_embedder_config=vanna_embedder_config,
        vector_store_type=config.vector_store_type,
        vector_store_path=config.vector_store_path,
        elasticsearch_url=config.elasticsearch_url,
        elasticsearch_index_name=config.elasticsearch_index_name,
        elasticsearch_username=config.elasticsearch_username,
        elasticsearch_password=config.elasticsearch_password,
        elasticsearch_api_key=config.elasticsearch_api_key,
        db_connection_string_or_path=config.db_connection_string_or_path,
        db_type=config.db_type,
        training_data_path=config.vanna_training_data_path
    )
    
    def get_vanna_instance():
        """
        Get the pre-initialized Vanna instance from VannaManager.
        Training has already been completed during VannaManager initialization.
        """
        return vanna_manager.get_instance()

    async def _response_fn(input_question_in_english: str) -> str:
        # Process the input_question_in_english and generate output using VannaManager
        logger.info(f"RESPONSE: Starting question processing for: {input_question_in_english}")
        
        sql = None
        try:
            # CRITICAL: Ensure VannaManager instance is created before using it
            # This creates the instance if it doesn't exist (lazy initialization)
            vn_instance = get_vanna_instance()
            
            # Use VannaManager for safe SQL generation
            sql = vanna_manager.generate_sql_safe(question=input_question_in_english)
            logger.info(f"Generated SQL: {sql}")
            
        except Exception as e:
            logger.error(f"RESPONSE: Exception during generate_sql_safe: {e}")
            return f"Error generating SQL: {e}"

        # vn_instance is already available from above
        
        if not vn_instance.run_sql_is_set:
            return f"Database is not connected via Vanna: {sql}"

        try:
            df = vn_instance.run_sql(sql)
            if df is None:
                return f"Vanna run_sql returned None: {sql}"
            if df.empty:
                return f"No data found for the generated SQL: {sql}"
            
            num_rows = df.shape[0]
            num_columns = df.shape[1]
            columns = df.columns.tolist()
            
            # Get sample data (first 3 rows for preview)
            sample_data = df.head(3).to_dict('records')
            
            # Use LLM to generate intelligent response
            response = await output_message.ainvoke({
                "original_question": input_question_in_english,
                "sql_query": sql,
                "num_rows": num_rows,
                "num_columns": num_columns,
                "columns": ", ".join(columns),
                "sample_data": json.dumps(sample_data, indent=2),
                "output_dir": config.output_folder
            })
            
            # Check if LLM response suggests saving data (look for keywords or patterns)
            llm_response = response.content if hasattr(response, 'content') else str(response)
            # Clean up the LLM response and add file save confirmation
            # Remove any object references that might have slipped through
            import re
            llm_response = re.sub(r',\[object Object\],?', '', llm_response)

            # if "save" in llm_response.lower():
            # Clean the question for filename
            clean_question = re.sub(r'[^\w\s-]', '', input_question_in_english.lower())
            clean_question = re.sub(r'\s+', '_', clean_question.strip())[:30]
            suggested_filename = f"{clean_question}_results.json"

            sql_output_path = os.path.join(config.output_folder, suggested_filename)

            # Save the data to JSON file
            os.makedirs(config.output_folder, exist_ok=True)
            json_result = df.to_json(orient="records")
            with open(sql_output_path, 'w') as f:
                json.dump(json.loads(json_result), f, indent=4)

            logger.info(f"Data saved to {sql_output_path}")

            llm_response += f"\n\nData has been saved to file: {suggested_filename}"

            return llm_response

            # return llm_response
            
        except Exception as e:
            return f"Error running SQL query '{sql}': {e}"

    description = """
    Use this tool to automatically generate SQL queries for the user's question, retrieve the data from the SQL database and provide a summary of the data or save the data in a JSON file.
    Do not provide SQL query as input, only a question in plain english.
    
    Input: 
    - input_question_in_english: User's question or a question that you think is relevant to the user's question in plain english
    
    Output: Status of the generated SQL query's execution along with the output path.
    """
    yield FunctionInfo.from_fn(_response_fn, 
                               input_schema=GenerateSqlQueryInputSchema,
                               description=description)
    try:
        pass
    except GeneratorExit:
        logger.info("Generate SQL query and retrieve function exited early!")
    finally:
        logger.info("Cleaning up generate_sql_query_and_retrieve_tool workflow.")
