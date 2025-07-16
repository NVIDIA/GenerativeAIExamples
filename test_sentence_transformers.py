#!/usr/bin/env python3
"""
Simple test to verify sentence-transformers installation and functionality.
"""

import sys

print("Testing sentence-transformers installation...")

try:
    from sentence_transformers import SentenceTransformer
    print("✓ sentence-transformers imported successfully")
    
    # Try to initialize a model
    print("Initializing model 'all-MiniLM-L6-v2'...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("✓ Model loaded successfully")
    
    # Test encoding
    test_sentences = ["This is a test sentence", "Another test sentence"]
    print(f"Encoding {len(test_sentences)} test sentences...")
    embeddings = model.encode(test_sentences)
    print(f"✓ Embeddings shape: {embeddings.shape}")
    
    # Test similarity
    from sentence_transformers.util import cos_sim
    similarity = cos_sim(embeddings[0], embeddings[1])
    print(f"✓ Cosine similarity: {similarity.item():.3f}")
    
    print("\n✅ All tests passed! sentence-transformers is working correctly.")
    
except ImportError as e:
    print(f"✗ Failed to import sentence-transformers: {e}")
    print("\nPlease install with: pip3 install sentence-transformers")
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"   Type: {type(e).__name__}") 