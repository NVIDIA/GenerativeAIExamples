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

"""The API client for the langchain-esque service."""

from collections import deque
from datetime import datetime

import logging
import threading
import typing
import time
import os
import requests

_LOG_LEVEL = logging.getLevelName(os.environ.get('FRONTEND_LOG_LEVEL', 'WARN').upper())
_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(_LOG_LEVEL)

class ChatClient:
    """ A client for connecting the the lanchain-esque service.
    """

    def __init__(self, server_url: str, model_name: str) -> None:
        """Initialize the client."""
        self.server_url = server_url
        self._model_name = model_name
        self._riva_thread = None
        self._riva_output_box = None
        self._buffer = deque(maxlen=50)
        self._lock = threading.Lock()
        self._running_buffer = ""
        self._finalized_buffer = deque(maxlen=50)
        self._timetag_len = len(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}] ')
        self._wait_for_server()

    def _server_is_ready(self):
        try:
            response = requests.get(f"{self.server_url}/serverStatus")
            if response.status_code == 200 and response.json()["is_ready"]:
                return True
        except requests.ConnectionError:
            return False

    def _wait_for_server(self, timeout=300, wait_sec=5):
        """ Wait for server URL to open
        """
        start_time = time.time()
        while not self._server_is_ready():
            # Check for timeout
            elapsed_time = time.time() - start_time
            if elapsed_time > timeout:
                _LOGGER.error(
                    f"Timeout reached: {self.server_url} is not open after {timeout} seconds."
                    f"Waited {elapsed_time} seconds"
                )
                raise TimeoutError

            # Wait a short period before trying again
            _LOGGER.warning(f"Waiting {wait_sec}s for application at {self.server_url}")
            time.sleep(wait_sec)

    @property
    def model_name(self) -> str:
        """Return the friendly model name."""
        return self._model_name

    def get_obj_status(self) -> str:
        connected = False
        max_tries = 60
        tries = 0
        while not connected:
            try:
                response = requests.post(f"{self.server_url}/app/get_all_devices_status")
                connected = True
            except Exception as e:
                tries += 1
                if tries >= max_tries:
                    raise e
                time.sleep(1)
                pass
        return response

    def predict(self, query: str, params: dict) -> typing.Generator[str, None, None]:
        defaults = {
            "question": query,
            "name": "mixtral_8x7b",
            "engine": "nvai-api-endpoint",
            "use_knowledge_base": True,
            "temperature": 1.0,
            "max_docs": 4,
            "num_tokens": 512
        }
        data = {**defaults, **params}
        url = (f"{self.server_url}/generate")
        _LOGGER.debug("making request - %s", str({"server_url": url, "post_data": data}))
        with requests.get(url, stream=True, json=data) as req:
            for chunk in req.iter_content():
                yield chunk.decode("UTF-8", "ignore")

    def update_running_buffer(self, transcript):
        with self._lock:
            # Strip datetime tag and set
            self._running_buffer = transcript[self._timetag_len:]
        yield "Updated transcript buffer"

    def update_finalized_buffer(self, transcript):
        with self._lock:
            # Insert a newline after the datetime tag
            tag, text = transcript[:self._timetag_len], transcript[self._timetag_len:]
            transcript = f"{tag}\n{text}"
            self._finalized_buffer.append(f"{transcript}\n\n")
        yield "Updated transcript buffer"

    def upload_documents(self, file_paths: typing.List[str]) -> None:
        raise NotImplementedError

    def search(self, prompt: str) -> typing.List[typing.Dict[str, typing.Union[str, float]]]:
        raise NotImplementedError