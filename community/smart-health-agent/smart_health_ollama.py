# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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
import json
import requests
import gradio as gr
import pandas as pd
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

# Define Ollama configuration - change this value to match your Ollama host on Google Cloud Run
OLLAMA_HOST = ""

# LangGraph imports
from langgraph.graph import StateGraph, END, START

# Core LLM / embedding imports
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage

# Use OllamaLLM for simpler streaming
from langchain_ollama import OllamaLLM
from langchain_huggingface import HuggingFaceEmbeddings

# Optional Google Fitness imports (if user selects Google Fit)
from google_fit_utils import get_google_fitness_data

# RAG / Milvus imports
from langchain_milvus import Milvus

# Import document processor helper module
import document_processor as dp

# Global LLM instance
llm = OllamaLLM(
    model='gemma3:4b-it-q4_K_M',
    temperature=0.2,
    streaming=True,
    base_url=OLLAMA_HOST
)

def WeatherAgent(latitude: float, longitude: float) -> dict:
    """
    Agent: Retrieves and analyzes weather conditions to inform health recommendations.
    Provides insights on optimal exercise settings based on current weather.
    """
    base_url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ["temperature_2m", "relative_humidity_2m", "weather_code"],
        "timezone": "America/Los_Angeles"
    }
    
    # Default values in case API fails
    weather_data = {"temperature": 20, "humidity": 50, "condition": "Unknown"}
    
    try:
        resp = requests.get(base_url, params=params)
        data = resp.json()
        if resp.status_code == 200 and "current" in data:
            current = data["current"]
            weather_descriptions = {
                0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy",
                3: "Overcast", 45: "Foggy", 51: "Light drizzle",
                53: "Moderate drizzle", 61: "Light rain",
                63: "Moderate rain", 65: "Heavy rain"
            }
            weather_data = {
                "temperature": current.get("temperature_2m", 20),
                "humidity": current.get("relative_humidity_2m", 50),
                "condition": weather_descriptions.get(current.get("weather_code", 0), "Unknown")
            }
    except Exception as e:
        print(f"[WEATHER_AGENT] Error retrieving weather data: {e}")
    
    def get_fallback_recommendations():
        temp = weather_data.get('temperature', 20)
        condition = weather_data.get('condition', 'Unknown')
        return {
            'exercise_recommendation': 'Indoor' if (temp > 30 or temp < 5) else 'Outdoor',
            'intensity_level': 'Moderate' if 15 <= temp <= 25 else 'Low',
            'weather_alert': condition.lower() in ['rain', 'drizzle', 'snow', 'storm', 'foggy'],
            'reasoning': f"Based on {temp}°C and {condition} conditions, recommend {'indoor' if (temp > 30 or temp < 5) else 'outdoor'} exercise at {'moderate' if 15 <= temp <= 25 else 'low'} intensity."
        }
    
    try:
        prompt = f"""Analyze weather conditions (Temperature: {weather_data['temperature']}°C, Condition: {weather_data['condition']}, Humidity: {weather_data['humidity']}%) and provide exercise recommendations in JSON format with these exact keys:
            - exercise_recommendation: "Indoor" or "Outdoor"
            - intensity_level: "Low", "Moderate", or "High"
            - weather_alert: true or false
            - reasoning: brief explanation
            Return only JSON."""
        
        response = llm.invoke(prompt)
        llm_recommendations = json.loads(response)
        
        # Verify all required fields exist
        required_fields = ['exercise_recommendation', 'intensity_level', 'weather_alert', 'reasoning']
        if all(field in llm_recommendations for field in required_fields):
            weather_data.update(llm_recommendations)
        else:
            weather_data.update(get_fallback_recommendations())
            
    except (json.JSONDecodeError, Exception) as e:
        print(f"[WEATHER_AGENT] LLM recommendation failed: {e}")
        weather_data.update(get_fallback_recommendations())
    
    return weather_data

###############################################################################
# SHARED STATE & AGENTS
###############################################################################

class HealthAgentState(BaseModel):
    """
    State object for the health agent workflow
    """
    messages: List[BaseMessage] = Field(default_factory=list)
    health_data: Dict[str, Any] = Field(default_factory=dict)
    weather_data: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[BaseMessage] = Field(default_factory=list)
    rag_context: Dict[str, Any] = Field(default_factory=dict)
    streaming_response: str = Field(default="")
    # Simple agent reasoning storage
    agent_reasoning: Dict[str, str] = Field(default_factory=dict)

def HealthMetricsAgent(state: HealthAgentState) -> HealthAgentState:
    """
    Agent: Analyzes fitness data and evaluates vitals/status.
    """
    print("\n[HEALTH_AGENT] Processing health data...")
    vitals_status = {}
    
    # Check if we have 7-day averages or single values
    if 'heart_rate_avg_7d' in state.health_data:
        hr = state.health_data.get('heart_rate_avg_7d', 0)
        sleep_hrs = state.health_data.get('sleep_hours_avg_7d', 0)
        steps = state.health_data.get('steps_avg_7d', 0)
        # Store both 7d average and regular format for compatibility
        state.health_data['heart_rate'] = hr
        state.health_data['sleep_hours'] = sleep_hrs
        state.health_data['steps'] = steps
    else:
        hr = state.health_data.get('heart_rate', 0)
        sleep_hrs = state.health_data.get('sleep_hours', 0)
        steps = state.health_data.get('steps', 0)
    
    print(f"[HEALTH_AGENT] Current metrics - HR: {hr}, Sleep: {sleep_hrs}, Steps: {steps}")

    vitals_status['heart_rate'] = 'Normal' if 60 <= hr <= 100 else 'Abnormal'
    vitals_status['sleep'] = 'Optimal' if 7 <= sleep_hrs <= 9 else 'Suboptimal'
    vitals_status['activity'] = 'Active' if steps >= 10000 else 'Sedentary'
    
    if not state.weather_data or 'exercise_recommendation' not in state.weather_data:
        state.weather_data = WeatherAgent(36.1699, -115.1398)  # Las Vegas coordinates
    
    state.health_data['vitals_status'] = vitals_status
    state.health_data['weather_impact'] = state.weather_data
    state.health_data['last_processed'] = pd.Timestamp.now()
    
    # Simple reasoning
    state.agent_reasoning["HealthMetrics"] = f"Analyzed vitals: HR {vitals_status['heart_rate']}, Sleep {vitals_status['sleep']}, Activity {vitals_status['activity']}"
    
    print(f"[HEALTH_AGENT] Processed vitals status: {vitals_status}")
    return state

def MedicalKnowledgeAgent(state: HealthAgentState) -> HealthAgentState:
    """
    Agent: Searches medical documents for relevant health insights using the globally initialized vectorstore.
    """
    print(f"\n[KNOWLEDGE_AGENT] Processing medical knowledge...")
    global global_vectorstore

    relevant_docs = []
    num_docs = 0
    
    # Check if the global vectorstore is initialized
    if global_vectorstore:
        query = f"Health insights for: Heart rate: {state.health_data.get('heart_rate')}, Sleep: {state.health_data.get('sleep_hours')} hours, Steps: {state.health_data.get('steps')}"
        try:
            relevant_docs = global_vectorstore.similarity_search(query, k=3)
            num_docs = len(relevant_docs)
        except Exception as e:
            print(f"[KNOWLEDGE_AGENT] Error during similarity search: {e}")
            relevant_docs = []
    else:
        print("[KNOWLEDGE_AGENT] Warning: Global vectorstore not initialized. Skipping document search.")

    state.rag_context["retrieved_knowledge"] = "\n".join([doc.page_content for doc in relevant_docs])
    state.rag_context["current_metrics"] = state.health_data
    
    state.agent_reasoning["MedicalKnowledge"] = f"Retrieved {num_docs} medical documents" if global_vectorstore else "Skipped document retrieval (vectorstore not initialized)"
    
    print("[KNOWLEDGE_AGENT] Updated state with retrieved knowledge")
    return state

def RecommendationAgent(state: HealthAgentState) -> HealthAgentState:
    """
    Agent: Generates personalized health recommendations based on all collected data.
    """
    print("\n[RECOMMENDATION_AGENT] Generating personalized health plan...")
    weather_data = state.weather_data
    
    context = f"""
    Medical Knowledge: {state.rag_context.get('retrieved_knowledge', 'No medical context available')}
    
    Current Health Metrics:
    - Heart Rate: {state.health_data.get('heart_rate')} bpm - Status: {state.health_data.get('vitals_status', {}).get('heart_rate', 'Unknown')}
    - Sleep: {state.health_data.get('sleep_hours')} hours - Status: {state.health_data.get('vitals_status', {}).get('sleep', 'Unknown')}
    - Steps: {state.health_data.get('steps')} - Status: {state.health_data.get('vitals_status', {}).get('activity', 'Unknown')}
    
    Weather Analysis:
    - Current Weather: {weather_data.get('condition')} at {weather_data.get('temperature')}°C
    - Recommended Location: {weather_data.get('exercise_recommendation')}
    - Suggested Intensity: {weather_data.get('intensity_level')}
    - Weather Alerts: {"Yes" if weather_data.get('weather_alert') else "None"}
    - Weather Assessment: {weather_data.get('reasoning', '')}
    """
    
    prompt = f"""As the Health Recommendation Agent, generate personalized health advice:
    
    1. Consider the user's metrics (HR: {state.health_data.get('heart_rate')}, Sleep: {state.health_data.get('sleep_hours')}, Steps: {state.health_data.get('steps')})
    2. Factor in weather data from Weather Agent ({weather_data.get('temperature')}°C, {weather_data.get('condition')})
    3. Incorporate medical knowledge from documents
    
    Provide actionable recommendations for activity, nutrition, and sleep, with special focus on {weather_data.get('exercise_recommendation')} activities at {weather_data.get('intensity_level')} intensity.
    """
    
    response = ""
    for chunk in llm.stream(prompt):
        response += chunk
        state.streaming_response = response
    
    state.recommendations.append(AIMessage(content=response))
    state.agent_reasoning["Recommendations"] = f"Generated personalized health plan (recommending {weather_data.get('exercise_recommendation')} activities)"
    print("[RECOMMENDATION_AGENT] Generated recommendations successfully")
    return state

# Add global variable to store the vectorstore
global_vectorstore = None

def setup_rag_components(docs_folder: str):
    """
    Tool: Initialize RAG with a user-specified folder.
    """
    global global_vectorstore
    print(f"\n[RAG_SETUP] Initializing RAG with folder: {docs_folder}")

    if not os.path.exists(docs_folder):
        print(f"[RAG_SETUP] Error: Document folder does not exist: {docs_folder}")
        return None
        
    if global_vectorstore is None:
        print("[RAG_SETUP] No existing vectorstore found. Creating a new one.")
        embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        print(f"[RAG_SETUP] Processing documents from: {docs_folder}")
        documents = dp.process_health_documents(docs_folder, is_directory=True)
        print(f"[RAG_SETUP] Document processing complete. Found {len(documents)} documents.")
        
        if not documents:
            print("[RAG_SETUP] Warning: No documents found or processed.")
            return None

        chunked_docs = dp.chunk_documents(documents)
        print(f"[RAG_SETUP] Chunked documents into {len(chunked_docs)} chunks.")

        print("[RAG_SETUP] Creating Milvus vectorstore instance.")
        global_vectorstore = Milvus(
            embedding_function=embeddings,
            connection_args={"uri": "./milvus_health.db"},
            collection_name="health_docs_rag",
            index_params={"metric_type": "L2", "index_type": "FLAT", "params": {"nlist": 1024}},
            auto_id=True
        )
        print(f"[RAG_SETUP] Adding {len(chunked_docs)} chunks to the vectorstore.")
        global_vectorstore.add_documents(chunked_docs)
        print("[RAG_SETUP] Documents successfully added to the vectorstore.")
    else:
        print("[RAG_SETUP] Using existing vectorstore.")
    
    return global_vectorstore

def chat_interact(user_message, chat_history):
    """
    Chat function with streaming support
    """
    print(f"\n[CHAT] Received message: {user_message}")
    global global_vectorstore
    
    context = ""
    if global_vectorstore:
        print("[CHAT] Performing similarity search...")
        try:
            relevant_docs = global_vectorstore.similarity_search(user_message, k=3)
            context = "\n".join([doc.page_content for doc in relevant_docs])
            print(f"[CHAT] Found {len(relevant_docs)} relevant documents for context.")
        except Exception as e:
            print(f"[CHAT] Error during similarity search: {e}")
            context = "Error retrieving relevant documents."
    else:
        print("[CHAT] Warning: No vectorstore available for context retrieval.")
    
    history_str = "\n".join([
        f"User: {h['content'] if h['role'] == 'user' else ''}\nAI: {h['content'] if h['role'] == 'assistant' else ''}"
        for h in chat_history if h['content']
    ])
    
    prompt = f"""Context from medical documents: {context}

        Chat history:
        {history_str}

        User: {user_message}
        AI:"""
    
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": ""})
    
    print("[CHAT] Generating response...")
    for chunk in llm.stream(prompt):
        chat_history[-1]["content"] += chunk
        yield "", chat_history
    
    print("[CHAT] Completed response")
    return "", chat_history

def build_health_workflow():
    """
    Build a workflow that connects specialized health agents.
    """ 
    graph = StateGraph(HealthAgentState)
    graph.add_node("health_metrics", HealthMetricsAgent)
    graph.add_node("medical_knowledge", MedicalKnowledgeAgent) 
    graph.add_node("generate_recommendations", RecommendationAgent)
    graph.add_edge(START, "health_metrics")
    graph.add_edge("health_metrics", "medical_knowledge")
    graph.add_edge("medical_knowledge", "generate_recommendations")
    graph.add_edge("generate_recommendations", END)
    
    return graph.compile()

###############################################################################
# GRADIO UI STEPS
###############################################################################

def generate_synthetic_fitness_data() -> dict:
    """
    Generate synthetic health/fitness data for testing.
    """
    return {
        'heart_rate': 75,
        'steps': 8500,
        'sleep_hours': 7.5,
        'calories': 2100,
        'last_updated': pd.Timestamp.now().isoformat()
    }

def initialize_app(data_source: str, folder_path: str):
    """
    Initializes the health companion with streaming support
    """
    print(f"\n[INIT] Initializing app with data source: {data_source}")
    print(f"[INIT] Using folder path: {folder_path}")
    
    if data_source == "Google Fit":
        print("[INIT] Getting Google Fit data...")
        health_data = get_google_fitness_data()
    else:
        print("[INIT] Using synthetic data...")
        health_data = generate_synthetic_fitness_data()
    
    print("[INIT] Activating Weather Agent...")
    weather_data = WeatherAgent(36.1699, -115.1398)  # Las Vegas coordinates
    print(f"[INIT] Weather analysis complete: {weather_data.get('exercise_recommendation')} exercise recommended")
    
    print("[INIT] Creating initial state...")
    state = HealthAgentState(
        messages=[HumanMessage(content="User wants personalized recommendations")],
        health_data=health_data,
        weather_data=weather_data,
        recommendations=[]
    )

    print("[INIT] Building and running workflow...")
    
    context = f"""
    Current Health Metrics:
    - Heart Rate: {health_data.get('heart_rate')} bpm
    - Sleep: {health_data.get('sleep_hours')} hours
    - Steps: {health_data.get('steps')}
    
    Weather Conditions:
    - Temperature: {weather_data.get('temperature')}°C
    - Humidity: {weather_data.get('humidity')}%
    - Condition: {weather_data.get('condition')}
    - Activity Location: {weather_data.get('exercise_recommendation')}
    - Weather Assessment: {weather_data.get('reasoning', '')}
    """
    
    prompt = f"Based on the following health and weather data, provide detailed health recommendations:\n{context}"
    
    return llm, prompt

def get_coordinates(city_name):
    """Get coordinates for a city name using Nominatim geocoder"""
    try:
        geolocator = Nominatim(user_agent="smart_health_app")
        location = geolocator.geocode(city_name)
        return (location.latitude, location.longitude) if location else (37.7749, -122.4194)  # Default to San Francisco
    except (GeocoderTimedOut, Exception) as e:
        print(f"[GEOCODER] Error getting coordinates for {city_name}: {e}")
        return (37.7749, -122.4194)  # Default to San Francisco

def on_initialize(data_src, fpath, city_name):
    """
    Handler for initialization button click - runs the agent workflow.
    """
    print("[UI] Initialize button clicked.")
    print(f"[UI] Data Source: {data_src}, Folder/File Path: {fpath}, City: {city_name}")
    
    messages = [{"role": "assistant", "content": ""}]
    initialization_error = None
    global global_vectorstore
    global_vectorstore = None # Reset vectorstore on each initialization
    
    try:
        # 1. Get Location
        lat, lon = get_coordinates(city_name)
        
        # 2. Determine RAG Folder Path
        rag_folder_path = None
        if isinstance(fpath, str) and os.path.isdir(fpath):
            print(f"[UI] Using provided directory path for RAG: {fpath}")
            rag_folder_path = fpath
        elif hasattr(fpath, 'name'): 
             temp_file_path = fpath.name
             if not temp_file_path.lower().endswith(('.pdf')):
                 initialization_error = "Error: Only PDF files are accepted."
                 yield initialization_error, []
                 return
             rag_folder_path = os.path.dirname(temp_file_path)
             print(f"[UI] Processing uploaded PDF from temp directory: {rag_folder_path}")
        elif isinstance(fpath, str) and os.path.isfile(fpath): # File path string
             if not fpath.lower().endswith(('.pdf')):
                 initialization_error = "Error: Only PDF file paths are accepted."
                 yield initialization_error, []
                 return
             rag_folder_path = os.path.dirname(fpath)
             print(f"[UI] Processing single file path provided: {rag_folder_path}")
        else:
            print("[UI] No valid document path/upload provided. Skipping RAG setup.")

        # 3. Initialize RAG 
        if rag_folder_path:
             print(f"[UI] Setting up RAG with path: {rag_folder_path}")
             setup_rag_components(rag_folder_path) 
             if global_vectorstore is None:
                 print("[UI] RAG setup did not initialize the vector store.")
        else:
             print("[UI] Skipping RAG setup.")

        # 4. Get Health Data
        print(f"[UI] Getting health data (Source: {data_src})")
        if data_src == "Google Fit (Deprecated)":
            try:
                health_data = get_google_fitness_data()
                print("[UI] Successfully retrieved Google Fit data")
            except Exception as e:
                print(f"[UI] Error accessing Google Fit API: {e}")
                messages = [{"role": "assistant", "content": "Warning: Google Fit API is deprecated and will be discontinued in 2026. Please use Synthetic Data instead. For more information, visit the Health Connect migration guide."}]
                yield "Error: Could not access Google Fit API. Please use Synthetic Data instead.", messages
                return
        else: # Default to synthetic
            health_data = generate_synthetic_fitness_data()
            print(f"[UI] Using synthetic health data")
        
        # 5. Get Weather Data
        print("[UI] Activating Weather Agent...")
        weather_data = WeatherAgent(lat, lon)
        print(f"[UI] Weather analysis complete.") 
        
        # 6. Build the workflow
        print("[UI] Building the agent workflow...")
        app = build_health_workflow()
        
        # 7. Prepare initial state
        print("[UI] Preparing initial state for the workflow...")
        initial_state = HealthAgentState(
            health_data=health_data,
            weather_data=weather_data,
            messages=[HumanMessage(content="User requested initial health recommendations.")] 
        )

        # 8. Run the workflow
        print("[UI] Invoking the agent workflow...")
        # Use invoke to run the graph to completion
        final_state = app.invoke(initial_state)
        print("[UI] Workflow execution completed.")

        # 9. Extract and display the result
        response_content = final_state.get('streaming_response')
        
        if not response_content:
             if final_state.get('recommendations'):
                 response_content = final_state['recommendations'][-1].content
             else:
                 response_content = "Agent workflow finished, but no recommendation message was generated."
                 print("[UI] Warning: No response content found in final state.")

        messages = [{"role": "assistant", "content": response_content}]
        yield initialization_error or "[UI] Initialization complete. Agents activated.", messages

    except Exception as e:
        error_msg = f"Error during initialization workflow: {str(e)}"
        print(f"[UI] Error: {error_msg}")
        import traceback
        traceback.print_exc()
        yield error_msg, [{"role": "assistant", "content": f"An error occurred: {error_msg}"}]

def create_ui():
    """
    Creates the Gradio interface with streaming support
    """
    with gr.Blocks() as demo:
        gr.Markdown("# Smart Health Agent")
        gr.Markdown("### GPU-accelerated personalized health recommendations with specialized agents")
        
        with gr.Column(scale=1):
            data_source = gr.Radio(
                choices=["Synthetic Data", "Google Fit (Deprecated)"],
                value="Synthetic Data",
                label="Health Data Source",
                info="Note: Google Fit API is deprecated and will be discontinued in 2026. New developers should use Synthetic Data. Existing Google Fit API users can continue using their integration."
            )
            city = gr.Textbox(
                label="Your City",
                placeholder="Enter your city (e.g. San Francisco)",
                value="San Francisco",
                container=True
            )
            folder_path = gr.Textbox(
                label="Medical Knowledge Base",
                placeholder="Enter path to folder containing medical PDF documents",
                scale=1,
                container=True
            )
            
            init_button = gr.Button("Activate Agent System", scale=1)
            init_output = gr.Textbox(label="Initialization Status", visible=False)

            chatbot = gr.Chatbot(
                label="Smart Health Agent Chat",
                height=400,
                container=True,
                show_copy_button=True,
                render_markdown=True,
                type='messages'
            )
            
            with gr.Row():
                msg = gr.Textbox(
                    label="Ask your health-related questions",
                    placeholder="Type your message here...",
                    show_label=True,
                    lines=2,
                    container=True,
                    scale=4
                )
            
            with gr.Row():
                submit = gr.Button("Send Message", scale=2)
                clear_button = gr.Button("Clear Chat", scale=1)

        init_button.click(
            fn=on_initialize,
            inputs=[data_source, folder_path, city],
            outputs=[init_output, chatbot],
        )
        
        msg.submit(
            fn=chat_interact,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
            queue=True,
        )
        
        submit.click(
            fn=chat_interact,
            inputs=[msg, chatbot],
            outputs=[msg, chatbot],
            queue=True,
        )
        
        clear_button.click(lambda: ([], ""), inputs=None, outputs=[chatbot, msg])

    return demo

if __name__ == "__main__":
    with gr.Blocks(
        theme=gr.themes.Base(),
        title="Smart Health Agent"
    ) as demo:
        create_ui()
    
    demo.queue()
    demo.launch(
        share=False,
        debug=True
    )