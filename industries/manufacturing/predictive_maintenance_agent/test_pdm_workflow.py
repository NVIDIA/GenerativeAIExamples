# SPDX-FileCopyrightText: Copyright (c) 2025, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

import importlib
import importlib.resources
import inspect
import logging
import os
from pathlib import Path

import pytest
from predictive_maintenance_agent import register

from aiq.runtime.loader import load_workflow

logger = logging.getLogger(__name__)

def setup_environment():
    """Setup required environment variables for the workflow."""
    # Set PWD_PATH to current directory as mentioned in README
    current_dir = Path(__file__).parent.absolute()
    os.environ["PWD_PATH"] = str(current_dir)
    
    # Ensure NVIDIA_API_KEY is set (should be set externally
    os.environ["NVIDIA_API_KEY"] = "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"
    
    logger.error(f"PWD_PATH set to: {os.environ['PWD_PATH']}")


async def run_workflow_with_prompt(prompt: str):
    """
    Helper function to run the workflow with a given prompt.
    
    Args:
        prompt: The prompt to send to the agent workflow
        
    Returns:
        str: The result from the workflow execution
    """
    # Setup environment variables
    setup_environment()
    
    # Use our own package for config file location
    package_name = inspect.getmodule(register).__package__
    config_file: Path = importlib.resources.files(package_name).parent.parent.joinpath("configs", "config-reasoning.yml").absolute()

    async with load_workflow(config_file) as workflow:
        async with workflow.run(prompt) as runner:
            result = await runner.result(to_type=str)
        
        return result


@pytest.mark.e2e
async def test_data_retrieval_and_plotting():
    """Test retrieving time in cycles and operational setting 1 for unit 1 and plotting."""
    
    prompt = "Retrieve the time in cycles and operational setting 1 from the FD001 test table for unit number 1 and plot its value vs time."
    
    result = await run_workflow_with_prompt(prompt)
    result_lower = result.lower()
    
    # Verify that the workflow completed successfully and generated output
    assert "saved output to" in result_lower or "plot" in result_lower or "chart" in result_lower
    logger.info(f"Test 1 completed successfully: {result}")


@pytest.mark.e2e
async def test_rul_distribution_analysis():
    """Test retrieving real RUL values and plotting their distribution."""
    
    prompt = "Retrieve real RUL of each unit in the FD001 test dataset. Then plot a distribution of it."
    
    result = await run_workflow_with_prompt(prompt)
    result_lower = result.lower()
    
    # Verify that the workflow completed successfully and generated output
    assert "saved output to" in result_lower or "plot" in result_lower or "distribution" in result_lower
    logger.info(f"Test 2 completed successfully: {result}")
