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

"""This module contains the frontend gui for having a conversation."""
import functools
import os
import logging
import requests
from typing import Any, Dict, List, Tuple, Union

import gradio as gr
import pandas as pd

from frontend import assets, chat_client

_LOG_LEVEL = logging.getLevelName(os.environ.get('FRONTEND_LOG_LEVEL', 'WARN').upper())
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(_LOG_LEVEL)
PATH = "/converse"
TITLE = "Converse"
OUTPUT_TOKENS = 250
MAX_DOCS = 5

_LOCAL_CSS = """

#contextbox {
    overflow-y: scroll !important;
    max-height: 400px;
}

.submit-button {
    height: 40px;
    width: 80px;
}

"""

BACKEND_MAPPING = {
    "Local NVIDIA NIM": "triton-trt-llm",
    "NVIDIA API Endpoint": "nvai-api-endpoint"
}

def get_backend_and_model(option):
    backend, model = option.split(' - ')
    backend = BACKEND_MAPPING[backend]
    return backend, model

def build_page(client: chat_client.ChatClient) -> gr.Blocks:
    """Buiild the gradio page to be mounted in the frame."""
    kui_theme, kui_styles = assets.load_theme("kaizen")

    # Setup model options
    backend_options = []

    # Add local NIM if running
    nim_model = os.environ.get('NIM_LLM_DISPLAY', None)
    if os.environ.get('DEPLOY_LOCAL_NIM', 'False').lower() in ('true', '1'):
        backend_options.append(f"Local NVIDIA NIM - {nim_model}")

    # Get NVIDIA API Endpoint model options
    response = requests.get(f"{client.server_url}/availableNvidiaModels")
    for model in response.json()["models"]:
        backend_options.append(f"NVIDIA API Endpoint - {model}")

    with gr.Blocks(title=TITLE, theme=kui_theme, css=kui_styles + _LOCAL_CSS) as page:

        with gr.Row():

            # Chat column
            with gr.Column(scale=3):
                gr.Markdown(value="**<font size='4'>User Query</font>**")
                with gr.Row(equal_height=True):
                    chatbot = gr.Chatbot(height=700)
                    context = gr.JSON(
                        label="Knowledge Base Context",
                        visible=False,
                        elem_id="contextbox",
                    )
                with gr.Row():
                    msg = gr.TextArea(
                        show_label=False,
                        placeholder="Enter text and press ENTER",
                        container=False,
                        lines=3,
                        scale=7
                    )
                    submit_btn = gr.Button(
                        value="Submit",
                        elem_classes=["submit-button"]
                    )

                with gr.Row():
                    with gr.Column():
                        backend_dropdown = gr.Dropdown(
                            choices=backend_options,
                            value=backend_options[0],
                            label="LLM Backend / Model",
                            interactive=True
                        )
                        knowledge_checkbox = gr.Checkbox(
                            value=True,
                            label="Use knowledge base",
                            interactive=True
                        )
                        summary_checkbox = gr.Checkbox(
                            value=True,
                            label="Allow long-form summarization",
                            interactive=True
                        )
                    with gr.Column():
                        temp_slider = gr.Slider(
                            minimum=0,
                            maximum=1,
                            value=1,
                            label="Temperature",
                            step=0.05,
                            interactive=True
                        )
                        tokens_slider = gr.Slider(
                            minimum=32,
                            maximum=1024,
                            value=1024,
                            label="Max Tokens",
                            step=32,
                            interactive=True
                        )
                        entries_slider = gr.Slider(
                            minimum=1,
                            maximum=25,
                            value=25,
                            label="Retrieval Max Entries",
                            step=1,
                            interactive=True
                        )

            # Riva transcript
            with gr.Column(scale=2):

                gr.Markdown(value="**<font size='4'>Live Riva ASR</font>**")
                with gr.Row():
                    _ = gr.Textbox(value=get_running_buffer_data(client),
                                   every=0.5,
                                   lines=10,
                                   max_lines=10,
                                   interactive=False,
                                   container=False)

                gr.Markdown(value="**<font size='4'>Transcript</font>**")
                with gr.Row():
                    _ = gr.Textbox(value=get_finalized_buffer_data(client),
                                   every=1,
                                   lines=30,
                                   max_lines=30,
                                   interactive=False,
                                   container=False)

        # form actions
        _my_build_stream = functools.partial(_stream_predict, client)
        inputs = [
            backend_dropdown,
            knowledge_checkbox,
            summary_checkbox,
            temp_slider,
            tokens_slider,
            entries_slider,
            msg,
            chatbot
        ]
        history = [msg, chatbot, context]
        msg.submit(_my_build_stream, inputs, history)
        submit_btn.click(_my_build_stream, inputs, history)

    page.queue()
    return page

def get_running_buffer_data(client: chat_client.ChatClient) -> callable:
    def get_data() -> str:
        with client._lock:
            data = "".join(client._running_buffer)
        return data
    return get_data

def get_finalized_buffer_data(client: chat_client.ChatClient) -> callable:
    def get_data() -> str:
        with client._lock:
            data = "".join(client._finalized_buffer)
        return data
    return get_data

def _stream_predict(
    client: chat_client.ChatClient,
    backend_option: str,
    knowledge_checkbox: bool,
    summary_checkbox: bool,
    temperature: float,
    max_tokens: int,
    max_entries: int,
    question: str,
    chat_history: List[Tuple[str, str]]
) -> Any:
    """Make a prediction of the response to the prompt."""
    chunks = ""
    backend, model = get_backend_and_model(backend_option)
    params = {
        "question": question,
        "name": model,
        "engine": backend,
        "use_knowledge_base": knowledge_checkbox,
        "allow_summary": summary_checkbox,
        "temperature": temperature,
        "max_docs": max_entries,
        "num_tokens": max_tokens
    }
    _LOGGER.info(f"processing inference request - {question} [{params}]")

    documents: Union[None, List[Dict[str, Union[str, float]]]] = None

    for chunk in client.predict(question, params):
        chunks += chunk
        yield "", chat_history + [[question, chunks]], documents
