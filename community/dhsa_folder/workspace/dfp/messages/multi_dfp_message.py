# Copyright (c) 2021-2024, NVIDIA CORPORATION.
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
import logging
import typing

import pandas as pd

from morpheus.messages.message_meta import MessageMeta
from morpheus.messages.multi_message import MultiMessage

logger = logging.getLogger(__name__)


@dataclasses.dataclass(init=False)
class DFPMessageMeta(MessageMeta, cpp_class=None):
    """
    This class extends MessageMeta to also hold userid corresponding to batched metadata.

    Parameters
    ----------
    df : pandas.DataFrame
        Input rows in dataframe.
    user_id : str
        User id.

    """
    user_id: str

    def __init__(self, df: pd.DataFrame, user_id: str) -> None:
        super().__init__(df)
        self.user_id = user_id

    def get_df(self):
        return self.df

    def set_df(self, df):
        self._df = df


@dataclasses.dataclass
class MultiDFPMessage(MultiMessage):

    def __init__(self, *, meta: MessageMeta, mess_offset: int = 0, mess_count: int = -1):

        if (not isinstance(meta, DFPMessageMeta)):
            raise ValueError(f"`meta` must be an instance of `DFPMessageMeta` when creating {self.__class__.__name__}")

        super().__init__(meta=meta, mess_offset=mess_offset, mess_count=mess_count)

    @property
    def user_id(self):
        return typing.cast(DFPMessageMeta, self.meta).user_id

    def get_meta_dataframe(self):
        return typing.cast(DFPMessageMeta, self.meta).get_df()

    def set_meta_dataframe(self, columns: typing.Union[None, str, typing.List[str]], value):

        df = typing.cast(DFPMessageMeta, self.meta).get_df()

        if (columns is None):
            # Set all columns
            df[list(value.columns)] = value
        else:
            # If its a single column or list of columns, this is the same
            df[columns] = value

        typing.cast(DFPMessageMeta, self.meta).set_df(df)

    def copy_ranges(self, ranges: typing.List[typing.Tuple[int, int]]):

        sliced_rows = self.copy_meta_ranges(ranges)

        return self.from_message(self,
                                 meta=DFPMessageMeta(sliced_rows, self.user_id),
                                 mess_offset=0,
                                 mess_count=len(sliced_rows))
