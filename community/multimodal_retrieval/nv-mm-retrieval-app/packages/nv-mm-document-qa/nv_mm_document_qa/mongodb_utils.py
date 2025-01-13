from pymongo import MongoClient
from bson.objectid import ObjectId
import os

mongo_host = os.environ["MONGO_HOST"]
mongo_user = os.environ["MONGO_INITDB_ROOT_USERNAME"]
mongo_passwd = os.environ["MONGO_INITDB_ROOT_PASSWORD"]

# MongoDB connection setup
client = MongoClient(f'mongodb://{mongo_user}:{mongo_passwd}@{mongo_host}:27017/')  # Adjust as needed
print(mongo_host, mongo_user, mongo_passwd)
db = client['tme_urls_db']  # Replace with your database name
# collection = db['tme_docs']  # Replace with your collection name

def load_document_by_id(collection_name, document_id):
    """Load a MongoDB document by its _id from a specific collection."""
    collection = db[collection_name]  # Access the specified collection

    try:
        # Try to find the document using its _id
        document = collection.find_one({"_id": document_id})

        if document:
            return document
        else:
            return f"No document found with _id: {document_id}"

    except Exception as e:
        return f"An error occurred: {e}"

def merge_documents(collection_name, best_documents):
    markdown_string = ""
    for b_doc_id in best_documents:
        b_doc_md = load_document_by_id(collection_name, b_doc_id)

        # Append the document ID as a header (##) and the summary as body
        markdown_string += f"# {b_doc_id}\n{b_doc_md}\n\n"  # Two newlines act as a separator
    return markdown_string


def get_base64_image(image_collection_name, image_id):
    """Retrieve the base64-encoded image from the images collection by its image ID."""
    # Access the 'images' collection in MongoDB
    image_collection = db[image_collection_name]  # Access the specified image collection

    try:
        # Find the image document by its _id (image_id)
        image_document = image_collection.find_one({"_id": image_id})

        if image_document:
            # Return the base64-encoded image from the image document
            print("Found the image!")
            return image_document.get('image_data', f"No base64 image data found for image ID: {image_id}")

        # If no document is found with the given image_id
        return f"No image document found with ID: {image_id}"

    except Exception as e:
        return f"An error occurred: {e}"


# def get_base64_image(collection_name, document_id, image_id):
#     """Retrieve the base64-encoded image from a MongoDB document by its _id and image ID."""
#     collection = db[collection_name]  # Access the specified collection
#
#     try:
#         # Convert document_id to ObjectId if needed
#         # If your document_id is a string or already an ObjectId, you can use it directly
#         print(f"Collection Name: {collection_name}")
#         print(f"Document Identifier: {document_id}")
#         print(f"Image Indentifier: {image_id}")
#
#         document_id = ObjectId(document_id) if ObjectId.is_valid(document_id) else document_id
#
#         # Find the document by its _id
#         document = collection.find_one({"_id": document_id})
#
#         if document:
#             # Assuming images are stored as a list of dictionaries in the 'images' field
#             for image in document.get('images', []):
#                 if image_id in image:
#                     # Return the base64-encoded image
#                     return image[image_id]
#
#             # If the image_id is not found in the document
#             return f"No image found with ID: {image_id} in document {document_id}"
#         else:
#             return f"No document found with _id: {document_id}"
#
#     except Exception as e:
#         return f"An error occurred: {e}"


def get_document_summaries_markdown(collection_name):
    """
    This function retrieves all documents from the given collection that have a 'summary' field
    and returns a markdown-formatted string of document IDs as headers and their summaries as the body.

    Args:
    collection_name (str): The name of the MongoDB collection.

    Returns:
    str: A markdown-formatted string containing document IDs as headers and summaries as the body.
    """

    # Replace this with your MongoDB connection string
    collection = db[collection_name]

    # Query for documents that contain a 'summary' field
    documents = collection.find({"summary": {"$exists": True}})

    # Initialize an empty string to store the result
    markdown_string = ""

    # Loop through the documents
    for document in documents:
        document_id = document.get('_id')
        summary = document.get('summary', 'No summary available')

        # Append the document ID as a header (##) and the summary as body
        markdown_string += f"## {document_id}\n{summary}\n\n"  # Two newlines act as a separator

    return markdown_string

# Example usage:
# markdown_output = get_document_summaries_markdown('your_collection_name')
# print(markdown_output)
