#!/bin/bash

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

helpFunction()
{
   echo ""
   echo "usage: $0 [-s SOURCE_TYPE] [-n N_MESSAGES]"
   echo "options:"
   echo -e "  -h             Show this help message and exit."
   echo -e "  -s SOURCE_TYPE Source type to generate (url, raw, or both)"
   echo -e "  -n N_MESSAGES  Number of messages to publish to Kafka. (Default value: 1000)"

   exit 1 # Exit script after printing help
}

while getopts "h:s:n:" opt
do
   case "$opt" in
      s ) source_type="$OPTARG" ;;
      n ) n_messages="$OPTARG" ;;
      h ) helpFunction ;; # Print helpFunction in case parameter is non-existent      
      ? ) helpFunction ;; # Print helpFunction in case parameter is non-existent
   esac
done

# Print helpFunction in case parameters are empty
if [ -z "$source_type" ] || [ -z "$n_messages" ]
then
   echo "Some or all of the parameters are empty";
   helpFunction
fi

if [ "url" == "$source_type" ]
then
    docker exec -it producer bash -c " 
      python3 producer.py \
        --filepath data/url_sample.jsonl \
        --topic "scrape_queue" \
        --n-messages $n_messages \
      && echo Producing Complete!"
fi

if [ "raw" == "$source_type" ]
then
    docker exec -it producer bash -c "
      python3 producer.py \
        --filepath data/raw_sample.jsonl \
        --topic "raw_queue" \
        --n-messages $n_messages \
      && echo Producing Complete!"
fi

if [ "both" == "$source_type" ]
then
    docker exec -it producer bash -c " 
      python3 producer.py \
        --filepath data/raw_sample.jsonl \
        --topic "raw_queue" \
        --n-messages $n_messages & \
      python3 producer.py \
        --filepath data/url_sample.jsonl \
        --topic "scrape_queue" \
        --n-messages $n_messages &
      wait \
      && echo Producing Complete!"
fi
