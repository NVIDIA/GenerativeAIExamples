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

import os
import random
import time
import yaml
from typing import TypedDict, Optional
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langgraph.graph import StateGraph, MessagesState
from langgraph.prebuilt import create_react_agent
from tools import reconfigure_network, get_packetloss_logs
import logging 

# Configure the logger without timestamp and level tags
config_file =  yaml.safe_load(open('config.yaml', 'r'))

logging.basicConfig(
    filename= config_file['AGENT_LOG_FILE'],  # Log file name
    level=logging.INFO,   # Log level
    format="%(message)s"  # Only log the message
)

#llm api to use Nvidia NIM Inference Endpoints.
llm = ChatNVIDIA(
        model= config_file['model_name'],
        api_key= config_file['API_KEY'], 
        temperature=0.2,
        top_p=0.7,
        max_tokens=4096,
)

#State class for communication between agents
class State(TypedDict):
    start:  Optional[int] = None #pointer to start reading from gnodeB.log
    messages: Optional[str] = None
    agent_id: Optional[str] = None #useful for routing between agents
    files: Optional[dict] = None #pass error logs from Monitoring Agent to COnfiguration Agent
    consent: Optional[str] = None
    config_value: Optional[list] = None #keep a track of slice values
    count: Optional[int] = None 

def MonitoringAgent(state: State):
    response = "This is a Monitoring agent, monitoring logs for SDU buffer full error."
    logging.info(response)
    filename = config_file['gnb_logs']
    chunk_size = 1000
    start_val = state['start'] #Always start parsing logs from end of file to analayze the most recent logs

    #Keep reading the gnodeB logs file for chunks till an error is detected.
    with open(filename, 'r') as file:
        while True:
            file_size = os.path.getsize(filename)
            #Wait till there are substantial logs
            if (start_val + chunk_size) >= file_size:
                #print("Waiting for logs\n")
                logging.info("Waiting for logs \n")
                time.sleep(2) 
                continue
            file.seek(start_val)
            chunk = file.read(chunk_size)

            if chunk:
                start_val += len(chunk)
                prompt0 = f"""Hello, you are a Network Monitoring agent. You will be provided with a random chunk of text. Your task is to classify logs with "buffer full" errors:
                If it has a "buffer full" error just reply "yes". If it does not have a "buffer full" error reply "no". DO NOT provide explanation.
                Example of Log that HAS a  "buffer full" error:

                [RLC]   /home/nvidia/llm-slicing-5g-lab/openairinterface5g/openair2/LAYER2/nr_rlc/nr_rlc_entity_am.c:1769:nr_rlc_entity_am_recv_sdu: warning: 195 SDU rejected, SDU buffer full
                [NR_MAC]   Frame.Slot 896.0
                UE RNTI c1f9 CU-UE-ID 1 in-sync PH 0 dB PCMAX 0 dBm, average RSRP -44 (16 meas)
                UE c1f9: UL-RI 1, TPMI 0
                UE c1f9: dlsch_rounds 23415/1/0/0, dlsch_errors 0, pucch0_DTX 0, BLER 0.00000 MCS (0) 28
                UE c1f9: ulsch_rounds 8560/0/0/0, ulsch_errors 0, ulsch_DTX 0, BLER 0.00000 MCS (0) 9
                UE c1f9: MAC:    TX      177738642 RX         612401 bytes
                UE c1f9: LCID 1: TX           1022 RX            325 bytes

                Example of Log that does NOT have a "buffer full" error:

                [NR_MAC]   Frame.Slot 896.0
                UE RNTI c1f9 CU-UE-ID 1 in-sync PH 0 dB PCMAX 0 dBm, average RSRP -44 (16 meas)
                UE c1f9: UL-RI 1, TPMI 0
                UE c1f9: dlsch_rounds 56771/1/0/0, dlsch_errors 0, pucch0_DTX 0, BLER 0.00000 MCS (0) 9
                UE c1f9: ulsch_rounds 16844/0/0/0, ulsch_errors 0, ulsch_DTX 0, BLER 0.00000 MCS (0) 9
                UE c1f9: MAC:    TX      480086220 RX         941362 bytes
                UE c1f9: LCID 1: TX           1022 RX            325 bytes

                Logs to analyze:
                {chunk}
                """
                human_message0 = HumanMessage(content=prompt0)
                response0 = llm.invoke([human_message0])
                cleaned_content0 = response0.content
                logging.info("Response from Monitoring agent: Error Detected? %s\n", cleaned_content0)
                if cleaned_content0=='yes':
                    break
                else:
                    continue
    return {"messages":response, "start": start_val, "files":{"chunk": chunk} }

system_promt = 'You are a Configuration agent in a LangGraph. Your task is to help an user reconfigure a current 5G network. You must reply to the questions asked concisely, and exactly in the format directed to you.'
config_agent = create_react_agent(llm, tools=[reconfigure_network, get_packetloss_logs], prompt = system_promt)
def ConfigurationAgent(state: State):
    response = "This is a Configuration Agent, whose goal is to reconfigure the network to solve the SDU buffer full error."
    logging.info(response)
    logging.info("Error detected in logs: \n %s \n\n", state['files']['chunk'])
    prompt_0 = '''
    Your task is to determine which UE needs reconfiguration. Follow these steps exactly:

    1. Call the get_packetloss_logs tool to get packet loss logs.
    Action: get_packetloss_logs()

    2. Analyze the results:
    - Identify which UE (UE1 or UE3) has a higher packet loss, depending on lost_packets,loss_percentage and UE.
    - State which UE you've identified as needing reconfiguration. 
    If UE1 requires reconfiguration, just reply "UE1". If UE3 requires reconfiguration, just reply "UE3". DO NOT provide explanation.
    '''
    human_message = HumanMessage(content=prompt_0)
    response = config_agent.invoke({"messages":[human_message]})
    cleaned_content0 = response['messages'][-1].content
    
    prompt_1 = f'''

    Your task is to reconfigure the network using the `reconfigure_network` tool. The tool accepts the following parameters:
    1. `UE` = UE (UE1 or UE2) which requires reconfiguration
    2. `value_1_old` = Old value 1 of configs
    3. `value_2_old` = Old value 2 of configs

    Here is the input:
    - `UE` = {cleaned_content0}
    - `value_1_old` = {state['config_value'][0]}
    - `value_2_old` = {state['config_value'][1]}

    Use the tool to reconfigure the network. Return **only** the tool response list as the output.'''
    
    human_message2 = HumanMessage(content=prompt_1)
    response2 = config_agent.invoke({"messages":[human_message2]})
    config_value_updated = response2['messages'][-2].content
    config_value_updated = config_value_updated.strip("[]").replace("'", "").split(", ")
    count = state['count'] 
    count += 1

    #start monitoring from the end
    start = os.path.getsize(config_file['gnb_logs'])

    #take in human input
    consent = 'yes'
    if count >= config_file['interrupt_after']:
        consent = input("Do you want to continue Monitoring? (yes/no)")
    return {"messages":response, "agent_id": "Configuration Agent", "start": start, 'config_value':config_value_updated, 'count': count, 'consent': consent}

"""
**Exercise**
We saw how to run the configuration agent with 2 LLM calls to the agent. Can we use the create_react_agent to execute both tool calls with a single prompt?
TO DO:
Replace the below configuration agent to find out!

def ConfigurationAgent(state: State):
    response = "This is a Configuration Agent, whose goal is to reconfigure the network to solve the SDU buffer full error."
    logging.info(response)
    logging.info("Error detected in logs: \n %s \n\n", state['files']['chunk'])
    #test:
    combined_prompt =  f'''
    You are a network reconfiguration agent specializing in UE reconfiguration. Your task is to identify and reconfigure problematic UE equipment. Follow these steps exactly:

    1. **Get logs**:
    - Call `get_packetloss_logs` to retrieve network performance data
    Action: get_packetloss_logs()

    2. **Analysis**:
    - Identify which UE (UE1 or UE2) shows higher packet loss using these metrics:
        * Total lost_packets
        * loss_percentage
        * UE identifier
    - Store your conclusion as "target_UE"

    3. **Reconfiguration**:
    - Use `reconfigure_network` with parameters:
        1. UE = target_UE
        2. value_1_old = {state['config_value'][0]}
        3. value_2_old = {state['config_value'][1]}
    Action: reconfigure_network(UE=target_UE, value_1_old={state['config_value'][0]}, value_2_old={state['config_value'][1]})

    4. **Output**:
    - Return **only** the final tool response from `reconfigure_network`
    - No explanations or additional text
    '''
    config_agent = create_react_agent(llm, tools=[reconfigure_network, get_packetloss_logs], prompt=combined_prompt)
    time.sleep(2)
    human_message2 = HumanMessage(content="Please reconfigure the network")
    response2 = config_agent.invoke({"messages":[human_message2]})
    
    config_value_updated = response2['messages'][-2].content
    config_value_updated = config_value_updated.strip("[]").replace("'", "").split(", ")
    count = state['count'] 
    count += 1

    #start monitoring from the end
    start = os.path.getsize(state['logs_filename'])

    #take in human input 
    consent = 'yes'
    if count >= config_file['interrupt_after']:
        consent = input("Do you want to continue Monitoring? (yes/no)")
    return {"messages":response, "agent_id": "Configuration Agent", "start": start, 'config_value':config_value_updated, 'count': count, 'consent': consent}


"""