#!/usr/bin/env python3
# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""
Smart OPM examples ingestion - follows INCLUDE directives.

This script:
1. Scans all .DATA files
2. Parses INCLUDE directives to find referenced files
3. Ingests both .DATA files and their INCLUDEs
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Set, Dict, Tuple, Optional
from tqdm import tqdm
import hashlib
import time

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from pymilvus import MilvusClient, DataType

# Optional: use scripts/milvus/nvidia_embedding.py (same as run_milvus_pipeline)
_scripts_root = Path(__file__).resolve().parent.parent
_milvus_dir = _scripts_root / "milvus"
if _milvus_dir.exists() and str(_milvus_dir) not in sys.path:
    sys.path.insert(0, str(_milvus_dir))
try:
    from nvidia_embedding import EMBEDDING_DIM as NVIDIA_EMBED_DIM, embed_texts as nvidia_embed_texts, get_client as nvidia_get_client
    HAS_NVIDIA_EMBEDDING_MODULE = True
except ImportError:
    HAS_NVIDIA_EMBEDDING_MODULE = False

# Milvus URI: same as run_milvus_pipeline.py
DEFAULT_MILVUS_URI = os.environ.get("MILVUS_URI", "http://localhost:19530")


def find_data_files(base_dir: Path) -> List[Path]:
    """Find all .DATA files recursively."""
    return list(base_dir.rglob("*.DATA"))


def count_numerical_values_in_file(file_path: Path, sample_lines: int = 100) -> int:
    """
    Estimate the number of numerical values in a file.
    
    Samples the first N lines to detect if the file is mostly large arrays.
    
    Returns:
        Estimated number of numerical values
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            lines = []
            for i, line in enumerate(f):
                if i >= sample_lines:
                    break
                lines.append(line)
        
        # Count tokens that look like numbers
        number_count = 0
        for line in lines:
            # Remove comments
            line = line.split('--')[0]
            
            # Split into tokens
            tokens = line.split()
            
            for token in tokens:
                # Try to parse as float (including scientific notation)
                try:
                    float(token)
                    number_count += 1
                except ValueError:
                    # Also count patterns like: 1000*0.2 (repeat notation)
                    if '*' in token:
                        try:
                            parts = token.split('*')
                            if len(parts) == 2:
                                int(parts[0])  # repeat count
                                float(parts[1])  # value
                                number_count += int(parts[0])
                        except ValueError:
                            pass
        
        # Extrapolate to full file if we only sampled
        if len(lines) == sample_lines:
            # Estimate: if first 100 lines have lots of numbers, full file probably has more
            total_lines = sum(1 for _ in open(file_path, 'r', encoding='utf-8', errors='ignore'))
            number_count = int(number_count * (total_lines / sample_lines))
        
        return number_count
    
    except Exception:
        return 0


def should_skip_file(file_path: Path, max_size_mb: float = 10.0, max_numbers: int = 10000) -> Tuple[bool, str]:
    """
    Determine if a file should be skipped (e.g., large grid property files).
    
    Uses intelligent content analysis to detect files with large numerical arrays.
    
    Args:
        file_path: Path to file
        max_size_mb: Skip files larger than this (MB)
        max_numbers: Skip files with more than this many numerical values
    
    Returns:
        (should_skip: bool, reason: str)
    """
    if not file_path.exists():
        return False, ""
    
    # Check file size first (fast check)
    size_mb = file_path.stat().st_size / (1024 * 1024)
    if size_mb > max_size_mb:
        return True, f"Large file ({size_mb:.1f} MB > {max_size_mb} MB)"
    
    # Content-based analysis (smart check)
    # Skip if file is mostly large numerical arrays (grid properties)
    num_count = count_numerical_values_in_file(file_path)
    if num_count > max_numbers:
        return True, f"Large numerical array (~{num_count:,} values > {max_numbers:,})"
    
    return False, ""


def parse_include_files(data_file: Path) -> Set[Path]:
    """
    Parse a DATA file and extract all INCLUDE file paths.
    
    INCLUDE syntax in OPM:
        INCLUDE
           'filename.ext'
        /
    
    or:
        INCLUDE 'filename.ext' /
    """
    include_files = set()
    data_dir = data_file.parent
    
    try:
        with open(data_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Pattern 1: INCLUDE\n   'filename' /
        pattern1 = r"INCLUDE\s+['\"]([^'\"]+)['\"]"
        
        # Pattern 2: Multi-line INCLUDE
        pattern2 = r"INCLUDE\s*\n\s*['\"]([^'\"]+)['\"]"
        
        matches = re.findall(pattern1, content, re.IGNORECASE)
        matches += re.findall(pattern2, content, re.IGNORECASE)
        
        for match in matches:
            # Clean up the path
            include_path = match.strip()
            
            # Resolve relative to DATA file directory
            full_path = data_dir / include_path
            
            if full_path.exists():
                include_files.add(full_path)
            else:
                # Try without directory (sometimes includes are in same dir)
                alt_path = data_dir / Path(include_path).name
                if alt_path.exists():
                    include_files.add(alt_path)
                else:
                    print(f"⚠  Warning: INCLUDE file not found: {include_path} (in {data_file.name})")
    
    except Exception as e:
        print(f"⚠  Warning: Could not parse {data_file}: {e}")
    
    return include_files


def discover_all_files(base_dir: Path, max_file_size_mb: float = 10.0, max_numbers: int = 10000) -> Dict[str, List[Path]]:
    """
    Discover all files to ingest.
    
    Returns:
        dict with keys:
            - 'data_files': List of .DATA files
            - 'include_files': List of INCLUDE files (filtered)
            - 'skipped_files': List of skipped files with reasons
            - 'all_files': Combined list
    """
    print(f"🔍 Scanning for .DATA files in {base_dir}...")
    data_files = find_data_files(base_dir)
    print(f"✓ Found {len(data_files)} .DATA files")
    
    print(f"\n🔍 Parsing INCLUDE directives...")
    all_includes = set()
    
    for data_file in tqdm(data_files, desc="Parsing DATA files"):
        includes = parse_include_files(data_file)
        all_includes.update(includes)
    
    print(f"✓ Found {len(all_includes)} unique INCLUDE files")
    
    # Filter out grid properties and large files
    print(f"\n🧹 Filtering grid properties and large files...")
    include_files = []
    skipped_files = []
    skip_reasons = {}
    
    for file_path in tqdm(all_includes, desc="Analyzing files"):
        should_skip, reason = should_skip_file(file_path, max_size_mb=max_file_size_mb, max_numbers=max_numbers)
        if should_skip:
            skipped_files.append(file_path)
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
        else:
            include_files.append(file_path)
    
    print(f"✓ Keeping {len(include_files)} files")
    print(f"✗ Skipping {len(skipped_files)} files")
    
    if skip_reasons:
        print(f"\n📊 Skip reasons:")
        for reason, count in sorted(skip_reasons.items(), key=lambda x: -x[1]):
            print(f"  {reason}: {count} files")
    
    # Get file extensions for kept files
    extensions = {}
    for f in include_files:
        ext = f.suffix.lower()
        extensions[ext] = extensions.get(ext, 0) + 1
    
    if extensions:
        print(f"\n📊 INCLUDE file types (kept):")
        for ext, count in sorted(extensions.items(), key=lambda x: -x[1]):
            print(f"  {ext if ext else '(no extension)'}: {count} files")
    
    all_files = list(data_files) + list(include_files)
    
    return {
        'data_files': data_files,
        'include_files': include_files,
        'skipped_files': skipped_files,
        'all_files': all_files
    }


def load_documents(files: List[Path]) -> List[Document]:
    """Load files as LangChain documents."""
    documents = []
    
    for file_path in tqdm(files, desc="Loading files"):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Create document with metadata
            doc = Document(
                page_content=content,
                metadata={
                    'source': str(file_path),
                    'filename': file_path.name,
                    'directory': file_path.parent.name,
                    'extension': file_path.suffix,
                }
            )
            documents.append(doc)
        
        except Exception as e:
            print(f"⚠  Warning: Could not load {file_path}: {e}")
    
    print(f"✓ Loaded {len(documents)} files")
    return documents


def split_documents(documents: List[Document], chunk_size: int = 1000, chunk_overlap: int = 200) -> List[Document]:
    """Split documents into chunks."""
    print(f"\n📄 Splitting documents (chunk_size={chunk_size}, overlap={chunk_overlap})...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✓ Created {len(chunks)} chunks")
    
    return chunks


def generate_string_id(content: str, index: int) -> str:
    """Generate a unique string ID for a document chunk."""
    content_hash = hashlib.md5(content.encode()).hexdigest()[:16]
    return f"{content_hash}_{index:06d}"


def ingest_to_milvus(
    chunks: List[Document],
    collection_name: str,
    milvus_uri: Optional[str] = None,
    drop_old: bool = False,
    use_nvidia_embedding_module: bool = False,
):
    """Ingest document chunks into Milvus with proper string IDs."""
    if milvus_uri is None:
        milvus_uri = DEFAULT_MILVUS_URI
    print(f"\n📥 Ingesting to Milvus collection: {collection_name}")
    print(f"   Milvus URI: {milvus_uri}")
    
    # Check for API key
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY environment variable not set")
    
    print(f"   API key length: {len(api_key)}")
    
    use_nvidia_module = use_nvidia_embedding_module and HAS_NVIDIA_EMBEDDING_MODULE
    embeddings = None
    dimension = None
    nvidia_client = None

    if use_nvidia_module:
        # Use nvidia_embedding.py (same as run_milvus_pipeline)
        print("\n🔧 Using embedding: nvidia_embedding.py (nvidia/llama-3.2-nemoretriever-1b-vlm-embed-v1)")
        dimension = NVIDIA_EMBED_DIM
        nvidia_client = nvidia_get_client()
        print(f"   Embedding dimension: {dimension}")
    else:
        # Initialize embeddings via LangChain (try fallbacks if NV-Embed-QA not available)
        model_override = os.environ.get("OPM_EMBEDDING_MODEL")
        models_to_try = [model_override] if model_override else ["nvidia/nv-embed-v1", "NV-Embed-QA", "snowflake/arctic-embed-l"]
        for model in models_to_try:
            if not model:
                continue
            try:
                embeddings = NVIDIAEmbeddings(model=model, truncate="END")
                embeddings.embed_query("test")
                print(f"\n🔧 Using embedding model: {model}")
                if model != "NV-Embed-QA":
                    print(f"   Tip: set OPM_EMBEDDING_MODEL={model} when running the agent")
                break
            except Exception as e:
                print(f"   Model {model} failed: {e}")
                embeddings = None
        if embeddings is None and not use_nvidia_module:
            if HAS_NVIDIA_EMBEDDING_MODULE:
                raise RuntimeError("No LangChain embedding model available. Use --use-nvidia-embedding to use nvidia_embedding.py")
            raise RuntimeError("No embedding model available. Enable one at https://build.nvidia.com/ or set OPM_EMBEDDING_MODEL")
        if embeddings is not None:
            print("\n🔧 Getting embedding dimension...")
            sample_embedding = embeddings.embed_query("test")
            dimension = len(sample_embedding)
            print(f"   Embedding dimension: {dimension}")
    
    # Initialize Milvus client
    client = MilvusClient(uri=milvus_uri)
    
    # Drop collection if requested
    if drop_old and collection_name in client.list_collections():
        print(f"\n🗑  Dropping existing collection: {collection_name}")
        client.drop_collection(collection_name)
    
    # Create collection with explicit string ID field
    if collection_name not in client.list_collections():
        print(f"\n🏗  Creating collection with schema...")
        schema = MilvusClient.create_schema(
            auto_id=False,
            enable_dynamic_field=True,
        )
        
        # Add fields with VARCHAR primary key
        schema.add_field(field_name="pk", datatype=DataType.VARCHAR, is_primary=True, max_length=100)
        schema.add_field(field_name="text", datatype=DataType.VARCHAR, max_length=65535)
        schema.add_field(field_name="vector", datatype=DataType.FLOAT_VECTOR, dim=dimension)
        
        # Create index
        index_params = client.prepare_index_params()
        index_params.add_index(
            field_name="vector",
            metric_type="L2",
            index_type="IVF_FLAT",
            params={"nlist": 128}
        )
        
        client.create_collection(
            collection_name=collection_name,
            schema=schema,
            index_params=index_params,
        )
        print(f"   ✓ Created collection: {collection_name}")
    
    # Prepare data for insertion with batch embeddings
    print(f"\n⚙️  Embedding {len(chunks)} chunks...")
    data_to_insert = []
    
    # Process in batches to avoid rate limits
    embed_batch_size = 50 if not use_nvidia_module else 32
    
    for batch_start in tqdm(range(0, len(chunks), embed_batch_size), desc="Embedding batches"):
        batch_end = min(batch_start + embed_batch_size, len(chunks))
        batch_chunks = chunks[batch_start:batch_end]
        
        # Get texts for batch embedding
        texts = [chunk.page_content for chunk in batch_chunks]
        
        if use_nvidia_module and nvidia_client is not None:
            # nvidia_embedding.embed_texts (same as run_milvus_pipeline)
            embeddings_list = nvidia_embed_texts(nvidia_client, texts, input_type="passage", truncate="NONE")
            # embed_texts returns list[list[float]]; ensure we use lists for Milvus
            embeddings_list = [list(v) for v in embeddings_list]
        else:
            # LangChain NVIDIAEmbeddings
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    embeddings_list = embeddings.embed_documents(texts)
                    break
                except Exception as e:
                    if "429" in str(e) or "Too Many Requests" in str(e):
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 5
                            print(f"\n⏳ Rate limit hit, waiting {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            raise
                    else:
                        raise
        
        # Process each chunk in the batch
        for i, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings_list)):
            global_idx = batch_start + i
            
            # Generate string ID
            doc_id = generate_string_id(chunk.page_content, global_idx)
            
            # Prepare record
            record = {
                "pk": doc_id,
                "text": chunk.page_content,
                "vector": embedding,
            }
            
            # Add metadata fields
            if chunk.metadata:
                for key, value in chunk.metadata.items():
                    record[key] = str(value) if value is not None else ""
            
            data_to_insert.append(record)
        
        # Small delay between batches
        time.sleep(0.5)
    
    # Insert data in batches
    print(f"\n💾 Inserting {len(data_to_insert)} records...")
    batch_size = 100
    for i in tqdm(range(0, len(data_to_insert), batch_size), desc="Inserting batches"):
        batch = data_to_insert[i:i + batch_size]
        client.insert(collection_name=collection_name, data=batch)
    
    print(f"\n✅ Ingested {len(data_to_insert)} chunks to {collection_name}")
    
    # Verify
    stats = client.get_collection_stats(collection_name)
    print(f"   Collection stats: {stats}")
    
    return client


def main():
    # Default: sim_agent/data/knowledge_base/repos/opm-data (downloaded via download_required.sh)
    project_root = Path(__file__).resolve().parents[1]
    default_examples_dir = project_root / "data" / "knowledge_base" / "repos" / "opm-data"
    parser = argparse.ArgumentParser(
        description="Ingest OPM examples with INCLUDE file discovery"
    )
    parser.add_argument(
        '--examples-dir',
        type=str,
        default=str(default_examples_dir),
        help='Path to examples directory'
    )
    parser.add_argument(
        '--collection-name',
        type=str,
        default='simulator_input_examples',
        help='Milvus collection name'
    )
    parser.add_argument(
        '--milvus-uri',
        type=str,
        default=DEFAULT_MILVUS_URI,
        help='Milvus URI (default: MILVUS_URI env or http://localhost:19530, same as run_milvus_pipeline)'
    )
    parser.add_argument(
        '--use-nvidia-embedding',
        action='store_true',
        default=True,
        help='Use nvidia_embedding.py for embeddings (from scripts/milvus/)'
    )
    parser.add_argument(
        '--chunk-size',
        type=int,
        default=1000,
        help='Chunk size for text splitting'
    )
    parser.add_argument(
        '--chunk-overlap',
        type=int,
        default=200,
        help='Chunk overlap for text splitting'
    )
    parser.add_argument(
        '--max-file-size-mb',
        type=float,
        default=10.0,
        help='Skip INCLUDE files larger than this (MB). Default: 10.0'
    )
    parser.add_argument(
        '--max-numbers',
        type=int,
        default=10000,
        help='Skip INCLUDE files with more than this many numerical values. Default: 10000'
    )
    parser.add_argument(
        '--reset-collection',
        action='store_true',
        help='Drop existing collection and recreate'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without doing it'
    )
    
    args = parser.parse_args()
    
    # Check API key
    if not args.dry_run and not os.getenv('NVIDIA_API_KEY'):
        print("❌ Error: NVIDIA_API_KEY environment variable not set")
        print("Set it with: export NVIDIA_API_KEY='your-key'")
        return 1

    if args.use_nvidia_embedding and not HAS_NVIDIA_EMBEDDING_MODULE:
        print("❌ Error: --use-nvidia-embedding requested but nvidia_embedding module not found")
        print("Ensure scripts/milvus/nvidia_embedding.py exists and is importable.")
        return 1
    
    print("="*70)
    print("Simulator Examples Ingestion (with INCLUDE discovery)")
    print("="*70)
    print()
    
    # Resolve examples directory
    examples_dir = Path(args.examples_dir).resolve()
    if not examples_dir.exists():
        print(f"❌ Error: Examples directory not found: {examples_dir}")
        return 1
    
    print(f"📂 Examples directory: {examples_dir}\n")
    
    # Discover files
    files_info = discover_all_files(
        examples_dir, 
        max_file_size_mb=args.max_file_size_mb,
        max_numbers=args.max_numbers
    )
    
    print(f"\n📊 Summary:")
    print(f"   .DATA files: {len(files_info['data_files'])}")
    print(f"   INCLUDE files (kept): {len(files_info['include_files'])}")
    print(f"   INCLUDE files (skipped): {len(files_info['skipped_files'])}")
    print(f"   Total files to ingest: {len(files_info['all_files'])}")
    
    if args.dry_run:
        print(f"\n✓ DRY RUN complete - no ingestion performed")
        return 0
    
    # Load documents
    print(f"\n{'='*70}")
    print("Loading Documents")
    print("="*70)
    documents = load_documents(files_info['all_files'])
    
    # Split documents
    chunks = split_documents(
        documents,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    # Ingest to Milvus
    print(f"\n{'='*70}")
    print("Ingesting to Milvus")
    print("="*70)
    
    try:
        ingest_to_milvus(
            chunks,
            collection_name=args.collection_name,
            milvus_uri=args.milvus_uri,
            drop_old=args.reset_collection,
            use_nvidia_embedding_module=args.use_nvidia_embedding,
        )
        print(f"\n{'='*70}")
        print("✅ Ingestion Complete!")
        print("="*70)
        return 0
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
