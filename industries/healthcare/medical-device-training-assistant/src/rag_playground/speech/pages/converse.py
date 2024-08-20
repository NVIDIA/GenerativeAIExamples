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
import os
from typing import Any, Dict, List, Tuple, Union

import gradio as gr
import riva.client
from frontend import asr_utils, assets, chat_client, tts_utils

_LOGGER = logging.getLogger(__name__)
PATH = "/converse"
TITLE = "Converse"
OUTPUT_TOKENS = 1024
MAX_DOCS = 5

_LOCAL_CSS = """

#contextbox {
    overflow-y: scroll !important;
    max-height: 400px;
}
"""

# Extract environmental variables
RIVA_API_URI = os.getenv("RIVA_API_URI", None)
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY", None)
RIVA_ASR_FUNCTION_ID = os.getenv("RIVA_ASR_FUNCTION_ID", None)
RIVA_TTS_FUNCTION_ID = os.getenv("RIVA_TTS_FUNCTION_ID", None)

# Establish a connection to the Riva server
try:
    use_ssl = False
    metadata_asr = []
    metadata_tts = []
    if NVIDIA_API_KEY:
        use_ssl = True
        metadata_asr.append(("authorization", "Bearer " + NVIDIA_API_KEY))
        metadata_tts.append(("authorization", "Bearer " + NVIDIA_API_KEY))
    if RIVA_ASR_FUNCTION_ID:
        use_ssl = True
        metadata_asr.append(("function-id", RIVA_ASR_FUNCTION_ID))
    if RIVA_TTS_FUNCTION_ID:
        use_ssl = True
        metadata_tts.append(("function-id", RIVA_TTS_FUNCTION_ID))

    auth_tts = riva.client.Auth(None, use_ssl=use_ssl, uri=RIVA_API_URI, metadata_args=metadata_tts)
    auth_asr = riva.client.Auth(None, use_ssl=use_ssl, uri=RIVA_API_URI, metadata_args=metadata_asr)
    _LOGGER.info('Created riva.client.Auth success')
except:
    _LOGGER.info('Error creating riva.client.Auth')


def build_page(client: chat_client.ChatClient) -> gr.Blocks:
    """Build the gradio page to be mounted in the frame."""
    kui_theme, kui_styles = assets.load_theme("kaizen")

    asr_utils.asr_init(auth_asr)
    tts_utils.tts_init(auth_tts)

    with gr.Blocks(title=TITLE, theme=kui_theme, css=kui_styles + _LOCAL_CSS) as page:

        # session specific state across runs
        state = gr.State(value=asr_utils.ASRSession())

        # create the page header
        gr.Markdown(f"# {TITLE}")

        # chat logs
        with gr.Row(equal_height=True):
            chatbot = gr.Chatbot(scale=2, label=client.model_name)
            latest_response = gr.Textbox(visible=False)
            context = gr.JSON(scale=1, label="Knowledge Base Context", visible=False, elem_id="contextbox",)

        # TTS output box
        # visible so that users can stop or replay playback
        with gr.Row():
            output_audio = gr.Audio(
                label="Synthesized Speech",
                autoplay=True,
                interactive=False,
                streaming=True,
                visible=True,
                show_download_button=False,
            )

        # check boxes
        with gr.Row():
            with gr.Column(scale=10, min_width=150):
                kb_checkbox = gr.Checkbox(label="Use knowledge base", info="", value=False)
            with gr.Column(scale=10, min_width=150):
                tts_checkbox = gr.Checkbox(label="Enable TTS output", info="", value=False)

        # dropdowns
        with gr.Accordion("ASR and TTS Settings"):
            with gr.Row():
                asr_language_list = list(asr_utils.ASR_LANGS)
                asr_language_dropdown = gr.components.Dropdown(
                    label="ASR Language", choices=asr_language_list, value=asr_language_list[0],
                )
                tts_language_list = list(tts_utils.TTS_MODELS)
                tts_language_dropdown = gr.components.Dropdown(
                    label="TTS Language", choices=tts_language_list, value=tts_language_list[0],
                )
                all_voices = []
                try:
                    for model in tts_utils.TTS_MODELS:
                        all_voices.extend(tts_utils.TTS_MODELS[model]['voices'])
                    default_voice = tts_utils.TTS_MODELS[tts_language_list[0]]['voices'][0]
                except:
                    all_voices.append("No TTS voices available")
                    default_voice = "No TTS voices available"
                tts_voice_dropdown = gr.components.Dropdown(
                    label="TTS Voice", choices=all_voices, value=default_voice,
                )

        # audio and text input boxes
        with gr.Row():
            with gr.Column(scale=10, min_width=500):
                msg = gr.Textbox(show_label=False, placeholder="Enter text and press ENTER", container=False,)
            # For (at least) Gradio 3.39.0 and lower, the first argument
            # in the list below is named `source`. If not None, it must
            # be a single string, namely either "upload" or "microphone".
            # For more recent Gradio versions (such as 4.4.1), it's named
            # `sources`, plural. If not None, it must be a list, containing
            # either "upload", "microphone", or both.
            audio_mic = gr.Audio(
                sources=["microphone"],
                type="numpy",
                streaming=True,
                visible=True,
                label="Transcribe Audio Query",
                show_label=False,
                container=False,
                elem_id="microphone",
            )

        # user feedback
        with gr.Row():
            # _ = gr.Button(value="👍  Upvote")
            # _ = gr.Button(value="👎  Downvote")
            # _ = gr.Button(value="⚠️  Flag")
            submit_btn = gr.Button(value="Submit")
            _ = gr.ClearButton(msg)
            _ = gr.ClearButton([msg, chatbot], value="Clear History")
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
        msg.submit(_my_build_stream, [kb_checkbox, msg, chatbot], [msg, chatbot, context, latest_response])
        submit_btn.click(_my_build_stream, [kb_checkbox, msg, chatbot], [msg, chatbot, context, latest_response])

        tts_language_dropdown.change(
            tts_utils.update_voice_dropdown, [tts_language_dropdown], [tts_voice_dropdown], api_name=False
        )

        audio_mic.start_recording(
            asr_utils.start_recording, [audio_mic, asr_language_dropdown, state], [msg, state], api_name=False,
        )
        audio_mic.stop_recording(asr_utils.stop_recording, [state], [state], api_name=False)
        audio_mic.stream(
            asr_utils.transcribe_streaming, [audio_mic, asr_language_dropdown, state], [msg, state], api_name=False
        )
        audio_mic.clear(lambda: "", [], [msg], api_name=False)

        latest_response.change(
            tts_utils.text_to_speech,
            [latest_response, tts_language_dropdown, tts_voice_dropdown, tts_checkbox],
            [output_audio],
            api_name=False,
        )

    page.queue()
    return page


def _stream_predict(
    client: chat_client.ChatClient, use_knowledge_base: bool, question: str, chat_history: List[Tuple[str, str]],
) -> Any:
    """Make a prediction of the response to the prompt."""
    chunks = ""
    chat_history = chat_history or []
    _LOGGER.info(
        "processing inference request - %s", str({"prompt": question, "use_knowledge_base": use_knowledge_base}),
    )

    documents: Union[None, List[Dict[str, Union[str, float]]]] = None
    if use_knowledge_base:
        documents = client.search(prompt=question)

    for chunk in client.predict(query=question, use_knowledge_base=use_knowledge_base, num_tokens=OUTPUT_TOKENS):
        if chunk:
            chunks += chunk
            yield "", chat_history + [[question, chunks]], documents, ""
        else:
            yield "", chat_history + [[question, chunks]], documents, chunks
