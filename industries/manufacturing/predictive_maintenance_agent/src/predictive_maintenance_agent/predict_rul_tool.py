import json
import logging
import os
import warnings
import pickle
import joblib
import numpy as np

from pydantic import Field, BaseModel

from aiq.builder.builder import Builder
from aiq.builder.function_info import FunctionInfo
from aiq.cli.register_workflow import register_function
from aiq.data_models.function import FunctionBaseConfig

logger = logging.getLogger(__name__)

def verify_json_path(file_path: str) -> str:
    """
    Verify that the input is a valid path to a JSON file.
    
    Args:
        file_path (str): Path to verify
        
    Returns:
        str: Verified file path
        
    Raises:
        ValueError: If input is not a string or not a JSON file
        FileNotFoundError: If file does not exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    if not isinstance(file_path, str):
        return "Input must be a string path to a JSON file"
    
    if not file_path.lower().endswith('.json'):
        return "Input must be a path to a JSON file (ending with .json)"
        
    if not os.path.exists(file_path):
        return f"JSON file not found at path: {file_path}"
        
    try:
        with open(file_path, 'r') as f:
            json.load(f)  # Verify file contains valid JSON
    except json.JSONDecodeError:
        return f"File at {file_path} does not contain valid JSON data"
        
    return file_path

class PredictRulToolConfig(FunctionBaseConfig, name="predict_rul_tool"):
    """
    AIQ Toolkit function to predict RUL (Remaining Useful Life) using trained models and provided data.
    """
    # Runtime configuration parameters
    scaler_path: str = Field(description="Path to the trained StandardScaler model.", default="./models/scaler_model.pkl")
    model_path: str = Field(description="Path to the trained XGBoost model.", default="./models/xgb_model_fd001.pkl")
    output_folder: str = Field(description="The path to the output folder to save prediction results.", default="./output_data")

@register_function(config_type=PredictRulToolConfig)
async def predict_rul_tool(
    config: PredictRulToolConfig, builder: Builder
):
    class PredictRulInputSchema(BaseModel):
        json_file_path: str = Field(description="Path to a JSON file containing sensor measurements data for RUL prediction")

    def load_data_from_json(json_path: str):
        """Load data from JSON file into a pandas DataFrame."""
        import pandas as pd
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except FileNotFoundError:
            logger.warn(f"JSON file not found at {json_path}")
            return None
        except json.JSONDecodeError:
            logger.warn(f"Could not decode JSON from {json_path}")
            return None
        except Exception as e:
            logger.warn(f"Error loading data from '{json_path}': {e}")
            return None

    def predict_rul_from_data(data_json_path: str, scaler_path: str, model_path: str, output_dir: str):
        """
        Load data and trained models to make RUL predictions.
        
        Args:
            data_json_path (str): Path to the input JSON data file.
            scaler_path (str): Path to the trained StandardScaler model.
            model_path (str): Path to the trained XGBoost model.
            output_dir (str): Directory to save prediction results (unused - kept for compatibility).
            
        Returns:
            tuple: (predictions array, original file path)
        """
        import pandas as pd
        
        # Suppress warnings
        warnings.filterwarnings("ignore", message="X does not have valid feature names")
        
        # Load the data
        df = load_data_from_json(data_json_path)
        if df is None or df.empty:
            raise ValueError(f"Could not load data or data is empty from {data_json_path}")

        # Prepare features for prediction (exclude non-feature columns if present)
        required_columns = ['sensor_measurement_2', 
                            'sensor_measurement_3', 
                            'sensor_measurement_4', 
                            'sensor_measurement_7', 
                            'sensor_measurement_8', 
                            'sensor_measurement_11', 
                            'sensor_measurement_12', 
                            'sensor_measurement_13', 
                            'sensor_measurement_15', 
                            'sensor_measurement_17', 
                            'sensor_measurement_20', 
                            'sensor_measurement_21']
        feature_columns = [col for col in df.columns if col in required_columns]
        if not feature_columns:
            raise ValueError(f"No valid feature columns found in the data. Available columns: {df.columns.tolist()}")
        
        X_test = df[feature_columns].values
        logger.info(f"Using {len(feature_columns)} features for prediction: {feature_columns}")
        
        # Load the StandardScaler
        try:
            scaler_loaded = joblib.load(scaler_path)
            logger.info(f"Successfully loaded scaler from {scaler_path}")
        except Exception as e:
            raise FileNotFoundError(f"Could not load scaler from {scaler_path}: {e}")
        
        # Transform the test data using the loaded scaler
        X_test_scaled = scaler_loaded.transform(X_test)
        
        # Load the XGBoost model
        try:
            with open(model_path, 'rb') as f:
                xgb_model = pickle.load(f)
            logger.info(f"Successfully loaded XGBoost model from {model_path}")
        except Exception as e:
            raise FileNotFoundError(f"Could not load XGBoost model from {model_path}: {e}")
        
        # Make predictions
        y_pred = xgb_model.predict(X_test_scaled)
        logger.info(f"Generated {len(y_pred)} RUL predictions")
        
        # Create results DataFrame
        results_df = df.copy()
        results_df = results_df.rename(columns={'RUL': 'actual_RUL'})
        results_df['predicted_RUL'] = y_pred
        
        # Save results back to the original JSON file
        results_json = results_df.to_dict('records')
        with open(data_json_path, 'w') as f:
            json.dump(results_json, f, indent=2)
        
        logger.info(f"Prediction results saved back to original file: {data_json_path}")
        
        return y_pred, data_json_path

    async def _response_fn(json_file_path: str) -> str:
        """
        Process the input message and generate RUL predictions using trained models.
        """
        logger.info(f"Input message: {json_file_path}")
        data_json_path = verify_json_path(json_file_path)
        try:
            predictions, output_filepath = predict_rul_from_data(
                data_json_path=data_json_path,
                scaler_path=config.scaler_path,
                model_path=config.model_path,
                output_dir=config.output_folder
            )
            
            # Generate summary statistics
            avg_rul = np.mean(predictions)
            min_rul = np.min(predictions)
            max_rul = np.max(predictions)
            std_rul = np.std(predictions)
            
            # Create response with prediction summary
            response = f"""RUL predictions generated successfully! 📊

**Prediction Summary:**
- **Total predictions:** {len(predictions)}
- **Average RUL:** {avg_rul:.2f} cycles
- **Minimum RUL:** {min_rul:.2f} cycles  
- **Maximum RUL:** {max_rul:.2f} cycles
- **Standard Deviation:** {std_rul:.2f} cycles

**Results saved to:** {output_filepath}

The predictions have been added to the original dataset with column name 'predicted_RUL'. The original JSON file has been updated with the RUL predictions.
All columns from the original dataset have been preserved, and the predicted RUL column has been renamed to 'predicted_RUL' and the actual RUL column has been renamed to 'actual_RUL'."""
            
            return response
            
        except FileNotFoundError as e:
            error_msg = f"Required file not found for RUL prediction: {e}. Please ensure all model files and data are available."
            logger.warn(error_msg)
            return error_msg
        except ValueError as ve:
            error_msg = f"Data validation error for RUL prediction: {ve}. Check the input data format."
            logger.warn(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error during RUL prediction: {e}"
            logger.warn(error_msg)
            return error_msg

    prompt = """
    Predict RUL (Remaining Useful Life) for turbofan engines using trained machine learning models.

    Input:
    - Path to a JSON file containing sensor measurements.
        
    Required columns:
        * sensor_measurement_2
        * sensor_measurement_3
        * sensor_measurement_4
        * sensor_measurement_7
        * sensor_measurement_8
        * sensor_measurement_11
        * sensor_measurement_12
        * sensor_measurement_13
        * sensor_measurement_15
        * sensor_measurement_17
        * sensor_measurement_20
        * sensor_measurement_21

    Process:
    1. Load and preprocess data using StandardScaler
    2. Generate predictions using XGBoost model
    3. Calculate summary statistics (mean, min, max, std dev)
    4. Save predictions to JSON file

    Output:
    - RUL predictions for each engine unit
    - Summary statistics of predictions
    - Updated JSON file with predictions added as 'predicted_RUL' column
    """
    yield FunctionInfo.from_fn(_response_fn, 
                               input_schema=PredictRulInputSchema,
                               description=prompt)
    try:
        pass
    except GeneratorExit:
        logger.info("Predict RUL function exited early!")
    finally:
        logger.info("Cleaning up predict_rul_tool workflow.")