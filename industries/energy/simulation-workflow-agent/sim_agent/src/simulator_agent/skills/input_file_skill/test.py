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
Test suite for DATA File Skill tools.

Tests all tools related to parse_simulation_input_file from TOOL_DECISION_TREE.md:
- parse_simulation_input_file
- modify_simulation_input_file
- patch_simulation_input_keyword

Usage:
    python -m simulator_agent.skills.input_file_skill.test
    python -m simulator_agent.skills.input_file_skill.test --file path/to/test.DATA
"""

import argparse
import sys
import tempfile
from pathlib import Path

# Ensure src/ is on path so simulator_agent package is found when run as __main__
_skill_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_skill_root) not in sys.path:
    sys.path.insert(0, str(_skill_root))

from simulator_agent.skills.input_file_skill import (
    modify_simulation_input_file,
    parse_simulation_input_file,
    patch_simulation_input_keyword,
)


def test_parse_simulation_input_file(file_path: str) -> bool:
    """Test parse_simulation_input_file tool."""
    print("\n" + "="*80)
    print("TEST: parse_simulation_input_file")
    print("="*80)
    
    try:
        result = parse_simulation_input_file.invoke({"file_path": file_path})
        print(f"✅ SUCCESS")
        print(f"Result: {result}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_modify_simulation_input_file(file_path: str) -> bool:
    """Test modify_simulation_input_file tool."""
    print("\n" + "="*80)
    print("TEST: modify_simulation_input_file")
    print("="*80)
    
    try:
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.DATA', delete=False) as tmp:
            output_path = tmp.name
        
        # Test modification (add a comment)
        result = modify_simulation_input_file.invoke({
            "file_path": file_path,
            "modifications": "Add a comment line '-- Modified by test' at the beginning of the file",
            "output_path": output_path,
        })
        print(f"✅ SUCCESS")
        print(f"Result: {result}")
        
        # Verify output file exists
        if Path(output_path).exists():
            print(f"✅ Output file created: {output_path}")
            # Clean up
            Path(output_path).unlink()
        else:
            print(f"⚠️  Output file not found: {output_path}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_patch_simulation_input_keyword(file_path: str) -> bool:
    """Test patch_simulation_input_keyword tool."""
    print("\n" + "="*80)
    print("TEST: patch_simulation_input_keyword")
    print("="*80)
    
    try:
        # Create a temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.DATA', delete=False) as tmp:
            output_path = tmp.name
        
        # Read the file to find a keyword to patch
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Try to find a common keyword (e.g., DIMENS)
        keywords_to_try = ['DIMENS', 'TITLE', 'START']
        keyword_found = None
        
        for kw in keywords_to_try:
            if kw in content.upper():
                keyword_found = kw
                break
        
        if not keyword_found:
            print("⚠️  No common keywords found to patch. Skipping test.")
            return True
        
        # Test patching (this is a simple test - actual patching may need specific values)
        print(f"Attempting to patch keyword: {keyword_found}")
        result = patch_simulation_input_keyword.invoke({
            "file_path": file_path,
            "keyword": keyword_found,
            "output_path": output_path,
            "new_block_content": f"{keyword_found}\n/\n",  # Simple replacement
        })
        print(f"✅ SUCCESS")
        print(f"Result: {result}")
        
        # Verify output file exists
        if Path(output_path).exists():
            print(f"✅ Output file created: {output_path}")
            # Clean up
            Path(output_path).unlink()
        else:
            print(f"⚠️  Output file not found: {output_path}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests(file_path: str) -> None:
    """Run all tests."""
    print("\n" + "="*80)
    print("DATA FILE SKILL TEST SUITE")
    print("="*80)
    print(f"Test file: {file_path}")
    
    if not Path(file_path).exists():
        print(f"❌ ERROR: File not found: {file_path}")
        sys.exit(1)
    
    results = []
    
    # Test 1: parse_simulation_input_file
    results.append(("parse_simulation_input_file", test_parse_simulation_input_file(file_path)))
    
    # Test 2: modify_simulation_input_file (may require NVIDIA_API_KEY)
    results.append(("modify_simulation_input_file", test_modify_simulation_input_file(file_path)))
    
    # Test 3: patch_simulation_input_keyword
    results.append(("patch_simulation_input_keyword", test_patch_simulation_input_keyword(file_path)))
    
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
        description="Test DATA File Skill tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ## runs when your current working directory is: /workspace/sim_agent/src/
  python -m simulator_agent.skills.input_file_skill.test --file data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA --tool parse_simulation_input_file
    """
    )
    
    parser.add_argument(
        "--file",
        type=str,
        default="/workspace/sim_agent/data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA",
        help="Path to OPM DATA file to test with (default: SPE10_TOPLAYER.DATA)"
    )
    
    parser.add_argument(
        "--tool",
        type=str,
        choices=["parse_simulation_input_file", "modify_simulation_input_file", "patch_simulation_input_keyword"],
        help="Run only a specific tool test"
    )
    
    args = parser.parse_args()
    
    file_path = args.file
    
    if args.tool:
        # Run single tool test
        print(f"\nRunning single tool test: {args.tool}")
        print(f"File: {file_path}")
        
        if args.tool == "parse_simulation_input_file":
            success = test_parse_simulation_input_file(file_path)
        elif args.tool == "modify_simulation_input_file":
            success = test_modify_simulation_input_file(file_path)
        elif args.tool == "patch_simulation_input_keyword":
            success = test_patch_simulation_input_keyword(file_path)
        
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        run_all_tests(file_path)


if __name__ == "__main__":
    main()

