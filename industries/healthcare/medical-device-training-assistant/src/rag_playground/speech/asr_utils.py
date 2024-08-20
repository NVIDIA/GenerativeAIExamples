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

import logging
import queue
from threading import Thread

import gradio as gr
import grpc
import numpy as np
import pycountry
import riva.client
import riva.client.proto.riva_asr_pb2 as riva_asr
import riva.client.proto.riva_asr_pb2_grpc as rasr_srv


class ASRSession:
    def __init__(self):
        self.is_first_buffer = True
        self.request_queue = None
        self.response_stream = None
        self.response_thread = None
        self.transcript = ""


_LOGGER = logging.getLogger(__name__)

# Obtain the ASR languages available on the Riva server
ASR_LANGS = dict()
grpc_auth = None


def asr_init(auth):
    global ASR_LANGS
    global grpc_auth
    grpc_auth = auth
    try:
        _LOGGER.info("Available ASR languages")
        asr_client = riva.client.ASRService(grpc_auth)

        config_response = asr_client.stub.GetRivaSpeechRecognitionConfig(riva_asr.RivaSpeechRecognitionConfigRequest())
        for model_config in config_response.model_config:
            if model_config.parameters["type"] == "online" and model_config.parameters["streaming"]:
                language_code = model_config.parameters['language_code']
                language_name = f"{pycountry.languages.get(alpha_2=language_code[:2]).name} ({language_code})"
                _LOGGER.info(f"{language_name} {model_config.model_name}")
                ASR_LANGS[language_name] = {"language_code": language_code, "model": model_config.model_name}
    except grpc.RpcError as e:
        _LOGGER.info(e.details())
        ASR_LANGS["No ASR languages available"] = "No ASR languages available"
        gr.Info(
            'The app could not find any available ASR languages. Thus, none will appear in the "ASR Language" dropdown menu. Check that you are connected to a Riva server with ASR enabled.'
        )
        _LOGGER.info(
            'The app could not find any available ASR languages. Thus, none will appear in the "ASR Language" dropdown menu. Check that you are connected to a Riva server with ASR enabled.'
        )

    ASR_LANGS = dict(sorted(ASR_LANGS.items()))


def print_streaming_response(asr_session):
    asr_session.transcript = ""
    final_transcript = ""
    try:
        for response in asr_session.response_stream:
            final = ""
            partial = ""
            if not response.results:
                continue
            if len(response.results) > 0 and len(response.results[0].alternatives) > 0:
                for result in response.results:
                    if result.is_final:
                        final += result.alternatives[0].transcript
                    else:
                        partial += result.alternatives[0].transcript

                final_transcript += final
                asr_session.transcript = final_transcript + partial

    except grpc.RpcError as rpc_error:
        print(rpc_error.details())
        # TODO See if Gradio popup error mechanism can be used.
        # For now whow error via transcript text box.
        asr_session.transcript = rpc_error.details()
        return


def start_recording(audio, language, asr_session):
    _LOGGER.info('start_recording')
    asr_session.is_first_buffer = True
    asr_session.request_queue = queue.Queue()
    return "", asr_session


def stop_recording(asr_session):
    _LOGGER.info('stop_recording')
    try:
        asr_session.request_queue.put(None)
        asr_session.response_thread.join()
    except:
        pass
    return asr_session


def transcribe_streaming(audio, language, asr_session):
    _LOGGER.info('transcribe_streaming')
    if language == 'No ASR languages available':
        gr.Info(
            'The app cannot access ASR services. Any attempt to transcribe audio will be unsuccessful. Check that you are connected to a Riva server with ASR enabled.'
        )
        _LOGGER.info(
            'The app cannot access ASR services. Any attempt to transcribe audio will be unsuccessful. Check that you are connected to a Riva server with ASR enabled.'
        )
        return None, None
    rate, data = audio
    if len(data.shape) > 1:
        data = np.mean(data, axis=1)

    if not len(data):
        return asr_session.transcript, asr_session

    if asr_session.is_first_buffer:

        streaming_config = riva.client.StreamingRecognitionConfig(
            config=riva.client.RecognitionConfig(
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                language_code=ASR_LANGS[language]['language_code'],
                max_alternatives=1,
                profanity_filter=False,
                enable_automatic_punctuation=True,
                verbatim_transcripts=False,
                sample_rate_hertz=rate,
                audio_channel_count=1,
                enable_word_time_offsets=True,
                model=ASR_LANGS[language]['model'],
            ),
            interim_results=True,
        )

        rasr_stub = rasr_srv.RivaSpeechRecognitionStub(grpc_auth.channel)

        asr_session.response_stream = rasr_stub.StreamingRecognize(iter(asr_session.request_queue.get, None))

        # First buffer should contain only the config
        request = riva_asr.StreamingRecognizeRequest(streaming_config=streaming_config)
        asr_session.request_queue.put(request)

        asr_session.response_thread = Thread(target=print_streaming_response, args=(asr_session,))

        # run the thread
        asr_session.response_thread.start()

        asr_session.is_first_buffer = False

    request = riva_asr.StreamingRecognizeRequest(audio_content=data.astype(np.int16).tobytes())
    asr_session.request_queue.put(request)

    return asr_session.transcript, asr_session
