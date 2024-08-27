# Copyright (c) 2023-2024, NVIDIA CORPORATION.
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

import logging

from morpheus.llm import LLMContext
from morpheus.llm import LLMTaskHandler
from morpheus.messages import ControlMessage

logger = logging.getLogger(__name__)


class NIMTaskHandler(LLMTaskHandler):
    """
    Copies only one named field from the `LLMContext` into the ControlMessage. 

    Parameters
    ----------
    input_col_name : str, optional
        The name of the column in the `LLMContext` to store. Defaults to `response`.
        
    output_col_name : str, optional
        The name of the output column in which the response is stored. Defaults to `response`.
    """

    def __init__(self, input_col_name: str = "response", output_col_name: str = "response") -> None:
        super().__init__()

        self._output_columns = [input_col_name]
        self._response_col = output_col_name

    def get_input_names(self) -> list[str]:
        return self._output_columns

    # pylint: disable=invalid-overridden-method
    async def try_handle(self, context: LLMContext) -> list[ControlMessage]:

        input_dict = context.get_inputs()

        with context.message().payload().mutable_dataframe() as df:      
            df[self._response_col] = input_dict[self._output_columns[0]]

        return [context.message()]