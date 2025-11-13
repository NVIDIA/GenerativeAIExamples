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

logger = logging.getLogger(__name__)

# Global MOMENT model cache - key is forecast_horizon, value is (model, device)
_MOMENT_MODEL_CACHE: dict = {}

def _initialize_moment_model(forecast_horizon: int = 96):
    """Initialize MOMENT model and cache it for specific forecast horizon."""
    global _MOMENT_MODEL_CACHE
    
    # Check if we already have a model for this forecast horizon
    if forecast_horizon in _MOMENT_MODEL_CACHE:
        logger.info(f"MOMENT model already initialized for horizon {forecast_horizon}, reusing cached instance")
        return _MOMENT_MODEL_CACHE[forecast_horizon]
    
    try:
        logger.info(f"Initializing MOMENT-1-small model for forecasting horizon {forecast_horizon}...")
        import time
        start_time = time.time()
        
        from momentfm import MOMENTPipeline
        import torch
        
        # Initialize MOMENT pipeline for forecasting
        model_name = "MOMENT-1-small"
        model = MOMENTPipeline.from_pretrained(
            f"AutonLab/{model_name}",
            model_kwargs={
                'task_name': 'forecasting',
                'forecast_horizon': forecast_horizon
            }
        )
        model.init()
        
        # Move model to device
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model = model.to(device).float()
        
        # Cache the model for this forecast horizon
        _MOMENT_MODEL_CACHE[forecast_horizon] = (model, device)
        
        logger.info(f"MOMENT model initialized and cached in {time.time() - start_time:.2f} seconds on {device}")
        return model, device
        
    except Exception as e:
        logger.error(f"Failed to initialize MOMENT model: {e}")
        raise RuntimeError(f"MOMENT model initialization failed: {e}")

# Don't pre-initialize the model since forecast_horizon may vary
# Initialize on first use with the correct forecast_horizon
logger.info("MOMENT model will be initialized on first use with correct forecast_horizon")


class MomentPredictRulToolConfig(FunctionBaseConfig, name="moment_predict_rul_tool"):
    """
    NeMo Agent Toolkit function to predict RUL using MOMENT-1-small foundation model forecasting.
    """
    forecast_horizon: int = Field(description="Number of future timesteps to forecast for trend analysis", default=50)
    failure_threshold: float = Field(description="Degradation threshold in normalized space to indicate failure", default=-2.0)
    max_rul_cycles: int = Field(description="Maximum RUL prediction to cap unrealistic values", default=500)
    output_folder: str = Field(description="Path to output folder to save results", default="./output_data")

@register_function(config_type=MomentPredictRulToolConfig)
async def moment_predict_rul_tool(
    config: MomentPredictRulToolConfig, builder: Builder
):
    class MomentPredictRulInputSchema(BaseModel):
        sensor_data_json_path: str = Field(description="Path to JSON file containing sensor measurements data for RUL prediction")
        engine_unit: int = Field(description="Specific engine unit to analyze (optional, analyzes all if not specified)", default=None)

    def load_data_from_json(json_path: str, output_folder: str = None) -> pd.DataFrame:
        """Load data from JSON file into a pandas DataFrame."""
        try:
            # Resolve path relative to output folder if provided
            if output_folder:
                if os.path.isabs(json_path):
                    # If absolute path exists, use it
                    if os.path.exists(json_path):
                        resolved_path = json_path
                    else:
                        # If absolute path doesn't exist, try relative to output folder
                        basename = os.path.basename(json_path)
                        resolved_path = os.path.join(output_folder, basename)
                else:
                    # If relative path, first try relative to output folder
                    relative_to_output = os.path.join(output_folder, json_path)
                    if os.path.exists(relative_to_output):
                        resolved_path = relative_to_output
                    else:
                        # Then try as provided (relative to current working directory)
                        resolved_path = json_path
            else:
                resolved_path = json_path
                
            with open(resolved_path, 'r') as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            logger.info(f"Loaded data with shape: {df.shape}")
            return df
        except FileNotFoundError:
            logger.error(f"JSON file not found at {json_path}")
            raise FileNotFoundError(f"JSON file not found at {json_path}")
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {json_path}")
            raise ValueError(f"Invalid JSON format in {json_path}")
        except Exception as e:
            logger.error(f"Error loading data from '{json_path}': {e}")
            raise

    def prepare_sensor_data_for_moment(df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """Prepare sensor data for MOMENT input with proper normalization."""
        from sklearn.preprocessing import StandardScaler
        
        # Extract sensor data
        sensor_data = df[feature_columns].values
        logger.info(f"Raw sensor data shape: {sensor_data.shape}")
        
        # Normalize the data
        scaler = StandardScaler()
        normalized_data = scaler.fit_transform(sensor_data)
        logger.info(f"Normalized sensor data shape: {normalized_data.shape}")
        
        return normalized_data, scaler

    def forecast_sensor_degradation(model, device, sensor_data: np.ndarray, 
                                   sequence_length: int, forecast_horizon: int) -> np.ndarray:
        """Use MOMENT model to forecast sensor degradation patterns.
        
        Process each sensor individually as MOMENT forecasting works better with univariate time series.
        """
        import torch
        
        # MOMENT model expects exactly 512 timesteps for proper operation
        expected_seq_len = 512
        
        if len(sensor_data) < expected_seq_len:
            # Pad with zeros if insufficient data (front padding to preserve recent trends)
            padded_data = np.zeros((expected_seq_len, sensor_data.shape[1]))
            padded_data[-len(sensor_data):] = sensor_data
            input_data = padded_data
            logger.warning(f"Data length {len(sensor_data)} < expected_seq_len {expected_seq_len}. Padded with zeros.")
        else:
            # Take the last 512 timesteps
            input_data = sensor_data[-expected_seq_len:]
        
        logger.info(f"Final input data shape for MOMENT: {input_data.shape}")
        
        num_sensors = input_data.shape[1]
        seq_len = input_data.shape[0]
        
        logger.info(f"Processing {num_sensors} sensors individually, each with {seq_len} timesteps")
        
        all_forecasts = []
        
        # Process each sensor individually (univariate forecasting)
        for sensor_idx in range(num_sensors):
            try:
                # Extract single sensor time series
                sensor_ts = input_data[:, sensor_idx]  # Shape: (seq_len,)
                
                # Convert to tensor format: (batch_size=1, num_channels=1, seq_len)
                input_tensor = torch.FloatTensor(sensor_ts).unsqueeze(0).unsqueeze(0).to(device)  # (1, 1, seq_len)
                
                # Create input mask (all True since we don't have missing values)
                input_mask = torch.ones(seq_len, dtype=torch.bool).unsqueeze(0).to(device)  # (1, seq_len)
                
                with torch.no_grad():
                    # MOMENT forecasting for single sensor
                    forecast_output = model(x_enc=input_tensor, input_mask=input_mask)
                    forecast = forecast_output.forecast.cpu().numpy()  # Shape: (1, 1, forecast_horizon)
                    
                # Extract forecast for this sensor
                sensor_forecast = forecast.squeeze()  # Shape: (forecast_horizon,)
                all_forecasts.append(sensor_forecast)
                
                logger.info(f"Sensor {sensor_idx}: input shape {input_tensor.shape}, forecast shape {sensor_forecast.shape}")
                
            except Exception as e:
                logger.warning(f"Error forecasting sensor {sensor_idx}: {e}. Using zero forecast.")
                # Use zero forecast as fallback
                zero_forecast = np.zeros(forecast_horizon)
                all_forecasts.append(zero_forecast)
        
        # Combine all sensor forecasts
        combined_forecast = np.array(all_forecasts)  # Shape: (num_sensors, forecast_horizon)
        logger.info(f"Combined forecast shape: {combined_forecast.shape}")
        
        return combined_forecast

    def calculate_rul_from_degradation(current_values: np.ndarray, 
                                     forecasted_values: np.ndarray,
                                     forecast_horizon: int,
                                     failure_threshold: float,
                                     max_rul_cycles: int) -> float:
        """Calculate RUL based on sensor degradation trends.
        
        Args:
            current_values: Current sensor values, shape (num_sensors,)
            forecasted_values: Forecasted sensor values, shape (num_sensors, forecast_horizon)
            forecast_horizon: Number of forecast timesteps
            failure_threshold: Degradation threshold for failure
            max_rul_cycles: Maximum RUL prediction
        """
        
        # Calculate degradation rate across all sensors
        degradation_rates = []
        
        for i in range(len(current_values)):
            # Calculate degradation rate for each sensor using final forecasted value
            final_forecasted_value = forecasted_values[i, -1]  # Last forecasted timestep
            sensor_degradation_rate = (final_forecasted_value - current_values[i]) / forecast_horizon
            degradation_rates.append(sensor_degradation_rate)
        
        # Use average degradation rate
        avg_degradation_rate = np.mean(degradation_rates)
        current_degradation = np.mean(current_values)
        
        logger.info(f"Current degradation level: {current_degradation:.4f}")
        logger.info(f"Average degradation rate: {avg_degradation_rate:.6f}")
        logger.info(f"Individual sensor degradation rates: {[f'{rate:.6f}' for rate in degradation_rates]}")
        
        if avg_degradation_rate < 0:  # System is degrading
            # Calculate cycles until failure threshold is reached
            cycles_to_failure = (failure_threshold - current_degradation) / avg_degradation_rate
            rul_prediction = max(1, min(cycles_to_failure, max_rul_cycles))
        else:
            # System is improving or stable - predict high RUL
            rul_prediction = max_rul_cycles * 0.8  # 80% of max as conservative estimate
        
        return float(rul_prediction)

    def predict_rul_for_engine_unit(df: pd.DataFrame, unit_id: int, feature_columns: List[str],
                                   model, device) -> Tuple[float, dict]:
        """Predict RUL for a specific engine unit using MOMENT forecasting."""
        
        unit_data = df[df['unit_number'] == unit_id].copy()
        
        # Sort by time for proper time series analysis
        if 'time_in_cycles' in unit_data.columns:
            unit_data = unit_data.sort_values('time_in_cycles').reset_index(drop=True)
        
        logger.info(f"Processing engine unit {unit_id} with {len(unit_data)} timesteps")
        
        # Prepare sensor data
        normalized_data, scaler = prepare_sensor_data_for_moment(unit_data, feature_columns)
        
        if len(normalized_data) < 10:  # Need minimum data for meaningful prediction
            logger.warning(f"Insufficient data for unit {unit_id} ({len(normalized_data)} timesteps)")
            return config.max_rul_cycles * 0.5, {"status": "insufficient_data"}
        
        # Forecast sensor degradation using MOMENT's expected sequence length
        forecast = forecast_sensor_degradation(
            model, device, normalized_data, 
            512,  # MOMENT expects 512 timesteps
            config.forecast_horizon
        )
        
        # Calculate RUL
        current_values = normalized_data[-1]  # Last known sensor values (shape: num_sensors)
        forecasted_values = forecast  # Forecasted sensor values (shape: num_sensors, forecast_horizon)
        
        rul_prediction = calculate_rul_from_degradation(
            current_values, forecasted_values, 
            config.forecast_horizon, config.failure_threshold, config.max_rul_cycles
        )
        
        # Additional metrics for analysis
        final_forecasted_values = forecasted_values[:, -1]  # Last timestep of each sensor forecast
        metrics = {
            "rul_prediction": rul_prediction,
            "current_degradation": float(np.mean(current_values)),
            "forecast_degradation": float(np.mean(final_forecasted_values)),
            "degradation_rate": float((np.mean(final_forecasted_values) - np.mean(current_values)) / config.forecast_horizon),
            "data_points": len(unit_data),
            "sensors_analyzed": len(feature_columns),
            "forecast_horizon": config.forecast_horizon,
            "status": "success"
        }
        
        return rul_prediction, metrics

    async def _response_fn(
        sensor_data_json_path: str,
        engine_unit: int = None
    ) -> str:
        """
        Predict RUL using MOMENT-1-small foundation model forecasting.
        """
        try:
            # Validate file path
            if not sensor_data_json_path.lower().endswith('.json'):
                return "sensor_data_json_path must be a path to a JSON file (ending with .json)"
                
            if not os.path.exists(sensor_data_json_path):
                return f"JSON file not found at path: {sensor_data_json_path}"
            
            # Load data
            df = load_data_from_json(sensor_data_json_path, config.output_folder)
            
            if df.empty:
                return f"No data found in JSON file: {sensor_data_json_path}"
            
            # Define required sensor columns (same as traditional RUL models)
            required_columns = [
                'sensor_measurement_2', 'sensor_measurement_3', 'sensor_measurement_4', 
                'sensor_measurement_7', 'sensor_measurement_8', 'sensor_measurement_11', 
                'sensor_measurement_12', 'sensor_measurement_13', 'sensor_measurement_15', 
                'sensor_measurement_17', 'sensor_measurement_20', 'sensor_measurement_21'
            ]
            
            feature_columns = [col for col in df.columns if col in required_columns]
            if not feature_columns:
                return f"No valid sensor columns found. Available columns: {df.columns.tolist()}"
            
            logger.info(f"Using {len(feature_columns)} sensor features: {feature_columns}")
            
            # Initialize MOMENT model
            model, device = _initialize_moment_model(config.forecast_horizon)
            
            # Determine which engines to process
            if 'unit_number' in df.columns:
                if engine_unit is not None:
                    engine_units = [engine_unit] if engine_unit in df['unit_number'].unique() else []
                    if not engine_units:
                        available_units = sorted(df['unit_number'].unique())
                        return f"Engine unit {engine_unit} not found. Available units: {available_units}"
                else:
                    engine_units = sorted(df['unit_number'].unique())
            else:
                # No unit column - treat as single engine
                df['unit_number'] = 1
                engine_units = [1]
            
            logger.info(f"Processing {len(engine_units)} engine units: {engine_units}")
            
            # Process each engine unit
            results = []
            all_predictions = []
            unit_metrics = {}
            
            for unit_id in engine_units:
                try:
                    rul_pred, metrics = predict_rul_for_engine_unit(
                        df, unit_id, feature_columns, model, device
                    )
                    
                    results.append({
                        "unit_number": unit_id,
                        "predicted_RUL": rul_pred,
                        **metrics
                    })
                    
                    # Add predictions to all timesteps for this unit
                    unit_data = df[df['unit_number'] == unit_id]
                    unit_predictions = [rul_pred] * len(unit_data)
                    all_predictions.extend(unit_predictions)
                    unit_metrics[unit_id] = metrics
                    
                    logger.info(f"Unit {unit_id}: Predicted RUL = {rul_pred:.1f} cycles")
                    
                except Exception as e:
                    logger.error(f"Error processing unit {unit_id}: {e}")
                    results.append({
                        "unit_number": unit_id,
                        "predicted_RUL": None,
                        "status": "error",
                        "error": str(e)
                    })
            
            if not all_predictions:
                return "No successful RUL predictions could be generated"
            
            # Add predictions to original DataFrame
            df_result = df.copy()
            if 'RUL' in df_result.columns:
                df_result = df_result.rename(columns={'RUL': 'actual_RUL'})
            df_result['predicted_RUL'] = all_predictions
            
            # Save results back to the original JSON file (consistent with predict_rul_tool)
            # For saving, we want to save relative to output_folder if the original path was relative
            if not os.path.isabs(sensor_data_json_path):
                save_path = os.path.join(config.output_folder, os.path.basename(sensor_data_json_path))
            else:
                save_path = sensor_data_json_path
                
            results_json = df_result.to_dict('records')
            with open(save_path, 'w') as f:
                json.dump(results_json, f, indent=2)
            
            logger.info(f"MOMENT RUL prediction results saved back to file: {save_path}")
            results_filepath = save_path
            
            # Generate summary statistics
            valid_predictions = [p for p in all_predictions if p is not None]
            avg_rul = np.mean(valid_predictions)
            min_rul = np.min(valid_predictions)
            max_rul = np.max(valid_predictions)
            std_rul = np.std(valid_predictions)
            
            # Build response similar to predict_rul_tool format (relative path from output folder)
            results_relpath = os.path.relpath(results_filepath, config.output_folder)
            response = f"""RUL predictions generated successfully! 📊

**Model Used:** MOMENT-1-Small Foundation Model (Time Series Forecasting)

**Prediction Summary:**
- **Total predictions:** {len(valid_predictions)}
- **Average RUL:** {avg_rul:.2f} cycles
- **Minimum RUL:** {min_rul:.2f} cycles  
- **Maximum RUL:** {max_rul:.2f} cycles
- **Standard Deviation:** {std_rul:.2f} cycles

**Results saved to:** {results_relpath}

The predictions have been added to the original dataset with column name 'predicted_RUL'. The original JSON file has been updated with the RUL predictions.
All columns from the original dataset have been preserved, and the predicted RUL column has been renamed to 'predicted_RUL' and the actual RUL column has been renamed to 'actual_RUL'."""
            
            return response
            
        except Exception as e:
            error_msg = f"Error performing MOMENT-based RUL prediction: {e}"
            logger.error(error_msg)
            return error_msg

    description = """
    Predict RUL (Remaining Useful Life) using MOMENT-1-small foundation model with time series forecasting.
    
    This tool leverages the power of foundation models to forecast sensor degradation patterns and predict 
    remaining useful life without requiring domain-specific training data.
    
    Input:
      - sensor_data_json_path: Path to JSON file containing sensor measurements
      - engine_unit: Specific engine unit to analyze (optional, analyzes all units if not specified)
    
    Required Sensor Columns:
      • sensor_measurement_2, sensor_measurement_3, sensor_measurement_4
      • sensor_measurement_7, sensor_measurement_8, sensor_measurement_11  
      • sensor_measurement_12, sensor_measurement_13, sensor_measurement_15
      • sensor_measurement_17, sensor_measurement_20, sensor_measurement_21

    Output:
      - RUL predictions for each engine unit based on sensor forecasting
      - Detailed degradation analysis and trend metrics
      - Original JSON file updated with predictions added as 'predicted_RUL' column
      - Foundation model insights and confidence indicators
    """
    
    yield FunctionInfo.from_fn(_response_fn, 
                               input_schema=MomentPredictRulInputSchema,
                               description=description)
    try:
        pass
    except GeneratorExit:
        logger.info("MOMENT RUL prediction function exited early!")
    finally:
        logger.info("Cleaning up MOMENT RUL prediction workflow.")
