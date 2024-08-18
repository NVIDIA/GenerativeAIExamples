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

import json
import logging
import os
import time
from pathlib import Path
from threading import Thread
from typing import TYPE_CHECKING, Any, List

import gradio as gr
import numpy as np
import pycountry
import riva.client
import riva.client.proto.riva_tts_pb2 as riva_tts

_LOGGER = logging.getLogger(__name__)

tts_sample_rate = int(os.getenv("TTS_SAMPLE_RATE", 48000))

# Obtain the TTS languages and voices available on the Riva server
TTS_MODELS = dict()
grpc_auth = None


def tts_init(auth):
    global TTS_MODELS
    global grpc_auth
    grpc_auth = auth
    try:
        tts_client = riva.client.SpeechSynthesisService(auth)
        config_response = tts_client.stub.GetRivaSynthesisConfig(riva_tts.RivaSynthesisConfigRequest())
        for model_config in config_response.model_config:
            language_code = model_config.parameters['language_code']
            language_name = f"{pycountry.languages.get(alpha_2=language_code[:2]).name} ({language_code})"
            voice_name = model_config.parameters['voice_name']
            subvoices = [voice.split(':')[0] for voice in model_config.parameters['subvoices'].split(',')]
            full_voice_names = [voice_name + "." + subvoice for subvoice in subvoices]

            if language_name in TTS_MODELS:
                TTS_MODELS[language_name]['voices'].extend(full_voice_names)
            else:
                TTS_MODELS[language_name] = {"language_code": language_code, "voices": full_voice_names}

        TTS_MODELS = dict(sorted(TTS_MODELS.items()))

        _LOGGER.info(json.dumps(TTS_MODELS, indent=4))
    except:
        TTS_MODELS["No TTS languages available"] = "No TTS languages available"
        gr.Info(
            'The app could not find any available TTS languages. Thus, none will appear in the "TTS Language" or "TTS Voice" dropdown menus. Check that you are connected to a Riva server with TTS enabled.'
        )
        _LOGGER.info(
            'The app could not find any available TTS languages. Thus, none will appear in the "TTS Language" or "TTS Voice" dropdown menus. Check that you are connected to a Riva server with TTS enabled.'
        )


# Once the user selects a TTS language, narrow the options in the TTS voice
# dropdown menu accordingly
def update_voice_dropdown(language):
    if language == "No TTS languages available":
        voice_dropdown = gr.Dropdown(label="Voice", choices="No TTS voices available", value="No TTS voices available")
    else:
        voice_dropdown = gr.Dropdown(
            label="Voice", choices=TTS_MODELS[language]['voices'], value=TTS_MODELS[language]['voices'][0]
        )
    return voice_dropdown


def text_to_speech(text, language, voice, enable_tts):
    if enable_tts:
        if language == "No TTS languages available":
            gr.Info(
                'The app cannot access TTS services. Any attempt to synthesize audio will be unsuccessful. Check that you are connected to a Riva server with TTS enabled.'
            )
            _LOGGER.info(
                'The app cannot access TTS services. Any attempt to synthesize audio will be unsuccessful. Check that you are connected to a Riva server with TTS enabled.'
            )
            return None, gr.update(interactive=False)
        if not text:
            gr.Info('No text from which to synthesize a voice has been provided')
            return None, gr.update(interactive=False)
        if not voice:
            gr.Info('No TTS voice or an invalid TTS voice has been selected')
            return None, gr.update(interactive=False)
    else:
        _LOGGER.debug('TTS output is currently disabled. Click on the "Enable TTS output" checkbox to enable it.')
        return None, gr.update(interactive=False)

    first_buffer = True
    start_time = time.time()

    # TODO: Gradio Flagging doesn't work with streaming audio ouptut.
    # See https://github.com/gradio-app/gradio/issues/5806
    # TODO: Audio download does not work with streaming audio output.
    # See https://github.com/gradio-app/gradio/issues/6570

    tts_client = riva.client.SpeechSynthesisService(grpc_auth)

    _LOGGER.info(f"Calling synthesize_online")

    # To manage the 400-character limit for Riva's text-to-speech (TTS), longer answers are segmented by adding 'full stops' at every 300 characters (300 instead of 400 to take in account phoneme expansion)
    for i in range((len(text) // 300) + 1):
        indx = text.rfind(' ', 0, (i + 1) * 300)
        text = text[:indx] + ' . ' + text[indx:]

    response = tts_client.synthesize_online(
        text=text,
        voice_name=voice,
        language_code=TTS_MODELS[language]['language_code'],
        sample_rate_hz=tts_sample_rate,
    )
    for result in response:
        if len(result.audio):
            if first_buffer:
                _LOGGER.info(f"TTS request [{result.id.value}] first buffer latency: {time.time() - start_time} sec")
                first_buffer = False
            yield (tts_sample_rate, np.frombuffer(result.audio, dtype=np.int16))

    _LOGGER.info(f"TTS request [{result.id.value}] last buffer latency: {time.time() - start_time} sec")

    yield (tts_sample_rate, np.frombuffer(b'', dtype=np.int16))
