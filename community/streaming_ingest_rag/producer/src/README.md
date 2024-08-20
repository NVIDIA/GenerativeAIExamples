# Overview

Provides a sample data producer and consumer for the Streaming Embeddings RAG Workflow.

## Producer Usage

Output from help utility:

```bash
root@50c78a63ca48:/workspace/src# python3 producer.py --help
usage: producer.py [-h] [-f FILEPATH] [-b BOOTSTRAP_SERVERS] [-t TOPIC] [-i INTERVAL] [-c CLIENT_ID] [-d]

options:
  -h, --help            show this help message and exit
  -f FILEPATH, --filepath FILEPATH
                        Path to work queue jsonl file. (Default value: data/test.jsonl)
  -b BOOTSTRAP_SERVERS, --bootstrap-servers BOOTSTRAP_SERVERS
                        Kafka broker host:port. (Default value: kafka:19092)
  -t TOPIC, --topic TOPIC
                        Kafka topic used to publish work. (Default value: work_queue)
  -n N_MESSAGES, --n-messages N_MESSAGES
                        Total messages to produce. (Default value: 1000)
  -i INTERVAL, --interval INTERVAL
                        Inteval to publish messages. (Default value: 1.0)
  -l, --loop            Flag to continuously produce messages. (Default value: False)
  -c CLIENT_ID, --client-id CLIENT_ID
                        Client ID for the producer. (Default value: publisher)
  -d, --delete-topic    Flag to delete topic after producing completes. (Default value: False)
```

Example usage below:

```bash
python3 producer.py --filepath data/url_sample.jsonl \
    --bootstrap-servers kafka:19092 --topic scrape_queue \
    --n-messages 1000 --interval 0.1
```

## Consumer Usage

Output from help utility:

```bash
root@1e78121a14e0:/workspace/src# python3 consumer.py --help
usage: consumer.py [-h] [-f GROUP_ID] [-b BOOTSTRAP_SERVERS] [-t TOPIC] [-m MAX_MESSAGES] [-a AUTO_OFFSET_RESET]

options:
  -h, --help            show this help message and exit
  -f GROUP_ID, --group-id GROUP_ID
                        Specifies consumer groups subscriber will belong to. (Default value: morpheus)
  -b BOOTSTRAP_SERVERS, --bootstrap-servers BOOTSTRAP_SERVERS
                        Kafka broker host:port. (Default value: kafka:19092)
  -t TOPIC, --topic TOPIC
                        Kafka topic consumer will subscribe to. (Default value: work_queue)
  -m MAX_MESSAGES, --max-messages MAX_MESSAGES
                        Maximum messages to read from kafka topic. (Default value: 10)
  -a AUTO_OFFSET_RESET, --auto-offset-reset AUTO_OFFSET_RESET
                        Specify auto.offset.reset parameter driving when to consume messages in a topic. (Default value: smallest)
```

Example usage below:

```bash
python3 consumer.py --group-id morpheus \
  --bootstrap-servers kafka:19092 --topic scrape_queue \
  --max-messages 10 --auto-offset-reset smallest
```
