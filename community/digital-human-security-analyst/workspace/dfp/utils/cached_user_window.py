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

import dataclasses
import os
import pickle
import typing
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import numpy as np
import pandas as pd


@dataclasses.dataclass
class CachedUserWindow:
    user_id: str
    cache_location: str
    timestamp_column: str = "timestamp"
    total_count: int = 0
    count: int = 0
    min_epoch: datetime = datetime(1970, 1, 1, tzinfo=timezone(timedelta(hours=0)))
    max_epoch: datetime = datetime(1970, 1, 1, tzinfo=timezone(timedelta(hours=0)))
    batch_count: int = 0
    pending_batch_count: int = 0
    last_train_count: int = 0
    last_train_epoch: datetime = None
    last_train_batch: int = 0

    _trained_rows: pd.Series = dataclasses.field(init=False, repr=False, default_factory=pd.DataFrame)
    _df: pd.DataFrame = dataclasses.field(init=False, repr=False, default_factory=pd.DataFrame)

    def append_dataframe(self, incoming_df: pd.DataFrame) -> bool:

        # Filter the incoming df by epochs later than the current max_epoch
        filtered_df = incoming_df[incoming_df[self.timestamp_column] > np.datetime64(self.max_epoch)]

        if (len(filtered_df) == 0):
            # We have nothing new to add. Double check that we fit within the window
            before_history = incoming_df[incoming_df[self.timestamp_column] < np.datetime64(self.min_epoch)]

            return len(before_history) == 0

        # Increment the batch count
        self.batch_count += 1
        self.pending_batch_count += 1

        # Set the filtered index
        filtered_df.index = range(self.total_count, self.total_count + len(filtered_df))

        # Save the row hash to make it easier to find later. Do this before the batch so it doesn't participate
        filtered_df["_row_hash"] = pd.util.hash_pandas_object(filtered_df, index=False)

        # Use batch id to distinguish groups in the same dataframe
        filtered_df["_batch_id"] = self.batch_count

        # Append just the new rows
        self._df = pd.concat([self._df, filtered_df])

        self.total_count += len(filtered_df)
        self.count = len(self._df)

        if (len(self._df) > 0):
            self.min_epoch = self._df[self.timestamp_column].min()
            self.max_epoch = self._df[self.timestamp_column].max()

        return True

    def flush(self):
        self.batch_count = 0
        self.count = 0
        self._df = pd.DataFrame()
        self._trained_rows = pd.Series()
        self.last_train_batch = 0
        self.last_train_count = 0
        self.last_train_epoch = None
        self.max_epoch = datetime(1970, 1, 1, tzinfo=timezone(timedelta(hours=0)))
        self.min_epoch = datetime(1970, 1, 1, tzinfo=timezone(timedelta(hours=0)))
        self.pending_batch_count = 0
        self.total_count = 0

    def get_spanning_df(self, max_history) -> pd.DataFrame:
        return self.get_train_df(max_history)

    def get_train_df(self, max_history) -> pd.DataFrame:

        new_df = self.trim_dataframe(self._df,
                                     max_history=max_history,
                                     last_batch=self.batch_count - self.pending_batch_count,
                                     timestamp_column=self.timestamp_column)

        self.last_train_count = self.total_count
        self.last_train_epoch = datetime.now()
        self.last_train_batch = self.batch_count
        self.pending_batch_count = 0

        self._df = new_df

        if (len(self._df) > 0):
            self.min_epoch = self._df[self.timestamp_column].min()
            self.max_epoch = self._df[self.timestamp_column].max()

        return new_df

    def save(self):
        if (not self.cache_location):
            raise RuntimeError("No cache location set")

        # Make sure the directories exist
        os.makedirs(os.path.dirname(self.cache_location), exist_ok=True)

        with open(self.cache_location, "wb") as f:
            pickle.dump(self, f)

    @staticmethod
    def trim_dataframe(df: pd.DataFrame,
                       max_history: typing.Union[int, str],
                       last_batch: int,
                       timestamp_column: str = "timestamp") -> pd.DataFrame:
        if (max_history is None):
            return df

        # Want to ensure we always see data once. So any new data is preserved
        new_batches = df[df["_batch_id"] > last_batch]

        # See if max history is an int
        if (isinstance(max_history, int)):
            return df.tail(max(max_history, len(new_batches)))

        # If its a string, then its a duration
        if (isinstance(max_history, str)):
            # Get the latest timestamp
            latest = df[timestamp_column].max()

            time_delta = pd.Timedelta(max_history)

            # Calc the earliest
            earliest = min(latest - time_delta, new_batches[timestamp_column].min())

            return df[df[timestamp_column] >= earliest]

        raise RuntimeError("Unsupported max_history")

    @staticmethod
    def load(cache_location: str) -> "CachedUserWindow":
        if (cache_location is None):
            raise RuntimeError("No cache location set")

        with open(cache_location, "rb") as f:
            return pickle.load(f)
