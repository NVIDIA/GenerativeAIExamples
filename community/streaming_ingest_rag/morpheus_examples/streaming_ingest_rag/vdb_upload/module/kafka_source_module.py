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
from functools import partial
import time
import os
import typing
from enum import Enum
from io import StringIO

import confluent_kafka as ck
import mrc
import pandas as pd
from pydantic import ValidationError

import cudf

from morpheus.messages import MessageMeta
from morpheus.utils.module_utils import ModuleLoaderFactory
from vdb_upload.schemas.kafka_source_schema import KafkaSourceSchema
from morpheus.utils.module_utils import register_module

logger = logging.getLogger(__name__)

KafkaSourceLoaderFactory = ModuleLoaderFactory("kafka_source", "morpheus_examples_llm", KafkaSourceSchema)


class AutoOffsetReset(Enum):
    """The supported offset options in Kafka"""
    EARLIEST = "earliest"
    LATEST = "latest"
    NONE = "none"


@register_module("kafka_source", "morpheus_examples_llm")
def _kafka_source_pipe(builder: mrc.Builder):

    module_config = builder.get_current_module_config()

    # Validate the module configuration using the contract
    try:
        kafka_config = KafkaSourceSchema(**module_config)
    except ValidationError as e:
        error_messages = '; '.join([f"{error['loc'][0]}: {error['msg']}" for error in e.errors()])
        log_error_message = f"Invalid kafka configuration: {error_messages}"
        logger.error(log_error_message)
        raise ValueError(log_error_message)         

    _max_batch_size = kafka_config.max_batch_size
    bootstrap_servers = kafka_config.bootstrap_servers
    input_topic = kafka_config.input_topic
    group_id = kafka_config.group_id
    client_id = None #module_config.client_id
    poll_interval = kafka_config.poll_interval
    disable_commit = kafka_config.disable_commit
    disable_pre_filtering = kafka_config.disable_pre_filtering
    auto_offset_reset = AutoOffsetReset(kafka_config.auto_offset_reset)
    stop_after = kafka_config.stop_after
    async_commits = kafka_config.async_commits

    if (input_topic is None):
        input_topic = ["work_queue"]

    if isinstance(auto_offset_reset, AutoOffsetReset):
        auto_offset_reset = auto_offset_reset.value

    if (bootstrap_servers == "auto"):
        bootstrap_servers = auto_determine_bootstrap()

    _consumer_params = {
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'session.timeout.ms': "60000",
        "auto.offset.reset": auto_offset_reset
    }
    if client_id is not None:
        _consumer_params['client.id'] = client_id

    if isinstance(input_topic, str):
        input_topic = [input_topic]

    # Remove duplicate topics if there are any.
    topics = list(set(input_topic))

    # Flag to indicate whether or not we should stop
    stop_requested = False
    poll_interval = pd.Timedelta(poll_interval).total_seconds()
    started = False

    records_emitted = 0
    num_messages = 0

    def _process_batch(consumer, batch, records_emitted, num_messages):
        message_meta = None
        if len(batch):
            buffer = StringIO()

            for msg in batch:
                payload = msg.value()
                if payload is not None:
                    buffer.write(payload.decode("utf-8"))
                    buffer.write("\n")

            df = None
            try:
                buffer.seek(0)
                df = cudf.io.read_json(buffer, engine='cudf', lines=True, orient='records')
                df['summary'] = "summary"
                df['title'] = "title"
                df['link'] = "link"
            except Exception as e:
                logger.error("Error parsing payload into a dataframe : %s", e)
            finally:
                if (not disable_commit):
                    for msg in batch:
                        consumer.commit(message=msg, asynchronous=async_commits)

            if df is not None:
                num_records = len(df)
                message_meta = MessageMeta(df)
                records_emitted += num_records
                num_messages += 1

                if stop_after > 0 and records_emitted >= stop_after:
                    stop_requested = True

            batch.clear()

        return message_meta, records_emitted, num_messages  


    def _source_generator(records_emitted, num_messages):

        consumer = None
        try:
            consumer = ck.Consumer(_consumer_params)
            consumer.subscribe(topics)

            batch = []

            while not stop_requested:
                do_process_batch = False
                do_sleep = False

                msg = consumer.poll(timeout=1.0)
                if msg is None:
                    do_process_batch = True
                    do_sleep = True

                else:
                    msg_error = msg.error()
                    if msg_error is None:
                        batch.append(msg)
                        if len(batch) == _max_batch_size:
                            do_process_batch = True

                    elif msg_error == ck.KafkaError._PARTITION_EOF:
                        do_process_batch = True
                        do_sleep = True
                    else:
                        raise ck.KafkaException(msg_error)

                if do_process_batch:
                    message_meta, records_emitted, num_messages = _process_batch(
                        consumer, batch, records_emitted, num_messages)
                    if message_meta is not None:
                        yield message_meta

                if do_sleep and not stop_requested:
                    time.sleep(poll_interval)

            message_meta, records_emitted, num_messages = _process_batch(
                consumer, batch, records_emitted, num_messages)
            if message_meta is not None:
                yield message_meta
            
        finally:
            # Close the consumer and call on_completed
            if (consumer):
                consumer.close()        

    # add node to the graph
    source_generator = partial(_source_generator, records_emitted, num_messages)
    source = builder.make_source('kafka_source', source_generator)
    source.launch_options.pe_count = 1
    source.launch_options.engines_per_pe = os.cpu_count()

    # Register the output of the  module
    builder.register_module_output("output", source)      

