# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
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

# Simple Gradio Chatbot app, for details visit:
# https://www.gradio.app/guides/creating-a-custom-chatbot-with-blocks

import gradio as gr
import os
from chat_ui_utils import (
    ask_question,
    update_insert_button,
    update_reset_button,
    stream_response,
    get_chatnvidia_models,
    insert_model,
    get_api_model_parameters,
    update_yaml,
    initial_prompt,
    get_embedding_models,
    upload_file,
    show_loader,
    embedding_files,
    get_reranker_models,
    get_vs_embedding_model,
    update_rerank_size,
    update_search_size,
    update_reranker_settings,
    update_retrieval_db,
    delete_file_from_local,
    load_default_retrieval_db,
    load_local_files,
    clear_files,
    update_reset_fewshot_button
    )
                           

UI_SERVER_IP = os.getenv("UI_SERVER_IP", "0.0.0.0")
UI_SERVER_PORT = int(os.getenv("UI_SERVER_PORT", 80))

    
css = """
.gradio-container {
    max-width: 100%;
    margin: auto;
    padding: 0px;
}

.gr-button {
    color: #76b900;
}

#loader {
    position: fixed;
    left: 50%;
    top: 50%;
    z-index: 1000;
    width: 120px;
    height: 120px;
    margin: -76px 0 0 -76px;
    border: 16px solid #f3f3f3;
    border-radius: 50%;
    border-top: 16px solid #76b900;
    -webkit-animation: spin 2s linear infinite;
    animation: spin 2s linear infinite;
}

@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
"""

js = """
() => {
            document.body.classList.toggle('dark');
            document.querySelector('gradio-app').style.backgroundColor = 'black'
        }"""

def main():
    title = "Testing UI"

    theme = gr.themes.Monochrome(text_size=gr.themes.sizes.text_md,spacing_size="md").set(
        button_primary_background_fill="#76b900",
        button_primary_background_fill_dark="#76b900",
        checkbox_label_text_color="#171717",
        checkbox_label_background_fill="#f5f5f5",
        link_text_color_visited="#76b900",
        link_text_color_visited_dark="#76b900",
        link_text_color="#76b900",
        link_text_color_dark="#76b900",
    )

    with gr.Blocks(
        css=css,
        theme=theme,
        title=title,
        js=js,
        fill_height=True
    ) as demo:
        with gr.Group(visible=True):
            with gr.Row(variant="pannel"):
                        gr.Markdown(
                            """
                            # Designer of LLMs parameters
                            This tool help you to evaluate or do some prompt engineering with specified chat LLMs deployed in [API Catalog](https://build.nvidia.com/explore/discover) or self-host NIMs.    
                            If the new added models are not listed in the dropdown list, feel free to insert it with the same name in API Catalog.    
                            The default parameter settings are loaded from the config.yaml file of this project. You can change any of it in config.yaml file or modify it in UI than click "Update Yaml" button to update related config for the selected models.    
                            Try to start...
                            """)
        with gr.Tab("LLM Prompt Designer"):
            with gr.Row(variant="pannel"):
                # with gr.Column(scale=10):
                    chatbot = gr.Chatbot(
                            value=[(None, initial_prompt)],
                            label="Testing API Chatbot",
                            elem_id="chatbot",
                            scale = 20,
                            avatar_images=['./data/user.webp','./data/bot.webp'],
                            layout='bubble',
                            bubble_full_width = False,
                            container=False,
                        )
            with gr.Row(elem_id="input-row"):    
                    tbInput = gr.Textbox(
                                    placeholder="What questions do you have?",
                                    lines=1,
                                    label="Type text here...",
                                    scale = 5,
                                    container=False,
                                    # elem_id="msg",
                                    # variant="pannel"
                                )
                    btnChat = gr.Button("Generate",variant="primary",size="sm")
                    # btnChat = gr.Button(value="Generate",variant="primary",size="sm",elem_id="submit")
            with gr.Accordion("▼ Data Base settings", open=False) as more_settings:
                # infoLabel = gr.Label(value="Local temporary vector store")
                with gr.Accordion("> Local temporay vector store settings", open=False):
                    with gr.Row():
                        with gr.Column():
                            embedding_model_used = gr.Textbox(
                                        placeholder="Embedding model used to create vector store",
                                        label="Embedding model used to create vector store",
                                        value = "None",
                                        lines=1,
                                        interactive=False
                                        # scale = 5
                                    )
                        with gr.Column():
                            number_search = gr.Number(label="Number of chunks of searching",value=0,interactive=False)
                with gr.Accordion("> Self deployed vector database settings", open=False):
                    search_url = gr.Textbox(
                                placeholder="Set url for your self-deployed database searching, e.g. http://{IP}:{PORT}/search",
                                label="Url for your self-deployed database searching",
                                lines = 1,
                            )
                    json_input = gr.Textbox(placeholder="Search parameters as string template. e.g \n{\"query\":{input},\"num_docs\": 5} \nNOTE:make sure \"input\" as key for format.",label="JSON Input for the search",lines=4)

                with gr.Row():
                        with gr.Column():
                            retrieval_db = gr.Dropdown(
                                                        choices=['None'], 
                                                        value="None", 
                                                        label="Retrieval with below db, None to skip retrieval",
                                                        # scale = 5
                                                        interactive=True
                                                        )
                        with gr.Column():
                            reranker_model = gr.Dropdown(
                                                        choices=[], 
                                                        value="None", 
                                                        label="Reranker model, None to skip reranker",
                                                        # scale = 5
                                                        interactive=False
                                                        )
                        with gr.Column():
                            number_reranker = gr.Number(label="Number of chunks after reranker",value=3,interactive=False)
                     
            with gr.Row():
                with gr.Column(variant='panel',scale=1):
                    api_model = gr.Dropdown(
                                    choices=[], 
                                    value="meta/llama3-70b-instruct", 
                                    label="Available Models",
                                    # scale = 5
                                    )         
                    insertModeltxt = gr.Textbox(
                            placeholder="Model name in API catalog",
                            label="Model name not in the dropdown list",
                            lines=1
                            # scale = 5
                        )

                    insertModelBtn = gr.Button(value="Insert the model into list",
                                               variant="primary",
                                               interactive=False,
                                               size="sm")
                with gr.Column(variant='panel',scale=2):
                    system_prompt = gr.Textbox(
                            placeholder="You can define your system prompt for LLM (can be empty).\n Reset it to remove system prompt for backend",
                            label="Type an system prompt",
                            lines = 5,
                            # scale = 20
                        )
                    btnResetSysPrompt = gr.Button(value="Reset Defined System Prompt", variant='primary',interactive = True,size="sm")
                with gr.Column(variant="panel",scale=2):
                    few_shot_examples = gr.Textbox(
                                placeholder="Add some examples for generation with \n U: ...\n A: ...\n \n NOTE: examples must start with U: and A:",
                                lines=5,
                                label="Type examples here",
                                # scale = 10
                            )
                    btnResetExamples = gr.Button(value="Reset Defined Few-Shot Examples", variant='primary',interactive = True,size="sm")
            with gr.Accordion("▼ Show more settings", open=False) as more_settings:
                    temperature = gr.Slider(0, 1, step=0.1,value=0.2, label="Temperature",show_label=True,interactive = True, info="The sampling temperature to use for text generation between 0 an 1]")
                    top_p = gr.Slider(0, 1, step=0.1,value=0.7, label="Top P",show_label=True,interactive = True, info="The top-p sampling mass used for text generation between 0 an 1")
                    max_tokens = gr.Slider(1, 2048, step=128,value=1024, label="Max tokens",show_label=True,interactive = True, info="The maximum number of tokens to generate in any given call between 1 an 2048")
                    base_url = gr.Textbox(
                                placeholder="Set base url for your self-host NIMs, http://{IP}:{PORT}/v1",
                                label="Set base url for your self-host NIMs",
                                lines = 1,
                                # scale = 3
                            )
            
              
            with gr.Row():
                btnUpdateYaml = gr.Button(value="Update Yaml based on UI settings", variant='primary',interactive = True, size="sm")

        with gr.Tab("DataBase"):
            with gr.Row():
                 url_sources = gr.Textbox(
                                    placeholder="Downladable pdf URL or Html URL, using comma for list input",
                                    # lines=2,
                                    label="Data source be inserted to Vector Store",
                                    interactive = True,
                                    # scale = 25,
                                )
            with gr.Row():
                upload_button = gr.UploadButton(
                            "Click to Upload Local PDFs", 
                            file_types=[".pdf"], 
                            file_count="multiple",
                            variant='primary',
                            size="sm"
                        )
            with gr.Row():
                file_output = gr.File(visible=False)

            loader = gr.HTML("""<div id="loader"></div>""",visible=False)       
            with gr.Row():
                with gr.Column():         
                    chunk_size = gr.Number(label="Chunk Size",value=1024,interactive=True)
                with gr.Column():   
                    overlap_size = gr.Number(label="Chunk Overlap size",value=150,interactive=True)
                with gr.Column():   
                    embedding_model = gr.Dropdown(
                                        choices=[], 
                                        value="nvidia/nv-embed-v1", 
                                        label="Embedding model",
                                        # scale = 5
                                        interactive=True
                                        )
                insert_to_db = gr.Button("Embedding and Insert",variant='primary',size="sm")
            # delete_button = gr.Button("Delete",variant='primary',size="sm")

        demo.load(get_chatnvidia_models, inputs=[], outputs=[api_model])
        demo.load(get_embedding_models, inputs=[], outputs=[embedding_model])
        demo.load(get_reranker_models, inputs=[], outputs=[reranker_model])
        demo.load(get_api_model_parameters, [api_model,few_shot_examples], [system_prompt,temperature,top_p,max_tokens,few_shot_examples])
        demo.load(get_vs_embedding_model,[],[embedding_model_used])
        demo.load(load_default_retrieval_db,None,[retrieval_db])
        demo.load(load_local_files,None,[file_output])

        insertModeltxt.change(update_insert_button,[insertModeltxt],[insertModelBtn])
        system_prompt.change(update_reset_button,[system_prompt],[btnResetSysPrompt])
        few_shot_examples.change(update_reset_fewshot_button,[few_shot_examples],[btnResetExamples])
        insertModelBtn.click(insert_model,[insertModeltxt],[api_model,insertModelBtn])
        file_output.delete(delete_file_from_local, None, [file_output])
        file_output.clear(clear_files, None, [file_output,retrieval_db,embedding_model_used,number_search])
        insert_to_db.click(show_loader,None, loader).then(embedding_files,[url_sources,embedding_model,chunk_size,overlap_size],[file_output,loader,embedding_model_used,number_search,retrieval_db])
        # form actions
        upload_button.upload(show_loader,None, loader).then(
            lambda files: upload_file(files), upload_button, [file_output,loader]
        )
        search_url.change(update_retrieval_db,[search_url],[retrieval_db])

        retrieval_db.change(update_reranker_settings,[retrieval_db],[reranker_model])
        reranker_model.change(update_rerank_size,[reranker_model],[number_reranker])
        embedding_model_used.change(update_search_size,[embedding_model_used],[number_search])

        tbInput.submit(ask_question, [tbInput, chatbot], [tbInput, chatbot], queue=False).then(
            stream_response, [chatbot,system_prompt,api_model,temperature,top_p,max_tokens,few_shot_examples,base_url,reranker_model,number_search,number_reranker,retrieval_db,search_url,json_input], [chatbot]
        )
        btnChat.click(ask_question, [tbInput, chatbot], [tbInput, chatbot], queue=False).then(
            stream_response, [chatbot,system_prompt,api_model,temperature,top_p,max_tokens,few_shot_examples,base_url,reranker_model,number_search,number_reranker,retrieval_db,search_url,json_input], [chatbot]
        )
        btnResetSysPrompt.click(lambda: None,None, system_prompt, queue=False)
        btnResetExamples.click(lambda: None,None, few_shot_examples, queue=False)
        btnUpdateYaml.click(update_yaml,[api_model,system_prompt,temperature,top_p,max_tokens,few_shot_examples],None)
        api_model.change(get_api_model_parameters,[api_model,few_shot_examples],[system_prompt,temperature,top_p,max_tokens,few_shot_examples])
        

    demo.queue(max_size=99).launch(
        server_name=UI_SERVER_IP, server_port=UI_SERVER_PORT, debug=False, share=False, inbrowser=True
    )
   

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=9002)
    main()
    
