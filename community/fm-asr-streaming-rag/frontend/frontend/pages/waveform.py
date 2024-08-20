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
import os
from pathlib import Path
from typing import List, Tuple

import gradio as gr

from frontend import assets, chat_client

from math import log2, pow

import numpy as np
from scipy.fftpack import fft
# import matplotlib.pyplot as plt

PATH = "/waveform"
TITLE = "Input Audio Waveform"

def build_page() -> gr.Blocks:
    """Buiild the gradio page to be mounted in the frame."""
    kui_theme, kui_styles = assets.load_theme("kaizen")

    with gr.Blocks(title=TITLE, theme=kui_theme, css=kui_styles) as page:
        # create the page header
        gr.Markdown(f"# {TITLE}")
        _ = gr.Textbox(
            value="TBD - connect frequency plot here",
            label="Unimplemented",
            interactive=False
        )

    page.queue()
    return page