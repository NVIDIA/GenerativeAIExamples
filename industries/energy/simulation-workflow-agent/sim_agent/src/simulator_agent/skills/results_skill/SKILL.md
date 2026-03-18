---
name: results_skill
description: Read and analyze simulation binary output files. Use when extracting summary data, grid properties, or running flow diagnostics (time-of-flight, tracer, allocation, F-Phi, Lorenz) from completed simulations.
license: Apache-2.0
metadata:
  author: sim-agent
  version: "1.0"
  category: simulator
compatibility: Requires numpy and simulation output files (.SMSPEC, .INIT, .EGRID). Uses EclReader for summary/grid (Apache-2.0). Flow diagnostics requires pyflowdiagnostics and RPTRST FLOWS in the simulation.
---

# Results Skill

This skill provides tools for reading and analyzing simulation binary output files.

## Overview

The Results skill enables agents to:

- **Read** time-series summary data from simulation outputs
- **Extract** static grid properties from initialization files
- **Run flow diagnostics** (time-of-flight, tracer concentrations, allocation factors, F-Phi plots, Lorenz coefficient)
- **Access** binary simulation results programmatically

## Tools

### read_simulation_summary

Reads time-series data from simulation summary files (.UNSMRY / .SMSPEC).

**Usage:**
```python
read_simulation_summary(
    case_path: str,
    variables: List[str],
    entities: Optional[List[str]] = None
) -> str
```

**Parameters:**
- `case_path`: Path to the .DATA file (tool finds corresponding .SMSPEC file)
- `variables`: Summary variables to extract (e.g., ["FOPR", "FOPT", "WBHP"])
- `entities`: Optional well/group names to filter results (e.g., ["PROD1", "INJ1"])

**Example:**
```
read_simulation_summary(
    case_path="SPE1CASE1.DATA",
    variables=["FOPR", "FOPT"],
    entities=["PROD1"]
)
```

**Returns:** Summary data with time range, timesteps, and variable values.

**When to use:**
- When user asks for specific summary metrics (TOOL_DECISION_TREE.md Section 2.6, LLM choice)
- For extracting time-series data for analysis
- When comparing numerical results between cases

### read_grid_properties

Reads static grid properties from initialization files (.INIT / .EGRID).

**Usage:**
```python
read_grid_properties(
    case_path: str,
    properties: List[str]
) -> str
```

**Parameters:**
- `case_path`: Path to the .DATA file (tool finds corresponding .INIT or .EGRID file)
- `properties`: Properties to extract (e.g., ["PORO", "PERMX", "PERMY"])

**Example:**
```
read_grid_properties(
    case_path="SPE1CASE1.DATA",
    properties=["PORO", "PERMX"]
)
```

**Returns:** Grid dimensions, property statistics (min, max, mean), and property arrays.

**When to use:**
- When user asks for grid property information (Section 2.6, LLM choice)
- For analyzing reservoir characteristics
- When validating grid setup

**Note:** Spatial visualization (grid structure, permeability, porosity, pore volume, pressure, saturation, etc.) is not in the tool catalog; the agent suggests using a GUI (e.g. ResInsight) for those (Section 2.0).

### run_flow_diagnostics

Runs flow diagnostics on simulation results using [pyflowdiagnostics](https://github.com/GEG-ETHZ/pyflowdiagnostics). Computes time-of-flight (TOF), tracer concentrations, flow allocation factors, F-Phi (flow-storage capacity) curves, and Lorenz coefficients.

**Usage:**
```python
run_flow_diagnostics(
    case_path: str,
    time_step_ids: Optional[List[int]] = None,
) -> str
```

**Parameters:**
- `case_path`: Path to the .DATA file (simulation must have been run with RPTRST FLOWS)
- `time_step_ids`: Report step IDs to analyze (e.g. [1, 2, 3]). Default: last report step from SMSPEC

**Requirement:** Simulation must include flux output in RPTRST:
```
RPTRST
BASIC=2 FLOWS PRESSURE ALLPROPS /
```

**Output:** Creates `{case_stem}.fdout/` directory with JSON, CSV, Excel, and GRDECL files.

**When to use:**
- When user asks for flow diagnostics, time-of-flight, tracer, allocation, F-Phi, Lorenz coefficient
- To analyze injector-producer connectivity and sweep efficiency
- For post-processing of simulation results (see [MRST Flow Diagnostics](https://www.sintef.no/projectweb/mrst/modules/diagnostics/))

## Workflow Integration

This skill integrates with the Simulator Agent's decision tree (TOOL_DECISION_TREE.md):

1. **Results Analysis (Section 2.6):**
   ```
   read_simulation_summary (via LLM choice)
   read_grid_properties (via LLM choice)
   run_flow_diagnostics (via LLM choice)
   ```

2. **After Simulation (Section 3.3):**
   ```
   run_and_heal → summarize → optionally use results tools for detailed analysis
   ```

## Implementation Details

Tools are implemented as LangChain tools with Pydantic input schemas. The skill uses:

- **EclReader**: Apache-2.0 reader for summary (.SMSPEC/.UNSMRY) and grid (.INIT/.EGRID) files
- **File resolution**: Automatically finds .SMSPEC, .INIT, .EGRID files from .DATA path
- **Time axis handling**: Supports both date-based and step-based time axes
- **Well filtering**: Filters results by well/group names when provided

## Error Handling

All tools return descriptive error messages if:
- Case files are not found
- Required output files (.SMSPEC, .INIT) are missing
- Requested variables or properties are not available
- Binary file reading fails

## File Resolution

Tools automatically resolve output file paths from the DATA file path:
- `CASE.DATA` → `CASE.SMSPEC` (summary)
- `CASE.DATA` → `CASE.INIT` or `CASE.EGRID` (grid properties)
- Paths are resolved relative to the DATA file directory

## Limitations

- **Grid structure**: Grid dimensions, geometry, and EGRID are not in the tool catalog; use GUI tools (e.g., ResInsight)
- **Spatial visualization**: Grid, permeability, porosity, pore volume, pressure, saturation, and other spatial fields are not in the tool catalog; use GUI tools
- **Time-series plotting**: Use `plot_summary_metric` for visualization instead of raw data extraction

## References

- [Tool Decision Tree](references/TOOL_DECISION_TREE.md) - Routing logic
- [OPM Results Tools README](../../tools/README.md) - Detailed tool documentation

