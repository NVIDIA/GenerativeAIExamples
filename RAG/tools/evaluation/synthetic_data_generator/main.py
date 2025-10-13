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

import argparse
import logging
import os

from data_generator import generate_synthetic_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--docs", type=str, nargs="?", default="", help="Specify the folder path for dataset.",
    )
    parser.add_argument(
        "--gd_output", type=str, nargs="?", default="", help="Specify the .JSON file path for storing QnA pairs.",
    )

    args = parser.parse_args()

    generate_synthetic_data(
        dataset_folder_path=args.docs, qa_generation_file_path=args.gd_output,
    )
    logger.info("\DATA GENERATED\n")
