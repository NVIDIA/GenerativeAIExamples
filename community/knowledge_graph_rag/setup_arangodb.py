import os
from arango import ArangoClient

# Default ArangoDB connection parameters
DEFAULT_DATABASE_HOST = "http://localhost:8529"
DEFAULT_DATABASE_USERNAME = "root"
DEFAULT_DATABASE_PASSWORD = ""  # Replace with your default password if any
DEFAULT_DATABASE_NAME = "knowledge_graph_db"

# Override defaults with environment variables if set
DATABASE_HOST = os.environ.get("DATABASE_HOST", DEFAULT_DATABASE_HOST)
DATABASE_USERNAME = os.environ.get("DATABASE_USERNAME", DEFAULT_DATABASE_USERNAME)
DATABASE_PASSWORD = os.environ.get("DATABASE_PASSWORD", DEFAULT_DATABASE_PASSWORD)
DATABASE_NAME = os.environ.get("DATABASE_NAME", DEFAULT_DATABASE_NAME)

def setup_arangodb():
    """
    Sets up the ArangoDB database, graph, and collections.
    """
    try:
        # Establish a connection to the ArangoDB client
        client = ArangoClient(hosts=DATABASE_HOST)
        print(f"Successfully connected to ArangoDB client at {DATABASE_HOST}")

        # Connect to the _system database to manage database creation
        sys_db = client.db("_system", username=DATABASE_USERNAME, password=DATABASE_PASSWORD)
        print("Connected to _system database.")

        # Check if the target database exists. If not, create it.
        if not sys_db.has_database(DATABASE_NAME):
            sys_db.create_database(DATABASE_NAME)
            print(f"Database '{DATABASE_NAME}' created.")
        else:
            print(f"Database '{DATABASE_NAME}' already exists.")

        # Connect to the target database
        db = client.db(DATABASE_NAME, username=DATABASE_USERNAME, password=DATABASE_PASSWORD)
        print(f"Connected to database '{DATABASE_NAME}'.")

        # Check if the graph ('graph_data') exists. If not, create it.
        if not db.has_graph("graph_data"):
            graph = db.create_graph("graph_data")
            print("Graph 'graph_data' created.")
        else:
            graph = db.graph("graph_data")
            print("Graph 'graph_data' already exists.")

        # Check if the vertex collection ('vertices') exists within the graph.
        # If not, create it.
        if not graph.has_vertex_collection("vertices"):
            graph.create_vertex_collection("vertices")
            print("Vertex collection 'vertices' created in graph 'graph_data'.")
        else:
            print("Vertex collection 'vertices' already exists in graph 'graph_data'.")

        # Check if the edge collection ('edges') and its definition exist.
        # If not, create it with 'vertices' as both from and to collections.
        if not graph.has_edge_collection("edges"):
            # Define the edge definition
            edge_definition = {
                "edge_collection": "edges",
                "from_vertex_collections": ["vertices"],
                "to_vertex_collections": ["vertices"],
            }
            graph.create_edge_definition(**edge_definition)
            print("Edge collection 'edges' and its definition created in graph 'graph_data'.")
        else:
            print("Edge collection 'edges' already exists in graph 'graph_data'.")

        print("ArangoDB setup completed successfully.")

    except Exception as e:
        print(f"An error occurred during ArangoDB setup: {e}")
        sys.exit(1) # Exit with error code

if __name__ == "__main__":
    import sys # Make sure sys is imported
    setup_arangodb()
