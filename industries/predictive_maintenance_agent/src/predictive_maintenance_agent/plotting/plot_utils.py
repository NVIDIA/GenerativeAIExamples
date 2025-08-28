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
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

def resolve_relative_path(file_path: str, output_folder: str) -> str:
    """
    Resolve file path relative to output folder.
    
    Args:
        file_path: Input file path (can be relative or absolute)
        output_folder: Output folder to use as base for relative paths
        
    Returns:
        Resolved absolute path
    """
    if os.path.isabs(file_path):
        # If absolute path exists, use it
        if os.path.exists(file_path):
            return file_path
        # If absolute path doesn't exist, try relative to output folder
        basename = os.path.basename(file_path)
        relative_path = os.path.join(output_folder, basename)
        if os.path.exists(relative_path):
            return relative_path
        # Return original if neither exists (will be handled by calling function)
        return file_path
    else:
        # If relative path, first try relative to output folder
        relative_to_output = os.path.join(output_folder, file_path)
        if os.path.exists(relative_to_output):
            return relative_to_output
        # Then try as provided (relative to current working directory)
        if os.path.exists(file_path):
            return file_path
        # Return relative to output folder as default
        return relative_to_output

def load_data_from_json(json_path: str, output_folder: str = None) -> Optional[pd.DataFrame]:
    """Load data from JSON file into a pandas DataFrame."""
    try:
        # Resolve path relative to output folder if provided
        if output_folder:
            resolved_path = resolve_relative_path(json_path, output_folder)
        else:
            resolved_path = json_path
            
        with open(resolved_path, 'r') as f:
            data = json.load(f)
        return pd.DataFrame(data)
    except FileNotFoundError:
        logger.error(f"JSON file not found at {json_path} (resolved to {resolved_path if output_folder else json_path})")
        return None
    except json.JSONDecodeError:
        logger.error(f"Could not decode JSON from {json_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading data from '{json_path}': {e}")
        return None

def save_plotly_as_png(fig, filepath: str, width: int = 650, height: int = 450) -> bool:
    """
    Save plotly figure as PNG using matplotlib backend.
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        
        # Create matplotlib figure
        fig_mpl, ax = plt.subplots(figsize=(width/100, height/100))
        
        # Plot each trace with simplified approach
        for i, trace in enumerate(fig.data):
            if trace.type == 'scatter':
                # Handle line properties
                line_style = '-'
                color = '#1f77b4'  # default color
                
                # Extract line properties safely
                if hasattr(trace, 'line') and trace.line:
                    if hasattr(trace.line, 'dash') and trace.line.dash == 'dash':
                        line_style = '--'
                    if hasattr(trace.line, 'color') and trace.line.color:
                        color = trace.line.color
                
                # Extract marker color (takes precedence for better Plotly color preservation)
                if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color') and trace.marker.color:
                    color = trace.marker.color
                
                # Extract name safely
                name = trace.name if hasattr(trace, 'name') and trace.name else f'Trace {i+1}'
                
                # Plot based on mode
                mode = getattr(trace, 'mode', 'lines')
                if 'markers' in mode:
                    if mode == 'markers':
                        # Only markers, no lines
                        ax.plot(trace.x, trace.y, 'o', 
                               color=color, label=name, markersize=6)
                    else:
                        # Both markers and lines
                        ax.plot(trace.x, trace.y, 'o-', 
                               linestyle=line_style, color=color, 
                               label=name, linewidth=2, markersize=4)
                else:
                    ax.plot(trace.x, trace.y, linestyle=line_style, 
                           color=color, label=name, linewidth=2)
            
            elif trace.type == 'histogram':
                # Handle histogram properties
                color = '#e17160'  # default color
                if hasattr(trace, 'marker') and trace.marker and hasattr(trace.marker, 'color'):
                    color = trace.marker.color
                
                name = trace.name if hasattr(trace, 'name') and trace.name else f'Histogram {i+1}'
                ax.hist(trace.x, bins=30, alpha=0.8, color=color, 
                       edgecolor='white', linewidth=0.5, label=name)
        
        # Apply layout safely
        layout = fig.layout
        if hasattr(layout, 'title') and layout.title and hasattr(layout.title, 'text') and layout.title.text:
            ax.set_title(layout.title.text)
        if hasattr(layout, 'xaxis') and layout.xaxis and hasattr(layout.xaxis, 'title') and layout.xaxis.title and hasattr(layout.xaxis.title, 'text'):
            ax.set_xlabel(layout.xaxis.title.text)
        if hasattr(layout, 'yaxis') and layout.yaxis and hasattr(layout.yaxis, 'title') and layout.yaxis.title and hasattr(layout.yaxis.title, 'text'):
            ax.set_ylabel(layout.yaxis.title.text)
        
        # Show legend if there are multiple traces or if any trace has a name
        if len(fig.data) > 1 or (len(fig.data) == 1 and hasattr(fig.data[0], 'name') and fig.data[0].name):
            ax.legend()
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        logger.info(f"PNG saved using matplotlib: {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Matplotlib PNG generation failed: {e}")
        return False

def create_comparison_plot(output_dir: str, data_json_path: str, x_col: str, 
                         y_col_1: str, y_col_2: str, title: str) -> Tuple[str, Optional[str]]:
    """
    Generate comparison plot in both HTML and PNG formats.
    
    Returns:
        Tuple[str, Optional[str]]: (html_filepath, png_filepath)
    """
    import plotly.graph_objects as go
    import plotly.offline as pyo
    
    df = load_data_from_json(data_json_path, output_dir)
    if df is None or df.empty:
        raise ValueError(f"Could not load data or data is empty from {data_json_path}")

    # Check required columns
    required_columns = [x_col, y_col_1, y_col_2]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Data from {data_json_path} must contain columns: {required_columns}. Missing: {missing_columns}")

    # Sort by x-axis column for proper line plotting
    df_sorted = df.sort_values(x_col)
    
    # Create the comparison plot
    fig = go.Figure()
    
    # Add first line (dashed)
    fig.add_trace(go.Scatter(
        x=df_sorted[x_col],
        y=df_sorted[y_col_1],
        mode='lines',
        name=y_col_1,
        line=dict(color='#20B2AA', width=3, dash='dash'),
        hovertemplate=f'<b>{x_col}</b>: %{{x}}<br>' +
                     f'<b>{y_col_1}</b>: %{{y:.1f}}<br>' +
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
    
    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis=dict(title=dict(text=x_col, font=dict(size=14)), gridcolor='lightgray', gridwidth=0.5),
        yaxis=dict(title=dict(text='Value', font=dict(size=14)), gridcolor='lightgray', gridwidth=0.5),
        width=800, height=450, plot_bgcolor='white',
        legend=dict(x=1, y=0, xanchor='right', yanchor='bottom', 
                   bgcolor='rgba(255,255,255,0.8)', bordercolor='gray', borderwidth=1),
        hovermode='closest'
    )
    
    # Set y-axis range
    y_min = min(df_sorted[y_col_1].min(), df_sorted[y_col_2].min())
    y_max = max(df_sorted[y_col_1].max(), df_sorted[y_col_2].max())
    y_range = y_max - y_min
    fig.update_yaxes(range=[max(0, y_min - y_range * 0.05), y_max + y_range * 0.05])

    # Save files
    os.makedirs(output_dir, exist_ok=True)
    
    # HTML file
    html_filepath = os.path.join(output_dir, f"comparison_plot_{y_col_1}_vs_{y_col_2}.html")
    html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
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
    
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(full_html)
    logger.info(f"Comparison plot HTML saved: {html_filepath}")
    
    # PNG file
    png_filepath = os.path.join(output_dir, f"comparison_plot_{y_col_1}_vs_{y_col_2}.png")
    png_success = save_plotly_as_png(fig, png_filepath, width=800, height=450)
    
    return html_filepath, png_filepath if png_success else None

def create_line_chart(output_dir: str, data_json_path: str, x_col: str, 
                     y_col: str, title: str) -> Tuple[str, Optional[str]]:
    """
    Generate line chart in both HTML and PNG formats.
    
    Returns:
        Tuple[str, Optional[str]]: (html_filepath, png_filepath)
    """
    import plotly.graph_objects as go
    import plotly.offline as pyo
    
    df = load_data_from_json(data_json_path, output_dir)
    if df is None or df.empty:
        raise ValueError(f"Could not load data or data is empty from {data_json_path}")

    # Check required columns
    required_columns = [x_col, y_col]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise KeyError(f"Data from {data_json_path} must contain columns: {required_columns}. Missing: {missing_columns}")

    # Sort by x-axis column
    df_sorted = df.sort_values(x_col)
    
    # Create line chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df_sorted[x_col],
        y=df_sorted[y_col],
        mode='lines+markers',
        name=y_col,
        line=dict(color='#1f77b4', width=3),
        marker=dict(size=6, color='#1f77b4'),
        hovertemplate=f'<b>{x_col}</b>: %{{x}}<br>' +
                     f'<b>{y_col}</b>: %{{y:.2f}}<br>' +
                     '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        xaxis=dict(title=dict(text=x_col, font=dict(size=14)), gridcolor='lightgray', gridwidth=0.5),
        yaxis=dict(title=dict(text=y_col, font=dict(size=14)), gridcolor='lightgray', gridwidth=0.5),
        width=650, height=450, plot_bgcolor='white', showlegend=False, hovermode='closest'
    )
    
    # Set y-axis range
    y_min = df_sorted[y_col].min()
    y_max = df_sorted[y_col].max()
    y_range = y_max - y_min
    if y_range > 0:
        fig.update_yaxes(range=[y_min - y_range * 0.05, y_max + y_range * 0.05])
    
    # Save files
    os.makedirs(output_dir, exist_ok=True)
    
    # HTML file
    html_filepath = os.path.join(output_dir, f"line_chart_{x_col}_vs_{y_col}.html")
    html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
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
    
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(full_html)
    logger.info(f"Line chart HTML saved: {html_filepath}")
    
    # PNG file
    png_filepath = os.path.join(output_dir, f"line_chart_{x_col}_vs_{y_col}.png")
    png_success = save_plotly_as_png(fig, png_filepath, width=650, height=450)
    
    return html_filepath, png_filepath if png_success else None

def create_distribution_plot(output_dir: str, data_json_path: str, column_name: str, 
                           title: str) -> Tuple[str, Optional[str]]:
    """
    Generate distribution histogram in both HTML and PNG formats.
    
    Returns:
        Tuple[str, Optional[str]]: (html_filepath, png_filepath)
    """
    import plotly.graph_objects as go
    import plotly.offline as pyo
    
    df = load_data_from_json(data_json_path, output_dir)
    if df is None or df.empty:
        raise ValueError(f"Could not load data or data is empty from {data_json_path}")

    if column_name not in df.columns:
        raise KeyError(f"Data from {data_json_path} must contain '{column_name}' column. Found: {df.columns.tolist()}")

    # Create histogram
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df[column_name],
        nbinsx=30,
        name=column_name,
        marker=dict(color='#e17160', line=dict(color='white', width=1)),
        opacity=0.8,
        hovertemplate='<b>Range</b>: %{x}<br>' +
                     '<b>Count</b>: %{y}<br>' +
                     '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        xaxis=dict(title=dict(text=column_name, font=dict(size=12)), gridcolor='lightgray', gridwidth=0.5),
        yaxis=dict(title=dict(text='Frequency', font=dict(size=12)), gridcolor='lightgray', gridwidth=0.5),
        width=650, height=450, plot_bgcolor='white', showlegend=False, hovermode='closest'
    )

    # Save files
    os.makedirs(output_dir, exist_ok=True)
    
    # HTML file
    html_filepath = os.path.join(output_dir, f"distribution_plot_{column_name}.html")
    html_content = pyo.plot(fig, output_type='div', include_plotlyjs=True)
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
    
    with open(html_filepath, 'w', encoding='utf-8') as f:
        f.write(full_html)
    logger.info(f"Distribution plot HTML saved: {html_filepath}")
    
    # PNG file
    png_filepath = os.path.join(output_dir, f"distribution_plot_{column_name}.png")
    png_success = save_plotly_as_png(fig, png_filepath, width=650, height=450)
    
    return html_filepath, png_filepath if png_success else None


def create_moment_anomaly_visualization(df: pd.DataFrame, anomaly_indices, 
                                      anomaly_scores, sensor_name: str,
                                      output_dir: str, engine_unit: int, dataset_name: str) -> Tuple[str, str]:
    """Create interactive plot for MOMENT-based anomaly detection results for a single sensor."""
    try:
        import plotly.graph_objects as go
        import numpy as np
        
        if sensor_name not in df.columns:
            raise ValueError(f"Sensor '{sensor_name}' not found in data. Available sensors: {df.columns.tolist()}")
        
        # Create a simple single plot
        fig = go.Figure()
        
        # Create x-axis (check for various time column names)
        time_columns = ['time_in_cycles', 'cycle', 'time', 'timestamp']
        x_axis = None
        x_title = "Index"
        
        for col in time_columns:
            if col in df.columns:
                x_axis = df[col]
                x_title = col.replace('_', ' ').title()
                break
        
        if x_axis is None:
            x_axis = df.index
            x_title = "Index"
        
        # Plot all sensor readings as blue line (Observed)
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=df[sensor_name],
                mode='lines',
                name='Observed',
                line=dict(color='blue', width=2),
                opacity=0.8
            )
        )
        
        # Plot anomalous points as red markers
        if len(anomaly_indices) > 0 and np.any(anomaly_indices):
            # Find where anomalies are True
            anomaly_positions = np.where(anomaly_indices)[0]
            
            # Make sure we don't go beyond the dataframe length
            valid_positions = anomaly_positions[anomaly_positions < len(df)]
            
            if len(valid_positions) > 0:
                anomaly_x = x_axis.iloc[valid_positions]
                anomaly_y = df[sensor_name].iloc[valid_positions]
                
                fig.add_trace(
                    go.Scatter(
                        x=anomaly_x,
                        y=anomaly_y,
                        mode='markers',
                        name='Anomaly',
                        marker=dict(color='red', size=6, symbol='circle'),
                        opacity=0.9
                    )
                )
        
        fig.update_layout(
            title=f'MOMENT Anomaly Detection - {sensor_name} (Engine {engine_unit})',
            xaxis_title=x_title,
            yaxis_title=f"{sensor_name}",
            height=400,
            showlegend=True,
            font=dict(size=12),
            template="plotly_white"
        )
        
        # Save as HTML
        os.makedirs(output_dir, exist_ok=True)
        html_filename = f"moment_anomaly_detection_{sensor_name}_engine{engine_unit}.html"
        html_filepath = os.path.join(output_dir, html_filename)
        fig.write_html(html_filepath)
        
        # Save as PNG using the safe function from plot_utils
        png_filename = f"moment_anomaly_detection_{sensor_name}_engine{engine_unit}.png"
        png_filepath = os.path.join(output_dir, png_filename)
        png_success = save_plotly_as_png(fig, png_filepath, width=1200, height=400)
        
        logger.info(f"MOMENT anomaly visualization saved: HTML={html_filepath}, PNG={'Success' if png_success else 'Failed'}")
        
        return html_filepath, png_filepath if png_success else None
        
    except ImportError:
        logger.error("Plotly not available for visualization")
        return None, None
    except Exception as e:
        logger.error(f"Error creating MOMENT anomaly visualization: {e}")
        return None, None


def create_anomaly_plot_from_data(data_df: pd.DataFrame, sensor_name: str, engine_unit: int, 
                                 output_dir: str, plot_title: str = None) -> Tuple[str, str]:
    """
    Create anomaly detection visualization plot from sensor data with is_anomaly column.
    
    Args:
        data_df: DataFrame containing sensor data with 'is_anomaly' boolean column
        sensor_name: Name of the sensor column to plot
        engine_unit: Engine unit number for labeling
        output_dir: Directory to save plot files
        plot_title: Custom title for the plot (optional)
    
    Returns:
        Tuple of (html_filepath, png_filepath)
    """
    try:
        import plotly.graph_objects as go
        import numpy as np
        
        if sensor_name not in data_df.columns:
            raise ValueError(f"Sensor '{sensor_name}' not found in data. Available sensors: {data_df.columns.tolist()}")
        
        if 'is_anomaly' not in data_df.columns:
            raise ValueError("'is_anomaly' column not found in data. Make sure to use output from MOMENT anomaly detection tool.")
        
        # Create figure
        fig = go.Figure()
        
        # Determine time axis (check for various time column names)
        time_columns = ['time_in_cycles', 'cycle', 'time', 'timestamp']
        x_axis = None
        x_title = "Index"
        
        for col in time_columns:
            if col in data_df.columns:
                x_axis = data_df[col]
                x_title = col.replace('_', ' ').title()
                break
        
        if x_axis is None:
            x_axis = data_df.index
            x_title = "Index"
        
        # Plot all sensor readings as blue line (Observed)
        fig.add_trace(
            go.Scatter(
                x=x_axis,
                y=data_df[sensor_name],
                mode='lines',
                name='Observed',
                line=dict(color='blue', width=2),
                opacity=0.8
            )
        )
        
        # Extract anomaly points directly from the is_anomaly column
        anomaly_mask = data_df['is_anomaly'] == True
        anomaly_indices = data_df[anomaly_mask].index.values
        
        # Plot anomalous points as red markers
        if len(anomaly_indices) > 0:
            anomaly_x = x_axis.iloc[anomaly_indices]
            anomaly_y = data_df[sensor_name].iloc[anomaly_indices]
            
            fig.add_trace(
                go.Scatter(
                    x=anomaly_x,
                    y=anomaly_y,
                    mode='markers',
                    name='Anomaly',
                    marker=dict(color='red', size=8, symbol='circle'),
                    opacity=0.9
                )
            )
        
        fig.update_layout(
            title=f'Anomaly Detection - {sensor_name} (Engine {engine_unit})',
            xaxis_title=x_title,
            yaxis_title=f"{sensor_name}",
            height=500,
            showlegend=True,
            font=dict(size=12),
            template="plotly_white"
        )
        
        # Save files
        os.makedirs(output_dir, exist_ok=True)
        
        # HTML file
        html_filename = f"anomaly_plot_{sensor_name}_engine{engine_unit}.html"
        html_filepath = os.path.join(output_dir, html_filename)
        fig.write_html(html_filepath)
        
        # PNG file using thread-safe function
        png_filename = f"anomaly_plot_{sensor_name}_engine{engine_unit}.png"
        png_filepath = os.path.join(output_dir, png_filename)
        png_success = save_plotly_as_png(fig, png_filepath, width=1200, height=500)
        
        logger.info(f"Anomaly plot saved: HTML={html_filepath}, PNG={'Success' if png_success else 'Failed'}")
        
        return html_filepath, png_filepath if png_success else None
        
    except ImportError:
        logger.error("Plotly not available for visualization")
        return None, None
    except Exception as e:
        logger.error(f"Error creating anomaly plot: {e}")
        return None, None