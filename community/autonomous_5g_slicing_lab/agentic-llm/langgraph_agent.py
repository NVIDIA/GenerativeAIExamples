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
#script to define langgraph agent, and start the workflow
import json
import os
import time
import yaml
from typing import Literal
from langchain_core.messages import convert_to_messages, BaseMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, MessagesState, END
from langgraph.prebuilt import ToolNode
from IPython.display import Image, display
from agents import ConfigurationAgent, MonitoringAgent, State
from langchain_nvidia_ai_endpoints import ChatNVIDIA
import logging
import json

config_file =  yaml.safe_load(open('config.yaml', 'r'))
file_path = config_file['gnb_logs']
os.makedirs(os.path.dirname(config_file['AGENT_LOG_FILE']), exist_ok=True)

# Create the file if it doesn't exist
if not os.path.exists(config_file['AGENT_LOG_FILE']):
    with open(config_file['AGENT_LOG_FILE'], "w") as file:
        pass
        
#logger for printing output to a log file
logging.basicConfig(
    filename= config_file['AGENT_LOG_FILE'],  # Log file name
    level=logging.INFO,   # Log level
    format="%(message)s"  # Only log the message
)

#format the output
def pretty_print_message(update) -> str:
    output = ""
    if isinstance(update, tuple):
        ns, update = update
        # skip parent graph updates in the printouts
    #Work on this
    if len(ns) != 0:
        for node_name, node_update in update.items():
            for message in convert_to_messages(node_update["messages"]):
                output = f"[{message.type}]: {message.content}"
                if isinstance(message, AIMessage) and hasattr(message, 'tool_calls'):
                    tools = "\n".join(
                        f"- {tc['name']}({json.dumps(tc['args'], indent=2)})"
                        for tc in message.tool_calls
                    )
                    output += f"\nTools:\n{tools}"
    
    return output

#Build graph 
def create_graph(server=None, model=None, stop=None, model_endpoint=None, temperature=0):
    workflow = StateGraph(State)

    def monitor_decision(state:State)-> Literal["Monitoring Agent", "__end__"]: 
        if state['consent'] == 'yes':
            return "Monitoring Agent"
        else:
            return "__end__" 

    # Define the two nodes we will cycle between
    workflow.add_node("Monitoring Agent", MonitoringAgent)
    workflow.add_node("Configuration Agent", ConfigurationAgent)

    # Define edges of the graph
    workflow.add_edge("__start__", "Monitoring Agent")
    workflow.add_edge("Monitoring Agent", "Configuration Agent")
    workflow.add_conditional_edges("Configuration Agent", monitor_decision)
    return workflow

def compile_workflow(graph, img_name="./images/langgraph_DLI.png"):
    workflow = graph.compile()
    if img_name!=None:
        os.makedirs(os.path.dirname(img_name), exist_ok=True)
        png_data = workflow.get_graph().draw_mermaid_png()
        # Save the PNG data to a file
        with open(img_name, "wb") as file:
            file.write(png_data)
        print("Saved graph image as ", img_name)
    return workflow

def display_graph(workflow):
    try:
        print(workflow.get_graph())
        display(Image(workflow.get_graph().draw_mermaid_png()))
        # print("SUCCESS")
    except Exception as e:
        print("ERROR IN GRAPH")
        print(e)

def main():
    graph = create_graph()
    workflow = compile_workflow(graph)

    config = RunnableConfig(recursion_limit=1500)
    start = os.path.getsize(file_path)

    #input load to the agent
    input = {
        "messages": "Hey, can you monitor and reconfigure the network for me?",
        "agent_id": "human",
        "files": None,
        "start": start,
        "logs_filename": file_path,
        "config_value": ["50", "50"],
        "count": 0
    }
    count = 0
    for s in workflow.stream(input, config, subgraphs=True):
        formatted = pretty_print_message(s)
        logging.info(formatted)

if __name__ == "__main__":
    main()
