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

from langchain.chains import GraphQAChain
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph, get_entities
from langchain_nvidia_ai_endpoints import ChatNVIDIA

import streamlit as st
import json
import networkx as nx
st.set_page_config(layout = "wide")

from langchain_community.callbacks.streamlit import StreamlitCallbackHandler

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from vectorstore.search import SearchHandler

G =  nx.read_graphml("knowledge_graph.graphml")
graph = NetworkxEntityGraph(G)

models = ChatNVIDIA.get_available_models()
available_models = [model.id for model in models if model.model_type=="chat" and "instruct" in model.id]

with st.sidebar:
    llm = st.selectbox("Choose an LLM", available_models, index=available_models.index("mistralai/mixtral-8x7b-instruct-v0.1"))
    st.write("You selected: ", llm)
    llm = ChatNVIDIA(model=llm)

st.subheader("Chat with your knowledge graph!")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

with st.sidebar:
    use_kg = st.toggle("Use knowledge graph")

user_input = st.chat_input("Can you tell me how research helps users to solve problems?")

graph_chain = GraphQAChain.from_llm(llm = llm, graph=graph, verbose=True)

prompt_template = ChatPromptTemplate.from_messages(
    [("system", "You are a helpful AI assistant named Envie. You will reply to questions only based on the context that you are provided. If something is out of context, you will refrain from replying and politely decline to respond to the user."), ("user", "{input}")]
)

chain = prompt_template | llm | StrOutputParser()
search_handler = SearchHandler("hybrid_demo3", use_bge_m3=True, use_reranker=True)

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        if use_kg:
            entity_string = llm.invoke("""Return a JSON with a single key 'entities' and list of entities within this user query. Each element in your list MUST BE part of the user's query. Do not provide any explanation. If the returned list is not parseable in Python, you will be heavily penalized. For example, input: 'What is the difference between Apple and Google?' output: ['Apple', 'Google']. Always follow this output format. Here's the user query: """ + user_input)
            try:
                entities = json.loads(entity_string.content)['entities']
                with st.expander("Extracted triples"):
                    st.code(entities)
                res = search_handler.search_and_rerank(user_input, k=5)
                with st.expander("Retrieved and Reranked Sparse-Dense Hybrid Search"): 
                    st.write(res)
                context = "Here are the relevant passages from the knowledge base: \n\n" + "\n".join(item.text for item in res)
                all_triplets = []
                for entity in entities:
                    all_triplets.extend(graph_chain.graph.get_entity_knowledge(entity, depth=2))
                context += "\n\nHere are the relationships from the knowledge graph: " + "\n".join(all_triplets)
                with st.expander("All triplets"):
                    st.code(context)
            except Exception as e:
                st.write("Faced exception: ", e)
                context = "No graph triples were available to extract from the knowledge graph. Always provide a disclaimer if you know the answer to the user's question, since it is not grounded in the knowledge you are provided from the graph."
            message_placeholder = st.empty()
            full_response = ""
    
            for response in chain.stream("Context: " + context + "\n\nUser query: " + user_input):
                full_response += response
                message_placeholder.markdown(full_response + "▌")
        else:
            message_placeholder = st.empty()
            full_response = ""
            for response in chain.stream(user_input):
                full_response += response
                message_placeholder.markdown(full_response + "▌")
        message_placeholder.markdown(full_response)

    st.session_state.messages.append({"role": "assistant", "content": full_response})
