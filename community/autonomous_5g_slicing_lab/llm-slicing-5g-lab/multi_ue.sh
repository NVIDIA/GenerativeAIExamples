#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2023-2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

ue_id=-1

create_namespace() {
  ue_id=$1
  local name="ue$ue_id"
  echo "creating namespace for UE ID ${ue_id} name ${name}"
  ip netns add $name
  ip link add v-eth$ue_id type veth peer name v-ue$ue_id
  ip link set v-ue$ue_id netns $name
  BASE_IP=$((200+ue_id))
  ip addr add 10.$BASE_IP.1.100/24 dev v-eth$ue_id
  ip link set v-eth$ue_id up
  iptables -t nat -A POSTROUTING -s 10.$BASE_IP.1.0/255.255.255.0 -o lo -j MASQUERADE
  iptables -A FORWARD -i lo -o v-eth$ue_id -j ACCEPT
  iptables -A FORWARD -o lo -i v-eth$ue_id -j ACCEPT
  ip netns exec $name ip link set dev lo up
  ip netns exec $name ip addr add 10.$BASE_IP.1.$ue_id/24 dev v-ue$ue_id
  ip netns exec $name ip link set v-ue$ue_id up
}

delete_namespace() {
  local ue_id=$1
  local name="ue$ue_id"
  echo "deleting namespace for UE ID ${ue_id} name ${name}"
  ip link delete v-eth$ue_id
  ip netns delete $name
}

list_namespaces() {
  ip netns list
}

open_namespace() {
  if [[ $ue_id -lt 1 ]]; then echo "error: no last UE processed"; exit 1; fi
  local name="ue$ue_id"
  echo "opening shell in namespace ${name}"
  echo "type 'ip netns exec $name bash' in additional terminals"
  ip netns exec $name bash
}

usage () {
  echo "$1 -c <num>: create namespace \"ue<num>\""
  echo "$1 -d <num>: delete namespace \"ue<num>\""
  echo "$1 -e      : execute shell in last processed namespace"
  echo "$1 -l      : list namespaces"
  echo "$1 -o <num>: open shell in namespace \"ue<num>\""
}

prog_name=$(basename $0)

if [[ $(id -u) -ne 0 ]] ; then echo "Please run as root"; exit 1; fi
if [[ $# -eq 0 ]]; then echo "error: no parameters given"; usage $prog_name; exit 1; fi

while getopts c:d:ehlo: cmd
do
  case "${cmd}" in
    c) create_namespace ${OPTARG};;
    d) delete_namespace ${OPTARG};;
    e) open_namespace; exit;;
    h) usage ${prog_name}; exit;;
    l) list_namespaces;;
    o) ue_id=${OPTARG}; open_namespace;;
    /?) echo "Invalid option"; usage ${prog_name}; exit;;
  esac
done  
