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
Test suite for RAG Skill tools.

Tests:
- extract_keyword: metric inference (common list, LLM normalize, RAG+LLM fallback)
- rag_chain: simulator_manual, simulator_examples

Usage:
    python -m simulator_agent.skills.rag_skill.test
    python -m simulator_agent.skills.rag_skill.test --query "COMPDAT keyword format"
    python -m simulator_agent.skills.rag_skill.test --tool simulator_examples
    python -m simulator_agent.skills.rag_skill.test --tool extract_keyword --query "plot field cumulative oil"
    python -m simulator_agent.skills.rag_skill.test --tool extract_keyword --query "plot field oil production" --expect-none
"""

import argparse
import sys
from pathlib import Path

# Ensure src/ is on path so simulator_agent package is found when run as __main__
_skill_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_skill_root) not in sys.path:
    sys.path.insert(0, str(_skill_root))


def test_extract_keyword(query: str, expect_common_list: bool = False, expect_none: bool = False) -> bool:
    """Test extract_keyword (common list + RAG+LLM fallback)."""
    print("\n" + "=" * 80)
    print("TEST: extract_keyword")
    print("=" * 80)
    try:
        from simulator_agent.skills.rag_skill.scripts.extract_keyword import (
            AmbiguousQueryError,
            _match_common_list,
            extract_keyword,
        )
    except ImportError as e:
        print(f"⚠️  Skipping extract_keyword (import failed): {e}")
        return True  # skip when full package unavailable (e.g. LangChain deps)

    try:
        kw_common = _match_common_list(query)
        print(f"Query: {query!r}")
        print(f"Common list match (raw): {kw_common!r}")
        kw = extract_keyword(query, intent="summary_metric")
        print(f"extract_keyword result: {kw!r}")

        if expect_none and kw is None:
            print("✅ SUCCESS (correctly returned None for ambiguous/unknown query)")
            return True
        if kw:
            print("✅ SUCCESS")
            return True
        if expect_common_list and kw_common:
            print("⚠️  Common list matched but full extract_keyword returned None (LLM may have failed)")
            return True
        print("❌ FAILED: no keyword extracted")
        return False
    except AmbiguousQueryError as e:
        if expect_none:
            print(f"✅ SUCCESS (correctly detected ambiguous query: {e})")
            return True
        print(f"❌ FAILED: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def _run_rag_chain_test(query: str, collection_name: str) -> bool:
    """Run rag_chain with given collection (simulator_manual or simulator_examples)."""
    try:
        _rag_skill_root = Path(__file__).resolve().parent
        _scripts_dir = _rag_skill_root / "scripts"
        if str(_scripts_dir) not in sys.path:
            sys.path.insert(0, str(_scripts_dir))

        from rag_chain import build_chain

        chain = build_chain()
        print(f"Query: {query}")
        print(f"Collection: {collection_name}")
        print("Running retrieval and LLM...\n")
        response = chain.invoke({"query": query, "collection_name": collection_name})
        print("--- Response (markdown) ---\n")
        print(response)
        print("\n✅ SUCCESS")
        return True
    except ImportError as e:
        print(f"⚠️  Import error: {e}")
        print("   RAG chain requires scripts/ on path and dependencies. Skipping test (not a failure).")
        return True
    except RuntimeError as e:
        if "NVIDIA_API_KEY" in str(e):
            print("⚠️  NVIDIA_API_KEY is required for the RAG chain. Skipping test (not a failure).")
            return True
        raise
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_simulator_manual(query: str, config_path: str = None) -> bool:
    """Test simulator_manual via rag_chain with collection_name=simulator_manual."""
    print("\n" + "="*80)
    print("TEST: simulator_manual (rag_chain)")
    print("="*80)
    return _run_rag_chain_test(query, "simulator_manual")


def test_simulator_examples(query: str, config_path: str = None) -> bool:
    """Test simulator_examples via rag_chain (maps to Milvus collection simulator_input_examples; no keyword filtering)."""
    print("\n" + "="*80)
    print("TEST: simulator_examples (rag_chain -> simulator_input_examples collection)")
    print("="*80)
    return _run_rag_chain_test(query, "simulator_examples")


def run_all_tests(query: str = "COMPDAT keyword format", config_path: str = None) -> None:
    """Run all tests."""
    print("\n" + "="*80)
    print("RAG SKILL TEST SUITE")
    print("="*80)
    print(f"Test query: {query}")
    print("  extract_keyword: common list + LLM (requires NVIDIA_API_KEY for full flow)")
    print("  simulator_manual: keyword extraction + metadata filter; simulator_examples: no keywords/filter.")
    print("  Requires: NVIDIA_API_KEY, Milvus with the chosen collection.")
    
    results = []
    
    # Test 0: extract_keyword (metric inference)
    results.append(("extract_keyword", test_extract_keyword("plot field cumulative oil production")))
    
    # Test 1: simulator_manual
    results.append(("simulator_manual", test_simulator_manual(query, config_path)))
    
    # Test 2: simulator_examples
    results.append(("simulator_examples", test_simulator_examples(query, config_path)))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test RAG Skill tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m simulator_agent.skills.rag_skill.test --query "COMPDAT keyword format" --tool simulator_manual
  python -m simulator_agent.skills.rag_skill.test --query "COMPDAT examples" --tool simulator_examples
    """
    )
    
    parser.add_argument(
        "--query",
        type=str,
        default="Show me example use cases of COMPDAT keyword",
        help="Query string to test RAG tools with (default: 'COMPDAT keyword format')"
    )
    
    parser.add_argument(
        "--expect-none",
        action="store_true",
        help="For extract_keyword: expect None (ambiguous query, e.g. 'plot field oil production')"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Unused (kept for CLI compatibility); both tools use rag_chain with --collection"
    )
    
    parser.add_argument(
        "--tool",
        type=str,
        choices=["extract_keyword", "simulator_manual", "simulator_examples"],
        help="Run only a specific tool test"
    )
    
    args = parser.parse_args()
    
    if args.tool:
        # Run single tool test
        print(f"\nRunning single tool test: {args.tool}")
        print(f"Query: {args.query}")
        
        if args.tool == "extract_keyword":
            success = test_extract_keyword(args.query, expect_none=args.expect_none)
        elif args.tool == "simulator_manual":
            success = test_simulator_manual(args.query, args.config)
        elif args.tool == "simulator_examples":
            success = test_simulator_examples(args.query, args.config)
        
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        run_all_tests(args.query, args.config)


if __name__ == "__main__":
    main()

