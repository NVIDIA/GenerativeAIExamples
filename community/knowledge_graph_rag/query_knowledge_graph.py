# Copyright (c) 2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may
# obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import argparse
import getpass
import logging

try:
    import nx_arangodb as nxadb
    print("Successfully imported nx_arangodb as nxadb.")
except ImportError:
    print("Warning: Could not import nx_arangodb. Ensure nx_arangodb is installed.")
    nxadb = None

from langchain_nvidia_ai_endpoints import ChatNVIDIA

# Attempt relative import for graph_langchain_utils
# This should work if the script is run as part of a package or from the directory
try:
    from .graph_langchain_utils import NXCugraphEntityGraph, GPUGraphQAChain
except ImportError:
    # Fallback for running the script directly where relative import might fail
    # This assumes graph_langchain_utils.py is in the same directory
    from graph_langchain_utils import NXCugraphEntityGraph, GPUGraphQAChain


# --- ArangoDB Connection Parameters (similar to build_graph.py) ---
DEFAULT_DATABASE_HOST = "http://localhost:8529"
DEFAULT_DATABASE_USERNAME = "root"
DEFAULT_DATABASE_PASSWORD = ""
DEFAULT_DATABASE_NAME = "knowledge_graph_db"
DEFAULT_GRAPH_NAME = "graph_data" # This is the graph name used in build_graph and setup

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def load_graph_from_db(db_config: dict, graph_name: str):
    """
    Loads a graph from ArangoDB using nx_arangodb.
    Args:
        db_config: Dictionary with ArangoDB connection details
                   (host, username, password, db_name).
        graph_name: The name of the graph in ArangoDB.
    Returns:
        A networkx.MultiDiGraph object or None if loading fails.
    """
    if nxadb is None:
        logger.error("nx_arangodb library (nxadb) is not available. Cannot load graph.")
        return None

    logger.info(f"Attempting to load graph '{graph_name}' from ArangoDB...")
    logger.info(f"Connection details: host={db_config['host']}, dbName={db_config['db_name']}, username={db_config['username']}")

    try:
        # Ensure parameter names match nxadb.MultiDiGraph constructor
        nx_graph = nxadb.MultiDiGraph(
            name=graph_name,
            dbName=db_config['db_name'],
            host=db_config['host'],
            username=db_config['username'],
            password=db_config['password']
        )

        if nx_graph is not None:
            logger.info(f"Successfully loaded graph '{graph_name}' into NetworkX object.")
            logger.info(f"Number of nodes: {nx_graph.number_of_nodes()}, Number of edges: {nx_graph.number_of_edges()}")
            if nx_graph.number_of_nodes() == 0:
                logger.warning("The loaded graph has 0 nodes. Ensure the graph was populated correctly.")
            return nx_graph
        else:
            logger.error("Failed to load graph: nxadb.MultiDiGraph returned None.")
            return None
    except Exception as e:
        logger.error(f"Error loading graph from ArangoDB: {e}")
        logger.error("Please ensure ArangoDB is running, accessible, and the graph exists.")
        return None

def start_query_loop(graph_qa_chain: GPUGraphQAChain):
    """
    Starts a loop that prompts the user for questions and prints answers.
    Args:
        graph_qa_chain: An initialized GPUGraphQAChain instance.
    """
    logger.info("Starting interactive query session...")
    while True:
        try:
            question = input("Enter your question (or 'quit' to exit): ").strip()
            if not question:
                continue
            if question.lower() == 'quit':
                logger.info("Exiting query loop.")
                break

            logger.info(f"Processing question: {question}")
            # Use invoke for newer LangChain versions, with 'query' as the input key
            # The GPUGraphQAChain expects 'query' as per its _call method's input_key
            # and returns a dict with 'result' as per its output_key.
            # The base GraphQAChain uses self.input_key and self.output_key
            # which default to "query" and "result" respectively.
            answer_payload = graph_qa_chain.invoke({graph_qa_chain.input_key: question})
            answer = answer_payload[graph_qa_chain.output_key]

            print(f"\nAnswer: {answer}\n")

        except KeyboardInterrupt:
            logger.info("\nExiting query loop due to user interruption.")
            break
        except Exception as e:
            logger.error(f"An error occurred during query processing: {e}")
            print("Sorry, I encountered an error. Please try again.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query a knowledge graph using LangChain and NVIDIA LLMs.")

    # ArangoDB connection arguments
    parser.add_argument("--db_host", type=str, default=os.environ.get("DATABASE_HOST", DEFAULT_DATABASE_HOST), help="ArangoDB host URL.")
    parser.add_argument("--db_username", type=str, default=os.environ.get("DATABASE_USERNAME", DEFAULT_DATABASE_USERNAME), help="ArangoDB username.")
    parser.add_argument("--db_password", type=str, default=os.environ.get("DATABASE_PASSWORD", DEFAULT_DATABASE_PASSWORD), help="ArangoDB password.")
    parser.add_argument("--db_name", type=str, default=os.environ.get("DATABASE_NAME", DEFAULT_DATABASE_NAME), help="ArangoDB database name.")
    parser.add_argument("--graph_name", type=str, default=DEFAULT_GRAPH_NAME, help="Name of the graph in ArangoDB.")

    # LLM and API Key arguments
    parser.add_argument("--llm_model", type=str, default="mistralai/mixtral-8x22b-instruct-v0.1", help="Name of the LLM model to use.")
    parser.add_argument("--api_key", type=str, default=None, help="NVIDIA API Key. Overrides NVIDIA_API_KEY environment variable.")

    args = parser.parse_args()

    # API Key Setup
    nvidia_api_key = args.api_key or os.getenv("NVIDIA_API_KEY")
    if not nvidia_api_key:
        logger.warning("NVIDIA_API_KEY not found as environment variable or argument.")
        try:
            nvidia_api_key = getpass.getpass("Please enter your NVIDIA API Key: ")
        except Exception as e: # Handle cases where getpass might fail (e.g., no tty)
             logger.error(f"Failed to get API key via prompt: {e}")
             nvidia_api_key = None # Ensure it's None if not provided

    if not nvidia_api_key:
        logger.error("NVIDIA API Key is required. Exiting.")
        exit(1)

    # Initialize LLM
    try:
        logger.info(f"Initializing LLM: {args.llm_model}")
        llm = ChatNVIDIA(model=args.llm_model, nvidia_api_key=nvidia_api_key)
        # Perform a quick test if possible, e.g., llm.invoke("test")
        # This might require specific handling for ChatNVIDIA if it's stateful or needs setup.
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        exit(1)

    # Prepare ArangoDB configuration
    arangodb_config = {
        "host": args.db_host,
        "username": args.db_username,
        "password": args.db_password,
        "db_name": args.db_name,
    }

    # Load graph from ArangoDB
    logger.info("Loading graph from database...")
    networkx_graph = load_graph_from_db(arangodb_config, args.graph_name)

    if networkx_graph is None:
        logger.error("Failed to load graph from ArangoDB. Exiting.")
        exit(1)

    if networkx_graph.number_of_nodes() == 0:
        logger.warning("Graph loaded but contains 0 nodes. QA might not be effective.")
        # Decide if you want to exit or proceed if graph is empty
        # For now, let's proceed but with a warning.

    # Wrap graph for LangChain
    logger.info("Wrapping graph for LangChain...")
    try:
        langchain_graph_wrapper = NXCugraphEntityGraph(graph=networkx_graph)
    except Exception as e:
        logger.error(f"Failed to wrap graph with NXCugraphEntityGraph: {e}")
        exit(1)

    # Initialize QA Chain
    logger.info("Initializing GPUGraphQAChain...")
    try:
        graph_qa_chain = GPUGraphQAChain.from_llm(
            llm=llm,
            graph=langchain_graph_wrapper
            # prompt can be customized here if needed
        )
    except Exception as e:
        logger.error(f"Failed to initialize GPUGraphQAChain: {e}")
        exit(1)

    # Start query loop
    print("\nKnowledge Graph Query Interface Initialized.")
    print("============================================")
    print(f"Using LLM: {args.llm_model}")
    print(f"Connected to graph: {args.graph_name} in database {args.db_name}")
    print("Type 'quit' to exit the application.")

    start_query_loop(graph_qa_chain)

    logger.info("Application finished.")
