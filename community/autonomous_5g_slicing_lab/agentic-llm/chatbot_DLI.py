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

#Streamlit User Interface for visualizing the 5G Network Agent with Grafana
import streamlit as st
import pandas as pd
import time
import re
import numpy as np
import time
import streamlit as st
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os
import signal
import yaml
from gpudb import GPUdb
from dotenv import load_dotenv
import json
import logging
import colorlog
from influxdb_utils import InfluxDBMetricsClient


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
GRAPHANA_DASHBOARD = config_file['GRAPHANA_DASHBOARD']
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

# Initialize InfluxDB client
influx_client = InfluxDBMetricsClient()
influx_client.connect()

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

def get_grafana_dashboard_url():
    """Get the Grafana dashboard URL for embedding (cloud version)"""
    return f"https://9002-{GRAPHANA_DASHBOARD}.brevlab.com/d/5g-metrics/5g-network-metrics-dashboard?orgId=1&refresh=5s&theme=dark"

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
    
    # Check if Grafana is accessible
    try:
        import requests
        # In the health check, use the configured dashboard URL
        response = requests.get(f"https://9002-{GRAPHANA_DASHBOARD}.brevlab.com", timeout=5)
        if response.status_code == 200:
            
            # Embed Grafana dashboard
            dashboard_url = get_grafana_dashboard_url()
            st.markdown(f"""
            <iframe 
                src="{dashboard_url}" 
                width="100%" 
                height="800" 
                frameborder="0"
                style="border: 1px solid #ddd; border-radius: 5px;">
            </iframe>
            """, unsafe_allow_html=True)
            
            # Add link to open in new tab
            st.markdown(f"[🔗 Open Dashboard in New Tab]({dashboard_url})")
        else:
            st.error("❌ Grafana is not responding properly")
    except Exception as e:
        st.error(f"❌ Cannot connect to Grafana: {e}")
        st.info("💡 Please start Grafana services using: `./start_grafana_services.sh` or `start_grafana_services.bat`")

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

        # Fetch new data for UE1 and UE2 (restored to NVIDIA original)
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
        except Exception as error:
            logger.error(f"Error fetching UE1 data: {error}")

        try:
            new_data_ue2 = kdbc.to_df(sql=generate_sql_query(ue="UE3"))  # Use UE3 as in the original
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

        # Write new data to InfluxDB for real-time visualization
        if not st.session_state.data_ue1.empty:
            # Write latest UE1 data to InfluxDB
            latest_ue1 = st.session_state.data_ue1.iloc[-1]
            influx_client.write_metrics(
                ue="UE1",
                loss_percentage=latest_ue1["loss_percentage"],
                bitrate=latest_ue1["bitrate"],
                timestamp=latest_ue1["timestamp"]
            )
            
        if not st.session_state.data_ue2.empty:
            # Write latest UE2 data to InfluxDB
            latest_ue2 = st.session_state.data_ue2.iloc[-1]
            influx_client.write_metrics(
                ue="UE3",  # match Kinetica/original logic
                loss_percentage=latest_ue2["loss_percentage"],
                bitrate=latest_ue2["bitrate"],
                timestamp=latest_ue2["timestamp"]
            )

if stop_monitoring:
    status_placeholder.text("Monitoring Stopped")
    # Close InfluxDB connection
    influx_client.close()
    stop()