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

"""The API client for the langchain-esque service."""
import json
import logging
import mimetypes
import typing

import requests
from frontend import tracing
from requests.exceptions import ConnectionError

_LOGGER = logging.getLogger(__name__)


class ChatClient:
    """A client for connecting the the lanchain-esque service."""

    def __init__(self, server_url: str, model_name: str) -> None:
        """Initialize the client."""
        self.server_url = server_url
        self._model_name = model_name
        self.default_model = "meta/llama3-70b-instruct"

    @property
    def model_name(self) -> str:
        """Return the friendly model name."""
        return self._model_name

    @tracing.instrumentation_wrapper
    def search(self, carrier, prompt: str) -> typing.List[typing.Dict[str, typing.Union[str, float]]]:
        """Search for relevant documents and return json data."""
        data = {"query": prompt, "top_k": 4}
        headers = {**carrier, "accept": "application/json", "Content-Type": "application/json"}
        url = f"{self.server_url}/search"
        _LOGGER.debug("looking up documents - %s", str({"server_url": url, "post_data": data}))

        try:
            with requests.post(url, headers=headers, json=data, timeout=30) as req:
                req.raise_for_status()
                response = req.json()
                return typing.cast(typing.List[typing.Dict[str, typing.Union[str, float]]], response)
        except Exception as e:
            _LOGGER.error(
                f"Failed to get response from /documentSearch endpoint of chain-server. Error details: {e}. Refer to chain-server logs for details."
            )
            return typing.cast(typing.List[typing.Dict[str, typing.Union[str, float]]], [])

    @tracing.predict_instrumentation_wrapper
    def predict(
        self, carrier, query: str, use_knowledge_base: bool, num_tokens: int
    ) -> typing.Generator[str, None, None]:
        """Make a model prediction."""
        data = {
            "messages": [{"role": "user", "content": query}],
            "use_knowledge_base": use_knowledge_base,
        }
        url = f"{self.server_url}/generate"
        _LOGGER.debug("making inference request - %s", str({"server_url": url, "post_data": data}))

        try:
            with requests.post(url, stream=True, json=data, timeout=50, headers=carrier) as req:
                req.raise_for_status()
                for chunk in req.iter_lines():
                    raw_resp = chunk.decode("UTF-8")
                    if not raw_resp:
                        continue
                    resp_dict = None
                    try:
                        resp_dict = json.loads(raw_resp[6:])
                        resp_choices = resp_dict.get("choices", [])
                        if len(resp_choices):
                            resp_str = resp_choices[0].get("message", {}).get("content", "")
                            yield resp_str
                        else:
                            yield ""
                    except Exception as e:
                        raise ValueError(f"Invalid response json: {raw_resp}") from e

        except Exception as e:
            _LOGGER.error(
                f"Failed to get response from /generate endpoint of chain-server. Error details: {e}. Refer to chain-server logs for details."
            )
            yield str(
                "Failed to get response from /generate endpoint of chain-server. Check if the fastapi server in chain-server is up. Refer to chain-server logs for details."
            )

        # Send None to indicate end of response
        yield None

    @tracing.instrumentation_wrapper
    def upload_documents(self, carrier, file_paths: typing.List[str]) -> None:
        """Upload documents to the kb."""
        url = f"{self.server_url}/documents"
        headers = {
            **carrier,
            "accept": "application/json",
        }

        try:
            for fpath in file_paths:
                mime_type, _ = mimetypes.guess_type(fpath)
                # pylint: disable-next=consider-using-with # with pattern is not intuitive here
                files = {"file": (fpath, open(fpath, "rb"), mime_type)}

                _LOGGER.debug(
                    "uploading file - %s", str({"server_url": url, "file": fpath}),
                )

                resp = requests.post(
                    url, headers=headers, files=files, timeout=600  # type: ignore [arg-type]
                )
                if resp.status_code == 500:
                    raise ValueError(f"{resp.json().get('message', 'Failed to upload document')}")
        except Exception as e:
            _LOGGER.error(
                f"Failed to get response from /documents endpoint of chain-server. Error details: {e}. Refer to chain-server logs for details."
            )
            raise ValueError(f"{e}")

    @tracing.instrumentation_wrapper
    def delete_documents(self, carrier, file_name: str) -> str:
        """ Delete Selected documents"""
        headers = {**carrier, "accept": "application/json", "Content-Type": "application/json"}
        params = {'filename': file_name}
        url = f"{self.server_url}/documents"

        try:
            _LOGGER.debug(f"Delete request received for file_name: {file_name}")
            with requests.delete(url, headers=headers, params=params, timeout=30) as req:
                req.raise_for_status()
                response = req.json()
                return response
        except Exception as e:
            _LOGGER.error(
                f"Failed to delete {file_name} using /documents endpoint of chain-server. Error details: {e}. Refer to chain-server logs for details."
            )
            return ""

    @tracing.instrumentation_wrapper
    def get_uploaded_documents(self, carrier) -> typing.List[str]:
        """Get list of Uploaded documents."""
        url = f"{self.server_url}/documents"
        headers = {
            **carrier,
            "accept": "application/json",
        }
        uploaded_files = []
        try:
            resp = requests.get(url, headers=headers, timeout=600)
            response = json.loads(resp.content)
            if resp.status_code == 500:
                raise ValueError(f"{resp.json().get('message', 'Failed to get uploaded documents')}")
            else:
                uploaded_files = response['documents']
        except ConnectionError as e:
            # Avoid playground crash when chain server starts after rag-playground
            _LOGGER.error(f"Failed to connect /documents endpoint of chain-server. Error details: {e}.")
        except Exception as e:
            _LOGGER.error(
                f"Failed to get response from /documents endpoint of chain-server. Error details: {e}. Refer to chain-server logs for details."
            )
            raise ValueError(f"{e}")
        return uploaded_files
