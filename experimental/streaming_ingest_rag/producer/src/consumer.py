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

import json
import argparse

from abc import ABC, abstractmethod

from confluent_kafka.admin import AdminClient
from confluent_kafka import Consumer


class Subscriber(ABC):

    def __init__(
        self, 
        bootstrap_servers='kafka:19092', 
        group_id="morphues",
        auto_offset_reset='smallest',
        min_commit_count=5):

        self._conf = {
            'bootstrap.servers': bootstrap_servers,
            'group.id': group_id,
            'auto.offset.reset': auto_offset_reset}

        self._consumer = Consumer(self._conf)
        self._min_commit_count = min_commit_count


    def subscribe(self, topic, max_messages=None):

        try:
            self._consumer.subscribe([topic])

            msg_count = 0
            while(True):
                msg = self._consumer.poll(timeout=1.0)
                if msg is None: continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition event
                        sys.stderr.write('%% %s [%d] reached end at offset %d\n' %
                                        (msg.topic(), msg.partition(), msg.offset()))
                    elif msg.error():
                        raise KafkaException(msg.error())
                else:
                    self._msg_process(msg)
                    msg_count += 1
                    if msg_count % self._min_commit_count == 0:
                        self._consumer.commit(asynchronous=True)
                    
                    if (max_messages > 0) and (msg_count >= max_messages):
                        break

        finally:
            # Close down consumer to commit final offsets.
            self._consumer.close()

    def _msg_process(self, message):
        print(json.loads(message.value()))

def main(args):

    # initialize consumer
    bootstrap_servers = 'kafka:19092'
    group_id='morpheus'
    auto_offset_reset = 'smallest'

    subscriber = Subscriber(
        bootstrap_servers=args.bootstrap_servers, 
        group_id=args.group_id,
        auto_offset_reset=args.auto_offset_reset)

    # start consuming
    topic='work_queue'

    subscriber.subscribe(
        topic=args.topic, 
        max_messages=args.max_messages)
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    
    parser.add_argument("-f", "--group-id", type=str,
                        required=False, default="morpheus",
                        help="Specifies consumer groups subscriber will belong to. (Default value: morpheus)")
                        
    parser.add_argument("-b", "--bootstrap-servers", type=str,
                        required=False, default='kafka:19092',
                        help="Kafka broker host:port. (Default value: kafka:19092)")                        

    parser.add_argument("-t", "--topic", type=str,
                        required=False, default='work_queue',
                        help="Kafka topic consumer will subscribe to. (Default value: work_queue)")

    parser.add_argument("-m", "--max-messages", type=int,
                        required=False, default=0,
                        help="Maximum messages to read from kafka topic. (Default value: 10)")                        

    parser.add_argument("-a", "--auto-offset-reset", type=str,
                        required=False, default='smallest',
                        help="Specify auto.offset.reset parameter driving when to consume messages in a topic. (Default value: smallest)")     

    args = parser.parse_args()
    
    main(args)

