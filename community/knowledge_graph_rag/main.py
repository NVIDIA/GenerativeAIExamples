import argparse
import subprocess
import sys
import os

# Get the directory where main.py is located to find other scripts
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

def run_script(script_name: str, arguments_list: list = None):
    """
    Runs a Python script using the current Python interpreter.
    Args:
        script_name: The name of the script (e.g., "setup_arangodb.py").
        arguments_list: A list of command-line arguments to pass to the script.
    Returns:
        True if the script ran successfully, False otherwise.
    """
    if arguments_list is None:
        arguments_list = []

    full_script_path = os.path.join(SCRIPT_DIR, script_name)
    command = [sys.executable, full_script_path] + arguments_list

    print(f"\nRunning script: {script_name} with arguments: {' '.join(arguments_list)}")
    print(f"Full command: {' '.join(command)}")

    try:
        result = subprocess.run(command, check=True, text=True, capture_output=False) # stdout/stderr directly to console
        print(f"Script {script_name} completed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running script {script_name}:")
        print(f"Return code: {e.returncode}")
        # Output was already printed to console if capture_output=False
        # If capture_output=True:
        # print(f"Stdout: {e.stdout}")
        # print(f"Stderr: {e.stderr}")
        return False
    except FileNotFoundError:
        print(f"Error: Script {full_script_path} not found.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Main orchestrator for the Knowledge Graph RAG pipeline.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands", required=True)

    # --- setup ---
    parser_setup = subparsers.add_parser("setup", help="Run setup_arangodb.py to initialize the database.")
    # No arguments for setup for now, as setup_arangodb.py uses environment variables or defaults.

    # --- extract ---
    parser_extract = subparsers.add_parser("extract", help="Run extract_triplets.py to extract triplets from documents.")
    parser_extract.add_argument("--input_dir", type=str, help="Directory for input JSON files for triplet extraction.")
    parser_extract.add_argument("--output_dir", type=str, help="Directory to save individual triplet JSON outputs.")
    parser_extract.add_argument("--csv_output_path", type=str, help="Directory to save consolidated CSV files from extraction.")
    parser_extract.add_argument("--llm_model", type=str, help="LLM model for triplet extraction.")
    parser_extract.add_argument("--api_key", type=str, help="NVIDIA API Key for triplet extraction.")

    # --- build ---
    parser_build = subparsers.add_parser("build", help="Run build_graph.py to build the graph in ArangoDB from CSVs.")
    parser_build.add_argument("--csv_input_path", type=str, help="Path to the directory containing CSV files for graph building.")
    parser_build.add_argument("--clear_existing_data", action="store_true", help="Clear existing graph data before building.")
    # ArangoDB connection args for build_graph.py can be passed if needed, or rely on its defaults/env vars.
    # For simplicity, we'll assume build_graph.py handles its own DB connection details for now.

    # --- query ---
    parser_query = subparsers.add_parser("query", help="Run query_knowledge_graph.py to query the graph.")
    parser_query.add_argument("--llm_model", type=str, help="LLM model for querying.")
    parser_query.add_argument("--api_key", type=str, help="NVIDIA API Key for querying.")
    # ArangoDB connection args for query_knowledge_graph.py can be passed if needed.

    # --- all (setup, extract, build) ---
    parser_all = subparsers.add_parser("all", help="Run the full pipeline: setup, extract, then build.")
    # Arguments for extract part of 'all'
    parser_all.add_argument("--input_dir", type=str, help="Input dir for 'extract' step.")
    parser_all.add_argument("--output_dir", type=str, help="Output dir for 'extract' step (individual JSONs).")
    parser_all.add_argument("--csv_output_path", type=str, help="CSV output path for 'extract' step (becomes input for 'build').")
    parser_all.add_argument("--extract_llm_model", type=str, help="LLM model for 'extract' step.") # Renamed to avoid clash
    parser_all.add_argument("--extract_api_key", type=str, help="NVIDIA API Key for 'extract' step.") # Renamed

    # Arguments for build part of 'all'
    # --csv_input_path for build will typically be the --csv_output_path from extract.
    # We can make this implicit or explicit. Let's make it implicit for 'all'.
    parser_all.add_argument("--clear_existing_data", action="store_true", help="Clear existing graph data before 'build' step.")


    args = parser.parse_args()
    print(f"Executing command: {args.command}")

    success = True # Track overall success
    if args.command == "setup":
        if not run_script("setup_arangodb.py"):
            success = False

    elif args.command == "extract":
        extract_args_list = []
        if args.input_dir: extract_args_list.extend(["--input_dir", args.input_dir])
        if args.output_dir: extract_args_list.extend(["--output_dir", args.output_dir])
        if args.csv_output_path: extract_args_list.extend(["--csv_output_path", args.csv_output_path])
        if args.llm_model: extract_args_list.extend(["--llm_model", args.llm_model])
        if args.api_key: extract_args_list.extend(["--api_key", args.api_key])
        if not run_script("extract_triplets.py", extract_args_list):
            success = False

    elif args.command == "build":
        build_args_list = []
        if args.csv_input_path: build_args_list.extend(["--csv_input_path", args.csv_input_path])
        if args.clear_existing_data: build_args_list.append("--clear_existing_data")
        if not run_script("build_graph.py", build_args_list):
            success = False

    elif args.command == "query":
        query_args_list = []
        if args.llm_model: query_args_list.extend(["--llm_model", args.llm_model])
        if args.api_key: query_args_list.extend(["--api_key", args.api_key])
        # If query_knowledge_graph.py needs DB args, add them here
        if not run_script("query_knowledge_graph.py", query_args_list):
            success = False

    elif args.command == "all":
        print("--- Running 'setup' stage ---")
        if not run_script("setup_arangodb.py"):
            print("Setup stage failed. Aborting 'all' command.")
            success = False # Mark as failed

        if success: # Only proceed if previous step succeeded
            print("\n--- Running 'extract' stage ---")
            extract_args_list_all = []
        # Use defaults from extract_triplets.py if not provided in 'all'
        # Or, require them for 'all' / set specific defaults for 'all'
        # For now, pass if provided:
        default_csv_path_for_all = os.path.join(SCRIPT_DIR, "data/") # Default if not overridden

        csv_output_path_for_extract = args.csv_output_path if args.csv_output_path else default_csv_path_for_all

        if args.input_dir: extract_args_list_all.extend(["--input_dir", args.input_dir])
        if args.output_dir: extract_args_list_all.extend(["--output_dir", args.output_dir])
        extract_args_list_all.extend(["--csv_output_path", csv_output_path_for_extract]) # Ensure this is passed
        if args.extract_llm_model: extract_args_list_all.extend(["--llm_model", args.extract_llm_model])
        if args.extract_api_key: extract_args_list_all.extend(["--api_key", args.extract_api_key])

            if not run_script("extract_triplets.py", extract_args_list_all):
                print("Extract stage failed. Aborting 'all' command.")
                success = False # Mark as failed

        if success: # Only proceed if previous step succeeded
            print("\n--- Running 'build' stage ---")
            build_args_list_all = []
            # build_graph.py's --csv_input_path should be extract_triplets.py's --csv_output_path
            build_args_list_all.extend(["--csv_input_path", csv_output_path_for_extract])
            if args.clear_existing_data: build_args_list_all.append("--clear_existing_data")

            if not run_script("build_graph.py", build_args_list_all):
                print("Build stage failed.")
                success = False # Mark as failed

        if success:
            print("\n'all' command completed setup, extract, and build stages successfully.")
        else:
            print("\n'all' command failed at some stage.")

    if not success:
        print("\nOne or more stages reported errors.")
        sys.exit(1) # Exit main.py with error code if any stage failed

if __name__ == "__main__":
    main()
