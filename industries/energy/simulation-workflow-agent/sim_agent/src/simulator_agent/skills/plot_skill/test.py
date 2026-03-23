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
Test suite for Plot Skill tools.

Tests all tools related to plotting from TOOL_DECISION_TREE.md:
- plot_summary_metric
- plot_compare_summary_metric

Usage:
    python -m simulator_agent.skills.plot_skill.test
    python -m simulator_agent.skills.plot_skill.test --output-dir path/to/output
    ./plot_skill/test.py --output-dir path/to/output --tool plot_summary_metric --keep-plots
"""

import argparse
import sys
import tempfile
from pathlib import Path

# Ensure src/ is on path so simulator_agent package is found when run as __main__
_skill_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_skill_root) not in sys.path:
    sys.path.insert(0, str(_skill_root))

from simulator_agent.skills.plot_skill import (
    plot_compare_summary_metric,
    plot_summary_metric,
)


def test_plot_summary_metric(output_dir: str, keep_plots: bool = False) -> bool:
    """Test plot_summary_metric tool."""
    print("\n" + "="*80)
    print("TEST: plot_summary_metric")
    print("="*80)
    
    try:
        # Save plot to output directory instead of temp file
        output_path = Path(output_dir)
        save_path = str(output_path / "test_plot_FOPT.png")
        
        result = plot_summary_metric.invoke({
            "output_dir": output_dir,
            "metric_request": "FOPT",
            "save_path": save_path,
        })
        print(f"✅ SUCCESS")
        print(f"Result:\n{result}")
        
        # Verify plot file was created
        if Path(save_path).exists():
            print(f"✅ Plot file created: {save_path}")
            if not keep_plots:
                # Clean up
                Path(save_path).unlink()
                print(f"   (Cleaned up test plot file)")
            else:
                print(f"   (Plot file kept at: {save_path})")
        else:
            print(f"⚠️  Plot file not found: {save_path}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_plot_compare_summary_metric(output_dir: str, keep_plots: bool = False) -> bool:
    """Test plot_compare_summary_metric tool."""
    print("\n" + "="*80)
    print("TEST: plot_compare_summary_metric")
    print("="*80)
    
    try:
        # Check if multiple .SMSPEC files exist
        output_path = Path(output_dir)
        smspec_files = list(output_path.glob("*.SMSPEC"))
        
        if len(smspec_files) < 2:
            print(f"⚠️  Only {len(smspec_files)} .SMSPEC file(s) found. Need at least 2 for comparison.")
            print("   Skipping test (not a failure).")
            return True
        
        # Save plot to output directory instead of temp file
        save_path = str(output_path / "test_plot_compare_FOPT.png")
        
        # Extract case stems from .SMSPEC files
        case_stems = ",".join([f.stem for f in smspec_files[:2]])
        
        result = plot_compare_summary_metric.invoke({
            "output_dir": output_dir,
            "metric_request": "FOPT",
            "case_stems": case_stems,
            "save_path": save_path,
        })
        print(f"✅ SUCCESS")
        print(f"Result:\n{result}")
        
        # Verify plot file was created
        if Path(save_path).exists():
            print(f"✅ Plot file created: {save_path}")
            if not keep_plots:
                # Clean up
                Path(save_path).unlink()
                print(f"   (Cleaned up test plot file)")
            else:
                print(f"   (Plot file kept at: {save_path})")
        else:
            print(f"⚠️  Plot file not found: {save_path}")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests(output_dir: str, keep_plots: bool = False) -> None:
    """Run all tests."""
    print("\n" + "="*80)
    print("PLOT SKILL TEST SUITE")
    print("="*80)
    print(f"Output directory: {output_dir}")
    
    if not Path(output_dir).exists():
        print(f"❌ ERROR: Output directory not found: {output_dir}")
        sys.exit(1)
    
    # Check for .SMSPEC files
    output_path = Path(output_dir)
    smspec_files = list(output_path.glob("*.SMSPEC"))
    
    if not smspec_files:
        print(f"❌ ERROR: No .SMSPEC files found in {output_dir}")
        print("   Run a simulation first to generate output files.")
        sys.exit(1)
    
    print(f"Found {len(smspec_files)} .SMSPEC file(s)")
    
    results = []
    
    # Test 1: plot_summary_metric
    results.append(("plot_summary_metric", test_plot_summary_metric(output_dir, keep_plots)))
    
    # Test 2: plot_compare_summary_metric
    results.append(("plot_compare_summary_metric", test_plot_compare_summary_metric(output_dir, keep_plots)))
    
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
        description="Test Plot Skill tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  ## runs when your current working directory is: /workspace/sim_agent/src/
  python -m simulator_agent.skills.plot_skill.test  --output-dir /workspace/sim_agent/data/example_cases/SPE10/CASE --tool plot_summary_metric --keep-plots
  
  
        """
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/workspace/sim_agent/data/example_cases/SPE10/CASE",
        help="Output directory containing .SMSPEC files (default: CASE/BASE)"
    )
    
    parser.add_argument(
        "--tool",
        type=str,
        choices=["plot_summary_metric", "plot_compare_summary_metric"],
        help="Run only a specific tool test"
    )
    
    parser.add_argument(
        "--keep-plots",
        action="store_true",
        help="Keep plot files after test (default: delete them)"
    )
    
    args = parser.parse_args()
    
    output_dir = args.output_dir
    keep_plots = args.keep_plots
    
    if args.tool:
        # Run single tool test
        print(f"\nRunning single tool test: {args.tool}")
        print(f"Output directory: {output_dir}")
        
        if args.tool == "plot_summary_metric":
            success = test_plot_summary_metric(output_dir, keep_plots)
        elif args.tool == "plot_compare_summary_metric":
            success = test_plot_compare_summary_metric(output_dir, keep_plots)
        
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        run_all_tests(output_dir, keep_plots)


if __name__ == "__main__":
    main()

