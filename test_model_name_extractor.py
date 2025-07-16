#!/usr/bin/env python3
"""
Test file for ModelNameExtractor with sentence transformers.
Tests both semantic matching and fallback fuzzy matching.
"""

import sys
import logging
from typing import List, Tuple
import time

# Add the src directory to the path
sys.path.insert(0, 'src')

from apply_configuration import ModelNameExtractor, MODEL_TAGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test cases: (query, expected_model)
TEST_CASES: List[Tuple[str, str]] = [
    # Direct mentions
    ("I want to use Llama 3 8B", "meta-llama/Meta-Llama-3-8B-Instruct"),
    ("Deploy meta llama 3.1 8b instruct", "meta-llama/Llama-3.1-8B-Instruct"),
    ("We need the 70B Llama model", "meta-llama/Meta-Llama-3-70B-Instruct"),
    ("Use Llama 3.3 70B for this task", "meta-llama/Llama-3.3-70B-Instruct"),
    
    # Semantic variations
    ("I need a small llama model, around 8 billion parameters", "meta-llama/Meta-Llama-3-8B-Instruct"),
    ("Deploy the latest 70 billion parameter Llama", "meta-llama/Llama-3.3-70B-Instruct"),
    ("Meta's instruction tuned llama with 8B params", "meta-llama/Meta-Llama-3-8B-Instruct"),
    
    # Mistral mentions
    ("Use Mistral 7B instruct v0.3", "mistralai/Mistral-7B-Instruct-v0.3"),
    ("I want mistral ai's 7 billion model", "mistralai/Mistral-7B-Instruct-v0.3"),
    ("Deploy mistral's instruction model", "mistralai/Mistral-7B-Instruct-v0.3"),
    
    # Qwen mentions
    ("Deploy Qwen 14B model", "Qwen/Qwen3-14B"),
    ("Use alibaba's qwen with 14 billion parameters", "Qwen/Qwen3-14B"),
    ("I need Qwen3 14B", "Qwen/Qwen3-14B"),
    
    # Falcon mentions
    ("Use falcon 40b instruct", "tiiuae/falcon-40b-instruct"),
    ("Deploy the 180B falcon model", "tiiuae/falcon-180B"),
    ("TII's falcon with 40 billion parameters", "tiiuae/falcon-40b-instruct"),
    ("Technology Innovation Institute's largest model", "tiiuae/falcon-180B"),
    
    # Partial and fuzzy matches
    ("llama3", "meta-llama/Meta-Llama-3-8B-Instruct"),
    ("mistral7b", "mistralai/Mistral-7B-Instruct-v0.3"),
    ("qwen 14", "Qwen/Qwen3-14B"),
    ("falcon40", "tiiuae/falcon-40b-instruct"),
    
    # Context-based queries
    ("I need a model for chat, preferably meta's 8B one", "meta-llama/Meta-Llama-3-8B-Instruct"),
    ("What's the best instruction-following model around 7B?", "mistralai/Mistral-7B-Instruct-v0.3"),
    ("Deploy a large model, maybe falcon 180B", "tiiuae/falcon-180B"),
    
    # Edge cases
    ("", None),
    (None, None),
    ("random text with no model mention", None),
    ("xyz123 unknown model", None),
]

def test_with_enhanced_matching():
    """Test ModelNameExtractor with enhanced keyword matching."""
    logger.info("=" * 80)
    logger.info("Testing ModelNameExtractor with enhanced keyword matching")
    logger.info("=" * 80)
    
    # Create extractor with enhanced matching
    start_time = time.time()
    extractor = ModelNameExtractor(MODEL_TAGS, similarity_threshold=0.3)  # Lower threshold for keyword matching
    init_time = time.time() - start_time
    logger.info(f"Initialization time: {init_time:.3f}s")
    logger.info(f"✓ Initialized with {len(extractor._tag_keywords)} model configurations")
    
    run_tests(extractor)

def test_with_higher_threshold():
    """Test ModelNameExtractor with higher similarity threshold."""
    logger.info("=" * 80)
    logger.info("Testing ModelNameExtractor with higher threshold (0.5)")
    logger.info("=" * 80)
    
    # Create extractor with higher threshold
    extractor = ModelNameExtractor(MODEL_TAGS, similarity_threshold=0.5)
    
    logger.info("✓ Using higher similarity threshold")
    
    run_tests(extractor)

def run_tests(extractor: ModelNameExtractor):
    """Run all test cases with the given extractor."""
    passed = 0
    failed = 0
    total_time = 0
    
    logger.info("\nRunning test cases:")
    logger.info("-" * 80)
    
    for i, (query, expected) in enumerate(TEST_CASES, 1):
        start_time = time.time()
        result = extractor.extract(query)
        elapsed = (time.time() - start_time) * 1000  # Convert to ms
        total_time += elapsed
        
        # Check if result matches expected
        if result == expected:
            status = "✓ PASS"
            passed += 1
        else:
            status = "✗ FAIL"
            failed += 1
        
        # Format output
        query_str = f'"{query}"' if query else "None"
        if len(query_str) > 50:
            query_str = query_str[:47] + '..."'
        
        logger.info(f"Test {i:2d}: {status} | Query: {query_str:<50} | Time: {elapsed:6.2f}ms")
        
        if result != expected:
            logger.info(f"         Expected: {expected}")
            logger.info(f"         Got:      {result}")
    
    logger.info("-" * 80)
    logger.info(f"Results: {passed}/{len(TEST_CASES)} passed, {failed} failed")
    logger.info(f"Average extraction time: {total_time/len(TEST_CASES):.2f}ms")
    logger.info("")

def test_match_scores():
    """Test and display match scores for various queries."""
    logger.info("=" * 80)
    logger.info("Testing match scores with enhanced keyword matching")
    logger.info("=" * 80)
    
    extractor = ModelNameExtractor(MODEL_TAGS, similarity_threshold=0.3)
    
    # Test queries to show match scores
    test_queries = [
        "I want to use llama",
        "Deploy a 70 billion parameter model",
        "mistral instruction model",
        "What's the best chat model?",
        "falcon from TII",
        "I need a model for coding",
        "Deploy qwen model",
        "meta's latest model",
        "llama 3 8b",
        "mistral 7b v0.3",
    ]
    
    logger.info("\nMatch scores for test queries:")
    logger.info("-" * 80)
    
    for query in test_queries:
        # Calculate scores for all models
        scores = []
        for tag in extractor.tags:
            score = extractor._calculate_match_score(query, tag)
            if score > 0:
                scores.append((tag, score))
        
        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)
        
        logger.info(f"\nQuery: '{query}'")
        if scores:
            for i, (tag, score) in enumerate(scores[:3]):
                logger.info(f"  {i+1}. {tag:<50} (score: {score:.3f})")
        else:
            logger.info("  No matches found")

def main():
    """Run all tests."""
    logger.info("Starting ModelNameExtractor tests")
    logger.info("")
    
    # Test with enhanced matching
    test_with_enhanced_matching()
    
    # Test with higher threshold
    test_with_higher_threshold()
    
    # Test match scores
    test_match_scores()
    
    logger.info("\nAll tests completed!")

if __name__ == "__main__":
    main() 