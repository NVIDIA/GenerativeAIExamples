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
Flow Diagnostics Tools

Run flow diagnostics on OPM/Eclipse reservoir simulations using pyflowdiagnostics.
Computes time-of-flight, tracer concentrations, flow allocations, F-Phi plots,
and Lorenz coefficients from simulation outputs.

Requires: Simulation run with RPTRST BASIC=2 FLOWS PRESSURE ALLPROPS
Reference: https://github.com/GEG-ETHZ/pyflowdiagnostics
"""

import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

import pyflowdiagnostics.flow_diagnostics as pfd

logger = logging.getLogger(__name__)


def _get_last_report_step(case_path: str) -> int:
    """
    Get last report step from restart files (UNRST or X0001/X0002/...).
    Uses UNRST if present (counts INTEHEAD records); else picks max from X00xx files.
    Returns 1 if unavailable.
    """
    try:
        from .ecl_reader import EclReader

        reader = EclReader(case_path)
        return reader.get_last_restart_step()
    except Exception:
        return 1


# ============================================================================
# Input Schemas
# ============================================================================


class RunFlowDiagnosticsInput(BaseModel):
    case_path: str = Field(
        ...,
        description="Path to the .DATA file (simulation must have been run with RPTRST FLOWS)",
    )
    time_step_ids: List[int] = Field(
        default_factory=list,
        description="Report step IDs to analyze (e.g. [1, 2, 3]). Default: last report step.",
    )


# ============================================================================
# Tool Functions
# ============================================================================


@tool("run_flow_diagnostics", args_schema=RunFlowDiagnosticsInput)
def run_flow_diagnostics(
    case_path: str,
    time_step_ids: Optional[List[int]] = None,
) -> str:
    """
    Run flow diagnostics on OPM/Eclipse simulation results.

    Computes time-of-flight (TOF), tracer concentrations, flow allocation factors,
    F-Phi (flow-storage capacity) curves, and Lorenz coefficients. Output is written
    to a .fdout/ directory next to the DATA file.

    **Requirement:** The simulation must have been run with flux output in RPTRST:
      RPTRST
      BASIC=2 FLOWS PRESSURE ALLPROPS /

    **Output files:** FlowDiagnostics_{tstep}.json, F_Phi_*.csv, Allocation_Factor_*.xlsx,
    GridFlowDiagnostics_*.GRDECL (for visualization in Petrel).
    """
    if not time_step_ids:
        last_step = _get_last_report_step(case_path)
        time_step_ids = [last_step]

    try:
        if not os.path.exists(case_path):
            return f"Error: Case file not found: {case_path}"

        fd = pfd.FlowDiagnostics(case_path)
        for tstep in time_step_ids:
            fd.execute(tstep)

        # Build compact key-metrics summary (for user output) and full output (for LLM)
        key_metrics_parts = []
        summary_parts = [
            f"✓ Flow diagnostics completed for {os.path.basename(case_path)}",
            f"Output directory: {fd.output_dir}",
            f"Time steps analyzed: {time_step_ids}",
            "",
            "Metric definitions (for interpretation):",
            "- Lorenz: flow heterogeneity (0=uniform sweep, 1=highly heterogeneous). Derived from F-Phi curves.",
            "- Allocation: fraction of injector fluid reaching each producer, and vice versa (connectivity). Higher = stronger path.",
            "- Arrival time: days until injectant reaches producer (breakthrough). Lower = earlier breakthrough.",
            "",
        ]

        for tstep in time_step_ids:
            json_path = os.path.join(fd.output_dir, f"FlowDiagnostics_{tstep}.json")
            if os.path.exists(json_path):
                try:
                    with open(json_path) as f:
                        data = json.load(f)
                    metrics = data.get("flow_diagnostic_metrics", {})
                    summary_parts.append(f"--- Time step {tstep} ---")

                    # Time and grid (static context)
                    if "time" in data:
                        t = data["time"]
                        summary_parts.append(
                            f"  Date: {t.get('date', 'N/A')}, cumulative days: {t.get('days', 'N/A')}"
                        )
                    if "grid" in data:
                        g = data["grid"]
                        summary_parts.append(
                            f"  Grid: {g.get('nx')}x{g.get('ny')}x{g.get('nz')}, "
                            f"active cells: {g.get('num_active_cells')}, "
                            f"pore volume: {g.get('pore_volume_sum', 0):,.0f}"
                        )
                    if "wells" in data:
                        wells = data["wells"]
                        def _well_loc(w):
                            comps = w.get("completions") or []
                            if comps:
                                c = comps[0]
                                i, j, k = c.get("I"), c.get("J"), c.get("K")
                                if i is not None and j is not None and k is not None:
                                    return f"{w['name']} @ (I={i},J={j},K={k})"
                            return w.get("name", "?")
                        inj = [_well_loc(w) for w in wells if w.get("type") == "INJ"]
                        prd = [_well_loc(w) for w in wells if w.get("type") == "PRD"]
                        summary_parts.append(f"  Wells: injectors {inj}; producers {prd}")

                    # Lorenz (sweep efficiency)
                    if "lorenz" in metrics:
                        lc = metrics["lorenz"]
                        if isinstance(lc.get("global"), (int, float)):
                            summary_parts.append(f"  Lorenz coefficient (global): {lc['global']:.4f}")
                        if lc.get("well_pairs"):
                            summary_parts.append("  Lorenz per I-P streamtube:")
                            for wp in sorted(lc["well_pairs"], key=lambda x: (x.get("injector", ""), x.get("producer", ""))):
                                summary_parts.append(
                                    f"    {wp.get('injector')}→{wp.get('producer')}: {wp.get('lorenz_coefficient', 0):.4f} (n_cells={wp.get('n_cells', 0)})"
                                )

                    # Allocation (connectivity)
                    if "allocation" in metrics:
                        alloc = metrics["allocation"]
                        inj_alloc = alloc.get("injector_allocation", [])
                        if inj_alloc:
                            summary_parts.append("  Injector→producer allocation:")
                            for a in sorted(inj_alloc, key=lambda x: x["allocation"], reverse=True):
                                summary_parts.append(
                                    f"    {a['injector']}→{a['producer']}: {a['allocation']:.4f}"
                                )
                        prod_alloc = alloc.get("producer_allocation", [])
                        if prod_alloc:
                            summary_parts.append("  Producer←injector allocation:")
                            for a in prod_alloc:
                                summary_parts.append(
                                    f"    {a['producer']}←{a['injector']}: {a['allocation']:.4f}"
                                )

                    # Arrival times (breakthrough)
                    if "arrival_time" in metrics:
                        times = metrics["arrival_time"].get("producer_arrival_times", [])
                        if times:
                            summary_parts.append("  Producer arrival times (days):")
                            for a in times:
                                t = a.get("arrival_time")
                                summary_parts.append(
                                    f"    {a['producer']}: {t:.2f}" if t is not None else f"    {a['producer']}: N/A"
                                )
                    # Compact key metrics for summary block
                    km = []
                    if "lorenz" in metrics and isinstance(metrics["lorenz"].get("global"), (int, float)):
                        km.append(f"Lorenz={metrics['lorenz']['global']:.3f}")
                    if "allocation" in metrics:
                        inj = metrics["allocation"].get("injector_allocation", [])
                        if inj:
                            top = sorted(inj, key=lambda x: x["allocation"], reverse=True)[:3]
                            km.append("Connectivity: " + ", ".join(f"{a['injector']}→{a['producer']} {a['allocation']:.0%}" for a in top))
                    if "arrival_time" in metrics:
                        arr = metrics["arrival_time"].get("producer_arrival_times", [])
                        if arr:
                            sorted_arr = sorted(
                                [(a["producer"], a.get("arrival_time")) for a in arr if a.get("arrival_time") is not None],
                                key=lambda x: x[1],
                            )
                            arr_str = ", ".join(f"{p} {t:,.0f}d" for p, t in sorted_arr)
                            km.append(f"Arrival times: {arr_str}")
                    if km:
                        key_metrics_parts.append(f"  Step {tstep}: " + " | ".join(km))
                    summary_parts.append("")
                except Exception as e:
                    logger.debug(f"Could not parse {json_path}: {e}")

        summary_parts.append(
            "Files: FlowDiagnostics_*.json, F_Phi_*.csv, Allocation_Factor_*.xlsx, "
            "GridFlowDiagnostics_*.GRDECL"
        )
        full_output = "\n".join(summary_parts)
        if key_metrics_parts:
            full_output += "\n\n--- Key metrics summary ---\n" + "\n".join(key_metrics_parts)
        return full_output.strip()

    except (IOError, RuntimeError) as e:
        err_msg = str(e).lower()
        if "flux" in err_msg or "rptrst" in err_msg or "flows" in err_msg:
            return (
                f"Error: {e}\n\n"
                "Flow diagnostics requires flux data in the restart file. "
                "Add to RPTRST in the DATA file:\n"
                "  RPTRST\n"
                "  BASIC=2 FLOWS PRESSURE ALLPROPS /\n\n"
                "Then re-run the reservoir simulation to regenerate UNRST with fluxes."
            )
        return f"Error running flow diagnostics: {e}"
    except Exception as e:
        logger.exception("Flow diagnostics failed")
        return f"Error running flow diagnostics: {e}"
