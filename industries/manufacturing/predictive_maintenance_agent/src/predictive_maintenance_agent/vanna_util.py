from vanna.chromadb import ChromaDB_VectorStore
from vanna.base import VannaBase
from langchain_nvidia import ChatNVIDIA
from tqdm import tqdm

class NIMCustomLLM(VannaBase):
    def __init__(self, config=None):
        VannaBase.__init__(self, config=config)

        if not config:
            raise ValueError("config must be passed")

        # default parameters - can be overrided using config
        self.temperature = 0.7
        
        if "temperature" in config:
            self.temperature = config["temperature"]
        
        # If only config is passed
        if "api_key" not in config:
            raise ValueError("config must contain a NIM api_key")

        if "model" not in config:
            raise ValueError("config must contain a NIM model")

        api_key = config["api_key"]
        model = config["model"]
        
        # Initialize ChatNVIDIA client
        self.client = ChatNVIDIA(
            api_key=api_key,
            model=model,
            temperature=self.temperature,
        )
        self.model = model

    def system_message(self, message: str) -> any:
        return {"role": "system", "content": message+"\n DO NOT PRODUCE MARKDOWN, ONLY RESPOND IN PLAIN TEXT"}

    def user_message(self, message: str) -> any:
        return {"role": "user", "content": message}

    def assistant_message(self, message: str) -> any:
        return {"role": "assistant", "content": message}

    def submit_prompt(self, prompt, **kwargs) -> str:
        if prompt is None:
            raise Exception("Prompt is None")

        if len(prompt) == 0:
            raise Exception("Prompt is empty")

        # Count the number of tokens in the message log
        # Use 4 as an approximation for the number of characters per token
        num_tokens = 0
        for message in prompt:
            num_tokens += len(message["content"]) / 4
        print(f"Using model {self.model} for {num_tokens} tokens (approx)")
        
        response = self.client.invoke(prompt)
        return response.content
    
class NIMVanna(ChromaDB_VectorStore, NIMCustomLLM):
    def __init__(self, VectorConfig = None, LLMConfig = None):
        ChromaDB_VectorStore.__init__(self, config=VectorConfig)
        NIMCustomLLM.__init__(self, config=LLMConfig)
    
class CustomEmbeddingFunction:
    """
    A class that can be used as a replacement for chroma's DefaultEmbeddingFunction.
    It takes in input (text or list of texts) and returns embeddings using NVIDIA's API.
    """

    def __init__(self, api_key, model="nvidia/nv-embedqa-e5-v5"):
        """
        Initialize the embedding function with the API key and model name.

        Parameters:
        - api_key (str): The API key for authentication.
        - model (str): The model name to use for embeddings (default is "nvidia/nv-embedqa-e5-v5").
        """
        from langchain_nvidia import NVIDIAEmbeddings
        
        self.embeddings = NVIDIAEmbeddings(
            api_key=api_key,
            model_name=model,
            input_type="query",
            truncate="NONE"
        )

    def __call__(self, input):
        """
        Call method to make the object callable, as required by chroma's EmbeddingFunction interface.

        Parameters:
        - input (str or list): The input data for which embeddings need to be generated.

        Returns:
        - embedding (list): The embedding vector(s) for the input data.
        """
        # Ensure input is a list, as required by the API
        input_data = [input] if isinstance(input, str) else input
        
        # Generate embeddings
        embeddings = []
        for text in input_data:
            embedding = self.embeddings.embed_query(text)
            embeddings.append(embedding)
        
        return embeddings[0] if len(embeddings) == 1 and isinstance(input, str) else embeddings
    
    def name(self):
        """
        Returns a custom name for the embedding function.

        Returns:
            str: The name of the embedding function.
        """
        return "NVIDIA Embedding Function"
    
def initVannaBackup(vn):
    """
    Backup initialization function for Vanna with hardcoded NASA Turbofan Engine training data.
    
    This function provides the original hardcoded training approach for NASA Turbofan Engine
    predictive maintenance queries. Use this as a fallback if the JSON-based training fails.
    
    Args:
        vn: Vanna instance to be trained and configured
        
    Returns:
        None: Modifies the Vanna instance in-place
        
    Example:
        >>> from vanna.chromadb import ChromaDB_VectorStore
        >>> vn = NIMCustomLLM(config) & ChromaDB_VectorStore()
        >>> vn.connect_to_sqlite("path/to/nasa_turbo.db")
        >>> initVannaBackup(vn)
        >>> # Vanna is now ready with hardcoded NASA Turbofan training
    """
    import json
    import os
    
    # Get and train DDL from sqlite_master
    df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
    for ddl in df_ddl['sql'].to_list():
        vn.train(ddl=ddl)

    # Fallback to default NASA Turbofan training
    fd_datasets = ["FD001", "FD002", "FD003", "FD004"]
    for fd in fd_datasets:
        vn.train(ddl=f"""
            CREATE TABLE IF NOT EXISTS RUL_{fd} (
                "unit_number" INTEGER,
                "RUL" INTEGER
            )
        """)

    sensor_columns = """
        "unit_number" INTEGER,
        "time_in_cycles" INTEGER,
        "operational_setting_1" REAL,
        "operational_setting_2" REAL,
        "operational_setting_3" REAL,
        "sensor_measurement_1" REAL,
        "sensor_measurement_2" REAL,
        "sensor_measurement_3" REAL,
        "sensor_measurement_4" REAL,
        "sensor_measurement_5" REAL,
        "sensor_measurement_6" REAL,
        "sensor_measurement_7" REAL,
        "sensor_measurement_8" REAL,
        "sensor_measurement_9" REAL,
        "sensor_measurement_10" REAL,
        "sensor_measurement_11" REAL,
        "sensor_measurement_12" REAL,
        "sensor_measurement_13" REAL,
        "sensor_measurement_14" REAL,
        "sensor_measurement_15" REAL,
        "sensor_measurement_16" REAL,
        "sensor_measurement_17" INTEGER,
        "sensor_measurement_18" INTEGER,
        "sensor_measurement_19" REAL,
        "sensor_measurement_20" REAL,
        "sensor_measurement_21" REAL
    """

    for fd in fd_datasets:
        vn.train(ddl=f"CREATE TABLE IF NOT EXISTS train_{fd} ({sensor_columns})")
        vn.train(ddl=f"CREATE TABLE IF NOT EXISTS test_{fd} ({sensor_columns})")
        
    # Default documentation for NASA Turbofan
    dataset_documentation = """
    This SQL database contains train and test splits of four different datasets: FD001, FD002, FD003, FD004. 
    Each dataset consists of multiple multivariate time series from different engines of the same type.
    
    DATABASE STRUCTURE:
    The data is organized into separate tables for each dataset:
    
    Training Tables: train_FD001, train_FD002, train_FD003, train_FD004
    Test Tables: test_FD001, test_FD002, test_FD003, test_FD004  
    RUL Tables: RUL_FD001, RUL_FD002, RUL_FD003, RUL_FD004
    
    Each training and test table contains 26 columns with identical structure:
    - unit_number: INTEGER - Identifier for each engine unit
    - time_in_cycles: INTEGER - Time step in operational cycles
    - operational_setting_1: REAL - First operational setting affecting performance
    - operational_setting_2: REAL - Second operational setting affecting performance
    - operational_setting_3: REAL - Third operational setting affecting performance
    - sensor_measurement_1 through sensor_measurement_21: REAL/INTEGER - Twenty-one sensor measurements
    
    Each RUL table contains 2 columns:
    - unit_number: INTEGER - Engine unit identifier
    - RUL: INTEGER - Remaining Useful Life value for that test unit
    
    QUERY PATTERNS:
    
    Table References:
    - "train_FD001" or "dataset train_FD001" → Use table train_FD001
    - "test_FD002" or "dataset test_FD002" → Use table test_FD002
    - "FD003" (without train/test prefix) → Determine from context whether to use train_FD003 or test_FD003
    - For RUL queries: Use specific RUL table (RUL_FD001, RUL_FD002, RUL_FD003, or RUL_FD004)
    
    Counting Patterns:
    - "How many units" → Use COUNT(DISTINCT unit_number) to count unique engines
    - "How many records/data points/measurements/entries/rows" → Use COUNT(*) to count all records
    
    RUL Handling (CRITICAL DISTINCTION):
    
    1. GROUND TRUTH RUL (for test data):
       - Use when query asks for "actual RUL", "true RUL", "ground truth", or "what is the RUL"
       - Query specific RUL table: SELECT RUL FROM RUL_FD001 WHERE unit_number=N
       - For time-series with ground truth: ((SELECT MAX(time_in_cycles) FROM test_FDxxx WHERE unit_number=N) + (SELECT RUL FROM RUL_FDxxx WHERE unit_number=N) - time_in_cycles)
    
    2. PREDICTED/CALCULATED RUL (for training data or prediction requests):
       - Use when query asks to "predict RUL", "calculate RUL", "estimate RUL", or "find RUL" for training data
       - For training data: Calculate as remaining cycles until failure = (MAX(time_in_cycles) - current_time_in_cycles + 1)
       - Training RUL query: SELECT unit_number, time_in_cycles, (MAX(time_in_cycles) OVER (PARTITION BY unit_number) - time_in_cycles + 1) AS predicted_RUL FROM train_FDxxx
    
    DEFAULT BEHAVIOR: If unclear, assume user wants PREDICTION (since this is more common)
    
    Column Names (consistent across all training and test tables):
    - unit_number: Engine identifier
    - time_in_cycles: Time step
    - operational_setting_1, operational_setting_2, operational_setting_3: Operational settings
    - sensor_measurement_1, sensor_measurement_2, ..., sensor_measurement_21: Sensor readings
    
    IMPORTANT NOTES:
    - Each dataset (FD001, FD002, FD003, FD004) has its own separate RUL table
    - RUL tables do NOT have a 'dataset' column - they are dataset-specific by table name
    - Training tables contain data until engine failure
    - Test tables contain data that stops before failure
    - RUL tables provide the actual remaining cycles for test units
    
    ENGINE OPERATION CONTEXT:
    Each engine starts with different degrees of initial wear and manufacturing variation. 
    The engine operates normally at the start of each time series and develops a fault at some point during the series. 
    In the training set, the fault grows in magnitude until system failure. 
    In the test set, the time series ends some time prior to system failure.
    The objective is to predict the number of remaining operational cycles before failure in the test set.
    """
    vn.train(documentation=dataset_documentation)

    # Default training for NASA Turbofan
    queries = [
        # 1. JOIN pattern between training and RUL tables
        "SELECT t.unit_number, t.time_in_cycles, t.operational_setting_1, r.RUL FROM train_FD001 AS t JOIN RUL_FD001 AS r ON t.unit_number = r.unit_number WHERE t.unit_number = 1 ORDER BY t.time_in_cycles",
        
        # 2. Aggregation with multiple statistical functions
        "SELECT unit_number, AVG(sensor_measurement_1) AS avg_sensor1, MAX(sensor_measurement_2) AS max_sensor2, MIN(sensor_measurement_3) AS min_sensor3 FROM train_FD002 GROUP BY unit_number",
        
        # 3. Test table filtering with time-based conditions
        "SELECT * FROM test_FD003 WHERE time_in_cycles > 50 AND sensor_measurement_1 > 500 ORDER BY unit_number, time_in_cycles",
        
        # 4. Window function for predicted RUL calculation on training data
        "SELECT unit_number, time_in_cycles, (MAX(time_in_cycles) OVER (PARTITION BY unit_number) - time_in_cycles + 1) AS predicted_RUL FROM train_FD004 WHERE unit_number <= 3 ORDER BY unit_number, time_in_cycles",
        
        # 5. Direct RUL table query with filtering
        "SELECT unit_number, RUL FROM RUL_FD001 WHERE RUL > 100 ORDER BY RUL DESC"
    ]

    for query in tqdm(queries, desc="Training NIMVanna"):
        vn.train(sql=query)

    # Essential question-SQL training pairs (covering key RUL distinction)
    vn.train(question="Get time cycles and operational setting 1 for unit 1 from test FD001", 
             sql="SELECT time_in_cycles, operational_setting_1 FROM test_FD001 WHERE unit_number = 1")
    
    # Ground Truth RUL (from RUL tables)
    vn.train(question="What is the actual remaining useful life for unit 1 in test dataset FD001", 
             sql="SELECT RUL FROM RUL_FD001 WHERE unit_number = 1")
    
    # Predicted RUL (calculated for training data)
    vn.train(question="Predict the remaining useful life for each time cycle of unit 1 in training dataset FD001", 
             sql="SELECT unit_number, time_in_cycles, (MAX(time_in_cycles) OVER (PARTITION BY unit_number) - time_in_cycles + 1) AS predicted_RUL FROM train_FD001 WHERE unit_number = 1 ORDER BY time_in_cycles")
    
    vn.train(question="How many units are in the training data for FD002", 
             sql="SELECT COUNT(DISTINCT unit_number) FROM train_FD002")
    
    # Additional RUL distinction training
    vn.train(question="Calculate RUL for training data in FD003", 
             sql="SELECT unit_number, time_in_cycles, (MAX(time_in_cycles) OVER (PARTITION BY unit_number) - time_in_cycles + 1) AS predicted_RUL FROM train_FD003 ORDER BY unit_number, time_in_cycles")
    
    vn.train(question="Get ground truth RUL values for all units in test FD002", 
             sql="SELECT unit_number, RUL FROM RUL_FD002 ORDER BY unit_number")

def chunk_documentation(text: str, max_chars: int = 1500) -> list:
    """
    Split long documentation into smaller chunks to avoid token limits.
    
    Args:
        text: The documentation text to chunk
        max_chars: Maximum characters per chunk (approximate)
        
    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    # Split by paragraphs first
    paragraphs = text.split('\n\n')
    current_chunk = ""
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed the limit, save current chunk and start new one
        if len(current_chunk) + len(paragraph) + 2 > max_chars and current_chunk:
            chunks.append(current_chunk.strip())
            current_chunk = paragraph
        else:
            if current_chunk:
                current_chunk += "\n\n" + paragraph
            else:
                current_chunk = paragraph
    
    # Add the last chunk if it exists
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    
    # If any chunk is still too long, split it further
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chars:
            # Split long chunk into sentences
            sentences = chunk.split('. ')
            temp_chunk = ""
            for sentence in sentences:
                if len(temp_chunk) + len(sentence) + 2 > max_chars and temp_chunk:
                    final_chunks.append(temp_chunk.strip() + ".")
                    temp_chunk = sentence
                else:
                    if temp_chunk:
                        temp_chunk += ". " + sentence
                    else:
                        temp_chunk = sentence
            if temp_chunk.strip():
                final_chunks.append(temp_chunk.strip())
        else:
            final_chunks.append(chunk)
    
    return final_chunks

def initVanna(vn, training_data_path: str = None):
    """
    Initialize and train a Vanna instance for SQL generation using configurable training data.
    
    This function configures a Vanna SQL generation agent with training data loaded from a YAML file,
    making it scalable for different SQL data sources with different contexts.
    
    Args:
        vn: Vanna instance to be trained and configured
        training_data_path: Path to YAML file containing training data. If None, no training is applied.
        
    Returns:
        None: Modifies the Vanna instance in-place
        
    Example:
        >>> from vanna.chromadb import ChromaDB_VectorStore
        >>> vn = NIMCustomLLM(config) & ChromaDB_VectorStore()
        >>> vn.connect_to_sqlite("path/to/database.db")
        >>> initVanna(vn, "path/to/training_data.yaml")
        >>> # Vanna is now ready to generate SQL queries
    """
    import json
    import os
    import logging
    
    logger = logging.getLogger(__name__)
    logger.info("=== Starting Vanna initialization ===")
    
    # Get and train DDL from sqlite_master
    logger.info("Loading DDL from sqlite_master...")
    try:
        df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
        ddl_count = len(df_ddl)
        logger.info(f"Found {ddl_count} DDL statements in sqlite_master")
        
        for i, ddl in enumerate(df_ddl['sql'].to_list(), 1):
            logger.debug(f"Training DDL {i}/{ddl_count}: {ddl[:100]}...")
            vn.train(ddl=ddl)
        
        logger.info(f"Successfully trained {ddl_count} DDL statements from sqlite_master")
    except Exception as e:
        logger.error(f"Error loading DDL from sqlite_master: {e}")
        raise

    # Load and apply training data from YAML file
    if training_data_path:
        logger.info(f"Training data path provided: {training_data_path}")
        
        if os.path.exists(training_data_path):
            logger.info(f"Training data file exists, loading YAML...")
            
            try:
                import yaml
                with open(training_data_path, 'r') as f:
                    training_data = yaml.safe_load(f)
                
                logger.info(f"Successfully loaded YAML training data")
                logger.info(f"Training data keys: {list(training_data.keys()) if training_data else 'None'}")
                
                # Train synthetic DDL statements
                synthetic_ddl = training_data.get("synthetic_ddl", [])
                logger.info(f"Found {len(synthetic_ddl)} synthetic DDL statements")
                
                ddl_trained = 0
                for i, ddl_statement in enumerate(synthetic_ddl, 1):
                    if ddl_statement.strip():  # Only train non-empty statements
                        logger.debug(f"Training synthetic DDL {i}: {ddl_statement[:100]}...")
                        vn.train(ddl=ddl_statement)
                        ddl_trained += 1
                    else:
                        logger.warning(f"Skipping empty synthetic DDL statement at index {i}")
                
                logger.info(f"Successfully trained {ddl_trained}/{len(synthetic_ddl)} synthetic DDL statements")
                
                # Train documentation with chunking
                documentation = training_data.get("documentation", "")
                if documentation.strip():
                    logger.info(f"Training documentation ({len(documentation)} characters)")
                    logger.debug(f"Documentation preview: {documentation[:200]}...")
                    
                    # Chunk documentation to avoid token limits
                    doc_chunks = chunk_documentation(documentation)
                    logger.info(f"Split documentation into {len(doc_chunks)} chunks")
                    
                    for i, chunk in enumerate(doc_chunks, 1):
                        try:
                            logger.debug(f"Training documentation chunk {i}/{len(doc_chunks)} ({len(chunk)} chars)")
                            vn.train(documentation=chunk)
                        except Exception as e:
                            logger.error(f"Error training documentation chunk {i}: {e}")
                            # Continue with other chunks
                    
                    logger.info(f"Successfully trained {len(doc_chunks)} documentation chunks")
                else:
                    logger.warning("No documentation found or documentation is empty")

                # Train example queries
                example_queries = training_data.get("example_queries", [])
                logger.info(f"Found {len(example_queries)} example queries")
                
                queries_trained = 0
                for i, query_data in enumerate(example_queries, 1):
                    sql = query_data.get("sql", "")
                    if sql.strip():  # Only train non-empty queries
                        logger.debug(f"Training example query {i}: {sql[:100]}...")
                        vn.train(sql=sql)
                        queries_trained += 1
                    else:
                        logger.warning(f"Skipping empty example query at index {i}")
                
                logger.info(f"Successfully trained {queries_trained}/{len(example_queries)} example queries")
                
                # Train question-SQL pairs
                question_sql_pairs = training_data.get("question_sql_pairs", [])
                logger.info(f"Found {len(question_sql_pairs)} question-SQL pairs")
                
                pairs_trained = 0
                for i, pair in enumerate(question_sql_pairs, 1):
                    question = pair.get("question", "")
                    sql = pair.get("sql", "")
                    if question.strip() and sql.strip():  # Only train non-empty pairs
                        logger.debug(f"Training question-SQL pair {i}: Q='{question[:50]}...' SQL='{sql[:50]}...'")
                        vn.train(question=question, sql=sql)
                        pairs_trained += 1
                    else:
                        if not question.strip():
                            logger.warning(f"Skipping question-SQL pair {i}: empty question")
                        if not sql.strip():
                            logger.warning(f"Skipping question-SQL pair {i}: empty SQL")
                
                logger.info(f"Successfully trained {pairs_trained}/{len(question_sql_pairs)} question-SQL pairs")
                
                # Summary
                total_trained = ddl_trained + len(doc_chunks) + queries_trained + pairs_trained
                logger.info(f"=== Training Summary ===")
                logger.info(f"  Synthetic DDL: {ddl_trained}")
                logger.info(f"  Documentation chunks: {len(doc_chunks)}")
                logger.info(f"  Example queries: {queries_trained}")
                logger.info(f"  Question-SQL pairs: {pairs_trained}")
                logger.info(f"  Total items trained: {total_trained}")
                
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML file {training_data_path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Error loading training data from {training_data_path}: {e}")
                raise
        else:
            logger.warning(f"Training data file does not exist: {training_data_path}")
            logger.warning("Proceeding without YAML training data")
    else:
        logger.info("No training data path provided, skipping YAML training")
    
    logger.info("=== Vanna initialization completed ===")

