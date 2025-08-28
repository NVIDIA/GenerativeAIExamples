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
from typing import List, Tuple, Optional
from pydantic import Field, BaseModel

from nat.builder.builder import Builder
from nat.builder.function_info import FunctionInfo
from nat.cli.register_workflow import register_function
from nat.data_models.function import FunctionBaseConfig

# Note: Visualization is now handled by the separate plot_anomaly_tool

logger = logging.getLogger(__name__)

# Global model instance - initialized once when module is loaded
_MOMENT_MODEL: Optional[object] = None
_MODEL_DEVICE: Optional[str] = None

def _initialize_moment_model():
    """Initialize MOMENT model once and cache it globally."""
    global _MOMENT_MODEL, _MODEL_DEVICE
    
    if _MOMENT_MODEL is not None:
        logger.info("MOMENT model already initialized, reusing cached instance")
        return _MOMENT_MODEL, _MODEL_DEVICE
    
    try:
        logger.info("Initializing MOMENT-1-small model (one-time setup)...")
        import time
        start_time = time.time()
        
        from momentfm import MOMENTPipeline
        import torch
        
        # Initialize MOMENT pipeline for anomaly detection
        model_name = "MOMENT-1-small"
        _MOMENT_MODEL = MOMENTPipeline.from_pretrained(
            f"AutonLab/{model_name}",
            model_kwargs={"task_name": "reconstruction"}
        )
        _MOMENT_MODEL.init()
        
        # Move model to device
        _MODEL_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _MOMENT_MODEL = _MOMENT_MODEL.to(_MODEL_DEVICE).float()
        
        logger.info(f"MOMENT model initialized and cached in {time.time() - start_time:.2f} seconds on {_MODEL_DEVICE}")
        return _MOMENT_MODEL, _MODEL_DEVICE
        
    except Exception as e:
        logger.error(f"Failed to initialize MOMENT model: {e}")
        raise RuntimeError(f"MOMENT model initialization failed: {e}")

# Pre-initialize the model when module is imported (optional - can be lazy loaded)
try:
    _initialize_moment_model()
    logger.info("MOMENT model pre-loaded successfully")
except Exception as e:
    logger.warning(f"MOMENT model pre-loading failed, will initialize on first use: {e}")
    _MOMENT_MODEL = None
    _MODEL_DEVICE = None


class TimeSeriesAnomalyDetectionToolConfig(FunctionBaseConfig, name="moment_anomaly_detection_tool"):
    """
    NeMo Agent Toolkit function to perform anomaly detection using MOMENT-1-small foundation model.
    """
    output_folder: str = Field(description="The path to the output folder to save results.", default="./output_data")

@register_function(config_type=TimeSeriesAnomalyDetectionToolConfig)
async def moment_anomaly_detection_tool(
    config: TimeSeriesAnomalyDetectionToolConfig, builder: Builder
):
    class MomentAnomalyDetectionInputSchema(BaseModel):
        sensor_data_json_path: str = Field(description="Path to JSON file containing sensor data (from sql_retriever tool)")
        engine_unit: int = Field(description="Engine unit number to analyze", default=5)
        sensor_name: str = Field(description="Name of the sensor to analyze and plot (e.g., 'sensor_measurement_1', 'sensor_measurement_4')", default="sensor_measurement_1")

    def prepare_time_series_data_for_moment(df: pd.DataFrame, sensor_name: str, max_seq_len: int = 224) -> List[np.ndarray]:
        """Prepare time series data for MOMENT model input.
        
        MOMENT expects input shape: (batch_size, num_channels, seq_len)
        For single sensor analysis: (1, 1, seq_len) where seq_len <= 512
        
        Args:
            df: DataFrame with sensor data
            sensor_name: Name of the sensor column to process
            max_seq_len: Maximum sequence length (224 for MOMENT-1-small optimal)
        
        Returns:
            List of sequences with shape (1, 1, seq_len) - all patch-aligned
        """
        try:
            # Select single sensor column
            sensor_data = df[sensor_name].values
            logger.info(f"Original sensor data shape: {sensor_data.shape}")
            
            # Normalize the data
            from sklearn.preprocessing import StandardScaler
            scaler = StandardScaler()
            normalized_data = scaler.fit_transform(sensor_data.reshape(-1, 1)).flatten()
            logger.info(f"Normalized sensor data shape: {normalized_data.shape}")
            
            # Split data into chunks of max_seq_len
            sequences = []
            total_length = len(normalized_data)
            PATCH_LEN = 8  # MOMENT's default patch length
            
            i = 0
            while i < total_length:
                chunk = normalized_data[i:i + max_seq_len]
                
                # Truncate to largest multiple of PATCH_LEN (discard non-aligned timesteps)
                current_len = len(chunk)
                aligned_len = (current_len // PATCH_LEN) * PATCH_LEN
                
                if aligned_len > 0:  # Only keep if we have at least one complete patch
                    chunk = chunk[:aligned_len]
                    sequence = chunk.reshape(1, 1, -1)
                    sequences.append(sequence)
                    logger.info(f"Truncated sequence from {current_len} to {aligned_len} (discarded {current_len - aligned_len} timesteps)")
                else:
                    logger.info(f"Skipped sequence of length {current_len} (less than one patch)")
                
                i += max_seq_len
                
            logger.info(f"Created {len(sequences)} sequences, shapes: {[seq.shape for seq in sequences]}")
            
            return sequences
            
        except Exception as e:
            logger.error(f"Error preparing time series data for MOMENT: {e}")
            return None

    def create_moment_dataset(sequences: List[np.ndarray]):
        """Create a dataset compatible with MOMENT from sequences (all same length after truncation)."""
        import torch
        from torch.utils.data import TensorDataset
        
        data_tensors = []
        labels = []
        
        for seq in sequences:
            # seq shape: (1, 1, seq_len) -> squeeze to (1, seq_len)
            seq_squeezed = seq.squeeze(0)  # Remove first dimension: (1, seq_len)
            data_tensors.append(torch.FloatTensor(seq_squeezed))
            labels.append(torch.tensor(0))  # Dummy label
        
        # All sequences now have patch-aligned lengths - stacking will work
        data = torch.stack(data_tensors)  # (num_sequences, 1, seq_len)
        labels = torch.stack(labels)     # (num_sequences,)
        
        logger.info(f"Dataset created - data shape: {data.shape}")
        
        return TensorDataset(data, labels)

    def detect_anomalies_with_moment(sequences: List[np.ndarray], threshold_percentile: float) -> Tuple[np.ndarray, np.ndarray]:
        """Detect anomalies using MOMENT-1-small foundation model following the official tutorial.
        
        Args:
            sequences: List of sequences with shape (1, 1, seq_len)
            threshold_percentile: Percentile for anomaly threshold
        
        Returns:
            anomalies: Boolean array indicating anomalies
            anomaly_scores: Array of reconstruction error scores (per timestep)
        """
        logger.info("Starting MOMENT-based anomaly detection...")
        
        from torch.utils.data import DataLoader
        from tqdm import tqdm
        import torch
        
        # Use pre-initialized global model or initialize if needed
        model, device = _initialize_moment_model()
        
        logger.info(f"Using cached MOMENT-1-small model for anomaly detection")
        logger.info(f"Number of sequences to process: {len(sequences)}")
        if sequences:
            logger.info(f"Each sequence shape: {sequences[0].shape}")
        
        # Create dataset without masks
        dataset = create_moment_dataset(sequences)  # Simplified call
        dataloader = DataLoader(dataset, batch_size=32, shuffle=False, drop_last=False)
        logger.info(f"Using device: {device}")
        
        # Process batches following the tutorial pattern
        model.eval()
        trues, preds = [], []
        with torch.no_grad():
            for batch_data in tqdm(dataloader, total=len(dataloader), desc="Processing batches"):
                # Unpack - now only batch_x and batch_labels (no masks)
                if len(batch_data) == 2:
                    batch_x, batch_labels = batch_data
                else:
                    batch_x, batch_masks, batch_labels = batch_data  # Fallback for old format
                    
                batch_x = batch_x.to(device).float()
                
                logger.info(f"Input batch_x shape: {batch_x.shape}")
                
                # MOMENT forward pass WITHOUT input_mask
                output = model(x_enc=batch_x)  # Simplified - no mask parameter
                
                logger.info(f"Output reconstruction shape: {output.reconstruction.shape}")
                
                # Continue with existing processing...
                batch_x_np = batch_x.detach().cpu().numpy()
                reconstruction_np = output.reconstruction.detach().cpu().numpy()
                
                # Handle potential shape differences (if any)
                if batch_x_np.shape != reconstruction_np.shape:
                    logger.warning(f"Shape mismatch: input {batch_x_np.shape} vs reconstruction {reconstruction_np.shape}")
                    min_seq_len = min(batch_x_np.shape[-1], reconstruction_np.shape[-1])
                    batch_x_np = batch_x_np[..., :min_seq_len]
                    reconstruction_np = reconstruction_np[..., :min_seq_len]
                    logger.info(f"Aligned shapes: input {batch_x_np.shape}, reconstruction {reconstruction_np.shape}")
                
                # Flatten to 1D for each sample in the batch
                for i in range(batch_x_np.shape[0]):
                    true_seq = batch_x_np[i].flatten()
                    pred_seq = reconstruction_np[i].flatten()
                    
                    trues.append(true_seq)
                    preds.append(pred_seq)
        
        # Concatenate all results
        trues = np.concatenate(trues, axis=0)
        preds = np.concatenate(preds, axis=0)
        
        logger.info(f"Final concatenated shapes - trues: {trues.shape}, preds: {preds.shape}")
        
        # Ensure shapes match for calculation (they should already match due to our alignment above)
        if len(trues) != len(preds):
            min_length = min(len(trues), len(preds))
            logger.warning(f"Final shape mismatch: trues={len(trues)}, preds={len(preds)}. Trimming to {min_length}")
            trues = trues[:min_length]
            preds = preds[:min_length]
        else:
            logger.info(f"Shapes are aligned: trues={len(trues)}, preds={len(preds)}")
        
        # Calculate anomaly scores using MSE (following tutorial)
        anomaly_scores = (trues - preds) ** 2
        
        # Determine anomaly threshold
        threshold = np.percentile(anomaly_scores, threshold_percentile)
        anomalies = anomaly_scores > threshold
        
        logger.info(f"MOMENT Anomaly Detection: {np.sum(anomalies)} anomalies detected out of {len(anomalies)} timesteps")
        logger.info(f"Anomaly threshold ({threshold_percentile}th percentile): {threshold:.6f}")
        logger.info(f"Anomaly scores range: {np.min(anomaly_scores):.6f} - {np.max(anomaly_scores):.6f}")
        
        return anomalies
            


    async def _response_fn(
        sensor_data_json_path: str,
        engine_unit: int = 5,
        sensor_name: str = "sensor_measurement_1"
    ) -> str:
        """
        Perform anomaly detection using MOMENT-1-Small foundation model on JSON data from sql_retriever.
        """
        # Set default parameters (not exposed to LLM)ensor
        threshold_percentile = 95.0
        
        try:
            if not sensor_data_json_path.lower().endswith('.json'):
                return "sensor_data_json_path must be a path to a JSON file (ending with .json)"
                
            if not os.path.exists(sensor_data_json_path):
                return f"JSON file not found at path: {sensor_data_json_path}"
            
            # Load data from JSON file (output from sql_retriever)
            from ..plotting.plot_utils import load_data_from_json
            combined_df = load_data_from_json(sensor_data_json_path, config.output_folder)
            
            if combined_df is None or combined_df.empty:
                return f"Could not load data or data is empty from JSON file: {sensor_data_json_path}"
            
            # Filter for specific engine unit if specified
            if 'unit_number' in combined_df.columns:
                engine_data = combined_df[combined_df['unit_number'] == engine_unit]
                if engine_data.empty:
                    return f"No data found for engine unit {engine_unit} in the provided JSON file. Available units: {sorted(combined_df['unit_number'].unique())}"
                
            # Sort by cycle for proper time series analysis
            if 'time_in_cycles' in engine_data.columns:
                engine_data = engine_data.sort_values('time_in_cycles').reset_index(drop=True)
            
            logger.info(f"Engine data shape: {engine_data.shape}")
            logger.info(f"Analyzing sensor: {sensor_name}")
            logger.info(f"MOMENT sequence length: 512")
            
            # Prepare time series data for MOMENT (single sensor)
            sequences = prepare_time_series_data_for_moment(engine_data, sensor_name, max_seq_len=224)
            
            if sequences is None:
                return "Failed to prepare time series data for MOMENT analysis"
            
            logger.info("Starting MOMENT-based anomaly detection...")
            anomaly_indices = detect_anomalies_with_moment(sequences, threshold_percentile)
            
            # Add is_anomaly column to the original dataframe
            # Handle case where MOMENT output length differs from input length
            if len(anomaly_indices) == len(engine_data):
                engine_data['is_anomaly'] = anomaly_indices
            elif len(anomaly_indices) < len(engine_data):
                # MOMENT output is shorter - pad with False for remaining timesteps
                padded_anomalies = np.zeros(len(engine_data), dtype=bool)
                padded_anomalies[:len(anomaly_indices)] = anomaly_indices
                engine_data['is_anomaly'] = padded_anomalies
                logger.warning(f"MOMENT output length ({len(anomaly_indices)}) < input length ({len(engine_data)}). Padded with False.")
            else:
                # MOMENT output is longer - trim to match input length
                engine_data['is_anomaly'] = anomaly_indices[:len(engine_data)]
                logger.warning(f"MOMENT output length ({len(anomaly_indices)}) > input length ({len(engine_data)}). Trimmed to match.")
            
            # Calculate summary statistics using the final anomaly column
            final_anomalies = engine_data['is_anomaly']
            total_anomalies = np.sum(final_anomalies)
            anomaly_rate = total_anomalies / len(final_anomalies) * 100
            
            # Save results
            os.makedirs(config.output_folder, exist_ok=True)
            
            # Save the original data with is_anomaly column added
            # For saving, we want to save relative to output_folder if the original path was relative
            if not os.path.isabs(sensor_data_json_path):
                save_path = os.path.join(config.output_folder, os.path.basename(sensor_data_json_path))
            else:
                # If it was an absolute path, create a results file in output folder
                results_filename = f"moment_anomaly_results_engine{engine_unit}.json"
                save_path = os.path.join(config.output_folder, results_filename)
                
            engine_data.to_json(save_path, orient='records', indent=2)
            results_filepath = save_path
            
            # Build comprehensive response
            response_parts = [
                "MOMENT-1-Small FOUNDATION MODEL ANOMALY DETECTION COMPLETED SUCCESSFULLY",
                "",
                f"Analysis Details:",
                f"   • Engine Unit: {engine_unit}",
                f"   • Source Data: {os.path.basename(sensor_data_json_path)}",
                f"   • Sensor Analyzed: {sensor_name}",
                f"   • Model: MOMENT-1-Small Foundation Model",
                f"   • Max Sequence Length: 512",
                f"   • Threshold Percentile: {threshold_percentile}%",
                "",
                f"Anomaly Detection Results:",
                f"   • Total Timesteps Analyzed: {len(final_anomalies)}",
                f"   • Anomalous Timesteps Detected: {total_anomalies}",
                f"   • Anomaly Rate: {anomaly_rate:.2f}%",
                "",
                f"Output Files Generated:",
                f"   • Enhanced Data with is_anomaly Column: {os.path.relpath(results_filepath, config.output_folder)}"
            ]
            
            response_parts.extend([
                "",
                f"Key Insights:",
                f"   • MOMENT-1-Small foundation model provides state-of-the-art time series anomaly detection",
                f"   • Pre-trained on diverse time series data for superior pattern recognition without additional training",
                f"   • {total_anomalies} anomalous time periods identified out of {len(final_anomalies)} analyzed sequences",
                "",
                f"Output Format:",
                f"   • Original sensor data with added 'is_anomaly' boolean column",
                f"   • Use the enhanced JSON file with plot_anomaly_tool for visualization",
                "",
                "MOMENT-1-Small ANOMALY DETECTION COMPLETE"
            ])
            
            return "\n".join(response_parts)
            
        except Exception as e:
            error_msg = f"Error performing MOMENT-based anomaly detection: {e}"
            logger.error(error_msg)
            return error_msg

    description = """
    Perform state-of-the-art anomaly detection using MOMENT-1-Small foundation model on sensor data from JSON files.
    Outputs detailed anomaly detection results. Use plot_anomaly_tool afterward for visualization.
    
    Input:
      - sensor_data_json_path: File path to a JSON containing sensor data. The file must include timestamp and engine unit number columns along with sensor data columns.
      - engine_unit: Engine unit number to analyze (default: 5)
      - sensor_name: Name of the specific sensor to analyze and plot (e.g., 'sensor_measurement_1', 'sensor_measurement_4', 'sensor_measurement_7', 'sensor_measurement_11') (default: 'sensor_measurement_1')
    
    Output:
    - JSON file containing original sensor data with added 'is_anomaly' boolean column 
    - Comprehensive analysis summary with key insights
    """
    
    yield FunctionInfo.from_fn(_response_fn, 
                               input_schema=MomentAnomalyDetectionInputSchema,
                               description=description)
    try:
        pass
    except GeneratorExit:
        logger.info("moment based anomaly detection function exited early!")
    finally:
        logger.info("Cleaning up moment based anomaly detection workflow.")