# SPDX-FileCopyrightText: Copyright (c) 2024, NVIDIA CORPORATION & AFFILIATES.
# All rights reserved.
# SPDX-License-Identifier: Apache-2.0

import asyncio
import json
import logging
import os
from typing import Dict
from typing import List
from typing import Optional

import httpx

logger = logging.getLogger(__name__)


class AsyncZipkinClient:

    def __init__(self, host: str, port: int, concurrent_requests: int, max_retries: int = 10, retry_delay: int = 5):
        if host.startswith("http"):
            self._host = host
        else:
            logger.debug("Defaulting to http:// for Zipkin host protocol")
            self._host = "http://" + host

        self._port = port
        self._concurrent_requests = concurrent_requests
        self._max_retries = max_retries
        self._retry_delay = retry_delay

    async def fetch(self, sem, trace_id: str, url: str) -> Dict[str, str]:
        """
        Perform a GET request to the given URL with retry logic for 404 status codes.

        :param url: URL to make the GET request to.
        :param sem: Semaphore to ensure only X concurrent requests are in flight
        :param trace_id: The trace_id for the request
        :param url: The complete URL for the request.

        :return: Dict[str, str] Containing trace_id and JSON str response
        :raises: RuntimeError if the maximum retries are exceeded.
        """
        attempt = 0
        while attempt < self._max_retries:
            timeout = httpx.Timeout(10.0)
            async with sem:
                async with httpx.AsyncClient() as client:
                    response = await client.get(url, timeout=timeout)
                    if response.status_code == 404:
                        attempt += 1
                        logger.info(
                            f"Attempt {attempt}/{self._max_retries} for trace_id: {trace_id} failed with 404. "
                            f"Retrying in {self._retry_delay} seconds..."
                        )
                        await asyncio.sleep(self._retry_delay)
                    else:
                        return {"trace_id": trace_id, "json": response.text}

        raise RuntimeError(f"Max retries exceeded for URL: {url}")

    async def get_metrics(self, trace_ids: List[str]):
        urls = []
        for trace_id in trace_ids:
            logger.debug(f"Trace-ID in URL: {trace_id}")
            urls.append((trace_id, f"{self._host}:{self._port}/api/v2/trace/{trace_id}"))

        sem = asyncio.Semaphore(self._concurrent_requests)
        tasks = [self.fetch(sem, url[0], url[1]) for url in urls]
        responses = await asyncio.gather(*tasks)

        return responses


def collect_traces_from_zipkin(
    zipkin_host: str, zipkin_port: int, trace_id_map: Dict[str, str], concurrent_requests: Optional[int] = 1
) -> Dict[str, str]:
    zipkin_client = AsyncZipkinClient(zipkin_host, zipkin_port, concurrent_requests)

    # Take the Dictionary of filenames -> trace_ids and build just a list of trace_ids to send to Zipkin
    trace_ids = []
    for filename in trace_id_map.keys():
        trace_ids.append(trace_id_map[filename])

    traces = asyncio.run(zipkin_client.get_metrics(trace_ids=trace_ids))
    return traces


def write_results_to_output_directory(
    output_directory: str,
    trace_responses: List[Dict[str, str]],
) -> None:
    logger.info(f"Writing {len(trace_responses)} to output_directory: {output_directory}")

    # Check if the output directory exists; if not, create it
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
        logger.info(f"Created directory: {output_directory}")

    # Define the subdirectory path
    zipkin_profiles_directory = os.path.join(output_directory, "zipkin_profiles")

    # Ensure the subdirectory exists
    if not os.path.exists(zipkin_profiles_directory):
        os.makedirs(zipkin_profiles_directory)
        logger.debug(f"Created subdirectory: {zipkin_profiles_directory}")

    # For each input file, create an output file with its profile data
    for trace in trace_responses:
        with open(f"{zipkin_profiles_directory}/{trace['trace_id']}.json", "w") as trace_file:
            trace_file.write(json.dumps(trace["json"]))

    # Write all of the combined profile data to a single file
    with open(f"{zipkin_profiles_directory}/combined.json", "w") as combined_file:
        combined_file.write(json.dumps(trace_responses))
