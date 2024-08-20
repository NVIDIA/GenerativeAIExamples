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

"""This module contains the frontend gui for chat."""
from pathlib import Path
from typing import List
from datetime import datetime

import psutil
import gradio as gr

from frontend import assets

from pynvml import *

PATH = "/stats"
TITLE = "Statistics Page"


def build_page() -> gr.Blocks:
    """Buiild the gradio page to be mounted in the frame."""
    kui_theme, kui_styles = assets.load_theme("kaizen")

    with gr.Blocks(title=TITLE, theme=kui_theme, css=kui_styles) as page:
        # create the page header
        gr.Markdown(f"# {TITLE}")

        # TODO: Code to display stats
        _ = gr.Textbox(value = _get_cpu_stats(), label = "CPU Stats", interactive=False, every=2)
        _ = gr.Textbox(value = _get_gpu_stats(), label = "GPU Stats", interactive=False, every=2)


    page.queue()
    return page

def _get_cpu_stats() -> callable:
    def _cpu_stats():
        print_str = (f"| CPU Utilization: {psutil.cpu_percent()}% | Memory utilization: {psutil.virtual_memory().percent}% |")
        return print_str
    return _cpu_stats

def _get_gpu_stats() -> callable:
    def _gpu_stats():
        print_str = ""
        nvmlInit()
        deviceCount = nvmlDeviceGetCount()
        for i in range(deviceCount):
            handle = nvmlDeviceGetHandleByIndex(i)
            name = nvmlDeviceGetName(handle)
            util = nvmlDeviceGetUtilizationRates(handle)
            mem = nvmlDeviceGetMemoryInfo(handle)
            print_str += (f"| Device {i} | {name} | Mem Free: {mem.free/1024**2:5.2f}MB / {mem.total/1024**2:5.2f}MB | gpu-util: {util.gpu:3.0%} | gpu-mem: {util.memory:3.1%} |\n")
        return print_str
    return _gpu_stats


