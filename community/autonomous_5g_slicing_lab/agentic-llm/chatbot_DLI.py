#Streamlit User Interface for visualizing the 5G Network Agent
import streamlit as st
import pandas as pd
import time
import re
import matplotlib.pyplot as plt
import numpy as np
import time
import streamlit as st
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from matplotlib.ticker import FuncFormatter
import subprocess
import os
import signal
import yaml
from gpudb import GPUdb
from dotenv import load_dotenv
import json
import logging
import colorlog


# Configure colored logging.
handler = colorlog.StreamHandler()
handler.setFormatter(colorlog.ColoredFormatter(
    fmt="%(log_color)s%(asctime)s %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    log_colors={
        'DEBUG':    'blue',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'red,bg_white',
    }
))
logger = colorlog.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False

# Configuration: Paths for both log files
config_file =  yaml.safe_load(open('config.yaml', 'r'))
AGENT_LOG_FILE = config_file['AGENT_LOG_FILE']
os.makedirs(os.path.dirname(AGENT_LOG_FILE), exist_ok=True)

# Create the file if it doesn't exist
if not os.path.exists(AGENT_LOG_FILE):
    with open(AGENT_LOG_FILE, "w") as file:
        pass
        
WINDOW_SIZE_SECONDS = 60
process = None
logs = []

load_dotenv("../llm-slicing-5g-lab/.env")
kdbc_options = GPUdb.Options()
kdbc_options.username = os.environ.get("KINETICA_USERNAME")
kdbc_options.password = os.environ.get("KINETICA_PASSWORD")
kdbc_options.disable_auto_discovery = True
kdbc: GPUdb = GPUdb(
    host=os.environ.get("KINETICA_HOST"),
    options=kdbc_options
)

def generate_sql_query(ue:str):
    load_dotenv("../llm-slicing-5g-lab/.env")
    return f"""
            SELECT
                "timestamp",
                "loss_percentage",
                "bitrate"
            FROM
                {os.environ.get("IPERF3_RANDOM_TABLE_NAME")}
            WHERE
                "ue"='{ue}' AND "timestamp" >= current_datetime() - INTERVAL {WINDOW_SIZE_SECONDS} SECONDS
            ORDER BY
                "timestamp" DESC
            """

# Initialize session state for persistent data storage
if "data_ue1" not in st.session_state:
    st.session_state.data_ue1 = pd.DataFrame()
if "data_ue2" not in st.session_state:
    st.session_state.data_ue2 = pd.DataFrame()

#Class for streaming Agent logs to UI
class LogFileHandler(FileSystemEventHandler):
    def __init__(self, callback):
        self.callback = callback
       
    def on_modified(self, event):
        if event.src_path == AGENT_LOG_FILE:
            self.callback()

def tail_logs():
    """
    Generator function that yields new log lines from Agent_logs (all lines that appeared 
    since the last iteration) so we do not artificially delay reading them.
    """
    with open(AGENT_LOG_FILE, 'r') as file:
        # Move to the end of file
        file.seek(0, 2)
       
        while True:
            current_position = file.tell()
            lines = file.readlines()
            yield lines  

def start():
    #Start Agent 
    process = subprocess.Popen(['python3', 'langgraph_agent.py'])
    
    # Read stdout and stderr line by line
    # for line in process.stdout:
    #     logger.info(line.strip())  # Log stdout

    # for line in process.stderr:
    #     logger.error(line.strip())  # Log stderr

def stop():
    if process is not None:
        st.session_state.data_ue1 = None
        st.session_state.data_ue2 = None
        os.kill(process.pid, signal.SIGTERM)

def get_cutoff_time() -> str:
    current_time = pd.Timestamp.utcnow().tz_convert("UTC")
    return (current_time - pd.Timedelta(seconds=WINDOW_SIZE_SECONDS))

def create_plot():
    plt.close("all")
    plt.style.use("dark_background")
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4,4))
    ax1.set_title("User Equipment 1", fontsize=8, color="white")
    ax1.grid(True, linestyle="--", linewidth=0.5, color="gray")
    ax1.set_ylim(0, 100)
    ax1.tick_params(axis="y", colors="#FFD700", labelsize=5)
    ax1.tick_params(axis="x", colors="#FFD700", labelsize=5)

    ax1_twin = ax1.twinx()
    ax1_twin.set_ylim(0, 60)
    ax1_twin.tick_params(axis="y", colors="#FF8C00", labelsize=5)

    ax2.set_title("User Equipment 2", fontsize=8, color="white")
    ax2.grid(True, linestyle="--", linewidth=0.5, color="gray")
    ax2.set_ylim(0, 100)
    ax2.tick_params(axis="y", colors="#FFD700", labelsize=5)
    ax2.tick_params(axis="x", colors="#FFD700", labelsize=5)

    ax2_twin = ax2.twinx()
    ax2_twin.set_ylim(0, 60)
    ax2_twin.tick_params(axis="y", colors="#FF8C00", labelsize=5)
    plt.tight_layout(pad=2.0)

    return fig


st.set_page_config(page_title="Real-Time Packet Loss & Transfer Rate",  layout="wide")
st.title("5G-Network Configuration Agent")
status_placeholder = st.empty()
status_placeholder.text("Press the button to start monitoring!")

# Set up file watcher (though we mainly rely on tail_logs)
event_handler = LogFileHandler(lambda: None)
observer = Observer()
observer.schedule(event_handler, path=AGENT_LOG_FILE)
observer.start()
log_generator = tail_logs()

col_logs, col_charts = st.columns([3, 3])
with col_logs:
    button_col1, button_col2 = st.columns(2)
    with button_col1:
        start_monitoring = st.button("Start Monitoring", key="start", use_container_width=True)
    
    with button_col2:
        stop_monitoring = st.button("Stop Monitoring", key="stop", use_container_width=True)

    log_display = st.empty()  # For log text area
    log_display.code('', height=600)

with col_charts:
    # Create placeholders for the charts
    chart_placeholder = st.empty()
    fig = create_plot()
    chart_placeholder.pyplot(fig)

if start_monitoring:
    status_placeholder.text("Monitoring in Progress")
    start()
    while True:
        # Read the latest log data for UE1 and UE2
        new_log = next(log_generator)
        logs.extend([line.strip() for line in new_log])

        #erase old logs
        if len(logs) > 10000:
            logs.pop(0)
            
        # Update the display with the last 200 lines
        log_display.code('\n'.join(logs[-200:]), height=600)
        st.markdown("""
        <script>
            window.addEventListener('DOMContentNodeInserted', function() {
                window.scrollTo(0, document.body.scrollHeight);
            });
        </script>
        """, unsafe_allow_html=True)

        # Fetch new data for UE1 and UE2
        cutoff_time = get_cutoff_time()

        try:
            new_data_ue1 = kdbc.to_df(sql=generate_sql_query(ue="UE1"))
            new_data_ue1["timestamp"] = pd.to_datetime(new_data_ue1["timestamp"]).dt.tz_localize("UTC")

            if not new_data_ue1.empty:
                st.session_state.data_ue1 = (
                    pd.concat([st.session_state.data_ue1, new_data_ue1])
                    .drop_duplicates(subset=["timestamp"])
                    .sort_values("timestamp")
                    .query("timestamp > @cutoff_time")
                    .reset_index(drop=True)
                )
                # Compute the cutoff time for filtering
    
        except Exception as error:
            logger.error(f"Error fetching UE1 data: {error}")

        try:
            new_data_ue2 = kdbc.to_df(sql=generate_sql_query(ue="UE3"))
            new_data_ue2["timestamp"] = pd.to_datetime(new_data_ue2["timestamp"]).dt.tz_localize("UTC")

            if not new_data_ue2.empty:
                st.session_state.data_ue2 = (
                    pd.concat([st.session_state.data_ue2, new_data_ue2])
                    .drop_duplicates(subset=["timestamp"])
                    .sort_values("timestamp")
                    .query("timestamp > @cutoff_time")
                    .reset_index(drop=True)
                )
        except Exception as error:
            logger.error(f"Error fetching UE2 data: {error}")

        # If both datasets have data, update the charts
        if not st.session_state.data_ue1.empty and not st.session_state.data_ue2.empty:
            plt.close("all")  # Close previous figures
            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(4,4))  # Two side-by-side charts

            # Generate x-axis as a rolling index for left-to-right movement
            x_axis_ue1 = st.session_state.data_ue1["timestamp"]
            x_axis_ue2 = st.session_state.data_ue2["timestamp"]

            # **User Equipment 1 Chart**
            ax1.set_title("User Equipment 1", fontsize=8, color="white")
            ax1.grid(True, linestyle="--", linewidth=0.5, color="gray")
            ax1.set_ylim(0, 100)  # Set y-axis range for packet loss

            line1, = ax1.plot(x_axis_ue1, st.session_state.data_ue1["loss_percentage"], 
                            color="#FFD700", linestyle="--", linewidth=1, label="Packet Loss (%)")

            ax1.tick_params(axis="y", colors="#FFD700", labelsize=5)
            ax1.tick_params(axis="x", colors="#FFD700", labelsize=5)

            ax1_twin = ax1.twinx()
            ax1_twin.set_ylim(0, 160)  # Set y-axis range for bitrate
            line2, = ax1_twin.plot(x_axis_ue1, st.session_state.data_ue1["bitrate"], 
                                color="#FF8C00", linestyle="-", linewidth=1, label="Transfer Rate (MBytes)")
            ax1_twin.tick_params(axis="y", colors="#FF8C00", labelsize=5)

            # **User Equipment 2 Chart**
            ax2.set_title("User Equipment 2", fontsize=8, color="white")
            ax2.grid(True, linestyle="--", linewidth=0.5, color="gray")
            ax2.set_ylim(0, 100)  # Set y-axis range for packet loss

            line3, = ax2.plot(x_axis_ue2, st.session_state.data_ue2["loss_percentage"], 
                            color="#FFD700", linestyle="--", linewidth=1, label="Packet Loss (%)")

            ax2.tick_params(axis="y", colors="#FFD700", labelsize=5)
            ax2.tick_params(axis="x", colors="#FFD700", labelsize=5)

            ax2_twin = ax2.twinx()
            ax2_twin.set_ylim(0, 160)  # Set y-axis range for bitrate
            line4, = ax2_twin.plot(x_axis_ue2, st.session_state.data_ue2["bitrate"], 
                                color="#FF8C00", linestyle="-", linewidth=1, label="Transfer Rate (MBytes)")
            ax2_twin.tick_params(axis="y", colors="#FF8C00", labelsize=5)

            # Add legend
            ax1.legend(handles=[line1, line2], loc="upper right", fontsize=6, facecolor="#333", edgecolor="white")
            ax2.legend(handles=[line3, line4], loc="upper right", fontsize=6, facecolor="#333", edgecolor="white")

            plt.tight_layout(pad=2.0)

            # Update the Streamlit plot
            chart_placeholder.pyplot(fig)

if stop_monitoring:
    status_placeholder.text("Monitoring in Stopped")
    fig = create_plot()
    chart_placeholder.pyplot(fig)
    stop()