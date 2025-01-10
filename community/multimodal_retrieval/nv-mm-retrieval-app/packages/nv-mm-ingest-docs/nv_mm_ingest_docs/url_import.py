import requests
from bs4 import BeautifulSoup
import base64
import hashlib
from PIL import Image
from io import BytesIO
from pymongo import MongoClient
from weasyprint import HTML
from pdf2image import convert_from_bytes
import io
import os

from nv_mm_ingest_docs.parse_image import call_api_for_image
from nv_mm_document_qa.chain import chain_metadata

# mongo_host = os.environ["MONGO_HOST"]
# mongo_user = os.environ["MONGO_INITDB_ROOT_USERNAME"]
# mongo_passwd = os.environ["MONGO_INITDB_ROOT_PASSWORD"]

mongo_host = "mongodb"
mongo_user = "admin"
mongo_passwd = "secret"

mongodb_user = os.environ["MONGO_INITDB_ROOT_USERNAME"]
mongodb_password = os.environ["MONGO_INITDB_ROOT_PASSWORD"]
mongodb_port = os.environ["MONGO_PORT"]
client = MongoClient(f'mongodb://{mongodb_user}:{mongodb_password}@mongodb:{mongodb_port}/')  # Adjust as needed

def save_to_mongodb(url, json_data, collection, backend_llm):
    """Save the given JSON data into MongoDB with the MD5 hash of the URL as the _id."""
    # Generate the MD5 hash of the URL to use as the _id for the text document
    url_hash = generate_md5_hash(url)
    document_id = backend_llm + "_" + url_hash

    # Prepare the main document (without images)
    main_document = {
        "_id": document_id,
        "text": json_data['text'],
        "url": url,
        "backend_llm": backend_llm,
        "image_ids": []  # List to store references to image document ids
    }

    # Save images as separate documents
    image_collection = collection.database['images']  # Use a separate collection for images
    for image, description in zip(json_data['images'], json_data['descriptions']):
        image_id = list(image.keys())[0]  # The MD5 hash of the image is the key
        image_data = image[image_id]
        image_description = description[image_id]

        # Create an image document
        image_document = {
            "_id": image_id,
            "image_data": image_data,
            "description": image_description,
            "source_document_id": document_id  # Reference to the parent text document
        }

        # Insert image document into the "images" collection
        image_collection.replace_one(
            {"_id": image_id},
            image_document,
            upsert=True
        )

        # Add image ID to the main document
        main_document['image_ids'].append(image_id)

    # Save the main text document with references to image documents
    collection.replace_one(
        {"_id": document_id},
        main_document,
        upsert=True
    )

    document_metadata = chain_metadata.invoke({"document_id": document_id, "collection_name": collection.name})

    collection.update_one(
        {"_id": document_id},
        {"$set": document_metadata.dict()}
    )

def generate_md5_hash(url):
    """Generate an MD5 hash for the given URL."""
    return hashlib.md5(url.encode('utf-8')).hexdigest()


def is_valid_image_format(img_url):
    """Check if the image URL is a PNG or JPEG format by inspecting the file extension."""
    return any(img_url.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg'])


def change_transparent_to_white(image_data):
    # Open the image from the binary data
    image = Image.open(BytesIO(image_data))

    # Ensure the image is in RGBA mode (which includes alpha for transparency)
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Create a new image with a white background (RGB mode)
    background = Image.new("RGB", image.size, (255, 255, 255))

    # Combine the image with the white background using alpha as a mask
    background.paste(image, mask=image.split()[3])  # Use the alpha channel as mask

    # Convert the image to bytes
    buffer = BytesIO()
    background.save(buffer, format="PNG")
    return buffer.getvalue()


def html_table_to_png(table_html, dpi=300):
    html_content = f"""
    <html>
      <body>
        {table_html}
      </body>
    </html>
    """

    # Convert HTML to PDF in memory
    pdf_bytes = HTML(string=html_content).write_pdf()
    images = convert_from_bytes(pdf_bytes, dpi=dpi)
    image = images[0]
    # Convert PDF to image
    image_io = io.BytesIO()
    image.save(image_io, format='PNG')
    return image_io.getvalue()

def url_to_text_and_images(url, backend_llm):
    """Fetch the URL content, process it, and return the JSON."""

    system_template = """
    Please describe this image in detail.
    """

    response = requests.get(url)

    if response.status_code != 200:
        return {'error': f"Unable to fetch the URL, status code: {response.status_code}"}

    html_content = response.content
    soup = BeautifulSoup(html_content, 'html.parser')

    image_list = []
    description_list = []
    text_content = ""

    # Process <p> tags for text and <img> tags for images
    for elem in soup.find_all(['p', 'img', 'table']):
        if elem.name == 'p':
            p_text = elem.get_text(separator=" ", strip=True)
            if p_text:
                text_content += p_text + "\n\n"

        elif elem.name == 'img':
            img_url = elem.get('src')

            # Check if the 'srcset' attribute exists for the image
            srcset = elem.get('srcset')

            if srcset:
                # Split the srcset into a list of (url, size) tuples
                srcset_images = [s.strip().split(' ') for s in srcset.split(',')]

                # print(srcset_images)
                # Sort the srcset images by the size in descending order and get the largest one
                full_size_url = sorted(srcset_images, key=lambda x: int(x[1][:-1]), reverse=True)[0][0]
                # print(full_size_url)
                # Use the full-size URL
                img_url = full_size_url

            if not img_url.startswith('http'):
                img_url = requests.compat.urljoin(url, img_url)

            if is_valid_image_format(img_url):
                try:
                    img_response = requests.get(img_url)
                    img_data_with_white_bg = change_transparent_to_white(img_response.content)
                    # print(img_response)
                    img_base64 = base64.b64encode(img_data_with_white_bg).decode('utf-8')

                    md5_hash = hashlib.md5(img_base64.encode('utf-8')).hexdigest()
                    image_description = call_api_for_image(img_base64, system_template, backend_llm)

                    text_content += f"![image {md5_hash}][{image_description}]\n\n"

                    image_list.append({md5_hash: img_base64})
                    description_list.append({md5_hash: image_description})

                except Exception as e:
                    print(f"Error processing image {img_url}: {e}")

        elif elem.name == 'table':
            # Process tables
            try:
                print("processing a table")
                table_html = str(elem)
                table_image_data = html_table_to_png(table_html)
                img_base64 = base64.b64encode(table_image_data).decode('utf-8')

                md5_hash = hashlib.md5(img_base64.encode('utf-8')).hexdigest()
                image_description = call_api_for_image(img_base64, system_template, backend_llm)
                print(image_description)

                text_content += f"![image {md5_hash}][{image_description}]\n\n"

                image_list.append({md5_hash: img_base64})
                description_list.append({md5_hash: image_description})

            except Exception as e:
                print(f"Error processing table: {e}")

    result = {
        'text': text_content.strip(),
        'images': image_list,
        'descriptions': description_list,
        'url': url,  # Add the URL to the JSON result
        'backend_llm': backend_llm
    }

    return result


def process_urls_and_save(urls, collection_name, backend_llm):
    """Process a list of URLs and save their processed data to the specified MongoDB collection."""
    # Access the specified collection in MongoDB
    db = client['tme_urls_db']  # Replace with your database name
    collection = db[collection_name]  # Use the input collection name
    all_data = []
    for url in urls:
        print(f"Processing {url}...")
        json_data = url_to_text_and_images(url, backend_llm)
        if 'error' not in json_data:
            save_to_mongodb(url, json_data, collection, backend_llm)
            print(f"Data for {url} saved to MongoDB collection {collection_name}.")
            all_data.append(json_data)
        else:
            print(f"Error processing {url}: {json_data['error']}")
    return {"imported_documents": all_data}


# Example usage:

# urls_list = [
#     "https://developer.nvidia.com/blog/breaking-mlperf-training-records-with-nvidia-h100-gpus/",
#     # "https://developer.nvidia.com/blog/beating-sota-inference-performance-on-nvidia-gpus-with-gpunet/",
#     # "https://developer.nvidia.com/blog/new-mlperf-inference-network-division-showcases-infiniband-and-gpudirect-rdma-capabilities",
#     # "https://developer.nvidia.com/blog/setting-new-records-in-mlperf-inference-v3-0-with-full-stack-optimizations-for-ai"
# ]
#
# collection_name = "test-tables"  # Specify the MongoDB collection name
# process_urls_and_save(urls_list, collection_name, "nvidia")
