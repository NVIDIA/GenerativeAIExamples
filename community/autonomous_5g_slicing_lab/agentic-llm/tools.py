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

# This file defines the tools that are used by the agents.

import pandas as pd
import time
import os
from langchain_core.tools import tool
import subprocess
import yaml
import logging
from dotenv import load_dotenv
import gpudb


config_file = yaml.safe_load(open('config.yaml', 'r'))
# Configure the logger without timestamp and level tags
logging.basicConfig(
    filename= config_file['AGENT_LOG_FILE'],  # Log file name
    level=logging.INFO,   # Log level
    format="%(message)s"  # Only log the message
)

load_dotenv("../llm-slicing-5g-lab/.env")

kdbc_options = gpudb.GPUdb.Options()
kdbc_options.username = os.environ.get("KINETICA_USERNAME")
kdbc_options.password = os.environ.get("KINETICA_PASSWORD")
kdbc_options.disable_auto_discovery = True
kdbc: gpudb.GPUdb = gpudb.GPUdb(
    host=os.environ.get("KINETICA_HOST"),
    options=kdbc_options
)


@tool
def reconfigure_network(UE: str, value_1_old: int, value_2_old: int):
    """
    Use this tool to reconfigure the network. The tool reconfigures network, and returns new configuration values.
    """
    time.sleep(2) #to improve logging
    logging.info(f"This is reconfigure_network Tool \n")
    logging.info(f"\n Executing reconfigure_network with UE={UE}, value_1_old={value_1_old}, value_2_old={value_2_old} \n")
    script_path = config_file['reconfig_script_path']
    config_value_1 = "20"
    config_value_2 = "80"
    args_1 = args_2 = None
    args_1 = ["20", "20"]
    
    if UE == "UE1":
       args_2 = ["80","20"]
    else: 
       args_2 = ["20","80"]
 
    try:
        result = subprocess.run([script_path] + args_1, check=True, text=True, capture_output=True)
        logging.info("\nScript output args_1:\n")
        logging.info(result.stdout)
        if args_2!=None:
          result = subprocess.run([script_path] + args_2, check=True, text=True, capture_output=True)
          logging.info("\nScript output args_2:\n")
          logging.info(result.stdout)

        time.sleep(10)
        logging.info("\n Wait for reconfiguration to kick in \n")
        if args_2 != None:
            return str(args_2)

        return str(args_1)
    except subprocess.CalledProcessError as e:
        logging.info("Error occurred:")
        logging.info(e.stderr)
        return "Reconfiguration unsuccessful"


@tool
def get_packetloss_logs() -> str:
    """
    Get the logs to determine which UE is failing.                    
    """ 
    time.sleep(2) #to improve logging
    logging.info(f"This is get_packetloss_logs Tool \n")
    logging.info("\nRetrieving packet loss logs from database\n")
    time.sleep(5) # wait for db to get updated
    iperf_random_table_name: str = os.environ.get('IPERF3_RANDOM_TABLE_NAME')
    # Just to be sure we have the latest randomly generated table name
    load_dotenv("../llm-slicing-5g-lab/.env")
        
    sql_query = f"SELECT lost_packets, loss_percentage, UE FROM {os.environ.get('IPERF3_RANDOM_TABLE_NAME')} ORDER BY timestamp DESC LIMIT 20;"
    result_df: pd.DataFrame = kdbc.to_df(
        sql=sql_query
    )
    
    if result_df is None or result_df.empty:
        return "WARNING: A Problem has occurred. No results were found at this time. Please try again later."
    
    
    return result_df.to_string(index=False)
