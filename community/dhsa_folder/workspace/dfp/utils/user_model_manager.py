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

import logging
import typing

import pandas as pd
from tqdm import tqdm

from morpheus.config import Config
from morpheus.models.dfencoder import AutoEncoder
from morpheus.utils.seed import manual_seed

logger = logging.getLogger(f"morpheus.{__name__}")


class DFPDataLoader:

    def __init__(self, batch_frames, filter_func, max_rows_per_batch=50000):
        self._aggregate_cache = None
        self._batch_frames = batch_frames
        self._current_index = 0
        self._filter_func = filter_func
        self._frame_count = len(self._batch_frames)
        self._max_rows_per_batch = max_rows_per_batch
        self._sample_frame = None

    def reset(self):
        self._current_index = 0

    def get_sample_frame(self):
        return self._sample_frame

    def get_next_frame(self):
        if (self._current_index == self._frame_count):
            return None

        if (self._aggregate_cache is not None):
            self._current_index = self._frame_count
            return self._aggregate_cache

        total_frames = 0
        aggregate_rows = 0
        aggregate_frame = pd.DataFrame()
        while (True):
            df_frame = self._filter_func(pd.read_pickle(self._batch_frames[self._current_index]))

            # Save the first row and the last row from every batch. Helps with statistics down the line
            if (self._sample_frame is None):
                self._sample_frame = df_frame.head(1)

            self._sample_frame = self._sample_frame.append(df_frame.tail(1))

            rows = df_frame.shape[0]

            if (aggregate_rows + rows < self._max_rows_per_batch):
                aggregate_frame = pd.concat([aggregate_frame, df_frame])
                aggregate_rows += rows
                total_frames += 1

                self._current_index = min((self._current_index + 1), self._frame_count)
            else:  # Adding another frame would exceed our memory limit, return
                if (total_frames == self._frame_count):
                    logger.debug("Caching full training set.")
                    self._aggregate_cache = aggregate_frame

                return aggregate_frame

            if (self._current_index != self._frame_count):
                continue

            # Epoch rolled, return what we have
            if (total_frames == self._frame_count):
                logger.debug("Caching full training set.")
                self._aggregate_cache = aggregate_frame

            return aggregate_frame


class InsufficientDataError(RuntimeError):
    pass


class UserModelManager:

    def __init__(self,
                 config: Config,
                 user_id: str,
                 save_model: bool,
                 epochs: int,
                 min_history: int,
                 max_history: int,
                 seed: int = None,
                 batch_files: typing.List = None,
                 model_class=AutoEncoder) -> None:
        super().__init__()

        if (batch_files is None):
            batch_files = []

        self._user_id = user_id
        self._history: pd.DataFrame = None
        self._min_history: int = min_history
        self._max_history: int = max_history
        self._seed: int = seed
        self._feature_columns = config.ae.feature_columns
        self._epochs = epochs
        self._save_model = save_model
        self._model_class = model_class
        self._batch_files = batch_files

        self._model: AutoEncoder = None

        self._last_train_count = 0

    @property
    def model(self):
        return self._model

    def train_from_batch(self, filter_func=lambda df: df):
        if (not self._batch_files):
            return None

        # If the seed is set, enforce that here
        if (self._seed is not None):
            manual_seed(self._seed)

        model = self._model_class(
            encoder_layers=[512, 500],  # layers of the encoding part
            decoder_layers=[512],  # layers of the decoding part
            activation='relu',  # activation function
            swap_p=0.2,  # noise parameter
            lr=0.001,  # learning rate
            lr_decay=.99,  # learning decay
            batch_size=512,
            # logger='ipynb',
            verbose=False,
            optimizer='sgd',  # SGD optimizer is selected(Stochastic gradient descent)
            scaler='standard',  # feature scaling method
            min_cats=1,  # cut off for minority categories
            progress_bar=False,
            device="cuda")

        # Loop each epoch
        logger.debug("Training AE model for user: '%s'...", self._user_id)
        loader = DFPDataLoader(self._batch_files, filter_func)
        try:
            for _ in tqdm(range(self._epochs), desc="Training"):
                batches = 0
                while (True):
                    df_batch = loader.get_next_frame()
                    if (df_batch is None):
                        break

                    if (batches == 0 and (df_batch.shape[0] < self._min_history)):
                        raise InsufficientDataError("Insuffient training data.")

                    if (df_batch.shape[0] < 10):  # If we've already trained on some data, make sure we can tts this.
                        break

                    model.fit(df_batch)
                    batches += 1

                loader.reset()

            if (self._save_model):
                self._model = model

            logger.debug("Training AE model for user: '%s'... Complete.", self._user_id)

            return model, loader.get_sample_frame()
        except InsufficientDataError:
            logger.debug("Training AE model for user: '%s... Skipped", self._user_id)
            return None, None
        except Exception:
            logger.exception("Error during training for user: %s", self._user_id, exc_info=True)
            return None, None

    def train(self, df: pd.DataFrame) -> AutoEncoder:

        # Determine how much history to save
        if (self._history is not None):
            if (self._max_history > 0):
                to_drop = max(len(df) + len(self._history) - self._max_history, 0)
            else:
                to_drop = 0

            history = self._history.iloc[to_drop:, :]

            combined_df = pd.concat([history, df])
        else:
            combined_df = df

        # Save the history for next time
        if (self._max_history > 0):
            self._history = combined_df.iloc[max(0, len(combined_df) - self._max_history):, :]
        else:
            self._history = combined_df

        # Ensure we have enough data
        if (len(combined_df) < self._last_train_count + self._min_history):
            return None

        # If the seed is set, enforce that here
        if (self._seed is not None):
            manual_seed(self._seed)

        model = self._model_class(
            encoder_layers=[512, 500],  # layers of the encoding part
            decoder_layers=[512],  # layers of the decoding part
            activation='relu',  # activation function
            swap_p=0.2,  # noise parameter
            lr=0.001,  # learning rate
            lr_decay=.99,  # learning decay
            batch_size=4096,
            # logger='ipynb',
            verbose=False,
            optimizer='sgd',  # SGD optimizer is selected(Stochastic gradient descent)
            scaler='standard',  # feature scaling method
            min_cats=1,  # cut off for minority categories
            progress_bar=False,
            device="cuda")

        final_df = combined_df[combined_df.columns.intersection(self._feature_columns)]

        logger.debug("Training AE model for user: '%s'...", self._user_id)
        model.fit(final_df, epochs=self._epochs)
        logger.debug("Training AE model for user: '%s'... Complete.", self._user_id)

        # Save the train count to prevent retrains
        self._last_train_count = len(final_df)

        if (self._save_model):
            self._model = model

        return model
