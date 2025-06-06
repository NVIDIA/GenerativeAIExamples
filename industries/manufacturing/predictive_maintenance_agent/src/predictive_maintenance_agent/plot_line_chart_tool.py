import json
import logging
import os

from pydantic import Field

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

class PlotLineChartToolConfig(FunctionBaseConfig, name="plot_line_chart_tool"):
    """
    AIQ Toolkit function to plot a line chart with specified x and y axis columns.
    """
    # Configuration parameters
    # data_json_path: str = Field(description="The path to the JSON file containing the data.", default="./output_data/sql_output.json")
    # x_axis_column: str = Field(description="The column name for x-axis data.", default="time_in_cycles")
    # y_axis_column: str = Field(description="The column name for y-axis data.", default="RUL")
    # plot_title: str = Field(description="The title for the plot.", default="Line Chart")
    output_folder: str = Field(description="The path to the output folder to save plots.", default="./output_data")

@register_function(config_type=PlotLineChartToolConfig)
async def plot_line_chart_tool(
    config: PlotLineChartToolConfig, builder: Builder
):
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

    def create_line_chart_plot_html(output_dir: str, data_json_path: str, x_col: str, y_col: str, title: str):
        """
        Generate and save line chart as HTML file using Bokeh.
        
        Args:
            output_dir (str): Directory to save the plot file.
            data_json_path (str): Path to the input JSON data file.
            x_col (str): Column name for x-axis.
            y_col (str): Column name for y-axis.
            title (str): Plot title.
            
        Returns:
            str: Path to the saved HTML file.
        """
        import bokeh.plotting as bp
        from bokeh.models import ColumnDataSource, HoverTool
        from bokeh.embed import file_html
        from bokeh.resources import CDN
        import pandas as pd
        
        df = load_data_from_json(data_json_path)
        if df is None or df.empty:
            raise ValueError(f"Could not load data or data is empty from {data_json_path}")

        # Check required columns
        required_columns = [x_col, y_col]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise KeyError(f"Data from {data_json_path} must contain columns: {required_columns}. Missing: {missing_columns}")

        # Sort by x-axis column for proper line plotting
        df_sorted = df.sort_values(x_col)
        
        # Create data source
        source = ColumnDataSource(data=dict(
            x=df_sorted[x_col],
            y=df_sorted[y_col]
        ))
        
        # Create hover tool
        hover = HoverTool(tooltips=[
            (f"{x_col}", "@x"),
            (f"{y_col}", "@y{0.00}")
        ])
        
        fig = bp.figure(
            title=title,
            x_axis_label=x_col,
            y_axis_label=y_col,
            width=650,
            height=450,
            tools=[hover, 'pan', 'box_zoom', 'wheel_zoom', 'reset', 'save'],
            toolbar_location="above"
        )
        
        # Add the line
        fig.line(
            'x', 'y', source=source,
            line_color='#1f77b4', line_width=3, alpha=0.9
        )
        
        # Add circle markers for data points
        fig.circle(
            'x', 'y', source=source,
            size=6, color='#1f77b4', alpha=0.7
        )
        
        # Style the plot
        fig.title.text_font_size = "16pt"
        fig.title.align = "center"
        fig.xaxis.axis_label_text_font_size = "14pt"
        fig.yaxis.axis_label_text_font_size = "14pt"
        fig.grid.grid_line_alpha = 0.3
        
        # Set axis ranges for better visualization
        y_min = df_sorted[y_col].min()
        y_max = df_sorted[y_col].max()
        y_range = y_max - y_min
        if y_range > 0:
            fig.y_range.start = y_min - y_range * 0.05
            fig.y_range.end = y_max + y_range * 0.05

        # Generate standalone HTML file
        html_content = file_html(fig, CDN, title)
        
        # Save the HTML file
        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f"line_chart_{x_col}_vs_{y_col}.html")
        with open(output_filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info(f"Line chart saved to {output_filepath}")
        
        return output_filepath

    async def _response_fn(data_json_path: str, x_axis_column: str, y_axis_column: str, plot_title: str) -> str:
        """
        Process the input message and generate line chart.
        """
        data_json_path = verify_json_path(data_json_path)
        
        try:
            # Load data to validate columns exist
            df = load_data_from_json(data_json_path)
            if df is None or df.empty:
                return "Could not load data or data is empty from the provided JSON file"
            
            # Check required columns
            required_columns = [x_axis_column, y_axis_column]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return f"Data from {data_json_path} must contain columns: {required_columns}. Missing: {missing_columns}"
            
            output_filepath = create_line_chart_plot_html(
                output_dir=config.output_folder,
                data_json_path=data_json_path,
                x_col=x_axis_column,
                y_col=y_axis_column,
                title=plot_title
            )
            
            # Convert absolute path to file:// URL for proper browser handling
            file_url = f"file://{output_filepath}"
            
            # Return a clear completion message that the LLM will understand
            return f"TASK COMPLETED SUCCESSFULLY\n\nLine chart has been generated and saved.\n\nChart Details:\n- Type: Line chart with markers\n- X-axis: {x_axis_column}\n- Y-axis: {y_axis_column}\n- Title: {plot_title}\n- Output File: {output_filepath}\n- File URL: {file_url}\n\n✅ CHART GENERATION COMPLETE - NO FURTHER ACTION NEEDED"
            
        except FileNotFoundError as e:
            error_msg = f"Required data file ('{data_json_path}') not found for line chart: {e}"
            logger.error(error_msg)
            return error_msg
        except KeyError as ke:
            error_msg = f"Missing required columns in '{data_json_path}' for line chart: {ke}"
            logger.error(error_msg)
            return error_msg
        except ValueError as ve:
            error_msg = f"Data validation error for line chart: {ve}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error generating line chart: {e}"
            logger.error(error_msg)
            return error_msg

    prompt = """
    Generate interactive line chart from JSON data.
    
    Input:
    - data_json_path: Path to the JSON file containing the data
    - x_axis_column: Column name for x-axis data
    - y_axis_column: Column name for y-axis data
    - plot_title: Title for the plot
    
    Output:
    - HTML file containing the line chart
    """
    yield FunctionInfo.from_fn(_response_fn, 
                               description=prompt)
    try:
        pass
    except GeneratorExit:
        logger.info("Plot line chart function exited early!")
    finally:
        logger.info("Cleaning up plot_line_chart_tool workflow.") 