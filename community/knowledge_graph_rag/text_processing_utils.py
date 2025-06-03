import re
import unicodedata
import json
import ast

# --- Text Processing Helper Functions ---

def preprocess_json_content(json_content: str) -> str:
    """
    Cleans up common escape sequences and formatting issues in JSON-like text.
    """
    # Replace common escape sequences
    json_content = json_content.replace("\\n", " ")
    json_content = json_content.replace("\\t", " ")
    json_content = json_content.replace("\\u201c", '"').replace("\\u201d", '"')
    json_content = json_content.replace("\\u2018", "'").replace("\\u2019", "'")
    json_content = json_content.replace("\\u2013", "-").replace("\\u2014", "--")
    json_content = json_content.replace("\\u00a0", " ")  # Non-breaking space
    # Remove extra whitespace
    json_content = re.sub(r'\s+', ' ', json_content).strip()
    return json_content

def preprocess_text(text: str, company_name: str) -> str:
    """
    Basic text cleaning: normalizes unicode, removes excessive newlines/tabs,
    and replaces company name with a placeholder.
    """
    if not isinstance(text, str):
        return ""
    text = unicodedata.normalize('NFKC', text)
    text = re.sub(r"(\n){2,}", "\n", text)
    text = re.sub(r"(\t){2,}", "\t", text)
    text = text.replace(company_name, "the company")
    text = text.lower() # Convert to lowercase
    text = re.sub(r'[^\x00-\x7F]+', ' ', text) # Remove non-ASCII characters
    return text

def process_response(triplets_str: str, section_name: str = "Unknown Section") -> list:
    """
    Parses the LLM's string output (expected to be a Python list of lists/tuples)
    into a list of triplets.
    """
    if not triplets_str or triplets_str.strip() == "None":
        return []
    try:
        # The output is often a string representation of a list of lists
        # We need to evaluate it safely.
        # First, try to directly parse as JSON if it's a valid JSON array string
        try:
            # Ensure the string is a valid list format (e.g. by replacing single quotes if necessary)
            # and that it's properly formed.
            processed_str = triplets_str.strip()
            if not processed_str.startswith('[') or not processed_str.endswith(']'):
                 # Attempt to fix if it's not a list but contains list-like content
                if '[' in processed_str and ']' in processed_str:
                    processed_str = '[' + processed_str.split('[', 1)[1].rsplit(']', 1)[0] + ']'
                else: # If no clear list structure, assume it's not parseable
                    print(f"Warning: Response for section '{section_name}' is not in the expected list format: {triplets_str}")
                    return []

            # Replace common problematic patterns from LLM output
            processed_str = processed_str.replace("'", '"') # Replace single with double quotes for JSON
            # Attempt to fix legitimate apostrophes misinterpreted as quotes, e.g. "company's" becoming "company"s"
            # This regex looks for a word character, a quote, and another word character.
            processed_str = re.sub(r'(\w)"(\w)', r"\1'\2", processed_str)


            triplets_list = json.loads(processed_str)
        except json.JSONDecodeError:
            # If JSON parsing fails, fall back to ast.literal_eval as a safer alternative to eval
            # This handles Python list/tuple string representations
            try:
                triplets_list = ast.literal_eval(triplets_str)
            except (ValueError, SyntaxError) as e:
                print(f"Warning: Could not parse response for section '{section_name}': {e}. Response: {triplets_str}")
                return []

        # Validate and clean the triplets
        valid_triplets = []
        if isinstance(triplets_list, list):
            for item in triplets_list:
                if isinstance(item, (list, tuple)) and len(item) == 3:
                    # Further clean each element of the triplet
                    subject = str(item[0]).strip().lower()
                    predicate = str(item[1]).strip().lower()
                    obj = str(item[2]).strip().lower()
                    if subject and predicate and obj: # Ensure no empty strings
                         valid_triplets.append((subject, predicate, obj))
                else:
                    print(f"Warning: Invalid triplet format in section '{section_name}': {item}")
        else:
            print(f"Warning: Parsed response for section '{section_name}' is not a list: {triplets_list}")
            return []

        return valid_triplets

    except Exception as e:
        print(f"Error processing LLM response for section '{section_name}': {e}. Response: {triplets_str}")
        return []
