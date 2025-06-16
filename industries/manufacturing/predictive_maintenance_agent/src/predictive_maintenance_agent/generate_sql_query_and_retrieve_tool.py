import json
import logging
import os

from aiq.builder.framework_enum import LLMFrameworkEnum
from pydantic import Field, BaseModel

from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

class GenerateSqlQueryAndRetrieveToolConfig(FunctionBaseConfig, name="generate_sql_query_and_retrieve_tool"):
    """
    AIQ Toolkit function to generate SQL queries and retrieve data.
    """
    # Runtime configuration parameters
    llm_name: str = Field(description="The name of the LLM to use for the function.")
    embedding_name: str = Field(description="The name of the embedding to use for the function.")
    vector_store_path: str = Field(description="The path to the vector store to use for the function.")
    db_path: str = Field(description="The path to the SQL database to use for the function.")
    output_folder: str = Field(description="The path to the output folder to use for the function.")

@register_function(config_type=GenerateSqlQueryAndRetrieveToolConfig)
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
    1. Analyze the SQL query results and determine the best response format
    2. For data extraction queries (multiple rows/complex data): recommend saving to JSON file and provide summary
    3. For simple queries (single values, counts, yes/no): provide direct answers without file storage
    4. Always be helpful and provide context about the results
    5. Generate a descriptive filename for data that should be saved

    Guidelines:
    - If results contain multiple rows or complex data (>5 rows or >3 columns): recommend saving to file
    - If results are simple (single value, count, or small lookup): provide direct answer
    - Always mention the SQL query that was executed
    - Be clear about whether data was saved to a file or not
    - For files to be saved, suggest a descriptive filename based on the query content (e.g., "sensor_data_unit_5.json", "engine_performance_analysis.json")
    """
    
    user_prompt = """
    Original Question: {original_question}
    
    SQL Query Executed: {sql_query}
    
    Query Results:
    - Number of rows: {num_rows}
    - Number of columns: {num_columns}
    - Columns: {columns}
    - Sample data (first few rows): {sample_data}
    
    Output directory: {output_dir}
    
    Please provide an appropriate response that either:
    1. Saves the data to JSON file and provides a summary (for complex/large datasets) - suggest a descriptive filename
    2. Directly answers the question with the results (for simple queries)
    
    Be conversational and helpful. Explain what was found and next steps if applicable.
    If saving data, suggest a meaningful filename in the format: "descriptive_name.json"
    
    Important: Do not use template variables or placeholders in your response. Provide actual values and descriptions.
    """
    
    prompt = ChatPromptTemplate.from_messages([("system", system_prompt), ("user", user_prompt)])
    output_message = prompt | llm
    
    from .vanna_util import NIMVanna, initVanna, CustomEmbeddingFunction
    def get_vanna_instance(vanna_llm_config, vanna_embedder_config, vector_store_path, db_path):
        """
        Get a Vanna instance for the given configuration.
        Initializes the Vanna instance if it is not already initialized.

        Args:
            vanna_llm_config (dict): The configuration for the Vanna LLM.
            vanna_embedder_config (dict): The configuration for the Vanna embedder.
            vector_store_path (str): The path to the vector store.
            db_path (str): The path to the SQL database.

        Returns:
            NIMVanna: A Vanna instance.
        """  
        vn_instance = NIMVanna(
            VectorConfig={
                "client": "persistent",
                "path": vector_store_path,
                "embedding_function": CustomEmbeddingFunction(
                    api_key=os.getenv("NVIDIA_API_KEY"), 
                    model=vanna_embedder_config.model_name)
            },
            LLMConfig={
                "api_key": os.getenv("NVIDIA_API_KEY"),
                "model": vanna_llm_config.model_name
            }
        )

        # Connect to SQLite database
        vn_instance.connect_to_sqlite(db_path)

        # Check if vector store directory is empty and initialize if needed
        list_of_folders = [d for d in os.listdir(vector_store_path) 
                        if os.path.isdir(os.path.join(vector_store_path, d))]
        if len(list_of_folders) == 0:
            logger.info("Initializing Vanna vector store...")
            try:
                initVanna(vn_instance)
                logger.info("Vanna vector store initialization complete.")
            except Exception as e:
                logger.error(f"Error initializing Vanna vector store: {e}")
                raise
        else:
            logger.info("Vanna vector store already initialized.")
        return vn_instance
        
    vn_instance = get_vanna_instance(vanna_llm_config, vanna_embedder_config, config.vector_store_path, config.db_path)

    async def _response_fn(input_question_in_english: str) -> str:
        # Process the input_question_in_english and generate output
        if vn_instance is None:
            return "Error: Vanna instance not available"
        
        sql = None
        try:
            sql = vn_instance.generate_sql(question=input_question_in_english)
            logger.info(f"Generated SQL: {sql}")
        except Exception as e:
            return f"Error generating SQL: {e}"

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
            
            # Save data if it's complex (multiple rows or columns) or LLM suggests saving
            should_save_data = (
                num_rows > 5 or 
                num_columns > 3 or 
                "save" in llm_response.lower() or 
                "saved" in llm_response.lower() or
                "file" in llm_response.lower()
            )
            
            if should_save_data:
                # Extract suggested filename from LLM response or use default
                import re
                filename_match = re.search(r'"([^"]+\.json)"', llm_response)
                if filename_match:
                    suggested_filename = filename_match.group(1)
                else:
                    # Generate a descriptive filename based on the question
                    import hashlib
                    # Clean the question for filename
                    clean_question = re.sub(r'[^\w\s-]', '', input_question_in_english.lower())
                    clean_question = re.sub(r'\s+', '_', clean_question.strip())[:30]
                    if clean_question:
                        suggested_filename = f"{clean_question}_results.json"
                    else:
                        query_hash = hashlib.md5(input_question_in_english.encode()).hexdigest()[:8]
                        suggested_filename = f"sql_results_{query_hash}.json"
                
                sql_output_path = os.path.join(config.output_folder, suggested_filename)
                
                # Save the data to JSON file
                os.makedirs(config.output_folder, exist_ok=True)
                json_result = df.to_json(orient="records")
                with open(sql_output_path, 'w') as f:
                    json.dump(json.loads(json_result), f, indent=4)
                logger.info(f"Data saved to {sql_output_path}")
                
                # Clean up the LLM response and add file save confirmation
                # Remove any object references that might have slipped through
                cleaned_response = re.sub(r',\[object Object\],?', '', llm_response)
                cleaned_response = re.sub(r'\[object Object\]', str(num_rows), cleaned_response)
                
                # If LLM didn't mention the actual saved path, append save confirmation
                if sql_output_path not in cleaned_response:
                    cleaned_response += f"\n\n📁 Data has been saved to: {sql_output_path}"
                    cleaned_response += f"\n📊 File contains {num_rows} rows with columns: {', '.join(columns)}"
                
                return cleaned_response
            
            return llm_response
            
        except Exception as e:
            return f"Error running SQL query '{sql}': {e}"

    description = """
    Use this tool to automatically generate SQL queries for the user's question, retrieve the data from the SQL database and store the data in a JSON file or provide a summary of the data.
    Do not provide SQL query as input, only a question in plain english.
    
    Input: 
    - input_question_in_english: User's question or a question that you think is relevant to the user's question in plain english
    
    Output: Status of the generated SQL query's execution along with the output path. The tool will automatically generate descriptive filenames for saved data.
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
