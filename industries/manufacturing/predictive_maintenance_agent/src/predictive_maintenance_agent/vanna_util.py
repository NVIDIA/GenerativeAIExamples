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
    
def initVanna(vn):
    # Get and train DDL from sqlite_master
    df_ddl = vn.run_sql("SELECT type, sql FROM sqlite_master WHERE sql is not null")
    for ddl in df_ddl['sql'].to_list():
        vn.train(ddl=ddl)

    # Define FD datasets and DDL for RUL tables
    fd_datasets = ["FD001", "FD002", "FD003", "FD004"]
    for fd in fd_datasets:
        vn.train(ddl=f"""
            CREATE TABLE IF NOT EXISTS RUL_{fd} (
                "unit_number" INTEGER,
                "RUL" INTEGER
            )
        """)

    # Common sensor columns for train and test tables
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

    # Create train and test tables for each FD dataset
    for fd in fd_datasets:
        vn.train(ddl=f"CREATE TABLE IF NOT EXISTS train_{fd} ({sensor_columns})")
        vn.train(ddl=f"CREATE TABLE IF NOT EXISTS test_{fd} ({sensor_columns})")
        
    dataset_documentation = """
    Data sets (FD001, FD002, FD003, FD004) consists of multiple multivariate time series. Each data set is further divided into training and test subsets. 
    Each time series is from a different engine � i.e., the data can be considered to be from a fleet of engines of the same type. 
    Each engine starts with different degrees of initial wear and manufacturing variation which is unknown to the user. T
    his wear and variation is considered normal, i.e., it is not considered a fault condition. There are three operational settings that have a substantial effect on engine performance. 
    These settings are also included in the data. The data is contaminated with sensor noise.

    The engine is operating normally at the start of each time series, and develops a fault at some point during the series. 
    In the training set, the fault grows in magnitude until system failure. In the test set, the time series ends some time prior to system failure. 
    The objective is to predict the number of remaining operational cycles before failure in the test set, i.e., the number of operational cycles after the last cycle that the engine will continue to operate. 
    Also provided a vector of true Remaining Useful Life (RUL) values only for the test data.

    The data are provided as a zip-compressed text file with 26 columns of numbers, separated by spaces. 
    Each row is a snapshot of data taken during a single operational cycle, each column is a different variable. The columns correspond to:
    1)	unit number
    2)	time, in cycles
    3)	operational setting 1
    4)	operational setting 2
    5)	operational setting 3
    6)	sensor measurement  1
    7)	sensor measurement  2
    ...
    26)	sensor measurement  26
    """

    # Additional training examples
    vn.train(documentation=dataset_documentation)

    # Additional training examples
    # vn.train(documentation="The engine_sensor_data table tracks operational settings and sensor measurements for multiple engines in a fleet. It includes Remaining Useful Life (RUL) predictions for each engine.")
    
    queries = [
        "SELECT * FROM train_FD001 AS t JOIN RUL_FD001 AS r ON t.unit_number = r.unit_number ORDER BY t.time_in_cycles DESC LIMIT 10",
        "SELECT unit_number, AVG(sensor_measurement_1), AVG(sensor_measurement_2), AVG(sensor_measurement_3) FROM train_FD001 GROUP BY unit_number",
        "SELECT unit_number, SUM(sensor_measurement_1), SUM(sensor_measurement_2), SUM(sensor_measurement_3) FROM train_FD001 GROUP BY unit_number",
        "SELECT * FROM train_FD002 WHERE time_in_cycles BETWEEN 50 AND 100",
        "SELECT * FROM train_FD003 WHERE unit_number = 1 ORDER BY time_in_cycles ASC",
        """
        SELECT unit_number, 
               MAX(sensor_measurement_1) AS max_sensor1, 
               MIN(sensor_measurement_1) AS min_sensor1, 
               AVG(sensor_measurement_1) AS avg_sensor1 
        FROM train_FD004 
        GROUP BY unit_number
        """,
        """
        SELECT unit_number, 
               AVG(sensor_measurement_5) AS avg_sensor5, 
               AVG(sensor_measurement_10) AS avg_sensor10 
        FROM train_FD001 
        GROUP BY unit_number
        """,
        "SELECT unit_number, MAX(time_in_cycles) AS last_cycle FROM train_FD002 GROUP BY unit_number",
        "SELECT * FROM train_FD003 WHERE sensor_measurement_17 < 0 OR sensor_measurement_18 < 0",
        """
        SELECT unit_number, 
               STDDEV(sensor_measurement_1) AS std_sensor1, 
               STDDEV(sensor_measurement_2) AS std_sensor2, 
               STDDEV(sensor_measurement_3) AS std_sensor3 
        FROM train_FD001 
        WHERE unit_number = 2
        GROUP BY unit_number
        """,
        """
        SELECT unit_number, 
               SUM(sensor_measurement_1) AS sum_sensor1, 
               SUM(sensor_measurement_2) AS sum_sensor2, 
               SUM(sensor_measurement_3) AS sum_sensor3, 
               SUM(sensor_measurement_4) AS sum_sensor4, 
               SUM(sensor_measurement_5) AS sum_sensor5 
        FROM train_FD004 
        GROUP BY unit_number
        """,
        "SELECT * FROM test_FD002 WHERE sensor_measurement_2 > 100",
        """
        SELECT unit_number, 
               MAX(sensor_measurement_3) AS max_sensor3, 
               MIN(sensor_measurement_6) AS min_sensor6, 
               AVG(sensor_measurement_9) AS avg_sensor9 
        FROM test_FD003 
        GROUP BY unit_number
        """,
        "SELECT * FROM test_FD004 WHERE unit_number IN (1, 2, 3) ORDER BY time_in_cycles ASC",
    ]

    for query in tqdm(queries, desc="Training NIMVanna"):
        vn.train(sql=query)

    # Additional specific training cases
    vn.train(question="Retrieve the time_in_cycles and operational_setting_1 from the test_FD001 for all records where the unit_id is equal to 1.", 
    sql="SELECT time_in_cycles, operational_setting_1 FROM test_FD001 WHERE unit_number = 1")
    vn.train(question="Retrieve the time_in_cycles and sensor_measurement_1 from the test_FD001 for all records where the unit_id is equal to 1.", 
    sql="SELECT time_in_cycles, sensor_measurement_1 FROM test_FD001 WHERE unit_number = 1")
    vn.train(question="Retrieve RUL of each unit from the train_FD001", 
    sql="SELECT unit_number, MAX(time_in_cycles) AS RUL FROM train_FD001 GROUP BY unit_number")
    vn.train(question="Retrieve the unit_number, time_in_cycles, real time Remaining Useful Life (RUL), and sensor_measurement_3 from table train_FD001, ordered by unit_number and time_in_cycles.", sql="SELECT unit_number, time_in_cycles, MAX(time_in_cycles) OVER (PARTITION BY unit_number) - time_in_cycles AS RUL, sensor_measurement_3 FROM train_FD001 ORDER BY unit_number, time_in_cycles")

