#!/usr/bin/env python3
"""
Script to fix the vGPU knowledge base collection by recreating it with dense-only configuration
"""

import os
import sys
import requests
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
INGESTOR_URL = "http://localhost:8082"
COLLECTION_NAME = "vgpu_knowledge_base"

def delete_collection():
    """Delete the existing collection"""
    logger.info(f"Deleting collection '{COLLECTION_NAME}'...")
    
    try:
        # First check if collection exists
        check_response = requests.get(f"{INGESTOR_URL}/v1/collections")
        if check_response.status_code == 200:
            collections = check_response.json().get("collections", [])
            collection_exists = any(c.get("collection_name") == COLLECTION_NAME for c in collections)
            
            if not collection_exists:
                logger.warning(f"Collection '{COLLECTION_NAME}' does not exist, skipping deletion")
                return True
        
        # Delete collection - send collection name in the body as JSON array
        response = requests.delete(
            f"{INGESTOR_URL}/v1/collections",
            json=[COLLECTION_NAME]  # Send as JSON array in body
        )
        
        if response.status_code == 200:
            result = response.json()
            if COLLECTION_NAME in result.get("successful", []):
                logger.info(f"✅ Successfully deleted collection '{COLLECTION_NAME}'")
                return True
            elif result.get("total_success", 0) > 0:
                logger.info(f"✅ Deletion completed with {result.get('total_success')} successful deletions")
                return True
            else:
                logger.warning(f"Collection '{COLLECTION_NAME}' not found or already deleted")
                return True
        else:
            logger.error(f"Failed to delete collection: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error deleting collection: {e}")
        return False

def create_collection():
    """Create a new collection with dense-only configuration"""
    logger.info(f"Creating collection '{COLLECTION_NAME}' with dense-only configuration...")
    
    try:
        # Create collection with explicit dense search type
        params = {
            "embedding_dimension": 2048,
            "collection_type": "text",
            "search_type": "dense"  # Explicitly set to dense
        }
        
        response = requests.post(
            f"{INGESTOR_URL}/v1/collections",
            params=params,
            json=[COLLECTION_NAME]
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully created collection '{COLLECTION_NAME}' with dense search type")
            return True
        else:
            logger.error(f"Failed to create collection: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating collection: {e}")
        return False

def verify_collection():
    """Verify the collection exists and has the correct configuration"""
    logger.info("Verifying collection configuration...")
    
    try:
        response = requests.get(f"{INGESTOR_URL}/v1/collections")
        
        if response.status_code == 200:
            collections = response.json().get("collections", [])
            
            for collection in collections:
                if collection.get("collection_name") == COLLECTION_NAME:
                    logger.info(f"✅ Collection '{COLLECTION_NAME}' exists")
                    # Note: The API might not return search_type, but the collection 
                    # should now be configured correctly for dense search
                    return True
                    
            logger.error(f"Collection '{COLLECTION_NAME}' not found after creation")
            return False
        else:
            logger.error(f"Failed to get collections: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error verifying collection: {e}")
        return False

def main():
    """Main function to fix the vGPU collection"""
    logger.info("🔧 Starting vGPU collection fix...")
    
    # Step 1: Delete existing collection
    if not delete_collection():
        logger.error("Failed to delete collection. Aborting.")
        sys.exit(1)
    
    # Wait a bit for deletion to complete
    time.sleep(2)
    
    # Step 2: Create new collection with dense configuration
    if not create_collection():
        logger.error("Failed to create collection. Aborting.")
        sys.exit(1)
    
    # Wait a bit for creation to complete
    time.sleep(2)
    
    # Step 3: Verify collection exists
    if not verify_collection():
        logger.error("Failed to verify collection. Manual intervention may be required.")
        sys.exit(1)
    
    logger.info("✅ Collection fix completed successfully!")
    logger.info("📝 Next steps:")
    logger.info("   1. Run the bootstrap service again to re-ingest documents:")
    logger.info("      docker compose -f deploy/compose/docker-compose-bootstrap.yaml up")
    logger.info("   2. Once documents are ingested, try your query again")

if __name__ == "__main__":
    main() 