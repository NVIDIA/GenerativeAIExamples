# SPDX-FileCopyrightText: Copyright (c) 2024-2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

"""
NVIDIA Nemotron Nano 9B v2 Coding Agent Demo 
Self-hosted deployment with reasoning, streaming, file context, and code extraction
"""

import re
import streamlit as st
import requests
import json
from transformers import AutoTokenizer
import time

# Page config
st.set_page_config(page_title="Reasoning Coder", page_icon="💻", layout="wide")

# Constants
MODEL_ID = "nvidia/NVIDIA-Nemotron-Nano-9B-v2"
DEFAULT_LOCAL_API = "http://localhost:8888/v1/chat/completions"
CHAT_STYLES = {
    "user": {"bg": "#1f77b4", "color": "white", "radius": "18px 18px 4px 18px", "align": "right"},
    "assistant": {"bg": "#f0f0f0", "color": "#333", "radius": "18px 18px 18px 4px", "align": "left"}
}

def parse_code_blocks(text: str):
    """Extract code blocks from Markdown response."""
    return [{"language": (m.group(1) or "").strip().lower() or "text", "code": m.group(2).strip()}
            for m in re.finditer(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", text, flags=re.DOTALL)]

def ext_to_language(filename: str) -> str:
    """Map file extension to language for syntax highlighting."""
    mapping = {".py": "python", ".js": "javascript", ".ts": "typescript", ".html": "html", ".css": "css",
               ".java": "java", ".cpp": "cpp", ".c": "c", ".go": "go", ".rs": "rust", ".json": "json",
               ".xml": "xml", ".yaml": "yaml", ".yml": "yaml", ".md": "markdown", ".csv": "text", ".txt": "text"}
    return next((lang for ext, lang in mapping.items() if filename.endswith(ext)), "text")

def display_code_blocks(blocks, title="### 🔍 Extracted Code Blocks"):
    """Display code blocks with consistent formatting."""
    if blocks:
        st.markdown(title)
        for i, block in enumerate(blocks, start=1):
            with st.expander(f"📄 Code Block {i} ({block['language']})", expanded=False):
                st.code(block["code"], language=block["language"], line_numbers=True)

def create_sidebar():
    """Create and return sidebar configuration."""
    st.sidebar.title("⚙️ Settings")
    st.sidebar.markdown("### Model Parameters")
    
    reasoning_enabled = st.sidebar.checkbox("Enable Reasoning", value=True, 
                                           help="Use /think for reasoning, /no_think for direct generation")
    streaming_enabled = st.sidebar.checkbox("Enable Streaming", value=False, disabled=reasoning_enabled,
                                           help="Streaming not supported with reasoning")
    
    if reasoning_enabled and streaming_enabled:
        st.sidebar.warning("⚠️ Streaming automatically disabled with reasoning")
        streaming_enabled = False
    
    temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.6, 0.1)
    top_p = st.sidebar.slider("Top P", 0.1, 1.0, 0.95, 0.05)
    max_thinking_budget = st.sidebar.slider("Max Thinking Budget", 64, 1024, 512, 64)
    max_tokens = st.sidebar.slider("Max Output Tokens", 512, 32768, 1024, 256)
    
    # Validation
    validation_error = reasoning_enabled and max_thinking_budget >= max_tokens
    if validation_error:
        st.sidebar.error("❌ Thinking budget must be smaller than max output tokens")
    if reasoning_enabled and max_tokens < 1024:
        st.sidebar.warning("⚠️ Consider at least 1024 tokens for reasoning tasks")
    
    # Chat management
    st.sidebar.markdown("### Chat Management")
    if st.sidebar.button("🗑️ Reset Chat", type="secondary", use_container_width=True):
        st.session_state.update({
            "chat_history": [], "current_prompt": "", "uploaded_files": [],
            "file_upload_key": f"file_upload_{int(time.time())}"
        })
        st.success("✅ Chat history cleared!")
        st.rerun()
    
    return reasoning_enabled, streaming_enabled, temperature, top_p, max_thinking_budget, max_tokens, validation_error

def finish_generation(content, blocks, elapsed_time, reasoning_enabled, current_prompt, context, reasoning_content=""):
    """Common logic for finishing generation and saving to history."""
    if blocks:
        display_code_blocks(blocks)
    
    # Show generation summary
    st.markdown("### 📊 Generation Summary")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Reasoning", f"~{len(reasoning_content.split())} words" if reasoning_content else "❌ Disabled")
    with col2:
        st.metric("Content", f"~{len(content.split())} words" if content else "❌ Failed")
    with col3:
        if elapsed_time is not None:
            st.metric("⏱️ Time", f"{elapsed_time:.2f}s")
        else:
            st.metric("⏱️ Time", "N/A")
    with col4:
        if elapsed_time is not None and elapsed_time > 0:
            st.metric("📊 Speed", f"~{len(content.split()) / elapsed_time:.1f} words/s")
        else:
            st.metric("📊 Speed", "N/A")
    
    # Save to chat history
    st.session_state.chat_history.extend([
        {"role": "user", "content": current_prompt, "context": context},
        {"role": "assistant", "content": content, "reasoning_content": reasoning_content,
         "code_blocks": blocks, "elapsed_time": elapsed_time, "original_reasoning_enabled": reasoning_enabled}
    ])
    
    st.success("✅ Response generated successfully!")
    st.rerun()

class NemotronCodingAgent:
    """Ultra-compact reasoning coding agent with reasoning capabilities."""
    
    def __init__(self):
        self.model_id = MODEL_ID
        self.api_endpoint = DEFAULT_LOCAL_API
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)

    def generate_code(self, prompt, context="", reasoning_enabled=True, max_thinking_budget=512, 
                      temperature=0.6, top_p=0.95, max_tokens=1024, stream=False, chat_history=None):
        """Main generation method with reasoning control."""
        try:
            messages = self._build_messages(prompt, context, chat_history)
            
            if reasoning_enabled:
                messages = self._add_system_message(messages, "/think")
                reasoning_content = self._generate_reasoning(messages, max_thinking_budget, temperature, top_p, chat_history)
                reasoning_tokens = len(self.tokenizer.encode(reasoning_content, add_special_tokens=False))
                remaining_tokens = max_tokens - reasoning_tokens
                
                if remaining_tokens <= 0:
                    return {"error": f"Remaining tokens must be positive. Got {remaining_tokens}"}
                
                content, finish_reason = self._generate_final_content(messages, reasoning_content, remaining_tokens, temperature, top_p)
                return {"reasoning_content": reasoning_content.strip().strip("</think>").strip(), "content": content, "finish_reason": finish_reason}
            else:
                messages = self._add_system_message(messages, "/no_think")
                response = requests.post(self.api_endpoint, json={
                    "model": self.model_id, "messages": messages, "max_tokens": max_tokens,
                    "temperature": temperature, "top_p": top_p
                })
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return {"choices": [{"message": {"content": content, "reasoning_content": ""}}]}
                
        except Exception as e:
            return {"error": f"Generation failed: {e}"}

    def _add_system_message(self, messages, instruction):
        """Add system message with instruction to messages list."""
        if messages and messages[0]["role"] == "system":
            messages[0]["content"] = f"{messages[0]['content']}\n\n{instruction}"
        else:
            messages.insert(0, {"role": "system", "content": instruction})
        return messages

    def _build_messages(self, prompt, context, chat_history):
        """Build messages list from chat history and current prompt."""
        messages = []
        if chat_history:
            recent_messages = chat_history[-4:] if len(chat_history) > 4 else chat_history
            for msg in recent_messages:
                if msg["role"] == "user":
                    content = f"Context: {msg['context']}\n\nTask: {msg['content']}" if msg.get("context") else msg["content"]
                    messages.append({"role": "user", "content": content})
                elif not msg.get("reasoning_content"):
                    messages.append({"role": "assistant", "content": msg["content"]})
        
        current_content = f"Context: {context}\n\nTask: {prompt}" if context else prompt
        messages.append({"role": "user", "content": current_content})
        return messages

    def _generate_reasoning(self, messages, max_thinking_budget, temperature, top_p, chat_history):
        """Generate reasoning content with limited thinking budget."""
        if chat_history:
            messages.insert(0, {"role": "system", "content": "This is a follow-up question. Provide fresh reasoning."})
        
        messages.append({"role": "system", "content": "End your reasoning with </think>"})
        
        response = requests.post(self.api_endpoint, json={
            "model": self.model_id, "messages": messages, "max_tokens": max_thinking_budget,
            "temperature": temperature, "top_p": top_p, "stop": ["</think>"]
        })
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return f"{content}.\n</think>\n\n" if "</think>" not in content else content.replace("</think>", "").strip() + "\n</think>\n\n"

    def _generate_final_content(self, messages, reasoning_content, remaining_tokens, temperature, top_p):
        """Generate final content using reasoning context."""
        messages.append({"role": "assistant", "content": reasoning_content})
        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, continue_final_message=True)
        
        completion_endpoint = self.api_endpoint.replace("/chat/completions", "/completions")
        response = requests.post(completion_endpoint, json={
            "model": self.model_id, "prompt": prompt, "max_tokens": remaining_tokens,
            "temperature": temperature, "top_p": top_p
        })
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["text"].strip(), data["choices"][0].get("finish_reason", "stop")

def display_chat_message(message, reasoning_enabled):
    """Display chat message with compact formatting."""
    if not message or "role" not in message or "content" not in message:
        st.warning("⚠️ Invalid message format")
        return
    
    role_icon = "👤" if message["role"] == "user" else "⚡"
    role_text = "You" if message["role"] == "user" else "Assistant"
    
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        st.markdown(f"**{role_icon} {role_text}:**")
        
        # Chat bubble styling
        style = CHAT_STYLES[message["role"]]
        st.markdown(f"""
        <div style="background-color: {style['bg']}; color: {style['color']}; padding: 12px 16px; 
                    border-radius: {style['radius']}; margin: 8px 0; text-align: {style['align']}; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            {message['content']}
        """, unsafe_allow_html=True)
        
        # Show context info for user messages
        if message.get('context') and message["role"] == "user":
            st.info("📁 **Files were uploaded as context**")
        
        # Show reasoning and code blocks for assistant messages
        if message["role"] == "assistant":
            if message.get('reasoning_content'):
                with st.expander("🧠 **View Reasoning Process**", expanded=False):
                    st.markdown(message['reasoning_content'])
            
            if message.get('code_blocks'):
                st.markdown("**🔍 Extracted Code:**")
                for j, block in enumerate(message['code_blocks']):
                    with st.expander(f"📄 Code Block {j+1} ({block['language']})", expanded=False):
                        st.code(block["code"], language=block["language"], line_numbers=True)
            
            # Generation summary
            if message.get('reasoning_content') or message.get('content'):
                st.markdown("### 📊 Generation Summary")
                col1, col2, col3, col4 = st.columns(4)
                
                original_reasoning = message.get('original_reasoning_enabled', reasoning_enabled)
                reasoning_content = message.get('reasoning_content', '')
                content = message.get('content', '')
                elapsed_time = message.get('elapsed_time')
                
                with col1:
                    if original_reasoning:
                        st.metric("Reasoning", f"~{len(reasoning_content.split())} words" if reasoning_content else "❌ Failed")
                    else:
                        st.metric("Reasoning", "❌ Disabled")
                
                with col2:
                    st.metric("Content", f"~{len(content.split())} words" if content else "❌ Failed")
                
                with col3:
                    if elapsed_time is not None:
                        st.metric("⏱️ Time", f"{elapsed_time:.2f}s")
                    else:
                        st.metric("⏱️ Time", "N/A")
                
                with col4:
                    if elapsed_time is not None and elapsed_time > 0:
                        st.metric("🏎️ Speed", f"~{len(content.split()) / elapsed_time:.1f} words/s")
                    else:
                        st.metric("🏎️ Speed", "N/A")

def main():
    st.title("💻 Reasoning Coder")
    st.markdown("""<div style='text-align:left;color:#666;'>Powered by <a href='https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-9B-v2' target='_blank'>NVIDIA Nemotron Nano 9B v2</a></div>""", unsafe_allow_html=True)
    st.markdown("---")

    # Initialize session state
    if "chat_history" not in st.session_state:
        st.session_state.update({
            "chat_history": [], "should_clear_input": False, 
            "input_key": "input_default", "uploaded_files": []
        })
    
    # Create sidebar and get configuration
    reasoning_enabled, streaming_enabled, temperature, top_p, max_thinking_budget, max_tokens, validation_error = create_sidebar()
    
    # Initialize agent
    agent = NemotronCodingAgent()
    
    # Chat history display
    if st.session_state.chat_history:
        st.markdown("### 💬 **Conversation History**")
        for message in st.session_state.chat_history:
            display_chat_message(message, reasoning_enabled)
        st.markdown("**💡 Continue below or reset to start fresh**")
        st.markdown("---")
    
    # File upload and example prompts
    st.markdown("**Upload files for context (optional)**")
    file_upload_key = st.session_state.get("file_upload_key", "file_upload_default")
    
    uploaded_files = st.file_uploader("Choose files", accept_multiple_files=True,
                                     type=["py", "js", "html", "css", "java", "cpp", "c", "txt", "md", "json", "xml", "yaml", "yml", "csv"],
                                     key=file_upload_key)
    
    if uploaded_files:
        st.session_state.uploaded_files = uploaded_files
        st.markdown("**📋 File Contents:**")
        file_contents = []
        for uf in uploaded_files:
            content_text = uf.read().decode("utf-8", errors="replace")
            file_contents.append((uf.name, content_text))
            with st.expander(f"📄 {uf.name}"):
                st.code(content_text, language=ext_to_language(uf.name))
        context = "\n".join([f"\n--- {name} ---\n{content}" for name, content in file_contents])
    else:
        context = ""
    
    # Input area
    if not st.session_state.chat_history:
        st.markdown("**💡 Example Prompts:**")
        examples = ["Implement a binary search tree with insertion and search operations", "Find longest palindromic substring", 
                   "Recursive Tower of Hanoi", "Validate email with regex", "Web scraper with requests"]
        cols = st.columns(len(examples))
        for i, prompt_example in enumerate(examples):
            if cols[i].button(f"Ex {i+1}", key=f"ex_{i}"):
                st.session_state["current_prompt"] = prompt_example
                st.rerun()
    else:
        st.markdown("*Ask follow-up questions, request modifications, or start a new topic*")
    
    # Handle input clearing
    if st.session_state.should_clear_input:
        st.session_state.current_prompt = ""
        st.session_state.should_clear_input = False
        st.session_state.input_key = f"input_{int(time.time())}"
    
    input_key = st.session_state.get("input_key", "input_default")
    prompt = st.text_area("💭 **What would you like me to help you with?**",
                          value=st.session_state.get("current_prompt", ""),
                          placeholder="Ask your question here...", height=150, key=input_key)
    
    # Generate button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        generate_button = st.button("🚀 Generate Response", type="primary", use_container_width=True)
    
    if generate_button:
        if validation_error:
            st.error("❌ Please fix validation errors above")
            return
        
        if not prompt.strip():
            st.warning("Please enter a prompt")
            st.session_state.current_prompt = ""
            st.rerun()
            return
        
        current_prompt = prompt
        st.session_state.should_clear_input = True
        
        status_text = st.empty()
        start_time = time.time()
        
        if streaming_enabled:
            # Streaming mode
            status_text.text("⚡ AI Agent streaming...")
            
            try:
                messages = agent._build_messages(current_prompt, context, st.session_state.chat_history)
                messages = agent._add_system_message(messages, "/no_think")
                
                response = requests.post(agent.api_endpoint, json={
                    "model": agent.model_id, "messages": messages, "max_tokens": max_tokens,
                    "temperature": temperature, "top_p": top_p, "stream": True
                }, stream=True)
                response.raise_for_status()
                
                full_content = ""
                content_placeholder = st.empty()
                content_placeholder.markdown("⏳ Waiting for content...")
                
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = line[6:]
                            if data == '[DONE]':
                                break
                            try:
                                chunk = json.loads(data)
                                if 'choices' in chunk and len(chunk['choices']) > 0:
                                    delta = chunk['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        full_content += delta['content']
                                        content_placeholder.markdown(full_content + "▌")
                            except json.JSONDecodeError:
                                continue
                
                elapsed_time = time.time() - start_time
                
                if full_content:
                    content_placeholder.markdown(full_content)
                    blocks = parse_code_blocks(full_content)
                    finish_generation(full_content, blocks, elapsed_time, False, current_prompt, context)
                else:
                    st.warning("⚠️ No content received from streaming")
                
            except Exception as e:
                st.error(f"❌ Streaming failed: {str(e)}")
                st.info("💡 Try disabling streaming or check vLLM server")
                st.rerun()
                return
            
            
        else:
            # Non-streaming mode
            status_text.text("⚡ AI Agent thinking...")
            
            response = agent.generate_code(
                prompt=current_prompt, context=context, reasoning_enabled=reasoning_enabled,
                max_thinking_budget=max_thinking_budget, temperature=temperature, top_p=top_p,
                max_tokens=max_tokens, stream=False, chat_history=st.session_state.chat_history
            )
            
            elapsed_time = time.time() - start_time
            
            if "error" in response:
                st.error(f"❌ {response['error']}")
                st.rerun()
                return
            
            # Extract content
            if isinstance(response, dict) and "reasoning_content" in response:
                reasoning_content = response.get("reasoning_content", "")
                content = response.get("content", "")
            else:
                content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
                reasoning_content = ""
            
            # Display reasoning if available
            if reasoning_enabled and reasoning_content:
                st.markdown("### 🧠 Reasoning Process")
                with st.expander("Click to see reasoning", expanded=True):
                    st.markdown(reasoning_content)
                st.markdown("---")
            
            st.markdown("### ⚡ Generated Code / Response")
            st.markdown(content or "(empty)")
            
            # Display code blocks and finish generation
            blocks = parse_code_blocks(content)
            finish_generation(content, blocks, elapsed_time, reasoning_enabled, current_prompt, context, reasoning_content)
        
        status_text.empty()
    
    st.markdown("---")

if __name__ == "__main__":
    main()
