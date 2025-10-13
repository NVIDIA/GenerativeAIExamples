#!/usr/bin/env python3
"""
Interactive demo for ModelNameExtractor with sentence transformers.
"""

import sys
import logging
import os

# Add the src directory to the path (parent directory)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from apply_configuration import ModelNameExtractor, MODEL_TAGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Run interactive demo."""
    print("=" * 80)
    print("ModelNameExtractor Interactive Demo")
    print("=" * 80)
    print()
    
    # Initialize the extractor
    print("Initializing ModelNameExtractor...")
    extractor = ModelNameExtractor(MODEL_TAGS, similarity_threshold=0.3)
    
    print("✓ Using enhanced keyword matching")
    print(f"  Configured {len(extractor._tag_keywords)} models")
    
    print()
    print("Available models:")
    for i, tag in enumerate(MODEL_TAGS, 1):
        print(f"  {i}. {tag}")
    
    print()
    print("Enter queries to find matching models (type 'quit' to exit)")
    print("Examples:")
    print("  - 'I need llama 3 with 8 billion parameters'")
    print("  - 'Deploy mistral for chat'")
    print("  - 'What's the best 70B model?'")
    print()
    
    while True:
        try:
            query = input("\nQuery: ").strip()
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not query:
                continue
            
            # Extract model
            result = extractor.extract(query)
            
            if result:
                print(f"✓ Matched model: {result}")
                
                # Show match scores for all models
                scores = []
                for tag in extractor.tags:
                    score = extractor._calculate_match_score(query, tag)
                    if score > 0:
                        scores.append((tag, score))
                
                # Sort by score
                scores.sort(key=lambda x: x[1], reverse=True)
                
                if scores:
                    print("\n  Top match scores:")
                    for i, (tag, score) in enumerate(scores[:3]):
                        marker = "→" if tag == result else " "
                        print(f"  {marker} {score:.3f} - {tag}")
            else:
                print("✗ No matching model found")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main() 