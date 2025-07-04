# SPDX-FileCopyrightText: Copyright (c) 2023-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Copyright (c) 2023-2025, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from typing import List, Dict, Any
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
import logging
import re
from multiprocessing import Queue
from config.config_loader import config_loader
import torch
# Simple text splitter implementation

# Load configurations
logger = logging.getLogger(__name__)
logger.info("Loading configurations for RAG service...")
rag_config = config_loader.get_rag_config()
app_config = config_loader.get_app_config()
logger.info(f"Loaded RAG config: {rag_config}")
logger.info(f"Loaded app config: {app_config}")

# Configure logging
logging.basicConfig(
    level=getattr(logging, rag_config['logging']['level']),
    format=rag_config['logging']['format']
)

class RAGService:
    def __init__(self):
        """Initialize RAG service with configuration from YAML"""
        model_config = rag_config['model']
        text_config = rag_config['text_processing']
        processing_config = rag_config['processing']
        search_config = rag_config['search']
        
        logger.info(f"Initializing RAG service with model: {model_config['name']}")
        logger.info(f"Using model dimension: {model_config['dimension']}")
        logger.info(f"Using chunk size: {text_config['chunk_size']}, overlap: {text_config['chunk_overlap']}")
        logger.info(f"Using batch size: {processing_config['batch_size']}, max workers: {processing_config['max_workers']}")
        
        # Initialize the model with proper configuration
        self.model = SentenceTransformer(
            model_config['name'],
            device='cpu'  # Force CPU to avoid MPS/CUDA issues
        )
        self.query_instruction = search_config.get('query_instruction', "Represent this sentence for searching relevant passages: ")
        
        self.index = None
        self.documents = []
        self.metadata = []  # Store metadata for each document
        self.dimension = model_config['dimension']
        self.chunk_size = text_config['chunk_size']
        self.chunk_overlap = text_config['chunk_overlap']
        self.min_chunk_words = text_config['min_chunk_words']
        self.batch_size = processing_config['batch_size']  # Get batch size from config
        self.max_workers = processing_config['max_workers']  # Get max workers from config
        self.search_multiplier = search_config.get('deduplication_multiplier', 2)  # Get search multiplier from config
        
        # Initialize text splitter configuration
        self.separators = text_config.get('separators', ["\n\n", "\n", ". ", "! ", "? ", ", ", " "])
        
        # Create index if it doesn't exist
        if not self.index:
            self.create_index()
        
    def create_index(self):
        """Create a new FAISS index"""
        logger.info("Creating new FAISS index")
        # Use L2 distance for normalized vectors (equivalent to cosine similarity)
        self.index = faiss.IndexFlatL2(self.dimension)
        self.documents = []  # Clear documents when creating new index
        self.metadata = []  # Clear metadata when creating new index
        logger.info("Cleared documents and metadata lists")
        
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks using simple implementation"""
        # Clean the text
        text = re.sub(r'\s+', ' ', text).strip()
        
        if len(text) <= self.chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            # Find the end of the current chunk
            end = start + self.chunk_size
            
            if end >= len(text):
                # Last chunk
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break
            
            # Try to find a good break point
            best_break = end
            for separator in self.separators:
                # Look for the separator in the overlap region
                overlap_start = max(start, end - self.chunk_overlap)
                pos = text.rfind(separator, overlap_start, end)
                if pos > start:
                    best_break = pos + len(separator)
                    break
            
            # Extract the chunk
            chunk = text[start:best_break].strip()
            if chunk:
                chunks.append(chunk)
            
            # Move to next chunk with overlap
            start = max(start + 1, best_break - self.chunk_overlap)
        
        logger.info(f"Created {len(chunks)} chunks from text")
        return chunks
        
    def add_documents(self, documents: List[str], metadata: List[Dict[str, Any]] = None, job_queue: Queue = None):
        """Add documents to the index with progress tracking"""
        try:
            if not self.index:
                self.create_index()
            
            if metadata is None:
                metadata = [{} for _ in documents]
            
            total_docs = len(documents)
            total_chunks = 0
            processed_chunks = 0
            batch_size = self.batch_size
            
            # Process each document into chunks
            all_chunks = []
            all_metadata = []
            
            for doc, meta in zip(documents, metadata):
                # Split document into chunks
                doc_chunks = self.chunk_text(doc)
                # Create metadata for each chunk
                for chunk in doc_chunks:
                    chunk_meta = meta.copy()
                    chunk_meta["chunk_text"] = chunk
                    all_chunks.append(chunk)
                    all_metadata.append(chunk_meta)
            
            total_chunks_to_process = len(all_chunks)
            logger.info(f"Total chunks to process: {total_chunks_to_process}")
            
            # Send initial progress
            if job_queue:
                job_queue.put({
                    "type": "processing",
                    "stage": "start",
                    "total_chunks": total_chunks_to_process,
                    "processed_chunks": 0,
                    "current_document": 0,
                    "total_documents": total_docs,
                    "current_batch": 0,
                    "total_batches": 0
                })
            
            # Process chunks in batches
            total_batches = (len(all_chunks) + batch_size - 1) // batch_size
            logger.info(f"Processing {len(all_chunks)} chunks in {total_batches} batches")
            
            for batch_start in range(0, len(all_chunks), batch_size):
                batch_end = min(batch_start + batch_size, len(all_chunks))
                batch = all_chunks[batch_start:batch_end]
                batch_metadata = all_metadata[batch_start:batch_end]
                current_batch = batch_start // batch_size + 1
                
                # Generate embeddings for batch
                embeddings = self.model.encode(batch)
                
                # Normalize embeddings for cosine similarity
                faiss.normalize_L2(embeddings)
                
                # Add embeddings to FAISS index
                self.index.add(np.array(embeddings).astype('float32'))
                
                # Store original chunks and their metadata
                self.documents.extend(batch)
                self.metadata.extend(batch_metadata)
                processed_chunks += len(batch)
                total_chunks = len(self.documents)
                
                # Calculate progress percentage
                progress_percent = (processed_chunks / total_chunks_to_process) * 100
                
                # Send progress update after each batch
                if job_queue:
                    job_queue.put({
                        "type": "processing",
                        "stage": "progress",
                        "total_chunks": total_chunks_to_process,
                        "processed_chunks": processed_chunks,
                        "current_document": total_docs,
                        "total_documents": total_docs,
                        "current_batch": current_batch,
                        "total_batches": total_batches,
                        "progress_percent": progress_percent
                    })
                
                logger.info(f"Processed batch {current_batch}/{total_batches}")
            
            # Send completion
            if job_queue:
                job_queue.put({
                    "type": "processing",
                    "stage": "complete",
                    "total_chunks": total_chunks,
                    "processed_chunks": processed_chunks,
                    "progress_percent": 100,
                    "current_document": total_docs,
                    "total_documents": total_docs,
                    "current_batch": total_batches,
                    "total_batches": total_batches
                })
            
            logger.info(f"Completed processing {total_chunks} chunks")
        except Exception as e:
            logger.error(f"Error adding documents: {str(e)}")
            if job_queue:
                job_queue.put({
                    "type": "error",
                    "message": str(e)
                })
            raise
        
    def get_document_count(self) -> int:
        """Get the current number of chunks in the index"""
        count = len(self.documents)
        logger.info(f"Current chunk count: {count}")
        return count

    def get_unique_document_count(self) -> int:
        """Get the number of unique source documents in the index"""
        # Get all source files from metadata
        source_files = []
        for meta in self.metadata:
            source_file = meta.get("source_file")
            if source_file and isinstance(source_file, str) and source_file.strip():
                source_files.append(source_file)
        
        # Count unique source files
        unique_docs = set(source_files)
        count = len(unique_docs)
        logger.info(f"Current unique document count: {count} (from {len(source_files)} total source files)")
        return count
        
    def clear(self):
        """Clear the index and documents"""
        logger.info("Clearing RAG index and documents")
        self.documents = []  # Clear documents first
        self.metadata = []   # Clear metadata
        self.create_index()  # This will also clear documents again, but that's fine
        logger.info("RAG index and documents cleared")
        
    def search(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        """Search for similar documents using the query"""
        try:
            if not self.index or len(self.documents) == 0:
                logger.warning("No documents in index")
                return []
            
            # Use configured default_k from RAG config
            if k is None:
                k = rag_config['search']['default_k']
            
            # Generate query embedding
            query_embedding = self.model.encode([query])[0]
            
            # Normalize query embedding for cosine similarity
            faiss.normalize_L2(query_embedding.reshape(1, -1))
            
            # Log query embedding stats
            logger.info(f"Query embedding stats - min: {query_embedding.min():.4f}, max: {query_embedding.max():.4f}, mean: {query_embedding.mean():.4f}, norm: {np.linalg.norm(query_embedding):.4f}")
            
            # Search for more results than needed to account for deduplication
            search_k = k * self.search_multiplier  # Use configurable multiplier
            
            # Search the index
            distances, indices = self.index.search(np.array([query_embedding]).astype('float32'), search_k)
            
            # Log raw distances
            logger.info(f"Raw distances - min: {distances[0].min():.4f}, max: {distances[0].max():.4f}, mean: {distances[0].mean():.4f}")
            
            # Get the results and deduplicate
            results = []
            seen_contents = set()
            
            for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
                if idx < len(self.documents):  # Ensure index is valid
                    # Convert L2 distance to cosine similarity using a more robust method
                    # For normalized vectors, cosine similarity = 1 - (L2_distance^2)/2
                    # Add a small epsilon to prevent numerical instability
                    epsilon = 1e-6
                    distance = max(0, min(2, distance))  # Clamp distance to [0, 2]
                    similarity = max(0, min(1, 1 - (distance * distance) / 2 + epsilon))
                    
                    # Log similarity calculation
                    logger.info(f"Result {i+1} - Distance: {distance:.4f}, Similarity: {similarity:.4f}")
                    
                    # Get the document text and metadata
                    document_text = self.documents[idx]
                    metadata = self.metadata[idx]
                    
                    # Check if this content is too similar to any existing result
                    is_duplicate = False
                    normalized_text = document_text.lower().strip()
                    
                    # Skip if we've seen this exact content before
                    if normalized_text in seen_contents:
                        continue
                    
                    # Check for partial matches (one content is contained within another)
                    for seen_text in seen_contents:
                        if normalized_text in seen_text or seen_text in normalized_text:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        seen_contents.add(normalized_text)
                        results.append({
                            "text": document_text,
                            "score": float(similarity),
                            "source_file": metadata.get("source_file")
                        })
                        
                        # Stop if we have enough unique results
                        if len(results) >= k:
                            break
            
            # Log final results
            if results:
                logger.info(f"Final results - min score: {min(r['score'] for r in results):.4f}, max score: {max(r['score'] for r in results):.4f}")
            else:
                logger.info("No results found after deduplication")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in search: {str(e)}")
            return []
    
    def save_index(self, directory: str):
        """Save the index and documents to disk"""
        if not self.index:
            logger.warning("No index to save")
            return
            
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        
        try:
            # Save FAISS index
            index_path = directory / "faiss.index"
            faiss.write_index(self.index, str(index_path))
            logger.info(f"Saved FAISS index to {index_path}")
            
            # Save documents and metadata
            docs_path = directory / "documents.json"
            with open(docs_path, "w") as f:
                json.dump({
                    "documents": self.documents,
                    "metadata": self.metadata
                }, f)
            logger.info(f"Saved {len(self.documents)} chunks to {docs_path}")
        except Exception as e:
            logger.error(f"Error saving index: {str(e)}")
            raise
            
    def load_index(self, directory: str):
        """Load the index and documents from disk"""
        directory = Path(directory)
        
        try:
            # Load FAISS index
            index_path = directory / "faiss.index"
            if index_path.exists():
                self.index = faiss.read_index(str(index_path))
                logger.info(f"Loaded FAISS index from {index_path}")
            else:
                logger.info("No existing FAISS index found")
                self.create_index()
                
            # Load documents and metadata
            docs_path = directory / "documents.json"
            if docs_path.exists():
                with open(docs_path, "r") as f:
                    data = json.load(f)
                    self.documents = data.get("documents", [])
                    self.metadata = data.get("metadata", [])
                logger.info(f"Loaded {len(self.documents)} chunks from {docs_path}")
            else:
                logger.info("No existing documents found")
                self.documents = []
                self.metadata = []
        except Exception as e:
            logger.error(f"Error loading index: {str(e)}")
            # Create new index if loading fails
            self.create_index()
            self.documents = []
            self.metadata = [] 

    def index_documents(self, documents: List[str], metadata: List[Dict[str, Any]] = None) -> None:
        """Index a list of documents"""
        try:
            if not documents:
                logger.warning("No documents to index")
                return
            
            # Generate embeddings for all documents
            embeddings = self.model.encode(documents)
            
            # Log embedding stats before normalization
            logger.info(f"Pre-normalization stats - min: {embeddings.min():.4f}, max: {embeddings.max():.4f}, mean: {embeddings.mean():.4f}")
            logger.info(f"Pre-normalization norms - min: {np.linalg.norm(embeddings, axis=1).min():.4f}, max: {np.linalg.norm(embeddings, axis=1).max():.4f}, mean: {np.linalg.norm(embeddings, axis=1).mean():.4f}")
            
            # Normalize embeddings for cosine similarity
            faiss.normalize_L2(embeddings)
            
            # Log embedding stats after normalization
            logger.info(f"Post-normalization stats - min: {embeddings.min():.4f}, max: {embeddings.max():.4f}, mean: {embeddings.mean():.4f}")
            logger.info(f"Post-normalization norms - min: {np.linalg.norm(embeddings, axis=1).min():.4f}, max: {np.linalg.norm(embeddings, axis=1).max():.4f}, mean: {np.linalg.norm(embeddings, axis=1).mean():.4f}")
            
            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            
            # Add vectors to the index
            self.index.add(embeddings.astype('float32'))
            
            # Store documents and metadata
            self.documents = documents
            self.metadata = metadata if metadata else [{}] * len(documents)
            
            logger.info(f"Indexed {len(documents)} documents with dimension {dimension}")
            
        except Exception as e:
            logger.error(f"Error in index_documents: {str(e)}")
            raise 