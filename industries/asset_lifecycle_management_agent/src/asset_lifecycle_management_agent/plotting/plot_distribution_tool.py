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

from pydantic import Field, BaseModel

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

def verify_json_path(file_path: str, output_folder: str = None) -> str:
    """
    Verify that the input is a valid path to a JSON file.
    
    Args:
        file_path (str): Path to verify
        output_folder (str): Output folder to use as base for relative paths
        
    Returns:
        str: Verified file path
        
    Raises:
        ValueError: If input is not a string or not a JSON file
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if not isinstance(file_path, str):
        raise ValueError("Input must be a string path to a JSON file")
    
    if not file_path.lower().endswith('.json'):
        raise ValueError("Input must be a path to a JSON file (ending with .json)")
    
    # Resolve path relative to output folder if provided
    if output_folder:
        from .plot_utils import resolve_relative_path
        resolved_path = resolve_relative_path(file_path, output_folder)
    else:
        resolved_path = file_path
        
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"JSON file not found at path: {file_path}")
        
    try:
        with open(resolved_path, 'r') as f:
            json.load(f)  # Verify file contains valid JSON
    except json.JSONDecodeError:
        raise ValueError(f"File at {file_path} does not contain valid JSON data")
        
    return resolved_path

class PlotDistributionToolConfig(FunctionBaseConfig, name="plot_distribution_tool"):
    """
    NeMo Agent Toolkit function to plot distribution histogram of a specified column.
    """
    output_folder: str = Field(description="The path to the output folder to save plots.", default="./output_data")

@register_function(config_type=PlotDistributionToolConfig)
async def plot_distribution_tool(
    config: PlotDistributionToolConfig, builder: Builder
):
    class PlotDistributionInputSchema(BaseModel):
        data_json_path: str = Field(description="The path to the JSON file containing the data")
        column_name: str = Field(description="The column name to create distribution plot for", default="RUL")
        plot_title: str = Field(description="The title for the plot", default="Distribution Plot")

    from .plot_utils import create_distribution_plot, load_data_from_json

    async def _response_fn(data_json_path: str, column_name: str, plot_title: str) -> str:
        """
        Process the input message and generate distribution histogram file.
        """
        data_json_path = verify_json_path(data_json_path, config.output_folder)
        try:
            # Load data to validate column exists
            df = load_data_from_json(data_json_path, config.output_folder)
            if df is None or df.empty:
                return "Could not load data or data is empty from the provided JSON file"
            
            if column_name not in df.columns:
                return f"Column '{column_name}' not found in data. Available columns: {df.columns.tolist()}"
            
            # Use utility function to create plot
            html_filepath, png_filepath = create_distribution_plot(
                output_dir=config.output_folder,
                data_json_path=data_json_path,
                column_name=column_name,
                title=plot_title
            )
            
            # Build file information for response (relative paths from output folder)
            html_relpath = os.path.relpath(html_filepath, config.output_folder)
            file_info = f"- HTML File: {html_relpath}"
            if png_filepath:
                png_relpath = os.path.relpath(png_filepath, config.output_folder)
                file_info += f"\n- PNG File: {png_relpath}"
            
            # Return a clear completion message that the LLM will understand
            return f"""TASK COMPLETED SUCCESSFULLY

Distribution histogram has been generated and saved in multiple formats.

Chart Details:
- Type: Distribution histogram (30 bins, Plotly)
- Column: {column_name}
- Title: {plot_title}
{file_info}

✅ CHART GENERATION COMPLETE - NO FURTHER ACTION NEEDED"""
            
        except FileNotFoundError as e:
            error_msg = f"Required data file ('{data_json_path}') not found for distribution plot: {e}"
            logger.error(error_msg)
            return error_msg
        except KeyError as ke:
            error_msg = f"Missing expected column '{column_name}' in '{data_json_path}' for distribution plot: {ke}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error generating distribution histogram: {e}"
            logger.error(error_msg)
            return error_msg

    prompt = """
    Generate interactive distribution histogram from JSON data using Plotly.
    Input:
    - data_json_path: Path to the JSON file containing the data
    - column_name: Column name for the distribution histogram
    - plot_title: Title for the plot
    
    Output:
    - HTML file containing the interactive distribution histogram
    - PNG file containing the static distribution histogram
    """
    yield FunctionInfo.from_fn(_response_fn, 
                               input_schema=PlotDistributionInputSchema,
                               description=prompt)
    try:
        pass
    except GeneratorExit:
        logger.info("Plot distribution function exited early!")
    finally:
        logger.info("Cleaning up plot_distribution_tool workflow.")
