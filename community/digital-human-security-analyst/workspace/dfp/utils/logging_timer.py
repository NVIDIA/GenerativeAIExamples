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
import typing
import warnings
from contextlib import contextmanager


@dataclasses.dataclass
class LogTimeInfo():
    log_fn: typing.Callable
    msg: str
    args: typing.Tuple
    kwargs: typing.Dict
    disabled: bool = False

    def disable(self):
        self.disabled = True

    def set_log(self, msg: str, *args, **kwargs):
        self.msg = msg
        self.args = args
        self.kwargs = kwargs

    def _do_log_message(self, duration_ms: float):

        if (self.disabled):
            return

        if (self.msg is None):
            warnings.warn("Must set log msg before end of context! Skipping log")
            return

        # Call the log function
        self.log_fn(self.msg.format(**{"duration": duration_ms}), *self.args, **self.kwargs)


@contextmanager
def log_time(log_fn, *args, msg: str = None, **kwargs):

    # Create an info object to allow users to set the message in the context block
    info = LogTimeInfo(log_fn=log_fn, msg=msg, args=args, kwargs=kwargs)

    import time

    start_time = time.time()

    yield info

    duration = (time.time() - start_time) * 1000.0

    info._do_log_message(duration)
