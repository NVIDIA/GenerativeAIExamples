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
"""Groups incomming messages into a rolling time window."""

import logging
import os
import typing
from contextlib import contextmanager

import mrc
import pandas as pd
from mrc.core import operators as ops

from morpheus.config import Config
from morpheus.pipeline.single_port_stage import SinglePortStage
from morpheus.pipeline.stage_schema import StageSchema

from ..messages.multi_dfp_message import DFPMessageMeta
from ..messages.multi_dfp_message import MultiDFPMessage
from ..utils.cached_user_window import CachedUserWindow
from ..utils.logging_timer import log_time

logger = logging.getLogger(f"morpheus.{__name__}")


class DFPRollingWindowStage(SinglePortStage):
    """
    This stage groups incomming messages into a rolling time window, emitting them only when the history requirements
    are met specified by the `min_history`, `min_increment` and `max_history` parameters.

    Incoming data is cached to disk (`cache_dir`) to reduce memory ussage. This computes a row hash for the first and
    last rows of the incoming `DataFrame` as such all data contained must be hashable, any non-hashable values such as
    `lists` should be dropped or converted into hashable types in the `DFPFileToDataFrameStage`.

    Parameters
    ----------
    c : `morpheus.config.Config`
        Pipeline configuration instance.
    min_history : int
        Exclude users with less than `min_history` records, setting this to `1` effectively disables this feature.
    min_increment : int
        Exclude incoming batches for users where less than `min_increment` new records have been added since the last
        batch, setting this to `0` effectively disables this feature.
    max_history : int or str
        When not `None`, include up to `max_history` records. When `max_history` is an int, then the last `max_history`
        records will be included. When `max_history` is a `str` it is assumed to represent a duration parsable by
        [`pandas.Timedelta`](https://pandas.pydata.org/docs/reference/api/pandas.Timedelta.html) and only those records
        within the window of [latest timestamp - `max_history`, latest timestamp] will be included.
    cache_dir : str
        Path to cache directory, cached items will be stored in a subdirectory under this directory named
        `rolling-user-data`. This directory, along with `cache_dir` will be created if it does not already exist.
    """

    def __init__(self,
                 c: Config,
                 min_history: int,
                 min_increment: int,
                 max_history: typing.Union[int, str],
                 cache_dir: str = "./.cache/dfp"):
        super().__init__(c)

        self._min_history = min_history
        self._min_increment = min_increment
        self._max_history = max_history
        self._cache_dir = os.path.join(cache_dir, "rolling-user-data")

        # Map of user ids to total number of messages. Keeps indexes monotonic and increasing per user
        self._user_cache_map: typing.Dict[str, CachedUserWindow] = {}

    @property
    def name(self) -> str:
        """Stage name."""
        return "dfp-rolling-window"

    def supports_cpp_node(self):
        """Whether this stage supports a C++ node."""
        return False

    def accepted_types(self) -> typing.Tuple:
        """Input types accepted by this stage."""
        return (DFPMessageMeta, )

    def compute_schema(self, schema: StageSchema):
        schema.output_schema.set_type(MultiDFPMessage)

    @contextmanager
    def _get_user_cache(self, user_id: str) -> typing.Generator[CachedUserWindow, None, None]:

        # Determine cache location
        cache_location = os.path.join(self._cache_dir, f"{user_id}.pkl")

        user_cache = None

        user_cache = self._user_cache_map.get(user_id, None)

        if (user_cache is None):
            user_cache = CachedUserWindow(user_id=user_id,
                                          cache_location=cache_location,
                                          timestamp_column=self._config.ae.timestamp_column_name)

            self._user_cache_map[user_id] = user_cache

        yield user_cache

        # # When it returns, make sure to save
        # user_cache.save()

    def _build_window(self, message: DFPMessageMeta) -> MultiDFPMessage:

        user_id = message.user_id

        with self._get_user_cache(user_id) as user_cache:

            incoming_df = message.get_df()
            # existing_df = user_cache.df

            if (not user_cache.append_dataframe(incoming_df=incoming_df)):
                # Then our incoming dataframe wasnt even covered by the window. Generate warning
                logger.warning(("Incoming data preceeded existing history. "
                                "Consider deleting the rolling window cache and restarting."))
                return None

            # Exit early if we dont have enough data
            if (user_cache.count < self._min_history):
                return None

            # We have enough data, but has enough time since the last training taken place?
            if (user_cache.total_count - user_cache.last_train_count < self._min_increment):
                return None

            # Save the last train statistics
            train_df = user_cache.get_train_df(max_history=self._max_history)

            # Hash the incoming data rows to find a match
            incoming_hash = pd.util.hash_pandas_object(incoming_df.iloc[[0, -1]], index=False)

            # Find the index of the first and last row
            match = train_df[train_df["_row_hash"] == incoming_hash.iloc[0]]

            if (len(match) == 0):
                raise RuntimeError(f"Invalid rolling window for user {user_id}")

            first_row_idx = match.index[0].item()
            last_row_idx = train_df[train_df["_row_hash"] == incoming_hash.iloc[-1]].index[-1].item()

            found_count = (last_row_idx - first_row_idx) + 1

            if (found_count != len(incoming_df)):
                raise RuntimeError(("Overlapping rolling history detected. "
                                    "Rolling history can only be used with non-overlapping batches"))

            # Otherwise return a new message
            return MultiDFPMessage(meta=DFPMessageMeta(df=train_df, user_id=user_id),
                                   mess_offset=0,
                                   mess_count=len(train_df))

    def on_data(self, message: DFPMessageMeta) -> MultiDFPMessage:
        """
        Emits a new message containing the rolling window for the user if and only if the history requirments are met,
        returns `None` otherwise.
        """
        with log_time(logger.debug) as log_info:

            result = self._build_window(message)

            if (result is not None):

                log_info.set_log(
                    ("Rolling window complete for %s in {duration:0.2f} ms. "
                     "Input: %s rows from %s to %s. Output: %s rows from %s to %s"),
                    message.user_id,
                    len(message.df),
                    message.df[self._config.ae.timestamp_column_name].min(),
                    message.df[self._config.ae.timestamp_column_name].max(),
                    result.mess_count,
                    result.get_meta(self._config.ae.timestamp_column_name).min(),
                    result.get_meta(self._config.ae.timestamp_column_name).max(),
                )
            else:
                # Dont print anything
                log_info.disable()

            return result

    def _build_single(self, builder: mrc.Builder, input_node: mrc.SegmentObject) -> mrc.SegmentObject:
        node = builder.make_node(self.unique_name, ops.map(self.on_data), ops.filter(lambda x: x is not None))
        builder.make_edge(input_node, node)

        return node
