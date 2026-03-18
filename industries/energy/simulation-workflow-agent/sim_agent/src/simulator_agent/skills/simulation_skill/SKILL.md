---
name: simulation_skill
description: Run, monitor, and control simulations. Use when executing simulations, checking progress, or stopping running simulations. Supports foreground and background execution, progress monitoring, and process management.
license: Apache-2.0
metadata:
  author: sim-agent
  version: "1.0"
  category: simulator
compatibility: Requires simulator installed, Python environment with langchain and subprocess support
---

# Simulation Skill

This skill provides tools for executing and managing simulations.

## Overview

The Simulation skill enables agents to:

- **Run** simulations from simulator input files
- **Run and heal** run + auto-fix on failure, it will launch both run and monitor in one go from user input files
- **Monitor** simulation progress and status
- **Stop** running simulations when needed
- **Manage** simulation processes and output directories

## Tools

### run_and_heal

Runs a simulation and, on failure, automatically parses PRT errors, optionally consults RAG (simulator_manual, simulator_examples), and produces a fixed DATA file. Implemented as a chain: run_simulation in parallel with PRT wait + error parsing; if errors are found, extract keyword, call RAG tools if config is available, then create a fixed DATA file (e.g. \*_FIXED.DATA).

**Implementation:** `simulator_agent/tools/self_heal_chain.py`

**Usage (script):**
```bash
python -m simulator_agent.tools.self_heal_chain \
  --prt-loc-dir /path/to/output/ \
  --data-file /path/to/CASE.DATA \
  [--config /path/to/config.yaml] \
  [--output-file /path/to/output/]
```

**Parameters:** `data_file`, `output_dir` (optional), `num_mpi_processes` (default: 1, for MPI parallel runs with np>1).

**When to use:**
- When the user wants to run a case and automatically attempt to fix and re-run on simulation failure (run-and-heal flow).
- Alternative to manual run_simulation → inspect failure → patch_simulation_input_keyword/modify_simulation_input_file → run_simulation.


### run_simulation

Runs a simulation from a DATA file. Supports both foreground (wait for completion) and background (return immediately) execution.

**Usage:**
```python
run_simulation(
    data_file: str,
    output_dir: Optional[str] = None,
    num_threads: int = 1,
    num_mpi_processes: int = 1,
    additional_args: Optional[str] = None,
    background: bool = True
) -> str
```

**Parameters:**
- `data_file`: Path to the simulator input (DATA) file to run
- `output_dir`: Optional output directory (default: same directory as DATA file)
- `num_threads`: Number of threads for parallel simulation (default: 1)
- `num_mpi_processes`: Number of MPI processes (np). When > 1, runs via `mpirun -np N flow ...` (default: 1). Set `OPM_MPI_LAUNCHER=mpiexec` to use mpiexec instead.
- `additional_args`: Optional additional command-line arguments
- `background`: If True, start and return immediately. If False, wait for completion and return full report including return code, stdout, stderr, and parsed PRT errors on failure.

**Example:**
```
run_simulation(
    data_file="SPE1CASE1_AGENT_GENERATED.DATA",
    output_dir="/path/to/output",
    num_threads=4,
    background=False
)
```

**Returns:** 
- Background mode: Simulation start confirmation with PID, output directory, and log paths
- Foreground mode: Full completion report with return code, stdout, stderr, and PRT errors (if failed)

**When to use:** 
- Direct run (TOOL_DECISION_TREE.md Section 2.3) when user provides DATA file path + run intent
- After scenario modifications (Section 2.4) to execute the modified case
- HITL confirm run flow (Section 2.1) after user confirms
- After auto-fix (Section 2.2) to re-run the fixed case

### monitor_simulation

Monitors the progress of a running simulation by reading the PRT file.

**Usage:**
```python
monitor_simulation(
    output_dir: str,
    tail_lines: int = 80,
    use_llm_summary: bool = False,
    llm_model: Optional[str] = None
) -> str
```

**Parameters:**
- `output_dir`: Directory containing simulation output files (must contain .PRT file)
- `tail_lines`: Number of lines to read from end of PRT file (default: 80)
- `use_llm_summary`: If True, use LLM to summarize the PRT tail (default: False)
- `llm_model`: Optional LLM model override for summary

**Example:**
```
monitor_simulation(
    output_dir="/path/to/output",
    tail_lines=100,
    use_llm_summary=True
)
```

**Returns:** Simulation status (running/completed/failed) and PRT tail content, optionally with LLM summary.

**When to use:** 
- When user asks to check simulation progress (Section 3.5, LLM choice)
- For background runs to track completion
- When debugging simulation issues

### stop_simulation

Stops a running simulation by process ID.

**Usage:**
```python
stop_simulation(
    pid: int,
    output_dir: Optional[str] = None,
    force: bool = False
) -> str
```

**Parameters:**
- `pid`: Process ID of the simulation to stop
- `output_dir`: Optional output directory with run metadata
- `force`: If True, use SIGKILL (force kill). If False, use SIGTERM (graceful shutdown).

**Example:**
```
stop_simulation(
    pid=12345,
    output_dir="/path/to/output",
    force=False
)
```

**Returns:** Confirmation message with PID, signal used, and metadata update status.

**When to use:**
- When user requests to stop a running simulation (Section 3.5, LLM choice)
- For process management and cleanup

## Workflow Integration

This skill integrates with the Simulator Agent's decision tree (TOOL_DECISION_TREE.md):

1. **Direct Run (Section 2.3):**
   ```
   run_and_heal (optionally after HITL confirm)
   ```

2. **Scenario Test Chain (Section 2.4):**
   ```
   parse_simulation_input_file → simulator_manual → simulator_examples → modify_simulation_input_file → run_and_heal
   ```

3. **HITL Confirm Run (Section 2.1):**
   ```
   User confirms → run_and_heal
   ```

4. **After run_and_heal (Section 3.3):**
   ```
   run_and_heal → (auto-fix if failed) → summarize
   ```

5. **Monitoring (Section 3.5):**
   ```
   monitor_simulation (via LLM choice)
   stop_simulation (via LLM choice)
   ```

## Implementation Details

Tools are implemented as LangChain tools with Pydantic input schemas. The skill uses:

- **Subprocess management**: For running Flow executables
- **Process tracking**: PID and metadata stored in run.json
- **Output parsing**: PRT file parsing for progress and errors
- **Error handling**: Comprehensive error messages and failure reporting

## Error Handling

All tools return descriptive error messages if:
- DATA files are not found
- Flow executable is not available
- Output directories cannot be created
- Processes cannot be stopped
- PRT files cannot be read

## Environment Variables

- `OPM_PROJECT_ROOT`: Used to resolve paths in Docker environments
- `OPM_FLOW_EXTRA_ARGS`: Additional arguments passed to Flow (e.g., `--CheckSatfuncConsistency=0`)

## References

- [Tool Decision Tree](references/TOOL_DECISION_TREE.md) - Routing logic
- [Simulation Tools README](../../tools/README.md) - Detailed tool documentation

