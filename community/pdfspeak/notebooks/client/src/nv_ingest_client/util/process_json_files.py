import json

import click


def ingest_json_results_to_blob(result_content):
    """
    Parse a JSON string or BytesIO object, combine and sort entries, and create a blob string.

    Returns:
        str: The generated blob string.
    """
    try:
        # Load the JSON data
        data = json.loads(result_content) if isinstance(result_content, str) else result_content

        # Smarter sorting: by page, then structured objects by x0, y0
        def sorting_key(entry):
            page = entry["metadata"]["content_metadata"]["page_number"]
            if entry["document_type"] == "structured":
                # Use table location's x0 and y0 as secondary keys
                x0 = entry["metadata"]["table_metadata"]["table_location"][0]
                y0 = entry["metadata"]["table_metadata"]["table_location"][1]
            else:
                # Non-structured objects are sorted after structured ones
                x0 = float("inf")
                y0 = float("inf")
            return page, x0, y0

        data.sort(key=sorting_key)

        # Initialize the blob string
        blob = []

        for entry in data:
            document_type = entry.get("document_type", "")

            if document_type == "structured":
                # Add table content to the blob
                blob.append(entry["metadata"]["table_metadata"]["table_content"])
                blob.append("\n")

            elif document_type == "text":
                # Add content to the blob
                blob.append(entry["metadata"]["content"])
                blob.append("\n")

            elif document_type == "image":
                # Add image caption to the blob
                caption = entry["metadata"]["image_metadata"].get("caption", "")
                blob.append(f"image_caption:[{caption}]")
                blob.append("\n")

        # Join all parts of the blob into a single string
        return "".join(blob)

    except Exception as e:
        print(f"[ERROR] An error occurred while processing JSON content: {e}")
        return ""


@click.command()
@click.argument("json_files", type=click.Path(exists=True), nargs=-1, required=True)
@click.option(
    "--output-file",
    type=click.Path(dir_okay=False, writable=True, resolve_path=True),
    required=True,
    help="Path to save the combined blob output file.",
)
def main(json_files, output_file):
    """
    Process multiple JSON files, combine and sort entries, and generate a single blob file.

    JSON_FILES: One or more JSON files to process.
    """
    click.echo(f"Processing {len(json_files)} JSON files...")
    all_entries = []

    try:
        # Read and collect entries from all files
        for json_file in json_files:
            click.echo(f"Reading file: {json_file}")
            with open(json_file, "r") as file:
                content = file.read()
                all_entries.extend(json.loads(content))

        # Convert collected entries to JSON string
        combined_content = json.dumps(all_entries)

        # Generate the blob string
        blob_string = ingest_json_results_to_blob(combined_content)

        if blob_string:
            # Write the blob to the output file
            with open(output_file, "w+") as file:
                file.write(blob_string)
            click.echo(f"Blob string has been generated and saved to: {output_file}")
        else:
            click.echo("No valid data processed. Blob file not created.")

    except Exception as e:
        click.echo(f"[ERROR] An error occurred: {e}")


if __name__ == "__main__":
    main()
