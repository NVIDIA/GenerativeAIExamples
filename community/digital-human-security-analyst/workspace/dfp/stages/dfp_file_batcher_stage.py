# Copyright (c) 2022-2024, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Groups incoming DataFrame objects into batches based on a time period."""

import logging
import typing
import warnings
from collections import namedtuple
from datetime import datetime
from datetime import timezone

import fsspec
import mrc
import pandas as pd
from mrc.core import operators as ops

from morpheus.config import Config
from morpheus.pipeline.single_port_stage import SinglePortStage
from morpheus.pipeline.stage_schema import StageSchema

logger = logging.getLogger(f"morpheus.{__name__}")

TimestampFileObj = namedtuple("TimestampFileObj", ["timestamp", "file_object"])


class DFPFileBatcherStage(SinglePortStage):
    """
    This stage groups data in the incoming `DataFrame` in batches of a time period (per day default), and optionally
    filtering incoming data to a specific time window.  This stage can potentially improve performance by combining
    multiple small files into a single batch.  This stage assumes that the date of the logs can be easily inferred such
    as encoding the creation time in the file name (for example, `AUTH_LOG-2022-08-21T22.05.23Z.json`), or using the
    modification time as reported by the file system. The actual method for extracting the date is encoded in a
    user-supplied `date_conversion_func` function.

    Note: Setting both `sampling_rate_s` and `sampling` will result in an error.

    Parameters
    ----------
    config : `morpheus.config.Config`
        Pipeline configuration instance.
    date_conversion_func : callable
        A function that takes a file object and returns a `datetime` object representing the date of the file.
    period : str, optional
        Time period to group data by, value must be one of pandas' offset strings
        https://pandas.pydata.org/docs/user_guide/timeseries.html#timeseries-offset-aliases
    sampling_rate_s: int, optional
        Deprecated consider using `sampling` instead.
        When defined a subset of the incoming data files will be sampled, taking the first row for each
        `sampling_rate_s` seconds.
    start_time : datetime, optional
        When not None incoming data files will be filtered, excluding any files created prior to `start_time`
    end_time : datetime, optional
        When not None incoming data files will be filtered, excluding any files created after `end_time`
    sampling : str, float, int, optional
        When non-None a subset of the incoming data files will be sampled.
        When a string, the value is interpreted as a pandas frequency. The first row for each frequency will be taken.
        When the value is between [0,1), a percentage of rows will be taken.
        When the value is greater than 1, the value is interpreted as the random count of rows to take.
    """

    def __init__(self,
                 config: Config,
                 date_conversion_func: typing.Callable[[fsspec.core.OpenFile], datetime],
                 period: str = "D",
                 sampling_rate_s: typing.Optional[int] = None,
                 start_time: datetime = None,
                 end_time: datetime = None,
                 sampling: typing.Union[str, float, int, None] = None):
        super().__init__(config)

        self._date_conversion_func = date_conversion_func
        self._period = period
        self._start_time = start_time
        self._end_time = end_time

        if (sampling_rate_s is not None and sampling_rate_s > 0):
            assert sampling is None, "Cannot set both sampling and sampling_rate_s at the same time"

            # Show the deprecation message
            warnings.warn(("The `sampling_rate_s` argument has been deprecated. "
                           "Please use `sampling={sampling_rate_s}S` instead"),
                          DeprecationWarning)

            sampling = f"{sampling_rate_s}S"

        self._sampling = sampling

    @property
    def name(self) -> str:
        """Returns the name of the stage."""
        return "dfp-file-batcher"

    def supports_cpp_node(self) -> bool:
        """Returns whether or not this stage supports a C++ node."""
        return False

    def accepted_types(self) -> typing.Tuple:
        """Accepted incoming types for this stage"""
        return (fsspec.core.OpenFiles, )

    def compute_schema(self, schema: StageSchema):
        schema.output_schema.set_type(typing.Tuple[fsspec.core.OpenFiles, int])

    def on_data(self, file_objects: fsspec.core.OpenFiles) -> typing.List[typing.Tuple[fsspec.core.OpenFiles, int]]:
        """
        Batches incoming data according to date, period and sampling, potentially filtering data based on file dates.
        """
        timestamps = []
        full_names = []
        file_objs = []

        # Determine the date of the file, and apply the window filter if we have one
        for file_object in file_objects:
            ts = self._date_conversion_func(file_object)

            # Exclude any files outside the time window
            if (ts.tzinfo is None):
                ts = ts.replace(tzinfo=timezone.utc)

            if ((self._start_time is not None and ts < self._start_time)
                    or (self._end_time is not None and ts > self._end_time)):
                continue

            timestamps.append(ts)
            full_names.append(file_object.full_name)
            file_objs.append(file_object)

        # Build the dataframe
        df = pd.DataFrame(index=pd.DatetimeIndex(timestamps), data={"filename": full_names, "objects": file_objs})

        # sort the incoming data by date
        df.sort_index(inplace=True)

        # If sampling was provided, perform that here
        if (self._sampling is not None):

            if (isinstance(self._sampling, str)):
                # We have a frequency for sampling. Resample by the frequency, taking the first
                df = df.resample(self._sampling).first().dropna()

            elif (self._sampling < 1.0):
                # Sample a fraction of the rows
                df = df.sample(frac=self._sampling).sort_index()

            else:
                # Sample a fixed amount
                df = df.sample(n=self._sampling).sort_index()

        # Early exit if no files were found
        if (len(df) == 0):
            return []

        if (self._period is None):
            # No period was set so group them all into one single batch
            return [(fsspec.core.OpenFiles(df["objects"].to_list(), mode=file_objects.mode, fs=file_objects.fs),
                     len(df))]

        # Now group the rows by the period
        resampled = df.resample(self._period)

        n_groups = len(resampled)

        output_batches = []

        for _, period_df in resampled:

            file_list = period_df["objects"].to_list()

            if (len(file_list) == 0):
                continue

            obj_list = fsspec.core.OpenFiles(file_list, mode=file_objects.mode, fs=file_objects.fs)

            output_batches.append((obj_list, n_groups))

        return output_batches

    def _build_single(self, builder: mrc.Builder, input_node: mrc.SegmentObject) -> mrc.SegmentObject:
        node = builder.make_node(self.unique_name, ops.map(self.on_data), ops.flatten())
        builder.make_edge(input_node, node)

        return node
