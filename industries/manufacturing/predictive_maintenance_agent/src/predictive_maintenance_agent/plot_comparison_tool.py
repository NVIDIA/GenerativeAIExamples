import json
import logging
import os
import pandas as pd

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
        raise ValueError("Input must be a string path to a JSON file")
    
    if not file_path.lower().endswith('.json'):
        raise ValueError("Input must be a path to a JSON file (ending with .json)")
        
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"JSON file not found at path: {file_path}")
        
    try:
        with open(file_path, 'r') as f:
            json.load(f)  # Verify file contains valid JSON
    except json.JSONDecodeError:
        raise ValueError(f"File at {file_path} does not contain valid JSON data")
        
    return file_path

def knee_RUL(cycle_list, max_cycle, MAXLIFE):
    '''
    Piecewise linear function with zero gradient and unit gradient
            ^
            |
    MAXLIFE |-----------
            |            \
            |             \
            |              \
            |               \
            |                \
            |----------------------->
    '''
    knee_RUL_values = []
    if max_cycle >= MAXLIFE:
        knee_point = max_cycle - MAXLIFE
        
        for i in range(0, len(cycle_list)):
            if i < knee_point:
                knee_RUL_values.append(MAXLIFE)
            else:
                tmp = knee_RUL_values[i - 1] - (MAXLIFE / (max_cycle - knee_point))
                knee_RUL_values.append(tmp)
    else:
        knee_point = MAXLIFE
        print("=========== knee_point < MAXLIFE ===========")
        for i in range(0, len(cycle_list)):
            knee_point -= 1
            knee_RUL_values.append(knee_point)
            
    return knee_RUL_values

def apply_piecewise_rul_to_data(df, cycle_col='time_in_cycles', max_life=125):
    """
    Apply piecewise RUL transformation to single-engine data.
    Uses original RUL values to determine proper failure point.
    
    Args:
        df (pd.DataFrame): Input dataframe (single engine)
        cycle_col (str): Column name for cycle/time
        max_life (int): Maximum life parameter for knee_RUL function
        
    Returns:
        pd.DataFrame: DataFrame with transformed RUL column
    """
    df_copy = df.copy()
    
    # Check if cycle column exists
    if cycle_col not in df_copy.columns:
        logger.warning(f"Cycle column '{cycle_col}' not found. Using row index as cycle.")
        df_copy[cycle_col] = range(1, len(df_copy) + 1)
    
    # Get cycle list for single engine
    cycle_list = df_copy[cycle_col].tolist()
    max_cycle_in_data = max(cycle_list)
    
    # Use original RUL values to determine true failure point
    # Following the original GitHub pattern: max_cycle = max(cycle_list) + final_rul
    # Get the final RUL value (RUL at the last cycle in our data)
    final_rul = df_copy.loc[df_copy[cycle_col] == max_cycle_in_data, 'actual_RUL'].iloc[0]
    # True failure point = last cycle in data + remaining RUL
    true_max_cycle = max_cycle_in_data + final_rul
    logger.info(f"Using original RUL data: final_rul={final_rul}, true_failure_cycle={true_max_cycle}")
    
    # Apply knee_RUL function with the true failure point
    rul_values = knee_RUL(cycle_list, true_max_cycle, max_life)
    
    # Replace actual_RUL column with piecewise values
    df_copy['actual_RUL'] = rul_values
    
    return df_copy

class PlotComparisonToolConfig(FunctionBaseConfig, name="plot_comparison_tool"):
    """
    AIQ Toolkit function to plot comparison of two y-axis columns against an x-axis column.
    """
    output_folder: str = Field(description="The path to the output folder to save plots.", default="./output_data")

@register_function(config_type=PlotComparisonToolConfig)
async def plot_comparison_tool(
    config: PlotComparisonToolConfig, builder: Builder
):
    class PlotComparisonInputSchema(BaseModel):
        data_json_path: str = Field(description="The path to the JSON file containing the data")
        x_axis_column: str = Field(description="The column name for x-axis data", default="time_in_cycles")
        y_axis_column_1: str = Field(description="The first column name for y-axis data", default="actual_RUL")
        y_axis_column_2: str = Field(description="The second column name for y-axis data", default="predicted_RUL")
        plot_title: str = Field(description="The title for the plot", default="Comparison Plot")

    def load_data_from_json(json_path: str):
        """Load data from JSON file into a pandas DataFrame."""
        import pandas as pd
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            return pd.DataFrame(data)
        except FileNotFoundError:
            logger.error(f"JSON file not found at {json_path}")
            return None
        except json.JSONDecodeError:
            logger.error(f"Could not decode JSON from {json_path}")
            return None
        except Exception as e:
            logger.error(f"Error loading data from '{json_path}': {e}")
            return None

    def create_comparison_plot_html(output_dir: str, data_json_path: str, x_col: str, y_col_1: str, y_col_2: str, title: str):
        """
        Generate and save comparison plot as HTML file using Plotly.
        
        Args:
            output_dir (str): Directory to save the plot file.
            data_json_path (str): Path to the input JSON data file.
            x_col (str): Column name for x-axis.
            y_col_1 (str): Column name for first y-axis line.
            y_col_2 (str): Column name for second y-axis line.
            title (str): Plot title.
            
        Returns:
            str: Path to the saved HTML file.
        """
        import plotly.graph_objects as go
        import plotly.offline as pyo
        
        df = load_data_from_json(data_json_path)
        if df is None or df.empty:
            raise ValueError(f"Could not load data or data is empty from {data_json_path}")

        # Check required columns
        required_columns = [x_col, y_col_1, y_col_2]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise KeyError(f"Data from {data_json_path} must contain columns: {required_columns}. Missing: {missing_columns}")

        # Apply piecewise RUL transformation if any column is "actual_RUL"
        rul_transformation_applied = False
        if y_col_1 == "actual_RUL" or y_col_2 == "actual_RUL":
            logger.info("Applying piecewise RUL transformation...")
            df = apply_piecewise_rul_to_data(df, x_col)
            rul_transformation_applied = True
            logger.info("Piecewise RUL transformation completed")

        # Sort by x-axis column for proper line plotting
        df_sorted = df.sort_values(x_col)
        
        # Create the comparison plot
        fig = go.Figure()
        
        # Add first line (dashed)
        label_1 = y_col_1 + (" (Piecewise)" if y_col_1 == "actual_RUL" and rul_transformation_applied else "")
        fig.add_trace(go.Scatter(
            x=df_sorted[x_col],
            y=df_sorted[y_col_1],
            mode='lines',
            name=label_1,
            line=dict(color='#20B2AA', width=3, dash='dash'),
            hovertemplate=f'<b>{x_col}</b>: %{{x}}<br>' +
                         f'<b>{label_1}</b>: %{{y:.1f}}<br>' +
                         '<extra></extra>'
        ))
        
        # Add second line (solid)
        fig.add_trace(go.Scatter(
            x=df_sorted[x_col],
            y=df_sorted[y_col_2],
            mode='lines',
            name=y_col_2,
            line=dict(color='#2E8B57', width=3),
            hovertemplate=f'<b>{x_col}</b>: %{{x}}<br>' +
                         f'<b>{y_col_2}</b>: %{{y:.1f}}<br>' +
                         '<extra></extra>'
        ))
        
        # Update layout with styling
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                font=dict(size=16)
            ),
            xaxis=dict(
                title=dict(text=x_col, font=dict(size=14)),
                gridcolor='lightgray',
                gridwidth=0.5
            ),
            yaxis=dict(
                title=dict(text='Value', font=dict(size=14)),
                gridcolor='lightgray',
                gridwidth=0.5
            ),
            width=800,
            height=450,
            plot_bgcolor='white',
            legend=dict(
                x=1,
                y=0,
                xanchor='right',
                yanchor='bottom',
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='gray',
                borderwidth=1,
                font=dict(size=12)
            ),
            hovermode='closest'
        )
        
        # Set y-axis range for better visualization
        y_min = min(df_sorted[y_col_1].min(), df_sorted[y_col_2].min())
        y_max = max(df_sorted[y_col_1].max(), df_sorted[y_col_2].max())
        y_range = y_max - y_min
        fig.update_yaxes(range=[max(0, y_min - y_range * 0.05), y_max + y_range * 0.05])

        # Save the HTML file
        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f"comparison_plot_{y_col_1}_vs_{y_col_2}.html")
        
        # Generate standalone HTML file
        html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
        
        # Create complete HTML page
        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <meta charset="utf-8">
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(full_html)
        logger.info(f"Comparison plot saved to {output_filepath}")
        
        return output_filepath

    async def _response_fn(data_json_path: str, x_axis_column: str, y_axis_column_1: str, y_axis_column_2: str, plot_title: str) -> str:
        """
        Process the input message and generate comparison plot.
        """
        try:
            # Load data to validate columns exist
            df = load_data_from_json(data_json_path)
            if df is None or df.empty:
                return "Could not load data or data is empty from the provided JSON file"
            
            # Check required columns
            required_columns = [x_axis_column, y_axis_column_1, y_axis_column_2]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return f"Data from {data_json_path} must contain columns: {required_columns}. Missing: {missing_columns}"
            
            output_filepath = create_comparison_plot_html(
                output_dir=config.output_folder,
                data_json_path=data_json_path,
                x_col=x_axis_column,
                y_col_1=y_axis_column_1,
                y_col_2=y_axis_column_2,
                title=plot_title
            )
            
            # Convert absolute path to file:// URL for proper browser handling
            file_url = f"file://{output_filepath}"
            
            # Add info about RUL transformation if applied
            rul_info = ""
            if y_axis_column_1 == "actual_RUL" or y_axis_column_2 == "actual_RUL":
                rul_info = f"\n- Piecewise RUL transformation applied (max_life=125)"
            
            # Return a clear completion message that the LLM will understand
            return f"""TASK COMPLETED SUCCESSFULLY

Comparison plot has been generated and saved.

Chart Details:
- Type: Comparison plot with two lines (Plotly)
- X-axis: {x_axis_column}
- Y-axis Line 1: {y_axis_column_1} (dashed teal)
- Y-axis Line 2: {y_axis_column_2} (solid green)
- Title: {plot_title}{rul_info}
- Output File: {output_filepath}
- File URL: {file_url}

✅ CHART GENERATION COMPLETE - NO FURTHER ACTION NEEDED"""
            
        except FileNotFoundError as e:
            error_msg = f"Required data file ('{data_json_path}') not found for comparison plot: {e}"
            logger.error(error_msg)
            return error_msg
        except KeyError as ke:
            error_msg = f"Missing required columns in '{data_json_path}' for comparison plot: {ke}"
            logger.error(error_msg)
            return error_msg
        except ValueError as ve:
            error_msg = f"Data validation error for comparison plot: {ve}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error generating comparison plot: {e}"
            logger.error(error_msg)
            return error_msg

    prompt = """
    Generate interactive comparison plot between two columns from JSON data using Plotly.
    
    Input:
    - data_json_path: Path to the JSON file containing the data
    - x_axis_column: Column name for x-axis data
    - y_axis_column_1: Column name for first y-axis data
    - y_axis_column_2: Column name for second y-axis data
    - plot_title: Title for the plot
    
    Output:
    - HTML file containing the comparison plot
    """
    yield FunctionInfo.from_fn(_response_fn, 
                               input_schema=PlotComparisonInputSchema,
                               description=prompt)
    try:
        pass
    except GeneratorExit:
        logger.info("Plot comparison function exited early!")
    finally:
        logger.info("Cleaning up plot_comparison_tool workflow.")
