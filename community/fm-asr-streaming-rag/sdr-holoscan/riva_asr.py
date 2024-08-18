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

import threading
import datetime
import requests

import riva.client
import riva.client.proto.riva_asr_pb2 as rasr

from queue import Queue
from copy import deepcopy
from common import setup_logging


class RivaThread(threading.Thread):
    def __init__(self, buffer: Queue, params, frontend_uri=None, database_uri=None):
        threading.Thread.__init__(self)
        self.buffer = buffer
        self.params = params
        self.frontend_uri = frontend_uri
        self.database_uri = database_uri
        self.logger = setup_logging("riva_asr")
        self._prev_partial_transcript = None

        # Riva handlers
        self._riva_auth = riva.client.Auth(uri=params['uri'])
        self._riva_client = riva.client.ASRService(self._riva_auth)
        self._riva_config = self._gen_config()
        self._kill = threading.Event()

    def run(self):
        while not self._kill.is_set():
            responses = self.make_riva_request()
            try:
                self.extract_transcripts(responses)
            except Exception as e:
                self.logger.error(f"Riva thread exception {e}")
                raise

    def _post_request(self, endpoint, data):
        try:
            client_response = requests.post(endpoint, json=data)
            self.logger.debug(f'Posted {data}, got response {client_response._content}')
            self.logger.debug("--------------------------")
        except requests.exceptions.ConnectionError:
            self.logger.error(f"Failed to connect to the '{endpoint}' endpoint")

    def _database_export(self, transcript):
        endpoint = f'http://{self.database_uri}/storeStreamingText'
        data = {
            'transcript': transcript,
            'source_id': "Channel 0",
            'timestamp': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self._post_request(endpoint, data)

    def _frontend_export(self, cmd, transcript):
        endpoint = f"http://{self.frontend_uri}/app/{cmd}"
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data = {'transcript': f"[{time}] {transcript}"}
        self._post_request(endpoint, data)

    def _export_final_transcript(self, transcript):
        """ Send final transcript to both database and frontend
        """
        self.logger.debug(f"Final: {transcript}")
        self._database_export(transcript)
        self._frontend_export("update_finalized_transcript", transcript)

    def _export_partial_transcript(self, transcript):
        """ Update frontend with partial transcript
        """
        if transcript == self._prev_partial_transcript:
            return

        self._prev_partial_transcript = transcript
        self.logger.debug(f"Partial: {transcript}")
        self._frontend_export("update_running_transcript", transcript)

    def extract_transcripts(self, responses):
        if not responses:
            return

        for response in responses:
            if self._kill.is_set():
                break
            if not response.results:
                continue

            is_final = False
            partial_transcript = ""
            for result in response.results:
                # Note: this assumes max_alternatives == 1
                transcript = result.alternatives[0].transcript
                if len(transcript) == 0:
                    continue

                if result.is_final:
                    is_final = True
                    self._export_final_transcript(transcript)
                else:
                    partial_transcript += transcript

            if not is_final:
                self._export_partial_transcript(partial_transcript)

    def _gen_config(self) -> riva.client.StreamingRecognitionConfig:
        asr_config = riva.client.RecognitionConfig(
                encoding=riva.client.AudioEncoding.LINEAR_PCM,
                language_code=self.params["src_lang_code"],
                max_alternatives=1,
                profanity_filter=False,
                enable_automatic_punctuation=self.params["automatic_punctuation"],
                verbatim_transcripts=self.params["verbatim_transcripts"],
                sample_rate_hertz=self.params["sample_rate"],
                audio_channel_count=1
            )
        streaming_config = riva.client.StreamingRecognitionConfig(
            config=deepcopy(asr_config),
            interim_results=True
        )
        return streaming_config

    def _request_generator(self):
        yield rasr.StreamingRecognizeRequest(streaming_config=self._riva_config)
        while True:
            yield self.buffer.get()

    def make_riva_request(self):
        responses = self._riva_client.stub.StreamingRecognize(
            self._request_generator(),
            metadata=self._riva_client.auth.get_auth_metadata()
        )
        return responses