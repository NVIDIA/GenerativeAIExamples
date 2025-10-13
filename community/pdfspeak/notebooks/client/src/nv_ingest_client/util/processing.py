# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import concurrent
import json
import logging
from typing import Any, Tuple
from typing import Dict
from typing import Optional

from nv_ingest_client.util.util import check_ingest_result

logger = logging.getLogger(__name__)


def handle_future_result(
    future: concurrent.futures.Future,
    timeout: Optional[int] = None,
) -> Tuple[Dict[str, Any], str]:
    """
    Handle the result of a completed future job and process annotations.

    This function processes the result of a future, extracts annotations (if any), logs them,
    and checks the validity of the ingest result. If the result indicates a failure, a
    `RuntimeError` is raised with a description of the failure.

    Parameters
    ----------
    future : concurrent.futures.Future
        A future object representing an asynchronous job. The result of this job will be
        processed once it completes.
    timeout : Optional[int], default=None
        Maximum time to wait for the future result before timing out.

    Returns
    -------
    Tuple[Dict[str, Any], str]
        - The result of the job as a dictionary, after processing and validation.
        - The trace_id returned by the submission endpoint

    Raises
    ------
    RuntimeError
        If the job result is invalid, this exception is raised with a description of the failure.

    Notes
    -----
    - The `future.result()` is assumed to return a tuple where the first element is the actual
      result (as a dictionary), and the second element (if present) can be ignored.
    - Annotations in the result (if any) are logged for debugging purposes.
    - The `check_ingest_result` function (assumed to be defined elsewhere) is used to validate
      the result. If the result is invalid, a `RuntimeError` is raised.

    Examples
    --------
    Suppose we have a future object representing a job, a dictionary of futures to job IDs,
    and a directory for saving results:

    >>> future = concurrent.futures.Future()
    >>> result, trace_id = handle_future_result(future, timeout=60)

    In this example, the function processes the completed job and returns the result dictionary.
    If the job fails, it raises a `RuntimeError`.

    See Also
    --------
    check_ingest_result : Function to validate the result of the job.
    """

    try:
        result, _, trace_id = future.result(timeout=timeout)[0]
        if ("annotations" in result) and result["annotations"]:
            annotations = result["annotations"]
            for key, value in annotations.items():
                logger.debug(f"Annotation: {key} -> {json.dumps(value, indent=2)}")

        failed, description = check_ingest_result(result)

        if failed:
            raise RuntimeError(f"{description}")
    except Exception as e:
        logger.debug(f"Error processing future result: {e}")
        raise e

    return (result, trace_id)
