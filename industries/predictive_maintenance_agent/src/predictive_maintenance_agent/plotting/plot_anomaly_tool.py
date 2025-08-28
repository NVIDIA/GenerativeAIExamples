# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import json
import logging
import os
import pandas as pd
from typing import Optional
from pydantic import Field, BaseModel

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

from .plot_utils import create_anomaly_plot_from_data

logger = logging.getLogger(__name__)


class PlotAnomalyToolConfig(FunctionBaseConfig, name="plot_anomaly_tool"):
    """
    NeMo Agent Toolkit function to create anomaly detection visualizations.
    """
    output_folder: str = Field(description="The path to the output folder to save plots.", default="./output_data")


@register_function(config_type=PlotAnomalyToolConfig)
async def plot_anomaly_tool(config: PlotAnomalyToolConfig, builder: Builder):
    
    class PlotAnomalyInputSchema(BaseModel):
        anomaly_data_json_path: str = Field(description="Path to JSON file containing sensor data with is_anomaly column")
        sensor_name: str = Field(description="Name of the sensor to plot", default="sensor_measurement_1")
        engine_unit: int = Field(description="Engine unit number", default=5)
        plot_title: Optional[str] = Field(description="Custom title for the plot", default=None)

    def load_json_data(json_path: str) -> Optional[pd.DataFrame]:
        """Load data from JSON file."""
        from .plot_utils import resolve_relative_path
        try:
            # Resolve path relative to output folder
            resolved_path = resolve_relative_path(json_path, config.output_folder)
            with open(resolved_path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except Exception as e:
            logger.error(f"Error loading JSON data from {json_path}: {e}")
            return None

    # Plotting logic moved to plot_utils.py for thread safety

    async def _response_fn(
        anomaly_data_json_path: str,
        sensor_name: str = "sensor_measurement_1",
        engine_unit: int = 5,
        plot_title: Optional[str] = None
    ) -> str:
        """
        Create anomaly detection visualization from sensor data with is_anomaly column.
        """
        try:
            # Load the data with anomaly information
            data_df = load_json_data(anomaly_data_json_path)
            if data_df is None:
                return f"Failed to load anomaly data from {anomaly_data_json_path}"
            
            logger.info(f"Loaded anomaly data: {data_df.shape}")
            
            # Create the plot using thread-safe utility function
            html_filepath, png_filepath = create_anomaly_plot_from_data(
                data_df, sensor_name, engine_unit, 
                config.output_folder, plot_title
            )
            
            if html_filepath is None:
                return "Failed to create anomaly visualization plot"
            
            # Build response
            response_parts = [
                "ANOMALY DETECTION VISUALIZATION COMPLETED SUCCESSFULLY",
                "",
                f"Plot Details:",
                f"   • Sensor: {sensor_name}",
                f"   • Engine Unit: {engine_unit}",
                f"   • Data Points: {len(data_df)}",
                f"   • Anomalous Points: {len(data_df[data_df['is_anomaly'] == True])}",
                "",
                f"Output Files:",
                f"   • Interactive HTML: {os.path.relpath(html_filepath, config.output_folder)}",
                f"   • PNG Image: {os.path.relpath(png_filepath, config.output_folder) if png_filepath else 'Not generated'}",
                "",
                f"Visualization Features:",
                f"   • Blue line shows observed sensor readings",
                f"   • Red markers highlight detected anomalies",
                f"   • Interactive plot with zoom and hover capabilities",
                "",
                "ANOMALY PLOT GENERATION COMPLETE"
            ]
            
            return "\n".join(response_parts)
            
        except Exception as e:
            logger.error(f"Error in plot_anomaly_tool: {e}")
            return f"Error creating anomaly plot: {str(e)}"

    description = """
    Create interactive anomaly detection visualizations from sensor data with is_anomaly column.
    
    This tool takes a single JSON file containing sensor data with an added 'is_anomaly' boolean column
    (typically output from MOMENT anomaly detection tool) and creates a clean visualization.
    
    Features:
    - Interactive HTML plot with zoom and hover capabilities
    - Blue line for observed sensor readings
    - Red markers for detected anomalies
    - Automatic time axis detection (cycle, time_in_cycles, etc.)
    - PNG export for reports and documentation
    - Customizable plot titles
    
    Input:
      - anomaly_data_json_path: Path to JSON file with sensor data and is_anomaly column [REQUIRED]
      - sensor_name: Name of sensor column to plot (default: "sensor_measurement_1")
      - engine_unit: Engine unit number for labeling (default: 5)
      - plot_title: Custom title for the plot (optional)
    
    Output:
    - Interactive HTML visualization file
    - PNG image file (if successfully generated)
    - Summary of plot generation with file paths
    """
    
    yield FunctionInfo.from_fn(_response_fn, 
                               input_schema=PlotAnomalyInputSchema,
                               description=description)