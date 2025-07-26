import json
import logging
import os

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

class PlotDistributionToolConfig(FunctionBaseConfig, name="plot_distribution_tool"):
    """
    AIQ Toolkit function to plot distribution histogram of a specified column.
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

    def create_distribution_plot_html(output_dir: str, data_json_path: str, column_name: str, title: str):
        """
        Generate and save distribution histogram as HTML file using Plotly.
        
        Args:
            output_dir (str): Directory to save the plot file.
            data_json_path (str): Path to the input JSON data file.
            column_name (str): Column name to create distribution for.
            title (str): Plot title.
            
        Returns:
            str: Path to the saved HTML file.
        """
        import plotly.graph_objects as go
        import plotly.offline as pyo
        import pandas as pd
        
        df = load_data_from_json(data_json_path)
        if df is None or df.empty:
            raise ValueError(f"Could not load data or data is empty from {data_json_path}")

        if column_name not in df.columns:
            raise KeyError(f"Data from {data_json_path} must contain '{column_name}' column. Found: {df.columns.tolist()}")

        # Create the histogram
        fig = go.Figure()
        
        fig.add_trace(go.Histogram(
            x=df[column_name],
            nbinsx=30,
            name=column_name,
            marker=dict(
                color='#e17160',
                line=dict(color='white', width=1)
            ),
            opacity=0.8,
            hovertemplate='<b>Range</b>: %{x}<br>' +
                         '<b>Count</b>: %{y}<br>' +
                         '<extra></extra>'
        ))
        
        # Update layout with styling
        fig.update_layout(
            title=dict(
                text=title,
                x=0.5,
                font=dict(size=14)
            ),
            xaxis=dict(
                title=dict(text=column_name, font=dict(size=12)),
                gridcolor='lightgray',
                gridwidth=0.5
            ),
            yaxis=dict(
                title=dict(text='Frequency', font=dict(size=12)),
                gridcolor='lightgray',
                gridwidth=0.5
            ),
            width=650,
            height=450,
            plot_bgcolor='white',
            showlegend=False,
            hovermode='closest'
        )

        # Save the HTML file
        os.makedirs(output_dir, exist_ok=True)
        output_filepath = os.path.join(output_dir, f"distribution_plot_{column_name}.html")
        
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
        logger.info(f"Distribution plot saved to {output_filepath}")
        
        return output_filepath

    async def _response_fn(data_json_path: str, column_name: str, plot_title: str) -> str:
        """
        Process the input message and generate distribution histogram file.
        """
        data_json_path = verify_json_path(data_json_path)
        try:
            # Load data to validate column exists
            df = load_data_from_json(data_json_path)
            if df is None or df.empty:
                return "Could not load data or data is empty from the provided JSON file"
            
            if column_name not in df.columns:
                return f"Column '{column_name}' not found in data. Available columns: {df.columns.tolist()}"
            
            output_filepath = create_distribution_plot_html(
                output_dir=config.output_folder,
                data_json_path=data_json_path,
                column_name=column_name,
                title=plot_title
            )
            
            # Convert absolute path to file:// URL for proper browser handling
            file_url = f"file://{output_filepath}"
            
            # Return a clear completion message that the LLM will understand
            return f"TASK COMPLETED SUCCESSFULLY\n\nDistribution histogram has been generated and saved.\n\nChart Details:\n- Type: Distribution histogram (30 bins, Plotly)\n- Column: {column_name}\n- Title: {plot_title}\n- Output File: {output_filepath}\n- File URL: {file_url}\n\n✅ CHART GENERATION COMPLETE - NO FURTHER ACTION NEEDED"
            
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
    - HTML file containing the distribution histogram
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
