# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

""" Module to provide utility functions for CSV RAG example"""

import json
import os
from typing import Dict, List

import pandas as pd
import yaml


def extract_df_desc(df) -> str:
    """
    Convert a pandas DataFrame to a string with column names and up to 3 random rows.

    Args:
    df (pandas.DataFrame): The DataFrame to convert.

    Returns:
    str: A string representation of the DataFrame.
    """
    column_names = ", ".join(df.columns)
    sample_rows = df.sample(min(3, len(df)))
    rows_str = sample_rows.to_string(header=False, index=False)
    result = column_names + "\n" + rows_str
    return result


def parse_prompt_config(config_path: str) -> Dict:
    "Parses csv yaml config and returns the config as list of prompts"
    # Check if the file exists
    if not os.path.isfile(config_path):
        raise FileNotFoundError(f"The file {config_path} does not exist")

    try:
        with open(config_path, "r", encoding="UTF-8") as file:
            data = yaml.safe_load(file)

            # Check if the expected key 'prompts' is in the data
            if "prompts" not in data or not isinstance(data["prompts"], dict):
                raise ValueError("Invalid YAML structure. Expected a 'prompts' key with a list of dictionaries.")

            env_prompts = None
            if "CSV_PROMPTS" in os.environ:
                try:
                    env_prompts = json.loads(os.environ["CSV_PROMPTS"])
                    if env_prompts is not None:
                        data["prompts"]["csv_prompts"].extend(env_prompts["csv_prompts"])
                except Exception as e:
                    print(f"Exception in parsing CSV prompt from environment variable {e}")

            # return the dict
            return data["prompts"]
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing YAML file: {e}")


def get_prompt_params(prompt_list: List) -> Dict[str, str]:
    """
    Takes a list of dictionaries and returns a formatted string.
    Each line in the string contains the 'id' and 'description' from one dictionary.
    """
    csv_name = os.getenv("CSV_NAME")

    # Check if the environment variable is not found
    if csv_name is None:
        raise Exception("Environment variable CSV_NAME not found.")

    # Check if the environment variable is set to an empty string
    if csv_name == "":
        raise ValueError("Environment variable CSV_NAME is set to an empty string.")

    if not prompt_list:
        raise ValueError("Config Prompt list is empty")

    for prompt in prompt_list:
        if csv_name == prompt.get("name"):
            print(f"Using prompt for {csv_name}")
            return {
                "description": prompt.get("description"),
                "instructions": prompt.get("instructions"),
            }

    return {}


def is_result_valid(result):
    """ Check for validity of resultant data frame"""
    if isinstance(result, pd.DataFrame):
        return not result.empty
    return bool(result)
