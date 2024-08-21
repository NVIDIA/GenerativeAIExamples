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

import hashlib
import logging
import threading
import typing
from contextlib import contextmanager
from datetime import datetime

import mlflow
from mlflow.entities.model_registry import RegisteredModel
from mlflow.exceptions import MlflowException
from mlflow.store.entities.paged_list import PagedList
from mlflow.tracking.client import MlflowClient

from morpheus.models.dfencoder import AutoEncoder

from .logging_timer import log_time

logger = logging.getLogger(f"morpheus.{__name__}")


@contextmanager
def timed_acquire(lock: threading.Lock, timeout: float):
    result = lock.acquire(timeout=timeout)

    if (not result):
        # Did not get the lock. Raise
        raise TimeoutError()

    # Got the lock
    try:
        yield

    finally:
        lock.release()


def user_to_model_name(user_id: str, model_name_formatter: str):

    kwargs = {
        "user_id": user_id,
        "user_md5": hashlib.md5(user_id.encode('utf-8')).hexdigest(),
    }

    return model_name_formatter.format(**kwargs)


class ModelCache:

    def __init__(self, reg_model_name: str, reg_model_version: str, model_uri: str) -> None:

        self._reg_model_name = reg_model_name
        self._reg_model_version = reg_model_version
        self._model_uri = model_uri

        self._last_checked: datetime = datetime.now()
        self._last_used: datetime = self._last_checked

        self._lock = threading.Lock()
        self._model: AutoEncoder = None

    @property
    def reg_model_name(self):
        return self._reg_model_name

    @property
    def reg_model_version(self):
        return self._reg_model_version

    @property
    def model_uri(self):
        return self._model_uri

    @property
    def last_used(self):
        return self._last_used

    @property
    def last_checked(self):
        return self._last_checked

    def load_model(self, _) -> AutoEncoder:

        now = datetime.now()

        # Ensure multiple people do not try to load at the same time
        with self._lock:

            if (self._model is None):

                # Cache miss. Release the lock while we check
                try:
                    with log_time(
                            logger.debug,
                            f"Downloaded model '{self.reg_model_name}:{self.reg_model_version}' in {{duration}} ms"):
                        self._model = mlflow.pytorch.load_model(model_uri=self._model_uri)

                except MlflowException:
                    logger.error("Error downloading model for URI: %s", self._model_uri, exc_info=True)
                    raise

            # Update the last time this was used
            self._last_used = now

            return self._model


class UserModelMap:

    def __init__(self, manager: "ModelManager", user_id: str, fallback_user_ids: typing.List[str]):

        self._manager = manager
        self._user_id = user_id
        self._fallback_user_ids = fallback_user_ids
        self._reg_model_name = manager.user_id_to_model(user_id)
        self._last_checked = None

        self._lock = threading.RLock()
        self._child_user_model_cache: UserModelMap = None

    def load_model_cache(self, client, timeout: float = 1.0) -> ModelCache:

        now = datetime.now()

        # Lock to prevent additional access
        try:
            with timed_acquire(self._lock, timeout=timeout):

                # Check if we have checked before or if we need to check again
                if (self._last_checked is None or (now - self._last_checked).seconds < self._manager.cache_timeout_sec):

                    # Save the last checked time
                    self._last_checked = now

                    # Try to load from the manager
                    model_cache = self._manager.load_model_cache(client=client,
                                                                 reg_model_name=self._reg_model_name,
                                                                 timeout=timeout)

                    # If we have a hit, there is nothing else to do
                    if (model_cache is None and len(self._fallback_user_ids) > 0):
                        # Our model does not exist, use fallback
                        self._child_user_model_cache = self._manager.load_user_model_cache(
                            self._fallback_user_ids[0], timeout, fallback_user_ids=self._fallback_user_ids[1:])
                    else:
                        return model_cache

                # See if we have a child cache and use that
                if (self._child_user_model_cache is not None):
                    return self._child_user_model_cache.load_model_cache(client=client, timeout=timeout)

                # Otherwise load the model
                model_cache = self._manager.load_model_cache(client=client,
                                                             reg_model_name=self._reg_model_name,
                                                             timeout=timeout)

                if (model_cache is None):
                    raise RuntimeError(f"Model was found but now no longer exists. Model: {self._reg_model_name}")

                return model_cache
        except TimeoutError as e:
            logger.error("Deadlock detected while loading model cache. Please report this to the developers.")
            raise RuntimeError("Deadlock detected while loading model cache") from e


class ModelManager:

    def __init__(self, model_name_formatter: str) -> None:
        self._model_name_formatter = model_name_formatter

        self._user_model_cache: typing.Dict[str, UserModelMap] = {}

        self._model_cache: typing.Dict[str, ModelCache] = {}
        self._model_cache_size_max = 100

        self._cache_timeout_sec = 600

        self._user_model_cache_lock = threading.RLock()
        self._model_cache_lock = threading.RLock()

        self._existing_models: typing.Set[str] = set()
        self._existing_models_updated = datetime(1970, 1, 1)

        # Force an update of the existing models
        self._model_exists("")

    @property
    def cache_timeout_sec(self):
        return self._cache_timeout_sec

    def _model_exists(self, reg_model_name: str, timeout: float = 1.0) -> bool:

        now = datetime.now()

        # See if the list of models needs to be updated
        if ((now - self._existing_models_updated).seconds > self._cache_timeout_sec):

            try:
                with timed_acquire(self._model_cache_lock, timeout=timeout):

                    logger.debug("Updating list of available models...")
                    client = MlflowClient()

                    results: PagedList[RegisteredModel] = PagedList([], token=None)

                    # clear the set to hanfle the case where a model has been removed
                    self._existing_models.clear()

                    # Loop over the registered models with the pagination
                    while ((results := client.search_registered_models(max_results=1000, page_token=results.token))
                           is not None):

                        self._existing_models.update(model.name for model in results)

                        if (results.token is None or len(results.token) == 0):
                            break

                    logger.debug("Updating list of available models... Done.")

                    # Save the update time
                    self._existing_models_updated = now

            except TimeoutError as e:
                logger.error("Deadlock detected checking for new models. Please report this to the developers.")
                raise RuntimeError("Deadlock detected checking for new models") from e
            except Exception:
                logger.exception("Exception occurred when querying the list of available models", exc_info=True)
                raise

        return reg_model_name in self._existing_models

    def user_id_to_model(self, user_id: str):
        return user_to_model_name(user_id=user_id, model_name_formatter=self._model_name_formatter)

    def load_user_model(self,
                        client,
                        user_id: str,
                        fallback_user_ids: typing.List[str],
                        timeout: float = 1.0) -> ModelCache:

        if fallback_user_ids is None:
            fallback_user_ids = []

        # First get the UserModel
        user_model_cache = self.load_user_model_cache(user_id=user_id,
                                                      timeout=timeout,
                                                      fallback_user_ids=fallback_user_ids)

        return user_model_cache.load_model_cache(client=client, timeout=timeout)

    def load_model_cache(self, client: MlflowClient, reg_model_name: str, timeout: float = 1.0) -> ModelCache:

        now = datetime.now()

        try:
            with timed_acquire(self._model_cache_lock, timeout=timeout):

                model_cache = self._model_cache.get(reg_model_name, None)

                # Make sure it hasnt been too long since we checked
                if (model_cache is not None and (now - model_cache.last_checked).seconds < self._cache_timeout_sec):

                    return model_cache

                # Cache miss. Try to check for a model
                try:
                    if (not self._model_exists(reg_model_name, timeout)):
                        # Break early
                        return None

                    latest_versions = client.get_latest_versions(reg_model_name)

                    if (len(latest_versions) == 0):
                        # Databricks doesn't like the `get_latest_versions` method for some reason. Before failing, try
                        # to just get the model and then use latest versions
                        reg_model_obj = client.get_registered_model(reg_model_name)

                        latest_versions = None if reg_model_obj is None else reg_model_obj.latest_versions

                        if (len(latest_versions) == 0):
                            logger.warning(
                                ("Registered model with no versions detected. Consider deleting this registered model."
                                 "Using fallback model. Model: %s, "),
                                reg_model_name)
                            return None

                    # Default to the first returned one
                    latest_model_version = latest_versions[0]

                    if (len(latest_versions) > 1):
                        logger.warning(("Multiple models in different stages detected. "
                                        "Defaulting to first returned. Model: %s, Version: %s, Stage: %s"),
                                       reg_model_name,
                                       latest_model_version.version,
                                       latest_model_version.current_stage)

                    model_cache = ModelCache(reg_model_name=reg_model_name,
                                             reg_model_version=latest_model_version.version,
                                             model_uri=latest_model_version.source)

                except MlflowException as e:
                    if e.error_code == 'RESOURCE_DOES_NOT_EXIST':
                        # No user found
                        return None

                    raise

                # Save the cache
                self._model_cache[reg_model_name] = model_cache

                # Check if we need to push out a cache entry
                if (len(self._model_cache) > self._model_cache_size_max):
                    time_sorted = sorted(list(self._model_cache.items()), key=lambda x: x[1].last_used)
                    to_delete = time_sorted[0][0]
                    self._model_cache.pop(to_delete)

                return model_cache

        except TimeoutError as e:
            logger.error("Deadlock when trying to acquire model cache lock")
            raise RuntimeError("Deadlock when trying to acquire model cache lock") from e

    def load_user_model_cache(self, user_id: str, timeout: float, fallback_user_ids: typing.List[str]) -> UserModelMap:

        try:
            with timed_acquire(self._user_model_cache_lock, timeout=timeout):

                if (user_id not in self._user_model_cache):
                    self._user_model_cache[user_id] = UserModelMap(manager=self,
                                                                   user_id=user_id,
                                                                   fallback_user_ids=fallback_user_ids)

                return self._user_model_cache[user_id]
        except TimeoutError as e:
            logger.error("Deadlock when trying to acquire user model cache lock", exc_info=True)
            raise RuntimeError("Deadlock when trying to acquire user model cache lock") from e
