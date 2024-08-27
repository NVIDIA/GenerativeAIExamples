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
import pickle
from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import mlflow
import pandas as pd

from morpheus.utils.logger import configure_logging

logger = logging.getLogger(f"morpheus.{__name__}")


@dataclass
class TimeFields:
    start_time: datetime
    end_time: datetime


class DFPArgParser:

    def __init__(self,
                 skip_user: str,
                 only_user: str,
                 start_time: str,
                 log_level: int,
                 cache_dir: str,
                 sample_rate_s: str,
                 duration: str,
                 source: str,
                 tracking_uri: str,
                 silence_monitors: bool,
                 mlflow_experiment_name_formatter: str,
                 mlflow_model_name_formatter: str,
                 train_users: str = None):

        self._skip_users = list(skip_user)
        self._only_users = list(only_user)
        self._start_time = start_time
        self._duration = duration
        self._log_level = log_level
        self._train_users = train_users
        self._cache_dir = cache_dir
        self._initialized = False
        self._tracking_uri = tracking_uri
        self._sample_rate_s = sample_rate_s
        self._source = source

        self._include_generic = None
        self._include_individual = None
        self._time_fields: TimeFields = None
        self._silence_monitors = silence_monitors

        self._model_name_formatter = mlflow_model_name_formatter
        self._experiment_name_formatter = mlflow_experiment_name_formatter

    @staticmethod
    def verify_init(func):
        """
        Decorator function that verifies DFPArgParser instance has been initialized.
        """

        def wrapper(self, *args, **kwargs):
            if not self._initialized:
                raise RuntimeError('Instance not initialized')
            return func(self, *args, **kwargs)

        return wrapper

    def _configure_logging(self):
        configure_logging(log_level=self._log_level)
        # To prevent unnecessary logs from the mlflow.tracking.fluent module, explicitly set the log level to WARN.
        logging.getLogger("mlflow").setLevel(logging.WARN)

    @property
    @verify_init
    def time_fields(self):
        return self._time_fields

    @property
    def silence_monitors(self):
        return self._silence_monitors

    @property
    @verify_init
    def include_generic(self):
        return self._include_generic

    @property
    def duration(self):
        return self._duration

    @property
    @verify_init
    def include_individual(self):
        return self._include_individual

    @property
    def sample_rate_s(self):
        return self._sample_rate_s

    @property
    def skip_users(self):
        return self._skip_users

    @property
    def only_users(self):
        return self._only_users

    @property
    def cache_dir(self):
        return self._cache_dir

    @property
    def source(self):
        return self._source

    @property
    def model_name_formatter(self):
        return self._model_name_formatter

    @property
    def experiment_name_formatter(self):
        return self._experiment_name_formatter

    def _set_include_generic(self):
        self._include_generic = self._train_users in ('all', 'generic')

    def _set_include_individual(self):
        self._include_individual = self._train_users != "generic"

    def _create_time_fields(self, duration) -> TimeFields:
        duration = timedelta(seconds=pd.Timedelta(duration).total_seconds())
        if self._start_time is None:
            end_time = datetime.now(tz=timezone.utc)
            self._start_time = end_time - duration
        else:
            if self._start_time.tzinfo is None:
                self._start_time = self._start_time.replace(tzinfo=timezone.utc)

            end_time = self._start_time + duration

        time_fields = TimeFields(self._start_time, end_time)

        return time_fields

    def _set_mlflow_tracking_uri(self):
        if self._tracking_uri is None:
            raise ValueError("tracking uri cannot be None.")
        # Initialize ML Flow
        mlflow.set_tracking_uri(self._tracking_uri)
        logger.info("Tracking URI: %s", mlflow.get_tracking_uri())

    def _set_time_fields(self):
        self._time_fields = self._create_time_fields(self._duration)

    def init(self):
        self._configure_logging()
        self._set_time_fields()
        self._set_include_generic()
        self._set_include_individual()
        self._set_mlflow_tracking_uri()
        self._initialized = True

        logger.info("Train generic_user: %s", self._include_generic)
        logger.info("Skipping users: %s", self._skip_users)
        logger.info("Start Time: %s", self._start_time)
        logger.info("Duration: %s", self._duration)
        logger.info("Cache Dir: %s", self._cache_dir)


def pyobj2str(pyobj, encoding):
    str_val = str(pickle.dumps(pyobj), encoding=encoding)
    return str_val
