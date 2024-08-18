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

"""
Document Retrieval Service.
Handle document ingestion and retrieval from a VectorDB.
"""

import logging
import os
import sys
import threading
import typing

from flask import Flask, request, jsonify, stream_with_context
from flask.views import MethodView

if typing.TYPE_CHECKING:
    from frontend.api import APIServer

_LOG_LEVEL = logging.getLevelName(os.environ.get('FRONTEND_LOG_LEVEL', 'WARN').upper())
flask_logger = logging.getLogger("werkzeug")
flask_logger.setLevel(logging.getLevelName(_LOG_LEVEL))

_LOG_FMT = f"[{os.getpid()}] %(asctime)15s [%(levelname)7s] - %(name)s - %(message)s"
_LOG_DATE_FMT = "%b %d %H:%M:%S"
_LOGGER = logging.getLogger(__name__)
app = Flask(__name__)

def bootstrap_logging(verbosity: str = 'WARN') -> None:
    """
    Configure Python's logger according to the given verbosity level.
    Use string input, options are any of 'logging' module's logging levels.
    """
    # determine log level
    log_level = logging.getLevelName(verbosity)

    # configure python's logger
    logging.basicConfig(format=_LOG_FMT, datefmt=_LOG_DATE_FMT, level=log_level)
    # update existing loggers
    _LOGGER.setLevel(log_level)
    for logger in [
        __name__,
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        for handler in logging.getLogger(logger).handlers:
            handler.setFormatter(logging.Formatter(fmt=_LOG_FMT, datefmt=_LOG_DATE_FMT))

class DemoAppAPI(MethodView):
    def __init__(self, client):
        self._client = client

    def post(self, action=None, device=None, state=None):
        '''
        This gets called first for an HTTP POST
        This functions determines which function to call based on the url
        e.g /apps/control_device will map method to control_device.
        Data is passed by post and processed in function itself
        '''
        try:
            method = getattr(self, action)
            return method()
        except AttributeError as e:
            return jsonify(f"Error -- no POST action {action} (error: {e})")
        except Exception as e:
            return jsonify(f"POST error {e}")

    def get(self, action):
        '''
        This gets called first for an HTTP GET
        This functions determines which function to call based on the url
        e.g /apps/control_device will map method to control_device.
        '''
        try:
            method = getattr(self, action)
            return method()
        except AttributeError as e:
            return jsonify(f"Error -- no GET action {action} (error: {e})")
        except Exception as e:
            return jsonify(f"GET error {e}")

    def update_running_transcript(self):
        """ Updates the Riva partial transcript """
        data = request.get_json()
        transcript = data.get('transcript')
        return app.response_class(
            stream_with_context(
                self._client.update_running_buffer(transcript)
            )
        )

    def update_finalized_transcript(self):
        """ Updates the Riva final transcript """
        data = request.get_json()
        transcript = data.get('transcript')
        return app.response_class(
            stream_with_context(
                self._client.update_finalized_buffer(transcript)
            )
        )

def create_app(client):
    app.add_url_rule('/app/<string:action>',
                        view_func=DemoAppAPI.as_view('flask_api', client),
                        methods=['POST','GET'])
    return app

def main() -> "APIServer":
    """
    Bootstrap and Execute the application.
    :returns: 0 if the application completed successfully, 1 if an error occurred.
    :rtype: Literal[0,1]
    """
    bootstrap_logging(_LOG_LEVEL)

    # load the application libraries
    # pylint: disable=import-outside-toplevel;
    #   this is intentional to allow for the environment to be configured before
    #   any of the application libraries are loaded.
    from frontend import api, chat_client, configuration

    # load config
    config_file = os.environ.get("APP_CONFIG_FILE", "/dev/null")
    _LOGGER.info("Loading application configuration.")
    config = configuration.AppConfig.from_file(config_file)
    if not config:
        sys.exit(1)
    _LOGGER.info("Configuration: \n%s", config.to_yaml())

    _ = threading.Lock()

    # Connect to other services
    client = chat_client.ChatClient(
        f"{config.server_url}:{config.server_port}", config.model_name
    )

    app_uri = os.environ.get("FRONTEND_URI", "localhost:6001")
    app_port = app_uri.split(':')[-1]
    flask_app = create_app(client)
    threading.Thread(target=lambda: flask_app.run(
        debug=True, host='0.0.0.0', use_reloader=False, port=app_port
    )).start()

    # Create api server
    _LOGGER.info("Instantiating the API Server.")
    server = api.APIServer(client)
    server.configure_routes()

    # Run until complete
    _LOGGER.info("Starting the API Server.")
    return server
