import os
import uvicorn
from fastapi import BackgroundTasks, FastAPI, UploadFile, WebSocket, WebSocketDisconnect, APIRouter, File
from fastapi.responses import JSONResponse
from fastapi import File, UploadFile
from fastapi.responses import PlainTextResponse
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pymongo import MongoClient
from bson import ObjectId
import base64
from fastapi.responses import Response
from pymongo import MongoClient
from bson.objectid import ObjectId


router = APIRouter()
# app = FastAPI(title="Riva as a service")



# Initialize FastAPI app
app = FastAPI()

mongodb_user = os.environ["MONGO_INITDB_ROOT_USERNAME"]
mongodb_password = os.environ["MONGO_INITDB_ROOT_PASSWORD"]
mongodb_port = os.environ["MONGO_PORT"]
client = MongoClient(f'mongodb://{mongodb_user}:{mongodb_password}@mongodb:{mongodb_port}/')  # Adjust as needed

# MongoDB connection setup
db = client['tme_urls_db']  # Replace with your database name


def get_base64_image(image_collection_name, image_id):
    """Retrieve the base64-encoded image from the images collection by its image ID."""
    image_collection = db[image_collection_name]  # Access the specified image collection

    try:
        # Find the image document by its _id (image_id)
        image_document = image_collection.find_one({"_id": image_id})

        if image_document:
            # Return the base64-encoded image from the image document, and None for the error
            return image_document.get('image_data'), None

        # If no document is found with the given image_id
        return None, f"No image document found with ID: {image_id}"

    except Exception as e:
        # If there's an error, return None for the image and the error message
        return None, f"An error occurred: {e}"

@router.get("/image/{collection_name}/{document_id}/{image_id}")
async def get_image(collection_name: str, document_id: str, image_id: str):
    # Retrieve the Base64 image using the provided function
    image_collection_name = "images"
    base64_image, error_message = get_base64_image(image_collection_name, image_id)

    if error_message:
        raise HTTPException(status_code=404, detail=error_message)

    try:
        # Decode the Base64 image data to bytes
        image_bytes = base64.b64decode(base64_image)

        # Return the image as raw bytes in the response
        return Response(content=image_bytes)

    except Exception as e:
        raise HTTPException(status_code=500, detail="Invalid image format")


# Endpoint to return health of the application
@router.get("/v1/health")
async def health():
    # response = await asr.get_health()
    # if response.status == health_pb2.HealthCheckResponse.SERVING:
    return "Riva service is healthy"
    # else:
    #     return "Riva service is not healthy"


if __name__ == "__main__":
    uvicorn.run("main:app", host='0.0.0.0', port=8000, reload=True)
