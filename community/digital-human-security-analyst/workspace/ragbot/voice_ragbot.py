import numpy as np
import riva.client
import pandas as pd
import os
import io

import soundfile as sf

import sounddevice as sd #for capturing mic audio
import a2f_client #only necessary if using Audio2Face App
import keyboard
import ast

from langchain_nvidia_ai_endpoints import ChatNVIDIA

import sys
sys.path.append(os.path.abspath(os.path.join('..', 'upload_intel')))
import nemo_retriever_client as nrc #importing file from upload_intel dir



from generate_checklist import *
from agent_tools import *

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*initialize_agent.*")


make_user_directory_retriever_client()
make_network_traffic_retriever_client()
make_threat_intelligence_retriever_client()
make_alert_summaries_retriever_client()
make_email_security_gateway_retriever_client()


def make_general_collection_retriever_client():
    global retriever_client_general_collection

    base_directory = "../upload_intel/intel/tools/"
    retriever_client_general_collection = nrc.RetrieverClient()
    loader = TextLoader(base_directory+"general_collection.txt")
    document = loader.load()
    retriever_client_general_collection.add_files(document)

make_general_collection_retriever_client()

from dotenv import load_dotenv
load_dotenv()
NGC_API_KEY = os.getenv("NGC_API_KEY")


#Configure Retriever and Riva IP and Port
RIVA_IP_AND_PORT = "YOUR RIVA IP AND PORT" #should be in format [IP]:[PORT]


#Configure path to a2f audio streaming receiver
#Only necessary if using Audio2Face App
A2F_PLAYER_STREAMING_LOCATION = "YOUR LOCATION TO A2F PLAYER STREAMING NODE" #Ex: /World/audio2face/PlayerStreaming



#Create LLM client (build.nvidia.com API)
client_chatnvidia = ChatNVIDIA(
  model="meta/llama-3.1-405b-instruct",
  api_key=NGC_API_KEY, 
)

#Create Riva client
auth = riva.client.Auth(uri=RIVA_IP_AND_PORT)


#Configure Riva Text-to-Speech
riva_tts = riva.client.SpeechSynthesisService(auth)
sample_rate = 44100
req = { 
        "language_code"  : "en-US",
        "encoding"       : riva.client.AudioEncoding.LINEAR_PCM ,   # LINEAR_PCM and OGGOPUS encodings are supported
        "sample_rate_hz" : sample_rate,                          # Generate 44.1KHz audio
        "voice_name"     : "English-US.Male-1"                    # The name of the voice to generate
}


#Configure Riva Automatic Speech Recognition
riva_asr = riva.client.ASRService(auth)

config = riva.client.RecognitionConfig()
config.language_code = "en-US"                    # Language code of the audio clip
config.max_alternatives = 1                       # How many top-N hypotheses to return
config.enable_automatic_punctuation = True        # Add punctuation when end of VAD detected
config.audio_channel_count = 1                    # Mono channel


recording = False
audio_data = []
stream = None

#For chat history context
prior_response = ""

def start_recording():
    global recording, audio_data, stream
    if not recording:
        print("Recording in progress...")
        recording = True
        audio_data = []
        sd.default.samplerate = sample_rate
        sd.default.channels = 1
        sd.default.dtype = 'int16'
        sd.default.latency = 'low'
        stream = sd.InputStream(callback=audio_callback)
        stream.start()

def stop_recording():
    global recording, stream
    if recording:
        recording = False
        stream.stop()
        #Do NOT use stream.close() bc that interrupts audio output

        print("Recording finished.")
        ragbot()

def audio_callback(indata, frames, time, status):
    if recording:
        audio_data.extend(indata[:, 0])

def ragbot():
    global audio_data
    if audio_data:
        audio_np = np.array(audio_data, dtype='int16') #convert list to np array

        byte_io = io.BytesIO() #convert np array to byte buffer


        wav.write(byte_io, sample_rate, audio_np)
        byte_io.seek(0)
        content = byte_io.read()

        response = riva_asr.offline_recognize(content, config)

        if not response.results:
            print("No transcription result found.")
            return
        
        #Else, since response is not empty:
        selected_query = response.results[0].alternatives[0].transcript
        print("\nUser Query: " + selected_query + "\n")

        
        #Determine if we need to use a checklist or if this is a one-step retrieval task
        #Determine if we need tools to accomplish the task
        use_checklist = 0
        use_tools = 0

        routing_prompt = f"1. Does the following query need tools (0 for false, 1 for true)? My tools include access to User Directory, Network Traffic db, Threat Intelligence info, and Alert Summaries. \
        2. Does the prompt require one tool (0) or multiple tools (1)?\
        Return your answer as a python list of ints. For example: [0,1]. It's crucial that you do not return anything else other than this list.\
        Query: {selected_query}"

        routing_reply=""
        
        for chunk in client_chatnvidia.stream([{"role":"user","content":routing_prompt}]): 
            routing_reply += chunk.content


        routing_reply_list = ast.literal_eval(routing_reply)
        use_tools = routing_reply_list[0]
        use_checklist = routing_reply_list[1]

        print("USE CHECKLIST: " + str(use_checklist))
        print("USE TOOLS: " + str(use_tools))


        #generate checklist and embed the checklist into final_query if routing says checklist is needed
        if use_checklist == 1:

            my_checklist = generate_checklist(selected_query, client_chatnvidia)
            print("Here is the checklist I will be following to determine the final answer. :\n")
            print(my_checklist)


        global prior_response #initialize variable for storing context

        # context and checklist both needed
        if use_checklist == 1 and use_tools == 1: #prints out langchain react thought process
            set_llm_client(client_chatnvidia)

            #capture the reasoning process

            capture = deploy_tools(my_checklist, NGC_API_KEY)
            voice_prompt = f"Generate a final answer based on the initial query and final response. Limit your response to one short sentence.\n\
            Query: {selected_query} \n\
            Rresponse: {capture}"

            voice = ""
            for chunk in client_chatnvidia.stream([{"role":"user","content":voice_prompt}]): 
                voice += chunk.content

            voice = voice + " You can check the above outputs for my full reasoning process!"
        
        elif use_tools == 1: #context needed but no checklist --> simple RAG

            raw_prompt = "Use the following context to answer the query. If the user asks for a retrieval task, do not summarize. Instead, give the raw context. \nHere is some more context: " + prior_response + "\n\n Question: "

            voice = retriever_client_general_collection.rag_query(selected_query, raw_prompt)
            prior_response = voice

        else: #no context or checklist needed
            voice = ""
            for chunk in client_chatnvidia.stream([{"role":"user","content":selected_query+"Limit your response to one short sentence"}]): 
                voice += chunk.content

            prior_response = voice

        
        #If the response is too long, rely on text output
        if len(voice) > 100:
            voice = "Here's what I found!"
        
        print("VOICEOVER: " + voice)
        req["text"] = voice

        #Riva TTS

        #for Audio2Face App rendering
        #resp = riva_tts.synthesize_online(**req) #audio is returned in chunks as they are synthesized
        #############################

        #for Unreal Engine rendering
        resp = riva_tts.synthesize(**req) #audio is returned all at once when synthesis is complete
        audio_samples = np.frombuffer(resp.audio, dtype=np.int16)
        output_file = "final_output.wav"
        sf.write(output_file, audio_samples, sample_rate)
        ############################


        try:
            #for Audio2Face App rendering
            #a2f_client.push_audio_track_stream("localhost:50051", a2f_client.audio_chunk_generator(resp), req["sample_rate_hz"], A2F_PLAYER_STREAMING_LOCATION)
            print("|||||||||||||||| Press Space bar to start recording again ||||||||||||||||")
        
        except Exception as e:
            print(f"Error occurred when streaming audio to a2f: {e}")


if __name__ == "__main__":
    # print("Press Space bar to start and stop recording. Press Escape to exit.")
    # keyboard.on_press_key("space", lambda _: start_recording() if not recording else stop_recording())
    # #Keep the script running

    # keyboard.wait('esc')  #Use Escape key to stop the script
    # print("Script stopped.")

    ragbot()
    print("finished ragbot script")


