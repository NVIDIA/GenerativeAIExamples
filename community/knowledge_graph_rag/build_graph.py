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
import pandas as pd
import argparse
from arango import ArangoClient
from arango.exceptions import DocumentInsertError, CollectionTruncateError
from networkx import MultiDiGraph

try:
    import nx_arangodb as nxadb
    print("Successfully imported nx_arangodb as nxadb.")
except ImportError:
    print("Warning: Could not import nx_arangodb. Ensure nx_arangodb is installed.")
    nxadb = None # Keep a placeholder if import fails


# --- ArangoDB Connection Parameters ---
DEFAULT_DATABASE_HOST = "http://localhost:8529"
DEFAULT_DATABASE_USERNAME = "root"
DEFAULT_DATABASE_PASSWORD = ""  # Replace with your default password if any
DEFAULT_DATABASE_NAME = "knowledge_graph_db" # Same as in setup_arangodb.py
DEFAULT_GRAPH_NAME = "graph_data"
DEFAULT_VERTEX_COLLECTION = "vertices"
DEFAULT_EDGE_COLLECTION = "edges"

# --- Helper Functions ---

def get_arango_db(args):
    """Establishes connection to ArangoDB and returns the database object."""
    db_host = os.environ.get("DATABASE_HOST", args.db_host)
    db_username = os.environ.get("DATABASE_USERNAME", args.db_username)
    db_password = os.environ.get("DATABASE_PASSWORD", args.db_password)
    db_name = os.environ.get("DATABASE_NAME", args.db_name)

    try:
        client = ArangoClient(hosts=db_host)
        db = client.db(db_name, username=db_username, password=db_password)
        if not db.has_database(db_name):
             print(f"Database '{db_name}' not found. Please run setup_arangodb.py first.")
             return None
        print(f"Successfully connected to ArangoDB database '{db_name}' at {db_host}")
        return db
    except Exception as e:
        print(f"Failed to connect to ArangoDB: {e}")
        return None

def clear_collections(db, vertex_collection_name, edge_collection_name):
    """Clears specified vertex and edge collections."""
    try:
        if db.has_collection(vertex_collection_name):
            vc = db.collection(vertex_collection_name)
            vc.truncate()
            print(f"Cleared vertex collection: {vertex_collection_name}")
        else:
            print(f"Warning: Vertex collection {vertex_collection_name} not found for clearing.")

        if db.has_collection(edge_collection_name):
            ec = db.collection(edge_collection_name)
            ec.truncate()
            print(f"Cleared edge collection: {edge_collection_name}")
        else:
            print(f"Warning: Edge collection {edge_collection_name} not found for clearing.")
    except CollectionTruncateError as e:
        print(f"Error truncating collections: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during clearing collections: {e}")


def load_data_from_csvs(csv_input_path, entities_file, relations_file, triples_file):
    """Loads graph data from CSV files into pandas DataFrames."""
    try:
        entities_df = pd.read_csv(os.path.join(csv_input_path, entities_file))
        relations_df = pd.read_csv(os.path.join(csv_input_path, relations_file))
        triples_df = pd.read_csv(os.path.join(csv_input_path, triples_file))
        print(f"Loaded {len(entities_df)} entities, {len(relations_df)} relations, and {len(triples_df)} triples.")
        return entities_df, relations_df, triples_df
    except FileNotFoundError as e:
        print(f"Error: One or more CSV files not found in '{csv_input_path}': {e}")
        return None, None, None
    except Exception as e:
        print(f"Error loading CSV files: {e}")
        return None, None, None

def insert_vertices(db, vertex_collection_name, entities_df):
    """Inserts vertices into the specified ArangoDB collection."""
    if not db.has_collection(vertex_collection_name):
        print(f"Error: Vertex collection '{vertex_collection_name}' not found.")
        return 0

    vc = db.collection(vertex_collection_name)
    inserted_count = 0
    skipped_count = 0

    print(f"Starting vertex insertion into '{vertex_collection_name}'...")
    for index, row in entities_df.iterrows():
        vertex_doc = {
            "_key": str(row['entity_id']), # Use entity_id as _key
            "name": row['entity_name'],    # Store entity_name as 'name'
            "entity_id": int(row['entity_id']) # Also store original entity_id if needed
        }
        try:
            vc.insert(vertex_doc)
            inserted_count += 1
        except DocumentInsertError as e:
            # This can happen if _key already exists and --clear_existing_data was false
            # print(f"Skipping duplicate vertex with _key '{vertex_doc['_key']}': {e}")
            skipped_count +=1
        except Exception as e:
            print(f"Error inserting vertex _key '{vertex_doc['_key']}': {e}")
            skipped_count +=1

        if (index + 1) % 1000 == 0:
            print(f"Processed {index + 1} vertices (inserted: {inserted_count}, skipped/errors: {skipped_count})...")

    print(f"Finished inserting vertices. Total inserted: {inserted_count}, total skipped/errors: {skipped_count}.")
    return inserted_count

def insert_edges(db, edge_collection_name, vertex_collection_name, triples_df, relations_df):
    """Inserts edges into the specified ArangoDB collection."""
    if not db.has_collection(edge_collection_name):
        print(f"Error: Edge collection '{edge_collection_name}' not found.")
        return 0

    ec = db.collection(edge_collection_name)
    relation_map = pd.Series(relations_df.relation_name.values, index=relations_df.relation_id).to_dict()
    inserted_count = 0
    skipped_count = 0

    print(f"Starting edge insertion into '{edge_collection_name}'...")
    for index, row in triples_df.iterrows():
        subject_id_str = str(row['subject_id'])
        object_id_str = str(row['object_id'])
        relation_id = int(row['relation_id'])
        relation_name = relation_map.get(relation_id, "UNKNOWN_RELATION")

        edge_doc = {
            # ArangoDB will generate _key if not provided or if it needs to be unique
            # "_key": f"{subject_id_str}_{relation_id}_{object_id_str}", # Optional: define your own key
            "_from": f"{vertex_collection_name}/{subject_id_str}",
            "_to": f"{vertex_collection_name}/{object_id_str}",
            "relation_id": relation_id,
            "relation_name": relation_name, # Using 'relation_name' as the attribute key for the name
            "predicate": relation_name # As per notebook example, often 'predicate' is used
        }
        try:
            ec.insert(edge_doc)
            inserted_count += 1
        except DocumentInsertError as e:
            # print(f"Skipping duplicate edge or error for edge from '{edge_doc['_from']}' to '{edge_doc['_to']}': {e}")
            skipped_count +=1
        except Exception as e:
            print(f"Error inserting edge from '{edge_doc['_from']}' to '{edge_doc['_to']}': {e}")
            skipped_count +=1

        if (index + 1) % 1000 == 0:
            print(f"Processed {index + 1} edges (inserted: {inserted_count}, skipped/errors: {skipped_count})...")

    print(f"Finished inserting edges. Total inserted: {inserted_count}, total skipped/errors: {skipped_count}.")
    return inserted_count


def load_graph_from_arangodb_to_networkx(args):
    """Loads graph data from ArangoDB into a NetworkX MultiDiGraph using nx_arangodb."""
    if nxadb is None:
        print("nx_arangodb library is not available (import failed). Skipping NetworkX graph loading.")
        return

    # Populate db_config from args or environment variables
    db_config = {
        'host': os.environ.get("DATABASE_HOST", args.db_host),
        'username': os.environ.get("DATABASE_USERNAME", args.db_username),
        'password': os.environ.get("DATABASE_PASSWORD", args.db_password),
        'db_name': os.environ.get("DATABASE_NAME", args.db_name)
    }
    graph_name_to_load = args.graph_name # The ArangoDB graph name

    print(f"\nAttempting to load graph '{graph_name_to_load}' from ArangoDB into NetworkX...")
    print(f"Using connection: host={db_config['host']}, dbName={db_config['db_name']}, username={db_config['username']}")

    try:
        # Using the pattern from 03_Dynamic_Database.ipynb
        # The MultiDiGraph constructor from nxadb takes these specific parameters
        nx_graph = nxadb.MultiDiGraph(
            name=graph_name_to_load,
            dbName=db_config['db_name'],
            host=db_config['host'],
            username=db_config['username'],
            password=db_config['password']
        )

        # A NetworkX graph object is returned by nxadb.MultiDiGraph.
        # We can check its properties directly.
        # If the graph doesn't exist in ArangoDB or connection fails,
        # nxadb might raise an exception or return an empty/None graph.
        # The original notebook implies it returns a graph object that might be empty.
        if nx_graph is not None: # Check if a graph object was returned
            print(f"Successfully loaded graph '{graph_name_to_load}' into NetworkX object.")
            print(f"Number of nodes in NetworkX graph: {nx_graph.number_of_nodes()}")
            print(f"Number of edges in NetworkX graph: {nx_graph.number_of_edges()}")
            if nx_graph.number_of_nodes() == 0:
                print("Warning: The loaded NetworkX graph has 0 nodes. This might be expected if ArangoDB graph is empty, or it could indicate an issue.")
        else:
            print("Failed to load graph into NetworkX (nx_graph object is None or connection failed before returning).")

    except Exception as e:
        print(f"Error loading graph from ArangoDB to NetworkX: {e}")
        print("Please ensure ArangoDB is running, the graph exists, and connection parameters are correct.")
        print("Also, verify that the nx_arangodb driver is compatible with your ArangoDB version and setup.")


# --- Main Execution ---

def main():
    parser = argparse.ArgumentParser(description="Build ArangoDB graph from CSV files.")
    # ArangoDB connection arguments
    parser.add_argument("--db_host", type=str, default=DEFAULT_DATABASE_HOST, help="ArangoDB host URL.")
    parser.add_argument("--db_username", type=str, default=DEFAULT_DATABASE_USERNAME, help="ArangoDB username.")
    parser.add_argument("--db_password", type=str, default=DEFAULT_DATABASE_PASSWORD, help="ArangoDB password.")
    parser.add_argument("--db_name", type=str, default=DEFAULT_DATABASE_NAME, help="ArangoDB database name.")
    parser.add_argument("--graph_name", type=str, default=DEFAULT_GRAPH_NAME, help="ArangoDB graph name.")
    parser.add_argument("--vertex_collection", type=str, default=DEFAULT_VERTEX_COLLECTION, help="ArangoDB vertex collection name.")
    parser.add_argument("--edge_collection", type=str, default=DEFAULT_EDGE_COLLECTION, help="ArangoDB edge collection name.")

    # CSV input path
    parser.add_argument("--csv_input_path", type=str, default="data/", help="Path to the directory containing CSV files.")
    parser.add_argument("--entities_file", type=str, default="entities_v1.csv", help="Name of the entities CSV file.")
    parser.add_argument("--relations_file", type=str, default="relations_v1.csv", help="Name of the relations CSV file.")
    parser.add_argument("--triples_file", type=str, default="triples_v1.csv", help="Name of the triples CSV file.")

    # Flags
    parser.add_argument(
        "--clear_existing_data",
        action="store_true",
        help="If set, truncates vertex and edge collections before inserting new data."
    )
    parser.add_argument(
        "--load_into_networkx",
        action="store_true",
        help="If set, demonstrates loading the graph from ArangoDB into NetworkX after insertion."
    )
    args = parser.parse_args()

    # Resolve CSV input path relative to the script's directory if it's not absolute
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_input_path = args.csv_input_path
    if not os.path.isabs(csv_input_path):
        csv_input_path = os.path.join(script_dir, csv_input_path)

    print(f"Using CSV input path: {csv_input_path}")

    # Connect to ArangoDB
    db = get_arango_db(args)
    if not db:
        print("Exiting due to database connection failure.")
        return

    # Clear existing data if requested
    if args.clear_existing_data:
        print("Clearing existing graph data as requested...")
        clear_collections(db, args.vertex_collection, args.edge_collection)

    # Load data from CSVs
    print("Loading data from CSV files...")
    entities_df, relations_df, triples_df = load_data_from_csvs(
        csv_input_path, args.entities_file, args.relations_file, args.triples_file
    )
    if entities_df is None:
        print("Exiting due to failure in loading CSV files.")
        return

    # Insert vertices and edges
    if not entities_df.empty:
        insert_vertices(db, args.vertex_collection, entities_df)
    else:
        print("No entities to insert.")

    if not triples_df.empty:
        insert_edges(db, args.edge_collection, args.vertex_collection, triples_df, relations_df)
    else:
        print("No edges/triples to insert.")

    print("\nGraph building process completed.")

    # Demonstrate loading into NetworkX if requested
    if args.load_into_networkx:
        if nxadb: # Check if the module was imported successfully
            load_graph_from_arangodb_to_networkx(args)
        else:
            print("Skipping NetworkX loading demonstration as nx_arangodb (nxadb) is not available.")

    print("Script finished.")

if __name__ == "__main__":
    print("Reminder: This script assumes ArangoDB is running and accessible,")
    print("and that `setup_arangodb.py` has been run to create the database and graph structure.")
    print("It also assumes the CSV files (entities_v1.csv, etc.) exist in the specified input path,")
    print("likely generated by `extract_triplets.py`.\n")
    main()
