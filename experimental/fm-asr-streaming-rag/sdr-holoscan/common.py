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

import os
import time
import socket
import logging

PARAM_FILE = os.path.join(os.path.dirname(__file__), 'params.yml')
LOG_LEVEL  = logging.getLevelName(os.environ.get('SDR_LOG_LEVEL', 'WARN').upper())
FRONTEND_URI = os.environ.get('FRONTEND_URI', 'localhost:6001')
DATABASE_URI = os.environ.get('DATABASE_URI', '0.0.0.0:8081')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class SignalEmission:
    """ 'data' holds signal data and 'fs' is the associated sample rate (Hz)
    """
    def __init__(self, data, fs):
        self.data = data
        self.fs = fs

class NameFuncFilter(logging.Filter):
    """ Concatenate the logger name and function name, then limit characters
    """
    def filter(self, record, nchar=30):
        record.name_func_combo = f"{record.name}.{record.funcName}"[:nchar]
        return True

def setup_logging(name):
    """ Build a logger that prints to screen within Holoscan pipeline
    """
    # Build a handler to make sure logging is printed to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOG_LEVEL)
    console_handler.addFilter(NameFuncFilter())
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(name_func_combo)-30s %(levelname)6s: %(message)s',
        datefmt='%I:%M:%S'
    )
    console_handler.setFormatter(console_formatter)

    # Create logger, add console handler, and return
    logger = logging.getLogger(name)
    logger.setLevel(LOG_LEVEL)
    logger.addHandler(console_handler)
    return logger

def wait_for_uri(uri, timeout=300, wait_sec=5):
    try:
        host, port = uri.split(':')
        port = int(port)
    except ValueError as e:
        logger.error(f"Invalid URI format. Expected format: 'host:port', got '{uri}'.")
        raise e

    start_time = time.time()
    while True:
        elapsed_time = time.time() - start_time

        if elapsed_time > timeout:
            logger.error(
                f"Timeout reached: {uri} is not open after {timeout} seconds."
                f"Waited {elapsed_time} seconds"
            )
            raise TimeoutError

        try:
            with socket.create_connection((host, port), timeout=timeout-elapsed_time):
                logger.info(f"{uri} is now open!")
                break
        except (ConnectionRefusedError, OSError, socket.timeout):
            # Wait a short period before trying again
            logger.warning(f"Waiting {wait_sec}s for application at {uri}")
            time.sleep(wait_sec)