# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import base64
import csv
import requests
import numpy as np
from pathlib import Path
from typing import List, Dict, Optional, Union
from PIL import Image
from io import BytesIO
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from config import *


def get_embedding(input_data: str, request_type: str = "query") -> List[float]:
    payload = {
        "input": [input_data],
        "request_type": request_type,
        "encoding_format": "float",
        "model": "nvidia/cosmos-embed1"
    }
    response = requests.post(COSMOS_API_URL, json=payload)
    response.raise_for_status()
    return response.json()["data"][0]["embedding"]


def encode_video_to_base64(video_path: Path) -> str:
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    video_b64 = base64.b64encode(video_bytes).decode('utf-8')
    return f"data:video/mp4;base64,{video_b64}"


def encode_image_to_base64(image_path: Path) -> str:
    img = Image.open(image_path).convert('RGB')
    buffer = BytesIO()
    img.save(buffer, format='JPEG')
    image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return f"data:image/jpeg;base64,{image_b64}"


def setup_qdrant(client: Optional[QdrantClient] = None) -> QdrantClient:
    if client is None:
        client = QdrantClient(url=QDRANT_URL)
    
    if client.collection_exists(COLLECTION_NAME):
        print(f"Deleting existing collection: {COLLECTION_NAME}")
        client.delete_collection(COLLECTION_NAME)
    
    print(f"Creating collection: {COLLECTION_NAME}")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )
    return client


def load_metadata() -> Dict[str, str]:
    metadata = {}
    if not METADATA_FILE.exists():
        print(f"Note: No metadata file found at {METADATA_FILE}")
        return metadata
    
    print(f"Loading metadata from {METADATA_FILE}")
    with open(METADATA_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row.get('file_name', '').strip()
            text = row.get('text', '').strip()
            if filename and text:
                metadata[filename] = text
    
    print(f"Loaded metadata for {len(metadata)} videos")
    return metadata


def fuse_embeddings(video_emb: list, text_emb: list, 
                   video_weight: float = VIDEO_WEIGHT, 
                   text_weight: float = TEXT_WEIGHT) -> list:
    video_arr = np.array(video_emb)
    text_arr = np.array(text_emb)
    fused = video_weight * video_arr + text_weight * text_arr
    norm = np.linalg.norm(fused)
    if norm > 0:
        fused = fused / norm
    return fused.tolist()


def index_videos(video_dir: Path = DATA_DIR, client: Optional[QdrantClient] = None) -> int:
    if client is None:
        client = QdrantClient(url=QDRANT_URL)
    
    metadata = load_metadata()
    use_text_fusion = len(metadata) > 0
    
    video_files = sorted([f for f in video_dir.glob("*.mp4") if f.is_file()])
    
    if not video_files:
        print(f"No videos found in {video_dir}")
        return 0
    
    print(f"Found {len(video_files)} videos to index")
    
    points = []
    for idx, video_file in enumerate(video_files):
        print(f"[{idx+1}/{len(video_files)}] Processing: {video_file.name}")
        
        try:
            video_b64 = encode_video_to_base64(video_file)
            video_embedding = get_embedding(video_b64, request_type="query")
            
            text_description = metadata.get(video_file.name, "")
            final_embedding = video_embedding
            
            if use_text_fusion and text_description:
                print(f"  Text: {text_description[:60]}...")
                text_embedding = get_embedding(text_description, request_type="query")
                final_embedding = fuse_embeddings(video_embedding, text_embedding)
                print(f"  ✓ Fused video + text embeddings")
            elif use_text_fusion:
                print(f"  ⚠ No text description found for {video_file.name}")
            
            point = PointStruct(
                id=idx,
                vector=final_embedding,
                payload={
                    "video_path": str(video_file),
                    "video_name": video_file.name,
                    "original_path": str(video_file),
                    "text_description": text_description,
                    "has_text_fusion": bool(text_description)
                }
            )
            points.append(point)
            
        except Exception as e:
            print(f"Error processing {video_file.name}: {e}")
            continue
    
    if points:
        print(f"\nUploading {len(points)} embeddings to Qdrant...")
        client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


class VideoSearchAgent:
    def __init__(self):
        self.client = QdrantClient(url=QDRANT_URL)
        if not self.client.collection_exists(COLLECTION_NAME):
            raise ValueError(
                f"Collection '{COLLECTION_NAME}' not found. "
                "Run index_videos.py first to create and populate the collection."
            )
    
    def search(self, query: Union[str, Path], top_k: int = 5) -> List[Dict]:
        if isinstance(query, (str, Path)) and Path(query).exists():
            query_path = Path(query)
            suffix = query_path.suffix.lower()
            
            if suffix in ['.jpg', '.jpeg', '.png']:
                print(f"Image query: {query_path.name}")
                query_data = encode_image_to_base64(query_path)
            elif suffix in ['.mp4', '.avi', '.mov', '.mkv']:
                print(f"Video query: {query_path.name}")
                query_data = encode_video_to_base64(query_path)
            else:
                print(f"Text query: {query}")
                query_data = str(query)
        else:
            print(f"Text query: {query}")
            query_data = str(query)
        
        embedding = get_embedding(query_data)
        
        results = self.client.search(
            collection_name=COLLECTION_NAME,
            query_vector=embedding,
            limit=top_k
        )
        
        matches = []
        for result in results:
            match = {
                "video_name": result.payload["video_name"],
                "video_path": result.payload["video_path"],
                "score": result.score
            }
            if "text_description" in result.payload and result.payload["text_description"]:
                match["text_description"] = result.payload["text_description"]
            matches.append(match)
        
        return matches
    
    def print_results(self, matches: List[Dict]):
        if not matches:
            print("\nNo matches found.")
            return
        
        print(f"\nTop {len(matches)} matches:")
        print("-" * 80)
        
        for i, match in enumerate(matches, 1):
            print(f"{i}. {match['video_name']}")
            print(f"   Score: {match['score']:.4f}")
            if 'text_description' in match:
                print(f"   Description: {match['text_description']}")
            print(f"   Path: {match['video_path']}")
            print()

