#!/usr/bin/env python3
"""
Script to fetch NVIDIA HelpSteer2 dataset from HuggingFace datasets server
and save it as JSONL format.
"""

import json
import requests
import sys

def fetch_helpsteer2_data(offset=0, length=100):
    """
    Fetch HelpSteer2 dataset from HuggingFace datasets server API.
    
    Args:
        offset: Starting position in the dataset
        length: Number of records to fetch
    
    Returns:
        dict: JSON response from the API
    """
    url = "https://datasets-server.huggingface.co/rows"
    params = {
        "dataset": "nvidia/HelpSteer2",
        "config": "default",
        "split": "validation",
        "offset": offset,
        "length": length
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        return None

def save_as_jsonl(data, output_file="helpsteer2_output.jsonl"):
    """
    Save the dataset rows as JSONL (JSON Lines) format.
    
    Args:
        data: Response data from the API
        output_file: Path to the output JSONL file
    """
    if not data or "rows" not in data:
        print("No valid data to save", file=sys.stderr)
        return False
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            for item in data["rows"]:
                # Extract the row data (usually in 'row' field)
                row_data = item.get("row", item)
                # Write each record as a separate JSON line
                json_line = json.dumps(row_data, ensure_ascii=False)
                f.write(json_line + '\n')
        
        print(f"Successfully saved {len(data['rows'])} records to {output_file}")
        return True
    except Exception as e:
        print(f"Error saving file: {e}", file=sys.stderr)
        return False

def main():
    """Main function to fetch and save the dataset."""
    
    # Configuration
    OFFSET = 0
    LENGTH = 100
    OUTPUT_FILE = "helpsteer2_dataset_validation.jsonl"
    
    print(f"Fetching HelpSteer2 dataset (offset={OFFSET}, length={LENGTH})...")
    
    # Fetch the data
    data = fetch_helpsteer2_data(offset=OFFSET, length=LENGTH)
    
    if data:
        # Display some information about the fetched data
        if "rows" in data:
            print(f"Fetched {len(data['rows'])} rows")
            
            # Show the structure of the first row (if available)
            if data["rows"]:
                first_row = data["rows"][0].get("row", data["rows"][0])
                print("\nFirst row fields:")
                for key in first_row.keys():
                    print(f"  - {key}")
        
        # Save as JSONL
        if save_as_jsonl(data, OUTPUT_FILE):
            print(f"\nDataset saved successfully to: {OUTPUT_FILE}")
            
            # Display sample of the saved data
            print("\nSample of saved data (first record):")
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                sample = json.loads(first_line)
                print(json.dumps(sample, indent=2)[:500] + "..." if len(json.dumps(sample)) > 500 else json.dumps(sample, indent=2))
    else:
        print("Failed to fetch data")
        sys.exit(1)

if __name__ == "__main__":
    main()