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

"""Main entrypoint for the model-server application."""
import argparse
import logging
import os
import sys

from . import main
from .errors import ModelServerException
from .model import ModelTypes

TERMINATION_LOG = "/dev/termination-log"

_LOG_FMT = f"[{os.getpid()}] %(asctime)15s [%(levelname)7s] - %(name)s - %(message)s"
_LOG_DATE_FMT = "%b %d %H:%M:%S"
_LOGGER = logging.getLogger("main")


def parse_args() -> argparse.Namespace:
    """Parse the comamnd line arguments."""
    parser = argparse.ArgumentParser(
        prog="model-server",
        description="Ingest models and host them with NVIDIA TensorRT LLM",
    )

    # options
    parser.add_argument(
        "-w",
        "--world-size",
        default=None,
        type=int,
        help="The number of GPUs to shard the model across. "
        + "By default, this value will be equal to the number of available GPUs.",
    )
    parser.add_argument(
        "--force-conversion",
        action="store_true",
        help="When this flag is set, the TensorRT engine conversion will occur, "
        + "even if a valid engine is in the cache.",
    )
    parser.add_argument(
        "--no-conversion",
        action="store_true",
        help="Skip the conversion. If no engine is available in the cache, an error will be raised.",
    )
    parser.add_argument(
        "--no-hosting",
        action="store_true",
        help="Do not start the Triton Inference Server. Only convert the model then exit.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=1,
        help="increase output verbosity",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="count",
        default=0,
        help="decrease output verbosity",
    )

    # builder customization
    parser.add_argument(
        "--max-input-length",
        type=int,
        default=3000,
        help="maximum number of input tokens",
    )
    parser.add_argument(
        "--max-output-length",
        type=int,
        default=512,
        help="maximum number of output tokens",
    )
    parser.add_argument(
        "--tensor-parallelism",
        type=int,
        default=None,
        help="number of tensor parallelism divisions (default: world_size/pipeline_parallelism)",
    )
    parser.add_argument(
        "--pipeline-parallelism",
        type=int,
        default=1,
        help="number of pipeline parallism divisions (default: 1)",
    )

    parser.add_argument(
        "--quantization",
        type=str,
        default=None,
        help="Quantization type to be used for LLMs",
    )

    # server customization
    parser.add_argument(
        "--http",
        action="store_true",
        help="change the api server to http instead of grpc (note: this will disable token streaming)",
    )

    # positional arguments
    supported_model_types = [e.name.lower().replace("_", "-") for e in ModelTypes]
    parser.add_argument(
        "type",
        metavar="TYPE",
        choices=supported_model_types,
        type=str.lower,
        help=f"{supported_model_types}    The type of model to process.",
    )

    args = parser.parse_args()

    if args.force_conversion and args.no_conversion:
        parser.error("--force_conversion and --no-conversion are mutually exclusive.")

    return args


def _bootstrap_logging(verbosity: int = 0) -> None:
    """Configure Python's logger according to the given verbosity level.

    :param verbosity: The desired verbosity level. Must be one of 0, 1, or 2.
    :type verbosity: typing.Literal[0, 1, 2]
    """
    # determine log level
    verbosity = min(2, max(0, verbosity))  # limit verbosity to 0-2
    log_level = [logging.WARN, logging.INFO, logging.DEBUG][verbosity]

    # configure python's logger
    logging.basicConfig(format=_LOG_FMT, datefmt=_LOG_DATE_FMT, level=log_level)
    # update existing loggers
    _LOGGER.setLevel(log_level)
    # pylint: disable-next=no-member; false positive
    for logger_name in logging.root.manager.loggerDict:
        logger = logging.getLogger(logger_name)
        for handler in logger.handlers:
            handler.setFormatter(logging.Formatter(fmt=_LOG_FMT, datefmt=_LOG_DATE_FMT))


def _k8s_error_handler(err: Exception) -> None:
    """When running in Kubernetes, write errors to the termination log."""
    with open(TERMINATION_LOG, "w", encoding="UTF-8") as term_log:
        # recursively write nested exceptions
        def _write_errors_to_term_log(e: BaseException) -> None:
            term_log.write(f"{type(e)}: {e}\n")
            if e.__cause__:
                _write_errors_to_term_log(e.__cause__)

        _write_errors_to_term_log(err)


def _error_handler(err: Exception) -> int:
    """Catch and handle exceptions from the applicaiton."""
    # keybaord interrupts are fine
    if isinstance(err, KeyboardInterrupt):
        return 0

    # on k8s, write errors to log file
    if os.path.isfile(TERMINATION_LOG):
        _k8s_error_handler(err)

    # raise uncaught errors
    if not isinstance(err, ModelServerException):
        raise err

    # gracefully handle caught errors
    _LOGGER.error(str(err))

    # if there is a nested error, raise it
    if err.__cause__:
        raise err.__cause__

    # we decided to quite gracefully
    return 1


if __name__ == "__main__":
    try:
        _ARGS = parse_args()
        _bootstrap_logging(_ARGS.verbose - _ARGS.quiet)
        sys.exit(main(_ARGS))
    # pylint: disable-next=broad-exception-caught; Error handling based on type is done in the handler
    except Exception as _ERR:
        sys.exit(_error_handler(_ERR))
