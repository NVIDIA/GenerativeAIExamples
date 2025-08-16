"""
VannaManager - A simplified manager for Vanna instances
"""
import os
import logging
import threading
import hashlib
from typing import Dict, Optional
from .vanna_util import NIMVanna, initVanna, CustomEmbeddingFunction

logger = logging.getLogger(__name__)

class VannaManager:
    """
    A simplified singleton manager for Vanna instances.
    
    Key features:
    - Singleton pattern to ensure only one instance per configuration
    - Thread-safe operations
    - Simple instance management
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
    
    def __init__(self, config_key: str, vanna_llm_config=None, vanna_embedder_config=None, vector_store_path: str = None, db_path: str = None, training_data_path: str = None):
        """Initialize the VannaManager and create Vanna instance immediately if all config is provided"""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        self.config_key = config_key
        self.lock = threading.Lock()
        
        # Store configuration
        self.vanna_llm_config = vanna_llm_config
        self.vanna_embedder_config = vanna_embedder_config
        self.vector_store_path = vector_store_path
        self.db_path = db_path
        self.training_data_path = training_data_path
        
        # Create and initialize Vanna instance immediately if all required config is provided
        self.vanna_instance = None
        if all([vanna_llm_config, vanna_embedder_config, vector_store_path, db_path]):
            logger.debug(f"VannaManager: Initializing with immediate Vanna instance creation")
            self.vanna_instance = self._create_instance()
        else:
            if any([vanna_llm_config, vanna_embedder_config, vector_store_path, db_path]):
                logger.debug(f"VannaManager: Partial configuration provided, Vanna instance will be created later")
            else:
                logger.debug(f"VannaManager: No configuration provided, Vanna instance will be created later")
        
        self._initialized = True
        logger.debug(f"VannaManager initialized for config: {config_key}")
    
    def get_instance(self, vanna_llm_config=None, vanna_embedder_config=None, vector_store_path: str = None, db_path: str = None, training_data_path: str = None) -> NIMVanna:
        """
        Get the Vanna instance. If not created during init, create it now with provided parameters.
        """
        with self.lock:
            if self.vanna_instance is None:
                logger.debug(f"VannaManager: No instance created during init, creating now...")
                
                # Update configuration with provided parameters
                self.vanna_llm_config = vanna_llm_config or self.vanna_llm_config
                self.vanna_embedder_config = vanna_embedder_config or self.vanna_embedder_config
                self.vector_store_path = vector_store_path or self.vector_store_path
                self.db_path = db_path or self.db_path
                self.training_data_path = training_data_path or self.training_data_path
                
                if all([self.vanna_llm_config, self.vanna_embedder_config, self.vector_store_path, self.db_path]):
                    self.vanna_instance = self._create_instance()
                else:
                    raise RuntimeError("VannaManager: Missing required configuration parameters")
            else:
                logger.debug(f"VannaManager: Returning pre-initialized Vanna instance (ID: {id(self.vanna_instance)})")
                
                # Show vector store status for pre-initialized instances
                try:
                    if os.path.exists(self.vector_store_path):
                        list_of_folders = [d for d in os.listdir(self.vector_store_path) 
                                          if os.path.isdir(os.path.join(self.vector_store_path, d))]
                        logger.debug(f"VannaManager: Vector store contains {len(list_of_folders)} collections/folders")
                        if list_of_folders:
                            logger.debug(f"VannaManager: Vector store folders: {list_of_folders}")
                    else:
                        logger.debug(f"VannaManager: Vector store directory does not exist")
                except Exception as e:
                    logger.warning(f"VannaManager: Could not check vector store status: {e}")
            
            return self.vanna_instance
    
    def _create_instance(self) -> NIMVanna:
        """
        Create a new Vanna instance using the stored configuration.
        """
        logger.info(f"VannaManager: Creating instance for {self.config_key}")
        logger.debug(f"VannaManager: Vector store path: {self.vector_store_path}")
        logger.debug(f"VannaManager: Database path: {self.db_path}")
        logger.debug(f"VannaManager: Training data path: {self.training_data_path}")
        
        # Create instance
        vn_instance = NIMVanna(
            VectorConfig={
                "client": "persistent",
                "path": self.vector_store_path,
                "embedding_function": CustomEmbeddingFunction(
                    api_key=os.getenv("NVIDIA_API_KEY"), 
                    model=self.vanna_embedder_config.model_name)
            },
            LLMConfig={
                "api_key": os.getenv("NVIDIA_API_KEY"),
                "model": self.vanna_llm_config.model_name
            }
        )
        
        # Connect to database
        logger.debug(f"VannaManager: Connecting to SQLite database...")
        vn_instance.connect_to_sqlite(self.db_path)
        
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
    
    def _needs_initialization(self) -> bool:
        """
        Check if the vector store needs initialization by checking if it's empty.
        """
        logger.debug(f"VannaManager: Checking if vector store needs initialization...")
        logger.debug(f"VannaManager: Vector store path: {self.vector_store_path}")
        
        try:
            if not os.path.exists(self.vector_store_path):
                logger.debug(f"VannaManager: Vector store directory does not exist -> needs initialization")
                return True
            
            # Check if there are any subdirectories (ChromaDB creates subdirectories when data is stored)
            list_of_folders = [d for d in os.listdir(self.vector_store_path) 
                              if os.path.isdir(os.path.join(self.vector_store_path, d))]
            
            logger.debug(f"VannaManager: Found {len(list_of_folders)} folders in vector store")
            if list_of_folders:
                logger.debug(f"VannaManager: Vector store folders: {list_of_folders}")
                logger.debug(f"VannaManager: Vector store is populated -> skipping initialization")
                return False
            else:
                logger.debug(f"VannaManager: Vector store is empty -> needs initialization")
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
            "has_instance": self.vanna_instance is not None
        }

    @classmethod
    def create_with_config(cls, vanna_llm_config, vanna_embedder_config, vector_store_path: str, db_path: str, training_data_path: str = None):
        """
        Class method to create a VannaManager with full configuration.
        Uses create_config_key to ensure singleton behavior based on configuration.
        """
        config_key = create_config_key(vanna_llm_config, vanna_embedder_config, vector_store_path, db_path)
        
        # Create instance with just config_key (singleton pattern)
        instance = cls(config_key)
        
        # If this is a new instance that hasn't been configured yet, set the configuration
        if not hasattr(instance, 'vanna_llm_config') or instance.vanna_llm_config is None:
            instance.vanna_llm_config = vanna_llm_config
            instance.vanna_embedder_config = vanna_embedder_config
            instance.vector_store_path = vector_store_path
            instance.db_path = db_path
            instance.training_data_path = training_data_path
            
            # Create Vanna instance immediately if all config is available
            if instance.vanna_instance is None:
                logger.debug(f"VannaManager: Creating Vanna instance for existing singleton")
                instance.vanna_instance = instance._create_instance()
        
        return instance

def create_config_key(vanna_llm_config, vanna_embedder_config, vector_store_path: str, db_path: str) -> str:
    """
    Create a unique configuration key for the VannaManager singleton.
    """
    config_str = f"{vanna_llm_config.model_name}_{vanna_embedder_config.model_name}_{vector_store_path}_{db_path}"
    return hashlib.md5(config_str.encode()).hexdigest()[:12]
