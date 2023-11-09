# SPDX-FileCopyrightText: Copyright (c) 2023 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import logging
from typing import Any, Dict, List, Tuple, Union

import gradio as gr

from frontend import assets, chat_client

_LOGGER = logging.getLogger(__name__)
PATH = "/converse"
TITLE = "Converse"
OUTPUT_TOKENS = 250
MAX_DOCS = 5

_LOCAL_CSS = """

#contextbox {
    overflow-y: scroll !important;
    max-height: 400px;
}
"""


def build_page(client: chat_client.ChatClient) -> gr.Blocks:
    """Buiild the gradio page to be mounted in the frame."""
    kui_theme, kui_styles = assets.load_theme("kaizen")

    with gr.Blocks(title=TITLE, theme=kui_theme, css=kui_styles + _LOCAL_CSS) as page:
        # create the page header
        gr.Markdown(f"# {TITLE}")

        # chat logs
        with gr.Row(equal_height=True):
            chatbot = gr.Chatbot(scale=2, label=client.model_name)
            context = gr.JSON(
                scale=1,
                label="Knowledge Base Context",
                visible=False,
                elem_id="contextbox",
            )

        with gr.Row():
            with gr.Column(scale=10, min_width=600):
                kb_checkbox = gr.Checkbox(
                    label="Use knowledge base", info="", value=False
                )
                msg = gr.Textbox(
                    show_label=False,
                    placeholder="Enter text and press ENTER",
                    container=False,
                )

        # user feedback
        with gr.Row():
            # _ = gr.Button(value="👍  Upvote")
            # _ = gr.Button(value="👎  Downvote")
            # _ = gr.Button(value="⚠️  Flag")
            submit_btn = gr.Button(value="Submit")
            _ = gr.ClearButton(msg)
            _ = gr.ClearButton([msg, chatbot], value="Clear history")
            ctx_show = gr.Button(value="Show Context")
            ctx_hide = gr.Button(value="Hide Context", visible=False)

        # hide/show context
        def _toggle_context(btn: str) -> Dict[gr.component, Dict[Any, Any]]:
            if btn == "Show Context":
                out = [True, False, True]
            if btn == "Hide Context":
                out = [False, True, False]
            return {
                context: gr.update(visible=out[0]),
                ctx_show: gr.update(visible=out[1]),
                ctx_hide: gr.update(visible=out[2]),
            }

        ctx_show.click(_toggle_context, [ctx_show], [context, ctx_show, ctx_hide])
        ctx_hide.click(_toggle_context, [ctx_hide], [context, ctx_show, ctx_hide])

        # form actions
        _my_build_stream = functools.partial(_stream_predict, client)
        msg.submit(
            _my_build_stream, [kb_checkbox, msg, chatbot], [msg, chatbot, context]
        )
        submit_btn.click(
            _my_build_stream, [kb_checkbox, msg, chatbot], [msg, chatbot, context]
        )

    page.queue()
    return page


def _stream_predict(
    client: chat_client.ChatClient,
    use_knowledge_base: bool,
    question: str,
    chat_history: List[Tuple[str, str]],
) -> Any:
    """Make a prediction of the response to the prompt."""
    chunks = ""
    _LOGGER.info(
        "processing inference request - %s",
        str({"prompt": question, "use_knowledge_base": use_knowledge_base}),
    )

    documents: Union[None, List[Dict[str, Union[str, float]]]] = None
    if use_knowledge_base:
        documents = client.search(question)

    for chunk in client.predict(question, use_knowledge_base, OUTPUT_TOKENS):
        chunks += chunk
        yield "", chat_history + [[question, chunks]], documents
