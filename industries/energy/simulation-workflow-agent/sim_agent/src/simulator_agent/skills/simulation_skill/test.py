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
Test suite for Simulation Skill tools.

Tests all tools related to simulation execution from TOOL_DECISION_TREE.md:
- run_simulation
- monitor_simulation
- stop_simulation

Usage:
    python -m simulator_agent.skills.simulation_skill.test --file 
    python -m simulator_agent.skills.simulation_skill.test --file path/to/test.DATA
"""

import argparse
import sys
import tempfile
import time
from pathlib import Path

# Ensure src/ is on path so simulator_agent package is found when run as __main__
_skill_root = Path(__file__).resolve().parent.parent.parent.parent
if str(_skill_root) not in sys.path:
    sys.path.insert(0, str(_skill_root))

from simulator_agent.skills.simulation_skill import (
    monitor_simulation,
    run_simulation,
    stop_simulation,
)


def test_run_simulation(data_file: str, output_dir: str = None, background: bool = True) -> bool:
    """Test run_simulation tool."""
    print("\n" + "="*80)
    print(f"TEST: run_simulation (background={background})")
    print("="*80)
    
    try:
        result = run_simulation.invoke({
            "data_file": data_file,
            "output_dir": output_dir,
            "num_threads": 1,
            "background": background,
        })
        print(f"✅ SUCCESS") 
        print(f"Result:\n{result}")
        
        # Determine output directory: use provided one, or extract from result, or use DATA file's parent
        if output_dir:
            output_path = Path(output_dir)
        else:
            # Extract from result or use DATA file's parent directory
            data_file_path = Path(data_file).resolve()
            output_path = data_file_path.parent
        
        # Check if output directory has expected files
        if output_path.exists():
            prt_files = list(output_path.glob("*.PRT"))
            smspec_files = list(output_path.glob("*.SMSPEC"))
            print(f"\nOutput directory: {output_path}")
            print(f"PRT files: {len(prt_files)}")
            print(f"SMSPEC files: {len(smspec_files)}")
        else:
            print(f"\n⚠️  Output directory does not exist yet: {output_path}")
            print("   (This is normal for background simulations that just started)")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monitor_simulation(output_dir: str) -> bool:
    """Test monitor_simulation tool."""
    print("\n" + "="*80)
    print("TEST: monitor_simulation")
    print("="*80)
    
    try:
        result = monitor_simulation.invoke({
            "output_dir": output_dir,
            "tail_lines": 50,
            "use_llm_summary": False,
        })
        print(f"✅ SUCCESS")
        print(f"Result:\n{result}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_stop_simulation(pid: int = None) -> bool:
    """Test stop_simulation tool."""
    print("\n" + "="*80)
    print("TEST: stop_simulation")
    print("="*80)
    
    try:
        # If no PID provided, use a dummy PID (will fail gracefully)
        if pid is None:
            print("⚠️  No PID provided. Testing with dummy PID (will fail gracefully).")
            test_pid = 99999
        else:
            test_pid = pid
        
        result = stop_simulation.invoke({
            "pid": test_pid,
            "force": False,
        })
        print(f"✅ SUCCESS (tool executed)")
        print(f"Result:\n{result}")
        
        # Note: This test may fail if PID doesn't exist, but that's expected
        if "Failed to stop" in result or "not found" in result.lower():
            print("⚠️  Expected: Process not found (dummy PID or already stopped)")
        
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests(data_file: str, output_dir: str = None) -> None:
    """Run all tests."""
    print("\n" + "="*80)
    print("SIMULATION SKILL TEST SUITE")
    print("="*80)
    print(f"Test file: {data_file}")
    
    if not Path(data_file).exists():
        print(f"❌ ERROR: File not found: {data_file}")
        sys.exit(1)
    
    results = []
    
    # Test 1: run_simulation (background mode - quick test)
    print("\n⚠️  Note: run_simulation test requires simulator to be installed.")
    print("   This test will start a simulation in background mode.")
    results.append(("run_simulation (background)", test_run_simulation(data_file, output_dir=output_dir, background=True)))
    
    # Test 2: monitor_simulation (if output_dir provided or from run_simulation)
    if output_dir and Path(output_dir).exists():
        ## always sleep 20 seconds before monitor_simulation 
        time.sleep(20)
        results.append(("monitor_simulation", test_monitor_simulation(output_dir)))
    else:
        print("\n⚠️  Skipping monitor_simulation: no output directory provided")
        print("   Run a simulation first or provide --output-dir")
        results.append(("monitor_simulation", True))  # Skip, not a failure
    
    # Test 3: stop_simulation (dummy test)
    results.append(("stop_simulation", test_stop_simulation()))
    
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
        description="Test Simulation Skill tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=r"""
Examples:
  ## runs when your current working directory is: /workspace/sim_agent/src/
  python -m simulator_agent.skills.simulation_skill.test \
  --file /workspace/sim_agent/data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA \
  --output-dir /workspace/output/ \
  --tool run_simulation

  python -m simulator_agent.skills.simulation_skill.test \
  --file /workspace/sim_agent/data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA \
  --output-dir /workspace/output/ \
  --tool monitor_simulation

  python -m simulator_agent.skills.simulation_skill.test \
  --file /workspace/sim_agent/data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA \
  --output-dir /workspace/output/ \
  --tool stop_simulation
        """
    )
    
    parser.add_argument(
        "--file",
        type=str,
        default="/workspace/sim_agent/data/example_cases/SPE10/CASE/SPE10_TOPLAYER.DATA",
        help="Path to OPM DATA file to test with (default: SPE10_TOPLAYER.DATA)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/workspace/sim_agent/data/example_cases/SPE10/CASE/",
        help="Output directory for monitor_simulation test (optional)"
    )
    
    parser.add_argument(
        "--tool",
        type=str,
        choices=["run_simulation", "monitor_simulation", "stop_simulation"],
        help="Run only a specific tool test"
    )
    
    parser.add_argument(
        "--pid",
        type=int,
        default=None,
        help="Process ID for stop_simulation test (optional)"
    )
    
    args = parser.parse_args()
    
    data_file = args.file
    
    if args.tool:
        # Run single tool test
        print(f"\nRunning single tool test: {args.tool}")
        print(f"File: {data_file}")
        
        if args.tool == "run_simulation":
            success = test_run_simulation(data_file, output_dir=args.output_dir, background=True)
        elif args.tool == "monitor_simulation":
            if not args.output_dir:
                print("❌ ERROR: --output-dir required for monitor_simulation test")
                sys.exit(1)
            ## make monitor_simulation test wait for 20 seconds before launching the simulation
            time.sleep(20)
            success = test_monitor_simulation(args.output_dir)
        elif args.tool == "stop_simulation":
            success = test_stop_simulation(args.pid)
        else:
            # This shouldn't happen due to choices, but handle it anyway
            print(f"❌ ERROR: Unknown tool: {args.tool}")
            sys.exit(1)
        
        sys.exit(0 if success else 1)
    else:
        # Run all tests
        run_all_tests(data_file, args.output_dir)


if __name__ == "__main__":
    main()

