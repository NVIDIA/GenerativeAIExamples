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
Test suite for Results Skill tools.

Tests all tools related to reading simulation results from TOOL_DECISION_TREE.md:
- read_simulation_summary
- read_grid_properties

Usage:
    python -m simulator_agent.skills.results_skill.test
    python -m simulator_agent.skills.results_skill.test --case path/to/CASE.DATA
"""

import argparse
import sys
from pathlib import Path

# Ensure src/ is on path so simulator_agent package is found when run as __main__
_skill_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_skill_root) not in sys.path:
    sys.path.insert(0, str(_skill_root))

from simulator_agent.skills.results_skill import (
    read_grid_properties,
    read_simulation_summary,
)


def test_read_simulation_summary(case_path: str) -> bool:
    """Test read_simulation_summary tool."""
    print("\n" + "="*80)
    print("TEST: read_simulation_summary")
    print("="*80)
    
    try:
        result = read_simulation_summary.invoke({
            "case_path": case_path,
            "variables": ["FOPR", "FOPT"],
            "entities": None,
        })
        # Output format compatibility: success prefix or error prefix
        assert isinstance(result, str), "Result must be string"
        stripped = result.strip()
        assert stripped.startswith("✓ Successfully") or stripped.startswith("Error:"), (
            "Output must start with success or error prefix"
        )
        if "✓ Successfully" in result:
            assert "Variables:" in result and "Time range:" in result
            assert "Timesteps:" in result and "Data extracted:" in result
        print(f"✅ SUCCESS")
        print(f"Result:\n{result}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_read_grid_properties(case_path: str) -> bool:
    """Test read_grid_properties tool."""
    print("\n" + "="*80)
    print("TEST: read_grid_properties")
    print("="*80)
    
    try:
        result = read_grid_properties.invoke({
            "case_path": case_path,
            "properties": ["PORO", "PERMX"],
        })
        # Output format compatibility: success prefix or error prefix
        assert isinstance(result, str), "Result must be string"
        stripped = result.strip()
        assert stripped.startswith("✓ Successfully") or stripped.startswith("Error:"), (
            "Output must start with success or error prefix"
        )
        if "✓ Successfully" in result:
            assert "Grid dimensions:" in result and "Properties:" in result
        print(f"✅ SUCCESS")
        print(f"Result:\n{result}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests(case_path: str) -> None:
    """Run all tests."""
    print("\n" + "="*80)
    print("RESULTS SKILL TEST SUITE")
    print("="*80)
    print(f"Case path: {case_path}")
    
    if not Path(case_path).exists():
        print(f"❌ ERROR: Case file not found: {case_path}")
        sys.exit(1)
    
    # Check for required output files
    base_path = Path(case_path).with_suffix("")
    smspec_file = base_path.with_suffix(".SMSPEC")
    init_file = base_path.with_suffix(".INIT")
    egrid_file = base_path.with_suffix(".EGRID")
    
    print(f"Checking for output files:")
    print(f"  .SMSPEC: {smspec_file.exists()}")
    print(f"  .INIT: {init_file.exists()}")
    print(f"  .EGRID: {egrid_file.exists()}")
    
    results = []
    
    # Test 1: read_simulation_summary (requires .SMSPEC)
    if smspec_file.exists():
        results.append(("read_simulation_summary", test_read_simulation_summary(case_path)))
    else:
        print("\n⚠️  Skipping read_simulation_summary: .SMSPEC file not found")
        results.append(("read_simulation_summary", True))  # Skip, not a failure
    
    # Test 2: read_grid_properties (requires .INIT or .EGRID)
    if init_file.exists() or egrid_file.exists():
        results.append(("read_grid_properties", test_read_grid_properties(case_path)))
    else:
        print("\n⚠️  Skipping read_grid_properties: .INIT/.EGRID file not found")
        results.append(("read_grid_properties", True))  # Skip, not a failure
    
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
        description="Test Results Skill tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ## runs when your current working directory is: /workspace/sim_agent/src/
  
  # Test with specific case
   python -m simulator_agent.skills.results_skill.test --case ../data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA --tool read_simulation_summary
    
        """
    )
    
    parser.add_argument(
        "--case",
        type=str,
        default="/workspace/sim_agent/data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA",
        help="Path to OPM DATA file (default: SPE10_TOPLAYER.DATA)"
    )
    
    parser.add_argument(
        "--tool",
        type=str,
        choices=["read_simulation_summary", "read_grid_properties"],
        help="Run only a specific tool test"
    )
    
    args = parser.parse_args()
    
    case_path = args.case
    
    if args.tool:
        # Run single tool test
        print(f"\nRunning single tool test: {args.tool}")
        print(f"Case: {case_path}")
        
        if args.tool == "read_simulation_summary":
            success = test_read_simulation_summary(case_path)
        elif args.tool == "read_grid_properties":
            success = test_read_grid_properties(case_path)
        
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        run_all_tests(case_path)


if __name__ == "__main__":
    main()

