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
OPM Results Analysis Tools

Tools for reading and analyzing OPM Flow simulation binary output files.
Provides access to grid properties, dynamic results, and summary data.

Uses ecl_reader (from physicsnemo sim_utils, Apache 2.0). No GPL dependencies.
"""

import os
import logging
from typing import List, Optional

import numpy as np
from langchain_core.tools import tool
from pydantic.v1 import BaseModel, Field

from .ecl_reader import EclReader

logger = logging.getLogger(__name__)


def _safe_fmt(val: float, precision: int = 2) -> str:
    """Format numeric value for output; handles NaN/Inf from reader variations."""
    if not np.isfinite(val):
        return "nan"
    return f"{val:.{precision}e}"


# ============================================================================
# Input Schemas
# ============================================================================


class ReadSimulationSummaryInput(BaseModel):
    case_path: str = Field(..., description="Path to the .DATA file")
    variables: List[str] = Field(
        ..., description="Summary variables to extract (e.g., ['WOPR', 'WBHP'])"
    )
    entities: Optional[List[str]] = Field(
        default=None, description="Optional well/group names"
    )


class ReadGridPropertiesInput(BaseModel):
    case_path: str = Field(..., description="Path to the .DATA file")
    properties: List[str] = Field(
        ..., description="Properties to extract (e.g., ['PORO', 'PERMX'])"
    )


# ============================================================================
# Tool Functions
# ============================================================================


@tool("read_simulation_summary", args_schema=ReadSimulationSummaryInput)
def read_simulation_summary(
    case_path: str, variables: List[str], entities: Optional[List[str]] = None
) -> str:
    """
    Read time series data from OPM simulation summary files (.UNSMRY).
    """
    try:
        if not os.path.exists(case_path):
            return f"Error: Case file not found: {case_path}"

        reader = EclReader(case_path)
        smry = reader.read_smry(keys=variables, entities=entities)

        # Normalize to numpy for reader output variations (list vs ndarray)
        time_arr = np.asarray(smry.get("TIME", np.array([])))
        length = int(len(time_arr))
        time_label = "days"
        time_range = (
            f"{time_arr[0]:.2f} to {time_arr[-1]:.2f}" if length > 0 else "N/A"
        )

        output = f"""
✓ Successfully read summary data from {os.path.basename(case_path)}

Variables: {', '.join(variables)}
Time range: {time_range} ({time_label})
Timesteps: {length}

Data extracted:
"""
        for var in variables:
            found = False
            for ent_name, ent_data in smry.items():
                if ent_name == "TIME":
                    continue
                if not isinstance(ent_data, dict) or var not in ent_data:
                    continue
                data = np.asarray(ent_data[var])
                if data.size == 0 or len(data) != length:
                    continue
                label = (
                    f"{var}:{ent_name}" if ent_name != "FIELD" else f"{var} (Field)"
                )
                mn, mx = np.nanmin(data), np.nanmax(data)
                final = float(data[-1]) if data.size > 0 else np.nan
                output += (
                    f"  {label}: min={_safe_fmt(mn)}, "
                    f"max={_safe_fmt(mx)}, final={_safe_fmt(final)}\n"
                )
                found = True
            if not found and entities:
                for entity in entities:
                    if entity not in smry or var not in smry[entity]:
                        continue
                    data = np.asarray(smry[entity][var])
                    if len(data) != length or data.size == 0:
                        continue
                    mn, mx = np.nanmin(data), np.nanmax(data)
                    final = float(data[-1]) if data.size > 0 else np.nan
                    output += (
                        f"  {var}:{entity}: min={_safe_fmt(mn)}, "
                        f"max={_safe_fmt(mx)}, final={_safe_fmt(final)}\n"
                    )

        return output

    except Exception as e:
        logger.error(f"Error reading summary: {e}")
        return f"Error reading summary data: {str(e)}"
    

@tool("read_grid_properties", args_schema=ReadGridPropertiesInput)
def read_grid_properties(case_path: str, properties: List[str]) -> str:
    """
    Read static grid properties from OPM simulation INIT file.
    """
    try:
        if not os.path.exists(case_path):
            return f"Error: Case file not found: {case_path}"

        reader = EclReader(case_path)
        keys = ["INTEHEAD"] + list(properties)
        ecl = reader.read_init(keys=keys)

        intehead = np.asarray(ecl.get("INTEHEAD", np.array([])))
        if len(intehead) < 11:
            return "Error: Could not read grid dimensions from INIT"
        nx, ny, nz = int(intehead[8]), int(intehead[9]), int(intehead[10])

        output = f"""
✓ Successfully read grid properties from {os.path.basename(case_path)}

Grid dimensions: {nx} x {ny} x {nz} = {nx*ny*nz} cells

Properties:
"""
        for prop in properties:
            arr = np.asarray(ecl.get(prop, np.array([])))
            if arr.size > 0:
                output += f"""
  {prop}:
    Min: {_safe_fmt(np.min(arr), 4)}
    Max: {_safe_fmt(np.max(arr), 4)}
    Mean: {_safe_fmt(np.mean(arr), 4)}
    Std: {_safe_fmt(np.std(arr), 4)}
"""
            else:
                output += f"\n  {prop}: Not found\n"

        return output

    except Exception as e:
        logger.error(f"Error reading grid properties: {e}")
        return f"Error reading grid properties: {str(e)}"
