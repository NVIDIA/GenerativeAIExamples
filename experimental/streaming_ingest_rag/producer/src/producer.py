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

import time
import json
import argparse
import os

from abc import ABC, abstractmethod

import jsonlines

from confluent_kafka.admin import AdminClient
from confluent_kafka.admin import NewTopic
from confluent_kafka import Producer

N_KAFKA_TOPIC_PARTITIONS = os.environ['N_KAFKA_TOPIC_PARTITIONS']

class Publisher(ABC):

    def __init__(
        self, 
        bootstrap_servers='kafka:19092', 
        client_id='publisher'):

        self._conf = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': client_id}

        self._kafka_admin = AdminClient(self._conf)

    def _check_topic(self, topic):
        topics = self._kafka_admin.list_topics().topics
        if not topics.get(topic):
            return False
        return True

    def create_topic(self, topic):

        if not self._check_topic(topic):

            topic_list = [NewTopic(
                topic, 
                num_partitions=int(N_KAFKA_TOPIC_PARTITIONS),
                replication_factor=1)]

            self._kafka_admin.create_topics(topic_list)

        while(True):
            if not self._check_topic(topic):
                time.sleep(1.0)
                continue
            break

        print(f"Topic Created: {topic}")
        print(f"Available Topics: \n {self._kafka_admin.list_topics().topics}")

    def delete_topic(self, topic):

        self._kafka_admin.delete_topics([topic]) # DELETE
        
        while(True):
            if not self._check_topic(topic):
                time.sleep(1.0)
                continue
            break

        print(f"Topic Deleted: {topic}")
        print(f"Available Topics: \n {self._kafka_admin.list_topics().topics}")

    def publish_infinit(self, messages, topic, interval=1.0, infinit=False):

        producer = Producer(self._conf)

        while(True):
            for msg in messages:

                curr_time = time.time()

                producer.produce(
                    topic, 
                    json.dumps(msg), 
                    callback=Publisher.acked)

                poll = producer.poll(1)
                end_time = time.time()
                # messages sents every interval seconds
                time_delta = end_time - curr_time
                time.sleep(min(max(0, interval - time_delta), interval))

        producer.flush()

    def publish_batch(self, messages, topic, interval=0.01, n_messages=1000):

        producer = Producer(self._conf)
        ctr = 0
        while(True):
            for msg in messages:

                if ctr >= n_messages:
                    producer.flush()

                    return
                    
                curr_time = time.time()
                
                producer.produce(
                    topic, 
                    json.dumps(msg), 
                    callback=Publisher.acked)

                poll = producer.poll(1)
                end_time = time.time()
                # messages sents every interval seconds
                time_delta = end_time - curr_time
                time.sleep(min(max(0, interval - time_delta), interval))
                ctr += 1

    def publish_single(self, message, topic):

        producer = Producer(self._conf)

        producer.produce(
            topic, 
            json.dumps(message), 
            callback=Publisher.acked)    

        poll = producer.poll(0)
        producer.flush()        


    @staticmethod
    def acked(err, msg):
    
        if err is not None:
            print("Failed to deliver message: %s: %s" % (str(msg), str(err)))
            
        else:
            print("Message produced: %s" % (str(msg))) 

def load_jsonl(fpath):
    jsonl_list = []
    with jsonlines.open(fpath) as f:
        for line in f:
            jsonl_list.append(line)
    return jsonl_list


def main(args):

    # load work queue
    work_queue = load_jsonl(args.filepath)

    # initialize publisher
    publisher = Publisher(
        bootstrap_servers=args.bootstrap_servers, 
        client_id=args.client_id)

    # publish messages
    publisher.create_topic(args.topic)

    if not args.loop:
        publisher.publish_batch(
            messages=work_queue, 
            topic=args.topic, 
            interval=args.interval,
            n_messages=args.n_messages)
    
    else:
        publisher.publish_infinit(
            messages=work_queue, 
            topic=args.topic, 
            interval=args.interval)    

    # delete topic
    if args.delete_topic:
        publisher.delete_topic(args.topic)
    

if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    
    parser.add_argument("-f", "--filepath", type=str,
                        required=False, default="data/raw_sample.jsonl",
                        help="Path to work queue jsonl file. (Default value: data/test.jsonl)")
                        
    parser.add_argument("-b", "--bootstrap-servers", type=str,
                        required=False, default='kafka:19092',
                        help="Kafka broker host:port. (Default value: kafka:19092)")                        

    parser.add_argument("-t", "--topic", type=str,
                        required=False, default='work_queue',
                        help="Kafka topic used to publish work. (Default value: work_queue)")

    parser.add_argument("-n", "--n-messages", type=int,
                        required=False, default=1000,
                        help="Total messages to produce. (Default value: 1000)")      

    parser.add_argument("-i", "--interval", type=float,
                        required=False, default=0.001,
                        help="Inteval to publish messages. (Default value: 1.0)")        

    parser.add_argument("-l", "--loop", 
                        action='store_true', default=False,
                        help="Flag to continuously produce messages. (Default value: False)")                         

    parser.add_argument("-c", "--client-id", type=str,
                        required=False, default='publisher',
                        help="Client ID for the producer. (Default value: publisher)")     

    parser.add_argument("-d", "--delete-topic", 
                        action='store_true', default=False, 
                        help="Flag to delete topic after producing completes. (Default value: False)")

    args = parser.parse_args()
    
    main(args)
