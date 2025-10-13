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

"""Entrypoint for the Conversation GUI.

The functions in this module are responsible for bootstrapping then executing the Conversation GUI server.
"""

import argparse
import os
import sys

import uvicorn


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the program.

    :returns: A namespace containing the parsed arguments.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="Document Retrieval Service")

    parser.add_argument(
        "--help-config", action="store_true", default=False, help="show the configuration help text",
    )

    parser.add_argument(
        "-c",
        "--config",
        metavar="CONFIGURATION_FILE",
        default="/dev/null",
        help="path to the configuration file (json or yaml)",
    )
    parser.add_argument(
        "-v", "--verbose", action="count", default=1, help="increase output verbosity",
    )
    parser.add_argument(
        "-q", "--quiet", action="count", default=0, help="decrease output verbosity",
    )

    parser.add_argument(
        "--host",
        metavar="HOSTNAME",
        type=str,
        default="0.0.0.0",  # nosec # this is intentional
        help="Bind socket to this host.",
    )
    parser.add_argument(
        "--port", metavar="PORT_NUM", type=int, default=8080, help="Bind socket to this port.",
    )
    parser.add_argument(
        "--workers", metavar="NUM_WORKERS", type=int, default=1, help="Number of worker processes.",
    )
    parser.add_argument("--ssl-keyfile", metavar="SSL_KEY", type=str, default=None, help="SSL key file")
    parser.add_argument(
        "--ssl-certfile", metavar="SSL_CERT", type=str, default=None, help="SSL certificate file",
    )

    cliargs = parser.parse_args()
    if cliargs.help_config:
        # pylint: disable=import-outside-toplevel; this is intentional to allow for the environment to be configured
        #                                          before any of the application libraries are loaded.
        from frontend.configuration import AppConfig

        sys.stdout.write("\nconfiguration file format:\n")
        AppConfig.print_help(sys.stdout.write)
        sys.exit(0)

    return cliargs


if __name__ == "__main__":
    args = parse_args()
    os.environ["APP_VERBOSITY"] = f"{args.verbose - args.quiet}"
    os.environ["APP_CONFIG_FILE"] = args.config
    uvicorn.run(
        "frontend:main",
        factory=True,
        host=args.host,
        port=args.port,
        workers=args.workers,
        ssl_keyfile=args.ssl_keyfile,
        ssl_certfile=args.ssl_certfile,
    )
