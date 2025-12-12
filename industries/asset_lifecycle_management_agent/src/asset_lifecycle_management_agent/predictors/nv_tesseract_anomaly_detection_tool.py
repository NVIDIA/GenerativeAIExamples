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
import numpy as np
import requests
from typing import List, Dict, Any
from pydantic import Field, BaseModel

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)


class NVTesseractAnomalyDetectionToolConfig(FunctionBaseConfig, name="nv_tesseract_anomaly_detection_tool"):
    """
    NeMo Agent Toolkit function to perform anomaly detection using NV Tesseract NIM.
    """
    nim_endpoint: str = Field(
        description="NV Tesseract NIM endpoint URL",
        default="http://localhost:8001"
    )
    timeout: int = Field(
        description="Request timeout in seconds",
        default=120
    )
    output_folder: str = Field(
        description="The path to the output folder to save results.",
        default="./output_data"
    )


@register_function(config_type=NVTesseractAnomalyDetectionToolConfig)
async def nv_tesseract_anomaly_detection_tool(
    config: NVTesseractAnomalyDetectionToolConfig, builder: Builder
):
    class NVTesseractAnomalyDetectionInputSchema(BaseModel):
        sensor_data_json_path: str = Field(
            description="Path to JSON file containing sensor data (from sql_retriever tool)"
        )
        engine_unit: int = Field(
            description="Engine unit number to analyze",
            default=5
        )
        sensor_name: str = Field(
            description="Name of the sensor to analyze (e.g., 'sensor_measurement_1', 'sensor_measurement_4')",
            default="sensor_measurement_1"
        )

    def call_nv_tesseract_nim(data_points: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Call NV Tesseract NIM API for anomaly detection.
        
        Args:
            data_points: List of {"ts": timestamp_or_index, "value": sensor_value}
        
        Returns:
            List of results with added anomaly detection fields
        """
        endpoint = f"{config.nim_endpoint}/v2/detect-anomalies"
        
        try:
            logger.info(f"Calling NV Tesseract NIM at {endpoint}")
            logger.info(f"Sending {len(data_points)} data points")
            
            response = requests.post(
                endpoint,
                json=data_points,
                timeout=config.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            results = response.json()
            
            logger.info(f"Received {len(results)} results from NV Tesseract NIM")
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling NV Tesseract NIM: {e}")
            raise RuntimeError(f"Failed to call NV Tesseract NIM: {e}")

    def prepare_data_for_nim(df: pd.DataFrame, sensor_name: str) -> List[Dict[str, Any]]:
        """Convert DataFrame to NV Tesseract NIM input format.
        
        Args:
            df: DataFrame with time series data
            sensor_name: Name of sensor column to process
        
        Returns:
            List of {"ts": index, "value": sensor_value}
        """
        if sensor_name not in df.columns:
            raise ValueError(f"Sensor '{sensor_name}' not found in data. Available: {df.columns.tolist()}")
        
        data_points = []
        for idx, row in df.iterrows():
            data_points.append({
                "ts": int(idx),  # Use index as timestamp
                "value": float(row[sensor_name])
            })
        
        logger.info(f"Prepared {len(data_points)} data points for NIM")
        return data_points

    def process_nim_results(df: pd.DataFrame, nim_results: List[Dict[str, Any]]) -> pd.DataFrame:
        """Add NIM anomaly detection results to DataFrame.
        
        Args:
            df: Original DataFrame
            nim_results: Results from NIM v2 with Anomaly field (boolean) and MAE metric
        
        Returns:
            DataFrame with added is_anomaly boolean column
        """
        # Extract anomaly labels (boolean in v2.0.0)
        anomalies = [result["Anomaly"] for result in nim_results]
        
        # Add to DataFrame
        df_result = df.copy()
        df_result['is_anomaly'] = [bool(a) for a in anomalies]
        
        # Add MAE metric from NIM v2
        df_result['anomaly_score'] = [result.get("MAE", 0.0) for result in nim_results]
        
        logger.info(f"Processed {len(anomalies)} anomaly results")
        logger.info(f"Detected {sum(anomalies)} anomalies")
        
        return df_result

    async def _response_fn(
        sensor_data_json_path: str,
        engine_unit: int = 5,
        sensor_name: str = "sensor_measurement_1"
    ) -> str:
        """
        Perform anomaly detection using NV Tesseract NIM on JSON data from sql_retriever.
        """
        try:
            # Validate inputs
            if not sensor_data_json_path.lower().endswith('.json'):
                return "sensor_data_json_path must be a path to a JSON file (ending with .json)"
            
            if not os.path.exists(sensor_data_json_path):
                return f"JSON file not found at path: {sensor_data_json_path}"
            
            # Load data from JSON file
            from ..plotting.plot_utils import load_data_from_json
            combined_df = load_data_from_json(sensor_data_json_path, config.output_folder)
            
            if combined_df is None or combined_df.empty:
                return f"Could not load data or data is empty from JSON file: {sensor_data_json_path}"
            
            # Filter for specific engine unit
            if 'unit_number' in combined_df.columns:
                engine_data = combined_df[combined_df['unit_number'] == engine_unit]
                if engine_data.empty:
                    available_units = sorted(combined_df['unit_number'].unique())
                    return f"No data found for engine unit {engine_unit}. Available units: {available_units}"
            else:
                engine_data = combined_df
            
            # Sort by cycle for proper time series analysis
            if 'time_in_cycles' in engine_data.columns:
                engine_data = engine_data.sort_values('time_in_cycles').reset_index(drop=True)
            else:
                engine_data = engine_data.reset_index(drop=True)
            
            logger.info(f"Engine data shape: {engine_data.shape}")
            logger.info(f"Analyzing sensor: {sensor_name}")
            
            # Prepare data for NIM
            data_points = prepare_data_for_nim(engine_data, sensor_name)
            
            # Call NV Tesseract NIM
            logger.info("Calling NV Tesseract NIM for anomaly detection...")
            nim_results = call_nv_tesseract_nim(data_points)
            
            # Process results and add to DataFrame
            result_df = process_nim_results(engine_data, nim_results)
            
            # Calculate summary statistics
            total_anomalies = result_df['is_anomaly'].sum()
            anomaly_rate = (total_anomalies / len(result_df)) * 100
            
            # Save results
            os.makedirs(config.output_folder, exist_ok=True)
            
            if not os.path.isabs(sensor_data_json_path):
                save_path = os.path.join(config.output_folder, os.path.basename(sensor_data_json_path))
            else:
                results_filename = f"nv_tesseract_anomaly_results_engine{engine_unit}.json"
                save_path = os.path.join(config.output_folder, results_filename)
            
            result_df.to_json(save_path, orient='records', indent=2)
            
            # Build response
            response_parts = [
                "NV TESSERACT NIM ANOMALY DETECTION COMPLETED SUCCESSFULLY",
                "",
                f"Analysis Details:",
                f"   • Engine Unit: {engine_unit}",
                f"   • Source Data: {os.path.basename(sensor_data_json_path)}",
                f"   • Sensor Analyzed: {sensor_name}",
                f"   • Model: NV Tesseract (NVIDIA Foundation Model)",
                f"   • NIM Endpoint: {config.nim_endpoint}",
                "",
                f"Anomaly Detection Results:",
                f"   • Total Timesteps Analyzed: {len(result_df)}",
                f"   • Anomalous Timesteps Detected: {total_anomalies}",
                f"   • Anomaly Rate: {anomaly_rate:.2f}%",
                "",
                f"Output Files Generated:",
                f"   • Enhanced Data with is_anomaly Column: {os.path.relpath(save_path, config.output_folder)}",
                "",
                f"Key Insights:",
                f"   • NV Tesseract provides production-grade anomaly detection via NIM",
                f"   • Scalable inference with GPU acceleration",
                f"   • {total_anomalies} anomalous time periods identified",
                "",
                f"Output Format:",
                f"   • Original sensor data with added 'is_anomaly' boolean column",
                f"   • Additional metrics: anomaly_score, lower_threshold, upper_threshold",
                f"   • Use the enhanced JSON file with plot_anomaly_tool for visualization",
                "",
                "NV TESSERACT ANOMALY DETECTION COMPLETE"
            ]
            
            return "\n".join(response_parts)
            
        except Exception as e:
            error_msg = f"Error performing NV Tesseract anomaly detection: {e}"
            logger.error(error_msg)
            return error_msg

    description = """
    Perform production-grade anomaly detection using NV Tesseract foundation model via NVIDIA NIM.
    Outputs detailed anomaly detection results. Use plot_anomaly_tool afterward for visualization.
    
    Input:
      - sensor_data_json_path: File path to JSON containing sensor data with timestamp and engine unit columns
      - engine_unit: Engine unit number to analyze (default: 5)
      - sensor_name: Name of sensor to analyze (e.g., 'sensor_measurement_1', 'sensor_measurement_4')
    
        Output:
          - JSON file with original data plus 'is_anomaly' boolean column
          - Additional NIM v2 metrics (MAE - Mean Absolute Error)
          - Comprehensive analysis summary
    """
    
    yield FunctionInfo.from_fn(
        _response_fn,
        input_schema=NVTesseractAnomalyDetectionInputSchema,
        description=description
    )
    
    try:
        pass
    except GeneratorExit:
        logger.info("NV Tesseract anomaly detection function exited early!")
    finally:
        logger.info("Cleaning up NV Tesseract anomaly detection workflow.")

