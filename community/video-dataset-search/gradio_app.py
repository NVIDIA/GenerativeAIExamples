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

import gradio as gr
from pathlib import Path
from typing import List, Tuple, Optional
from utils import VideoSearchAgent

agent = VideoSearchAgent()

def search_videos(text_query: str, file_path: str, top_k: int) -> Tuple[str, List[str], str]:
    try:
        if file_path and file_path.strip():
            query = file_path.strip()
        elif text_query and text_query.strip():
            query = text_query.strip()
        else:
            return "Please provide either a text query or a file path.", [], ""
        
        matches = agent.search(query, top_k=top_k)
        
        if not matches:
            return "No matches found.", [], ""
        
        results_text = f"### Found {len(matches)} matches:\n\n"
        video_choices = []
        
        for i, match in enumerate(matches, 1):
            results_text += f"**{i}. {match['video_name']}**\n"
            results_text += f"   - Similarity Score: {match['score']:.4f}\n"
            
            if 'text_description' in match and match['text_description']:
                results_text += f"   - Description: *{match['text_description']}*\n"
            
            results_text += f"   - Path: `{match['video_path']}`\n\n"
            
            video_choices.append(f"{i}. {match['video_name']} (Score: {match['score']:.4f})")
        
        top_video_path = matches[0]['video_path'] if matches else ""
        
        return results_text, video_choices, top_video_path
        
    except Exception as e:
        return f"Error: {str(e)}", [], ""

def load_selected_video(video_choice: str, results_text: str) -> Optional[str]:
    try:
        if not video_choice or not results_text:
            return None
        
        video_index = int(video_choice.split(".")[0])
        paths = [line.split("Path: `")[1].split("`")[0] 
                for line in results_text.split("\n") if "Path: `" in line]
        
        if 0 < video_index <= len(paths):
            return paths[video_index - 1]
        return None
    except Exception as e:
        print(f"Load error: {e}")
        return None

def create_interface():
    with gr.Blocks(title="Video Search System", theme=gr.themes.Glass()) as demo:
        gr.Markdown("# 🎥 Multimodal Video Search")
        gr.Markdown("Search your video dataset using text descriptions, images, or videos.")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Query Input")
                
                text_input = gr.Textbox(
                    label="Text Query",
                    lines=2
                )
                
                gr.Markdown("**OR**")
                
                file_path_input = gr.Textbox(
                    label="File Path (Image/Video)",
                    lines=1
                )
                
                top_k_slider = gr.Slider(
                    minimum=1,
                    maximum=10,
                    value=5,
                    step=1,
                    label="Number of Results"
                )
                
                search_btn = gr.Button("🔍 Search", variant="primary", size="lg")
            
            with gr.Column(scale=1):
                gr.Markdown("### Search Results")
                
                results_output = gr.Markdown(
                    value="Results will appear here...",
                    label="Matches",
                    height=600
                )
            
            with gr.Column(scale=1):
                gr.Markdown("### Video Player")
                
                video_dropdown = gr.Dropdown(
                    label="Select Video to Preview",
                    choices=[],
                    interactive=True
                )
                
                video_player = gr.Video(
                    label="Preview",
                    autoplay=False,
                    height=500
                )
        
        hidden_results = gr.State()
        
        def search_and_update(*args):
            results = search_videos(*args)
            video_choices = results[1]
            
            dropdown_update = gr.update(
                choices=video_choices,
                value=video_choices[0] if video_choices else None
            )
            
            return results[0], dropdown_update, results[2], results[0]
        
        search_btn.click(
            fn=search_and_update,
            inputs=[text_input, file_path_input, top_k_slider],
            outputs=[results_output, video_dropdown, video_player, hidden_results]
        )
        
        video_dropdown.change(
            fn=load_selected_video,
            inputs=[video_dropdown, hidden_results],
            outputs=video_player
        )
    
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(share=False, server_name="0.0.0.0", server_port=7860)
