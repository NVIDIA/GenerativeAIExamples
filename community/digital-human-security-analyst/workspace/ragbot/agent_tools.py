from langchain.agents import Tool
import pandas as pd
import os
import sys

from langchain_nvidia_ai_endpoints import ChatNVIDIA

from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory

from langchain_community.document_loaders import TextLoader


sys.path.append(os.path.abspath(os.path.join('..', 'upload_intel')))
import nemo_retriever_client as nrc #importing file from upload_intel dir



#each retriever client has its own vector store
def make_user_directory_retriever_client():
    global retriever_client_user_directory

    base_directory = "../upload_intel/intel/tools/"
    retriever_client_user_directory = nrc.RetrieverClient()
    loader = TextLoader(base_directory+"user_directory.txt")
    document = loader.load()
    retriever_client_user_directory.add_files(document)


def make_network_traffic_retriever_client():
    global retriever_client_network_traffic

    base_directory = "../upload_intel/intel/tools/"
    retriever_client_network_traffic = nrc.RetrieverClient()
    loader = TextLoader(base_directory+"network_traffic.txt")
    document = loader.load()
    retriever_client_network_traffic.add_files(document)


def make_threat_intelligence_retriever_client():
    global retriever_client_threat_intelligence

    base_directory = "../upload_intel/intel/tools/"
    retriever_client_threat_intelligence = nrc.RetrieverClient()
    loader = TextLoader(base_directory+"threat_intelligence.txt")
    document = loader.load()
    retriever_client_threat_intelligence.add_files(document)

def make_alert_summaries_retriever_client():
    global retriever_client_alert_summaries

    base_directory = "../upload_intel/intel/tools/"
    retriever_client_alert_summaries = nrc.RetrieverClient()
    loader = TextLoader(base_directory+"alert_summaries.txt")
    document = loader.load()
    retriever_client_alert_summaries.add_files(document)


def make_email_security_gateway_retriever_client():
    global retriever_client_email_security_gateway

    base_directory = "../upload_intel/intel/tools/"
    retriever_client_email_security_gateway = nrc.RetrieverClient()
    loader = TextLoader(base_directory+"email_security_gateway.txt")
    document = loader.load()
    retriever_client_email_security_gateway.add_files(document)



def set_llm_client(client):
    global llm_client
    llm_client = client

def deploy_tools(query, LANGCHAIN_KEY):

    llm = ChatNVIDIA(
        model="meta/llama-3.1-405b-instruct",
        api_key=LANGCHAIN_KEY
    )

    tools=[search_user_directory_tool, search_network_traffic_tool, search_threat_intelligence_tool, search_alert_summaries_tool]

    memory = ConversationBufferMemory()

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        memory=memory
    )

    my_full_prompt = "Answer the following question(s): " + query
    return agent.invoke({"input": my_full_prompt})



# RAG search in User Directory collection (tool 1)
def search_user_directory(query): #need to enter the correct collection id for User Directory documents
    #Send user query to Retriever for RAG

    raw_prompt = "Use the given context to extract information relevant to this parameter. \n\nParameter: "
    return retriever_client_user_directory.rag_query(query, raw_prompt)


search_user_directory_tool = Tool(
    name="search_user_directory",
    func=search_user_directory,
    description="User Directory: database matching user email to full name, endpoint device IPs, department, city, last login."
)


# RAG search in Network Traffic collection (tool 2)
def search_network_traffic(query):

    #Send user query to Retriever for RAG
    raw_prompt = "Use the given context to extract information relevant to this parameter. \n\nParameter: "
    return retriever_client_network_traffic.rag_query(query, raw_prompt)


search_network_traffic_tool = Tool(
    name="search_network_traffic",
    func=search_network_traffic,
    description="Network Traffic Database: This database contains RAW network traffic activity. You may filter by:\
        - timestamp (ie. timestamp=May 6th, 4:01) \
        - endpoint_IP (ie. endpoint_ip=192.165.110)\
        - user_email (ie. john@domain.com)\
        - port (ie. port=19)\
        - protocol (ie. protocol=TCP)\
        - destination URL (ie. destination_url=examplesite.com)"
)



# RAG search in Threat Intelligence collection (tool 3)
def search_threat_intelligence(query):
    #Send user query to Retriever for RAG

    raw_prompt = "I am retrieving from a database of known malicious domains, actors, and IPs. If my item is in this database, then my retrieval results will mention it meaning the item is known to be malicious. Otherwise, it is not known to be malicious. Return true/false. \n\nItem: "

    return retriever_client_threat_intelligence.rag_query(query, raw_prompt)


search_threat_intelligence_tool = Tool(
    name="search_threat_intelligence",
    func=search_threat_intelligence,
    description="The Threat Intelligence Database contains known malicious destination URLs and IPs. It will return whether an item is known to be malicious or not.\
        For example:\
        Input: destination_url=example.net, site.com, computers.net \
        Output: example.net and site.com were found to be malicious"
)


# RAG search in Alert Summaries collection (tool 4)
def search_alert_summaries(query):
    #Send user query to Retriever for RAG

    raw_prompt = "Use the following context to answer the user query. \n\nQuery: "
    return retriever_client_alert_summaries.rag_query(query, raw_prompt)
   

search_alert_summaries_tool = Tool(
    name="search_alert_summaries",
    func=search_alert_summaries,
    description="Alert Summaries: query a collection of natural language summaries of alerts, organized per user (each user has one report)"
)


# RAG search in Email Security Gateway collection (tool 5)
def search_email_security_gateway_tool(query):
    #Send user query to Retriever for RAG

    raw_prompt = "Use the following context to answer the user query. \n\nQuery: "
    return retriever_client_email_security_gateway.rag_query(query, raw_prompt)
    

search_email_security_gateway_tool = Tool(
    name="search_email_security_gateway_tool",
    func=search_email_security_gateway_tool,
    description="Email Security Gateway: query blocked potentially malicious emails as well as corresponding users they were sent to, and other metadata"
)