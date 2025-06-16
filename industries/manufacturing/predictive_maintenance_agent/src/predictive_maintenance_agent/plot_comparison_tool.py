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
        Generate and save comparison plot as HTML file using Bokeh.
        
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
        import bokeh.plotting as bp
        from bokeh.models import ColumnDataSource, HoverTool, Legend
        from bokeh.embed import file_html
        from bokeh.resources import CDN
        
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
        
        # Create data sources for each line
        line1_source = ColumnDataSource(data=dict(
            x=df_sorted[x_col],
            y=df_sorted[y_col_1],
            label=[y_col_1] * len(df_sorted)
        ))
        
        line2_source = ColumnDataSource(data=dict(
            x=df_sorted[x_col],
            y=df_sorted[y_col_2],
            label=[y_col_2] * len(df_sorted)
        ))
        
        # Create hover tools
        hover_line1 = HoverTool(tooltips=[
            (f"{x_col}", "@x"),
            (f"{y_col_1}", "@y{0.0}"),
            ("Type", "@label")
        ], renderers=[])
        
        hover_line2 = HoverTool(tooltips=[
            (f"{x_col}", "@x"),
            (f"{y_col_2}", "@y{0.0}"),
            ("Type", "@label")
        ], renderers=[])
        
        fig = bp.figure(
            title=title,
            x_axis_label=x_col,
            y_axis_label='Value',
            width=800,  # Increased width to provide more space
            height=450,
            tools=['pan', 'box_zoom', 'wheel_zoom', 'reset', 'save'],
            toolbar_location="above"
        )
        
        # Add the lines
        line2_render = fig.line(
            'x', 'y', source=line2_source,
            line_color='#2E8B57', line_width=3, alpha=0.9,
            legend_label=y_col_2
        )
        
        line1_render = fig.line(
            'x', 'y', source=line1_source,
            line_color='#20B2AA', line_width=3, alpha=0.9,
            line_dash='dashed', legend_label=y_col_1 + (" (Piecewise)" if y_col_1 == "actual_RUL" and rul_transformation_applied else "")
        )
        
        # Add hover tools to specific renderers
        hover_line2.renderers = [line2_render]
        hover_line1.renderers = [line1_render]
        fig.add_tools(hover_line2, hover_line1)
        
        # Style the plot
        fig.title.text_font_size = "16pt"
        fig.title.align = "center"
        fig.xaxis.axis_label_text_font_size = "14pt"
        fig.yaxis.axis_label_text_font_size = "14pt"
        
        # Position legend in bottom right and style it
        fig.legend.location = "bottom_right"
        fig.legend.label_text_font_size = "12pt"
        fig.legend.glyph_width = 30
        fig.legend.background_fill_alpha = 0.8
        fig.legend.background_fill_color = "white"
        fig.legend.border_line_color = "gray"
        fig.legend.border_line_width = 1
        fig.legend.padding = 10
        
        fig.grid.grid_line_alpha = 0.3
        
        # Set axis ranges for better visualization
        y_min = min(df_sorted[y_col_1].min(), df_sorted[y_col_2].min())
        y_max = max(df_sorted[y_col_1].max(), df_sorted[y_col_2].max())
        y_range = y_max - y_min
        fig.y_range.start = max(0, y_min - y_range * 0.05)
        fig.y_range.end = y_max + y_range * 0.05

        # Generate standalone HTML file
        html_content = file_html(fig, CDN, title)
        
        # Save the HTML file
        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f"comparison_plot_{y_col_1}_vs_{y_col_2}.html")
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
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
            return f"""
            TASK COMPLETED SUCCESSFULLY\n\nComparison plot has been generated and saved.
            \n\nChart Details:\n- 
            Type: Comparison plot with two lines\n- X-axis: {x_axis_column}\n- Y-axis Line 1: {y_axis_column_1} (dashed teal)\n- Y-axis Line 2: {y_axis_column_2} (solid green)\n- Title: {plot_title}{rul_info}\n- Output File: {output_filepath}\n- File URL: {file_url}\n\n✅ CHART GENERATION COMPLETE - NO FURTHER ACTION NEEDED
            """
            
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
    Generate interactive comparison plot between two columns from JSON data.
    
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
