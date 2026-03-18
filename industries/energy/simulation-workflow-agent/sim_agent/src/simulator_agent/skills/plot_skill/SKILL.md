---
name: plot_skill
description: Plot and compare simulation summary metrics. Use when visualizing time-series results, comparing multiple cases, or analyzing production performance. Supports single and multi-metric plots, case comparisons, and automatic metric keyword resolution.
license: Apache-2.0
metadata:
  author: sim-agent
  version: "1.0"
  category: simulator
compatibility: Requires matplotlib and simulation output files (.SMSPEC). Uses EclReader for summary (Apache-2.0).
---

# Plotting Skill

This skill provides tools for visualizing and comparing simulation results.

## Overview

The Plotting skill enables agents to:

- **Plot** summary metrics from simulation outputs
- **Compare** multiple cases on the same plot
- **Visualize** time-series data (rates, cumulative production, etc.)
- **Resolve** metric keywords automatically from user requests

## Tools

### plot_summary_metric

Plots one or more summary metrics from simulation outputs on the same plot.

**Usage:**
```python
plot_summary_metric(
    output_dir: str,
    metric_request: str,
    manual_hint: Optional[str] = None,
    save_path: Optional[str] = None
) -> str
```

**Parameters:**
- `output_dir`: Directory containing simulation output files (must contain .SMSPEC file)
- `metric_request`: User request or summary keyword(s). For multiple metrics on one plot, use comma-separated keywords (e.g., "FOPT, FWPT" or "FOPT,FWPT")
- `manual_hint`: Optional manual context or retrieved snippet to help map keywords
- `save_path`: Optional path to save the plot image

**Example:**
```
plot_summary_metric(
    output_dir="/path/to/output",
    metric_request="FOPT, FWPT",
    save_path="/path/to/plot.png"
)
```

**Returns:** Confirmation message with plot details and save path (if provided). Displays the plot.

**When to use:** 
- After simulation run when user asks to plot results (TOOL_DECISION_TREE.md Section 3.1)
- When user requests specific metrics (e.g., "Plot cumulative oil production")
- For visualizing time-series data from completed simulations

**Metric Keywords:**
Common summary keywords include:
- `FOPT`: Cumulative oil production
- `FOPR`: Oil production rate
- `FWPT`: Cumulative water production
- `FWPR`: Water production rate
- `FGPT`: Cumulative gas production
- `FGPR`: Gas production rate
- `WBHP`: Well bottom-hole pressure
- `WOPR`: Well oil production rate

### plot_compare_summary_metric

Plots a summary metric for two or more cases on the same axes for comparison.

**Usage:**
```python
plot_compare_summary_metric(
    output_dir: str,
    metric_request: str,
    case_stems: Optional[str] = None,
    case_paths: Optional[str] = None,
    save_path: Optional[str] = None
) -> str
```

**Parameters:**
- `output_dir`: Directory to save the plot and, when not using case_paths, directory containing .SMSPEC files to compare
- `metric_request`: Summary keyword to compare (e.g., "FOPT" for cumulative oil, "FOPR" for oil rate)
- `case_stems`: Comma-separated case name stems to compare (e.g., "SPE10_TOPLAYER,SPE10_TOPLAYER_AGENT_GENERATED"). If omitted and case_paths not set, all .SMSPEC files in output_dir are compared.
- `case_paths`: Comma-separated paths to simulator input files (or .SMSPEC) for the cases to compare. Use when comparing cases from different directories (e.g., "BASE/SPE10.DATA,INFILL/SPE10_INFILL.DATA").
- `save_path`: Optional path to save the comparison plot image

**Example:**
```
plot_compare_summary_metric(
    output_dir="/path/to/output",
    metric_request="FOPT",
    case_stems="SPE10_TOPLAYER,SPE10_TOPLAYER_AGENT_GENERATED"
)
```

**Returns:** Confirmation message with comparison plot details and save path (if provided). Displays the plot with different line styles for each case.

**When to use:**
- After running multiple cases when user asks to compare (Section 3.1)
- For comparing baseline vs modified scenarios
- When analyzing differences between simulation cases

## Workflow Integration

This skill integrates with the Simulator Agent's decision tree (TOOL_DECISION_TREE.md):

1. **Plot Results (Section 3.1):**
   ```
   User asks to plot → plot_summary_metric (if run_and_heal exists in history)
   ```

2. **Compare Cases (Section 3.1):**
   ```
   User asks to compare → plot_compare_summary_metric (if multiple cases available)
   ```

3. **After Simulation (Section 3.3):**
   ```
   run_and_heal → summarize → "Do you want me to plot the results?"
   ```

## Implementation Details

Tools are implemented as LangChain tools with Pydantic input schemas. The skill uses:

- **EclReader**: Apache-2.0 reader for .SMSPEC/.UNSMRY summary files
- **Matplotlib**: For generating plots
- **Metric resolution**: Automatic keyword mapping from user requests
- **Time axis handling**: Supports both date-based and step-based time axes

## Error Handling

All tools return descriptive error messages if:
- Output directories are not found
- .SMSPEC files are missing
- Requested metrics are not available
- Case files cannot be found
- Plot generation fails

## Metric Resolution

The tool automatically resolves metric keywords from user requests:
- Direct keywords (e.g., "FOPT") are used as-is
- Natural language (e.g., "cumulative oil production") is mapped to keywords
- Manual hints from `simulator_manual` can help with keyword mapping
- Multiple metrics can be plotted together using comma-separated keywords

## References

- [Tool Decision Tree](references/TOOL_DECISION_TREE.md) - Routing logic
- [Simulation Tools README](../../tools/README.md) - Detailed tool documentation

