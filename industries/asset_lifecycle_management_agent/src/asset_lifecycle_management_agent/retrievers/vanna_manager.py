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

"""
VannaManager - A simplified manager for Vanna instances
"""
import os
import logging
import threading
import hashlib
from typing import Dict, Optional
from .vanna_util import NIMVanna, ElasticNIMVanna, initVanna, NVIDIAEmbeddingFunction

logger = logging.getLogger(__name__)

class VannaManager:
    """
    A simplified singleton manager for Vanna instances.
    
    Key features:
    - Singleton pattern to ensure only one instance per configuration
    - Thread-safe operations
    - Simple instance management
    - Support for multiple database types: SQLite, generic SQL, and PostgreSQL
    """
    
    _instances: Dict[str, 'VannaManager'] = {}
    _lock = threading.Lock()
    
    def __new__(cls, config_key: str):
        """Ensure singleton pattern per configuration"""
        with cls._lock:
            if config_key not in cls._instances:
                logger.debug(f"VannaManager: Creating new singleton instance for config: {config_key}")
                cls._instances[config_key] = super().__new__(cls)
                cls._instances[config_key]._initialized = False
            else:
                logger.debug(f"VannaManager: Returning existing singleton instance for config: {config_key}")
            return cls._instances[config_key]
    
    def __init__(self, config_key: str, vanna_llm_config=None, vanna_embedder_config=None, 
                 vector_store_type: str = "chromadb", vector_store_path: str = None, 
                 elasticsearch_url: str = None, elasticsearch_index_name: str = "vanna_vectors",
                 elasticsearch_username: str = None, elasticsearch_password: str = None,
                 elasticsearch_api_key: str = None,
                 db_connection_string_or_path: str = None, db_type: str = "sqlite", 
                 training_data_path: str = None, nvidia_api_key: str = None):
        """Initialize the VannaManager and create Vanna instance immediately if all config is provided
        
        Args:
            config_key: Unique key for this configuration
            vanna_llm_config: LLM configuration object
            vanna_embedder_config: Embedder configuration object
            vector_store_type: Type of vector store - 'chromadb' or 'elasticsearch'
            vector_store_path: Path to ChromaDB vector store (required if vector_store_type='chromadb')
            elasticsearch_url: Elasticsearch URL (required if vector_store_type='elasticsearch')
            elasticsearch_index_name: Elasticsearch index name
            elasticsearch_username: Elasticsearch username for basic auth
            elasticsearch_password: Elasticsearch password for basic auth
            elasticsearch_api_key: Elasticsearch API key
            db_connection_string_or_path: Database connection (path for SQLite, connection string for others)
            db_type: Type of database - 'sqlite', 'postgres', or 'sql' (generic SQL with SQLAlchemy)
            training_data_path: Path to YAML training data file
            nvidia_api_key: NVIDIA API key (optional, can use NVIDIA_API_KEY env var)
        """
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.config_key = config_key
        self.lock = threading.Lock()
        
        # Store configuration
        self.vanna_llm_config = vanna_llm_config
        self.vanna_embedder_config = vanna_embedder_config
        self.vector_store_type = vector_store_type
        self.vector_store_path = vector_store_path
        self.elasticsearch_url = elasticsearch_url
        self.elasticsearch_index_name = elasticsearch_index_name
        self.elasticsearch_username = elasticsearch_username
        self.elasticsearch_password = elasticsearch_password
        self.elasticsearch_api_key = elasticsearch_api_key
        self.db_connection_string_or_path = db_connection_string_or_path
        self.db_type = db_type
        self.training_data_path = training_data_path
        self.nvidia_api_key = nvidia_api_key or os.getenv("NVIDIA_API_KEY")
        
        # Create and initialize Vanna instance immediately if all required config is provided
        self.vanna_instance = None
        has_vector_config = (
            (vector_store_type == "chromadb" and vector_store_path) or
            (vector_store_type == "elasticsearch" and elasticsearch_url)
        )
        if all([vanna_llm_config, vanna_embedder_config, has_vector_config, self.db_connection_string_or_path]):
            logger.debug(f"VannaManager: Initializing with immediate Vanna instance creation")
            self.vanna_instance = self._create_instance()
        else:
            if any([vanna_llm_config, vanna_embedder_config, vector_store_path, elasticsearch_url, self.db_connection_string_or_path]):
                logger.debug(f"VannaManager: Partial configuration provided, Vanna instance will be created later")
            else:
                logger.debug(f"VannaManager: No configuration provided, Vanna instance will be created later")
        
        self._initialized = True
        logger.debug(f"VannaManager initialized for config: {config_key}")
    
    def get_instance(self, vanna_llm_config=None, vanna_embedder_config=None, 
                     vector_store_type: str = None, vector_store_path: str = None,
                     elasticsearch_url: str = None, 
                     db_connection_string_or_path: str = None, db_type: str = None, 
                     training_data_path: str = None, nvidia_api_key: str = None):
        """
        Get the Vanna instance. If not created during init, create it now with provided parameters.
        """
        with self.lock:
            if self.vanna_instance is None:
                logger.debug(f"VannaManager: No instance created during init, creating now...")
                
                # Update configuration with provided parameters
                self.vanna_llm_config = vanna_llm_config or self.vanna_llm_config
                self.vanna_embedder_config = vanna_embedder_config or self.vanna_embedder_config
                self.vector_store_type = vector_store_type or self.vector_store_type
                self.vector_store_path = vector_store_path or self.vector_store_path
                self.elasticsearch_url = elasticsearch_url or self.elasticsearch_url
                self.db_connection_string_or_path = db_connection_string_or_path or self.db_connection_string_or_path
                self.db_type = db_type or self.db_type
                self.training_data_path = training_data_path or self.training_data_path
                self.nvidia_api_key = nvidia_api_key or self.nvidia_api_key
                
                # Check if we have required vector store config
                has_vector_config = (
                    (self.vector_store_type == "chromadb" and self.vector_store_path) or
                    (self.vector_store_type == "elasticsearch" and self.elasticsearch_url)
                )
                
                if all([self.vanna_llm_config, self.vanna_embedder_config, has_vector_config, self.db_connection_string_or_path]):
                    self.vanna_instance = self._create_instance()
                else:
                    raise RuntimeError("VannaManager: Missing required configuration parameters")
            else:
                logger.debug(f"VannaManager: Returning pre-initialized Vanna instance (ID: {id(self.vanna_instance)})")
                logger.debug(f"VannaManager: Vector store type: {self.vector_store_type}")
                
                # Show vector store status for pre-initialized instances
                try:
                    if self.vector_store_type == "chromadb" and self.vector_store_path:
                        if os.path.exists(self.vector_store_path):
                            list_of_folders = [d for d in os.listdir(self.vector_store_path) 
                                              if os.path.isdir(os.path.join(self.vector_store_path, d))]
                            logger.debug(f"VannaManager: ChromaDB contains {len(list_of_folders)} collections/folders")
                            if list_of_folders:
                                logger.debug(f"VannaManager: ChromaDB folders: {list_of_folders}")
                        else:
                            logger.debug(f"VannaManager: ChromaDB directory does not exist")
                    elif self.vector_store_type == "elasticsearch":
                        logger.debug(f"VannaManager: Using Elasticsearch at {self.elasticsearch_url}")
                except Exception as e:
                    logger.warning(f"VannaManager: Could not check vector store status: {e}")
            
            return self.vanna_instance
    
    def _create_instance(self):
        """
        Create a new Vanna instance using the stored configuration.
        Returns NIMVanna (ChromaDB) or ElasticNIMVanna (Elasticsearch) based on vector_store_type.
        """
        logger.info(f"VannaManager: Creating instance for {self.config_key}")
        logger.debug(f"VannaManager: Vector store type: {self.vector_store_type}")
        logger.debug(f"VannaManager: Database connection: {self.db_connection_string_or_path}")
        logger.debug(f"VannaManager: Database type: {self.db_type}")
        logger.debug(f"VannaManager: Training data path: {self.training_data_path}")
        
        # Create embedding function (used by both ChromaDB and Elasticsearch)
        embedding_function = NVIDIAEmbeddingFunction(
            api_key=self.nvidia_api_key, 
            model=self.vanna_embedder_config.model_name
        )
        
        # LLM configuration (common for both)
        llm_config = {
            "api_key": self.nvidia_api_key,
            "model": self.vanna_llm_config.model_name
        }
        
        # Create instance based on vector store type
        if self.vector_store_type == "chromadb":
            logger.debug(f"VannaManager: Creating NIMVanna with ChromaDB")
            logger.debug(f"VannaManager: ChromaDB path: {self.vector_store_path}")
            vn_instance = NIMVanna(
                VectorConfig={
                    "client": "persistent",
                    "path": self.vector_store_path,
                    "embedding_function": embedding_function
                },
                LLMConfig=llm_config
            )
        elif self.vector_store_type == "elasticsearch":
            logger.debug(f"VannaManager: Creating ElasticNIMVanna with Elasticsearch")
            logger.debug(f"VannaManager: Elasticsearch URL: {self.elasticsearch_url}")
            logger.debug(f"VannaManager: Elasticsearch index: {self.elasticsearch_index_name}")
            
            # Build Elasticsearch vector config
            es_config = {
                "url": self.elasticsearch_url,
                "index_name": self.elasticsearch_index_name,
                "embedding_function": embedding_function
            }
            
            # Add authentication if provided
            if self.elasticsearch_api_key:
                es_config["api_key"] = self.elasticsearch_api_key
                logger.debug("VannaManager: Using Elasticsearch API key authentication")
            elif self.elasticsearch_username and self.elasticsearch_password:
                es_config["username"] = self.elasticsearch_username
                es_config["password"] = self.elasticsearch_password
                logger.debug("VannaManager: Using Elasticsearch basic authentication")
            
            vn_instance = ElasticNIMVanna(
                VectorConfig=es_config,
                LLMConfig=llm_config
            )
        else:
            raise ValueError(
                f"Unsupported vector store type: {self.vector_store_type}. "
                "Supported types: 'chromadb', 'elasticsearch'"
            )
        
        # Connect to database based on type
        logger.debug(f"VannaManager: Connecting to {self.db_type} database...")
        if self.db_type == "sqlite":
            # Vanna's connect_to_sqlite has broken URL detection in 0.7.9
            # It tries to download everything with requests.get()
            # For local files, use direct SQLite connection
            import os
            db_path = self.db_connection_string_or_path
            
            # Convert relative paths to absolute
            if not os.path.isabs(db_path):
                db_path = os.path.abspath(db_path)
            
            # For local files, use sqlite3 directly
            if os.path.exists(db_path):
                import sqlite3
                import pandas as pd
                
                def run_sql_sqlite(sql: str):
                    """Execute SQL on local SQLite database."""
                    conn = sqlite3.connect(db_path)
                    try:
                        df = pd.read_sql_query(sql, conn)
                        return df
                    finally:
                        conn.close()
                
                vn_instance.run_sql = run_sql_sqlite
                vn_instance.run_sql_is_set = True
                logger.debug(f"VannaManager: Connected to local SQLite database: {db_path}")
            else:
                # If file doesn't exist, let Vanna try (maybe it's a URL)
                logger.warning(f"VannaManager: Database file not found: {db_path}")
                vn_instance.connect_to_sqlite(self.db_connection_string_or_path)
        elif self.db_type == "postgres" or self.db_type == "postgresql":
            self._connect_to_postgres(vn_instance, self.db_connection_string_or_path)
        elif self.db_type == "sql":
            self._connect_to_sql(vn_instance, self.db_connection_string_or_path)
        else:
            raise ValueError(
                f"Unsupported database type: {self.db_type}. "
                "Supported types: 'sqlite', 'postgres', 'sql'"
            )
        
        # Set configuration - allow LLM to see data for database introspection
        vn_instance.allow_llm_to_see_data = True
        logger.debug(f"VannaManager: Set allow_llm_to_see_data = True")
        
        # Initialize if needed (check if vector store is empty)
        needs_init = self._needs_initialization()
        if needs_init:
            logger.info("VannaManager: Vector store needs initialization, starting training...")
            try:
                initVanna(vn_instance, self.training_data_path)
                logger.info("VannaManager: Vector store initialization complete")
            except Exception as e:
                logger.error(f"VannaManager: Error during initialization: {e}")
                raise
        else:
            logger.debug("VannaManager: Vector store already initialized, skipping training")
        
        logger.info(f"VannaManager: Instance created successfully")
        return vn_instance
    
    def _connect_to_postgres(self, vn_instance: NIMVanna, connection_string: str):
        """
        Connect to a PostgreSQL database.

        Args:
            vn_instance: The Vanna instance to connect
            connection_string: PostgreSQL connection string in format:
                postgresql://user:password@host:port/database
        """
        try:
            import psycopg2
            from psycopg2.pool import SimpleConnectionPool

            logger.info("Connecting to PostgreSQL database...")

            # Parse connection string if needed
            if connection_string.startswith("postgresql://"):
                # Use SQLAlchemy-style connection for Vanna
                vn_instance.connect_to_postgres(url=connection_string)
            else:
                # Assume it's a psycopg2 connection string
                vn_instance.connect_to_postgres(url=f"postgresql://{connection_string}")

            logger.info("Successfully connected to PostgreSQL database")
        except ImportError:
            logger.error(
                "psycopg2 is required for PostgreSQL connections. "
                "Install it with: pip install psycopg2-binary"
            )
            raise
        except Exception as e:
            logger.error(f"Error connecting to PostgreSQL: {e}")
            raise

    def _connect_to_sql(self, vn_instance: NIMVanna, connection_string: str):
        """
        Connect to a generic SQL database using SQLAlchemy.

        Args:
            vn_instance: The Vanna instance to connect
            connection_string: SQLAlchemy-compatible connection string, e.g.:
                - MySQL: mysql+pymysql://user:password@host:port/database
                - PostgreSQL: postgresql://user:password@host:port/database
                - SQL Server: mssql+pyodbc://user:password@host:port/database?driver=ODBC+Driver+17+for+SQL+Server
                - Oracle: oracle+cx_oracle://user:password@host:port/?service_name=service
        """
        try:
            from sqlalchemy import create_engine

            logger.info("Connecting to SQL database via SQLAlchemy...")

            # Create SQLAlchemy engine
            engine = create_engine(connection_string)

            # Connect Vanna to the database using the engine
            vn_instance.connect_to_sqlalchemy(engine)

            logger.info("Successfully connected to SQL database")
        except ImportError:
            logger.error(
                "SQLAlchemy is required for generic SQL connections. "
                "Install it with: pip install sqlalchemy"
            )
            raise
        except Exception as e:
            logger.error(f"Error connecting to SQL database: {e}")
            raise
    
    def _needs_initialization(self) -> bool:
        """
        Check if the vector store needs initialization by checking if it's empty.
        For ChromaDB: checks directory existence and contents
        For Elasticsearch: checks if index exists and has data
        """
        logger.debug(f"VannaManager: Checking if vector store needs initialization...")
        logger.debug(f"VannaManager: Vector store type: {self.vector_store_type}")
        
        try:
            if self.vector_store_type == "chromadb":
                logger.debug(f"VannaManager: Checking ChromaDB at: {self.vector_store_path}")
                
                if not os.path.exists(self.vector_store_path):
                    logger.debug(f"VannaManager: ChromaDB directory does not exist -> needs initialization")
                    return True
                
                # Check if there are any subdirectories (ChromaDB creates subdirectories when data is stored)
                list_of_folders = [d for d in os.listdir(self.vector_store_path) 
                                  if os.path.isdir(os.path.join(self.vector_store_path, d))]
                
                logger.debug(f"VannaManager: Found {len(list_of_folders)} folders in ChromaDB")
                if list_of_folders:
                    logger.debug(f"VannaManager: ChromaDB folders: {list_of_folders}")
                    logger.debug(f"VannaManager: ChromaDB is populated -> skipping initialization")
                    return False
                else:
                    logger.debug(f"VannaManager: ChromaDB is empty -> needs initialization")
                    return True
                    
            elif self.vector_store_type == "elasticsearch":
                logger.debug(f"VannaManager: Checking Elasticsearch at: {self.elasticsearch_url}")
                
                # For Elasticsearch, check if training data is available in the instance
                # This is a simplified check - we assume if we can connect, we should initialize if no training data exists
                try:
                    if hasattr(self.vanna_instance, 'get_training_data'):
                        training_data = self.vanna_instance.get_training_data()
                        if training_data and len(training_data) > 0:
                            logger.debug(f"VannaManager: Elasticsearch has {len(training_data)} training data entries -> skipping initialization")
                            return False
                        else:
                            logger.debug(f"VannaManager: Elasticsearch has no training data -> needs initialization")
                            return True
                    else:
                        logger.debug(f"VannaManager: Cannot check Elasticsearch training data -> needs initialization")
                        return True
                except Exception as e:
                    logger.debug(f"VannaManager: Error checking Elasticsearch data ({e}) -> needs initialization")
                    return True
            else:
                logger.warning(f"VannaManager: Unknown vector store type: {self.vector_store_type}")
                return True
                
        except Exception as e:
            logger.warning(f"VannaManager: Could not check vector store status: {e}")
            logger.warning(f"VannaManager: Defaulting to needs initialization = True")
            return True
    
    def generate_sql_safe(self, question: str) -> str:
        """
        Generate SQL with error handling.
        """
        with self.lock:
            if self.vanna_instance is None:
                raise RuntimeError("VannaManager: No instance available")
            
            try:
                logger.debug(f"VannaManager: Generating SQL for question: {question}")
                
                # Generate SQL with allow_llm_to_see_data=True for database introspection
                sql = self.vanna_instance.generate_sql(question=question, allow_llm_to_see_data=True)
                
                # Validate SQL response
                if not sql or sql.strip() == "":
                    raise ValueError("Empty SQL response")
                
                return sql
                
            except Exception as e:
                logger.error(f"VannaManager: Error in SQL generation: {e}")
                raise
    
    def force_reset(self):
        """
        Force reset the instance (useful for cleanup).
        """
        with self.lock:
            if self.vanna_instance:
                logger.debug(f"VannaManager: Resetting instance for {self.config_key}")
                self.vanna_instance = None
    
    def get_stats(self) -> Dict:
        """
        Get manager statistics.
        """
        return {
            "config_key": self.config_key,
            "instance_id": id(self.vanna_instance) if self.vanna_instance else None,
            "has_instance": self.vanna_instance is not None,
            "db_type": self.db_type,
        }

    @classmethod
    def create_with_config(cls, vanna_llm_config, vanna_embedder_config, 
                          vector_store_type: str = "chromadb", vector_store_path: str = None,
                          elasticsearch_url: str = None, elasticsearch_index_name: str = "vanna_vectors",
                          elasticsearch_username: str = None, elasticsearch_password: str = None,
                          elasticsearch_api_key: str = None,
                          db_connection_string_or_path: str = None, db_type: str = "sqlite", 
                          training_data_path: str = None, nvidia_api_key: str = None):
        """
        Class method to create a VannaManager with full configuration.
        Uses create_config_key to ensure singleton behavior based on configuration.
        
        Args:
            vanna_llm_config: LLM configuration object
            vanna_embedder_config: Embedder configuration object
            vector_store_type: Type of vector store - 'chromadb' or 'elasticsearch'
            vector_store_path: Path to ChromaDB vector store (required if vector_store_type='chromadb')
            elasticsearch_url: Elasticsearch URL (required if vector_store_type='elasticsearch')
            elasticsearch_index_name: Elasticsearch index name
            elasticsearch_username: Elasticsearch username for basic auth
            elasticsearch_password: Elasticsearch password for basic auth
            elasticsearch_api_key: Elasticsearch API key
            db_connection_string_or_path: Database connection (path for SQLite, connection string for others)
            db_type: Type of database - 'sqlite', 'postgres', or 'sql'
            training_data_path: Path to YAML training data file
            nvidia_api_key: NVIDIA API key (optional)
        """
        config_key = create_config_key(
            vanna_llm_config, vanna_embedder_config, 
            vector_store_type, vector_store_path, elasticsearch_url,
            db_connection_string_or_path, db_type
        )
        
        # Create instance with just config_key (singleton pattern)
        instance = cls(config_key)
        
        # If this is a new instance that hasn't been configured yet, set the configuration
        if not hasattr(instance, 'vanna_llm_config') or instance.vanna_llm_config is None:
            instance.vanna_llm_config = vanna_llm_config
            instance.vanna_embedder_config = vanna_embedder_config
            instance.vector_store_type = vector_store_type
            instance.vector_store_path = vector_store_path
            instance.elasticsearch_url = elasticsearch_url
            instance.elasticsearch_index_name = elasticsearch_index_name
            instance.elasticsearch_username = elasticsearch_username
            instance.elasticsearch_password = elasticsearch_password
            instance.elasticsearch_api_key = elasticsearch_api_key
            instance.db_connection_string_or_path = db_connection_string_or_path
            instance.db_type = db_type
            instance.training_data_path = training_data_path
            instance.nvidia_api_key = nvidia_api_key
            
            # Create Vanna instance immediately if all config is available
            if instance.vanna_instance is None:
                logger.debug(f"VannaManager: Creating Vanna instance for existing singleton")
                instance.vanna_instance = instance._create_instance()
        
        return instance

def create_config_key(vanna_llm_config, vanna_embedder_config, 
                     vector_store_type: str, vector_store_path: str, elasticsearch_url: str,
                     db_connection_string_or_path: str, db_type: str = "sqlite") -> str:
    """
    Create a unique configuration key for the VannaManager singleton.
    
    Args:
        vanna_llm_config: LLM configuration object
        vanna_embedder_config: Embedder configuration object
        vector_store_type: Type of vector store
        vector_store_path: Path to ChromaDB vector store
        elasticsearch_url: Elasticsearch URL
        db_connection_string_or_path: Database connection (path for SQLite, connection string for others)
        db_type: Type of database
        
    Returns:
        str: Unique configuration key
    """
    vector_id = vector_store_path if vector_store_type == "chromadb" else elasticsearch_url
    config_str = f"{vanna_llm_config.model_name}_{vanna_embedder_config.model_name}_{vector_store_type}_{vector_id}_{db_connection_string_or_path}_{db_type}"
    return hashlib.md5(config_str.encode()).hexdigest()[:12]
