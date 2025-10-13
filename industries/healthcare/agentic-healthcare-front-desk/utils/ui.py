from typing import Any, Dict, List, Tuple, Literal, Callable, Annotated, Literal, Optional
import uuid
import sys 
import os
import logging
import riva.client
import gradio as gr
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))
from utils import asr_utils, tts_utils 
from ui_assets.css.css import css, theme



def get_config_with_new_thread_id():
    thread_id = str(uuid.uuid4())
    config = {
        "configurable": {
            # Checkpoints are accessed by thread_id
            "thread_id": thread_id,
        }
    }
    return config

def launch_demo_ui(assistant_graph, server_port, NVIDIA_API_KEY, RIVA_ASR_FUNCTION_ID, RIVA_TTS_FUNCTION_ID, RIVA_API_URI):
    # Establish a connection to the Riva server
    _LOGGER = logging.getLogger()
    try:
        use_ssl = False
        metadata_asr = []
        metadata_tts = []
        if NVIDIA_API_KEY:
            use_ssl = True
            metadata_asr.append(("authorization", "Bearer " + NVIDIA_API_KEY))
            metadata_tts.append(("authorization", "Bearer " + NVIDIA_API_KEY))
        if RIVA_ASR_FUNCTION_ID:
            use_ssl = True
            metadata_asr.append(("function-id", RIVA_ASR_FUNCTION_ID))
        if RIVA_TTS_FUNCTION_ID:
            use_ssl = True
            metadata_tts.append(("function-id", RIVA_TTS_FUNCTION_ID))

        auth_tts = riva.client.Auth(None, use_ssl=use_ssl, uri=RIVA_API_URI, metadata_args=metadata_tts)
        auth_asr = riva.client.Auth(None, use_ssl=use_ssl, uri=RIVA_API_URI, metadata_args=metadata_asr)
        _LOGGER.info('Created riva.client.Auth success')
    except:
        _LOGGER.info('Error creating riva.client.Auth')

    global config 
    config = get_config_with_new_thread_id()

    def _print_event(event: dict, _printed: set, max_length=1500):
        return_print = ""
        current_state = event.get("dialog_state")
        if current_state:
            print("Currently in: ", current_state[-1])
            return_print += "Currently in: "
            return_print += current_state[-1]
            return_print += "\n"
        message = event.get("messages")
        latest_msg_chatbot = ""
        if message:
            if isinstance(message, list):
                message = message[-1]
            if message.id not in _printed:
                msg_repr = message.pretty_repr()
                msg_repr_chatbot = str(message.content)
                if len(msg_repr) > max_length:
                    msg_repr = msg_repr[:max_length] + " ... (truncated)"
                    msg_repr_chatbot = msg_repr_chatbot[:max_length] + " ... (truncated)"
                return_print += msg_repr
                latest_msg_chatbot = msg_repr_chatbot
                print(msg_repr)
                _printed.add(message.id)
        return_print += "\n"
        return return_print, latest_msg_chatbot

    def interact(query: str, chat_history: List[Tuple[str, str]], full_response: str):
        _printed = set()
        # example with a single tool call
        events = assistant_graph.stream(
            {"messages": ("user", query)}, config, stream_mode="values"
        )
        
        latest_response = ""
        for event in events:
            return_print, latest_msg =  _print_event(event, _printed)
            full_response += return_print
            if latest_msg != "":
                latest_response = latest_msg

        yield "", chat_history + [[query, latest_response]], full_response, latest_response

    def new_thread():
        global config
        config = get_config_with_new_thread_id()

    # RIVA auth
    asr_utils.asr_init(auth_asr)
    tts_utils.tts_init(auth_tts)

    with gr.Blocks(title = "Welcome to the Healthcare Contact Center", theme=theme, css=css) as demo:
        gr.Markdown("# Welcome to the Healthcare Contact Center")

        # session specific state across runs
        state = gr.State(value=asr_utils.ASRSession())
        

        with gr.Row(equal_height=True):
            chatbot = gr.Chatbot(label="Healthcare Contact Center Agent", elem_id="chatbot", show_copy_button=True)
            latest_response = gr.Textbox(label = "Latest Response", visible=False)
            full_response = gr.Textbox(label = "Full Response Log", visible=False, elem_id="fullresponsebox", lines=25)
    

        
        # input
        with gr.Row():
            with gr.Column(scale = 10):
                msg = gr.Textbox(label = "Input Query", show_label=True, placeholder="Enter text and press ENTER", container=False,)
        #with gr.Row():
            audio_mic = gr.Audio(
                    sources=["microphone"],
                    type="numpy",
                    scale = 2,
                    streaming=True,
                    visible=True,
                    label="Transcribe Audio Query",
                    show_label=False,
                    container=False,
                    elem_id="microphone",
            )
        # buttons
        with gr.Row():
            submit_btn = gr.Button(value="Submit")
            _ = gr.ClearButton([msg, chatbot], value="Clear UI")
            full_resp_show = gr.Button(value="Show Full Response")
            full_resp_hide = gr.Button(value="Hide Full Response", visible=False)
        with gr.Row():
            new_thread_btn = gr.Button(value="Clear Chat Memory")
        
        # RIVA dropdowns
        with gr.Accordion("ASR and TTS Settings"):
                with gr.Row():
                    asr_language_list = list(asr_utils.ASR_LANGS)
                    asr_language_dropdown = gr.components.Dropdown(
                        label="ASR Language", choices=asr_language_list, value=asr_language_list[0],
                    )
                    tts_language_list = list(tts_utils.TTS_MODELS)
                    tts_language_dropdown = gr.components.Dropdown(
                        label="TTS Language", choices=tts_language_list, value=tts_language_list[0],
                    )
                    all_voices = []
                    try:
                        for model in tts_utils.TTS_MODELS:
                            all_voices.extend(tts_utils.TTS_MODELS[model]['voices'])
                        default_voice = tts_utils.TTS_MODELS[tts_language_list[0]]['voices'][0]
                    except:
                        all_voices.append("No TTS voices available")
                        default_voice = "No TTS voices available"
                    tts_voice_dropdown = gr.components.Dropdown(
                        label="TTS Voice", choices=all_voices, value=default_voice,
                    )

        # TTS output box
        # visible so that users can stop or replay playback
        with gr.Row():
                output_audio = gr.Audio(
                    label="Synthesized Speech",
                    autoplay=True,
                    interactive=False,
                    streaming=True,
                    visible=True,
                    show_download_button=False,
                )



        # hide/show context
        def _toggle_full_response(btn: str) -> Dict[gr.component, Dict[Any, Any]]:
            if btn == "Show Full Response":
                out = [True, False, True]
            if btn == "Hide Full Response":
                out = [False, True, False]
            return {
                full_response: gr.update(visible=out[0]),
                full_resp_show: gr.update(visible=out[1]),
                full_resp_hide: gr.update(visible=out[2]),
            }

        full_resp_show.click(_toggle_full_response, [full_resp_show], [full_response, full_resp_show, full_resp_hide])
        full_resp_hide.click(_toggle_full_response, [full_resp_hide], [full_response, full_resp_show, full_resp_hide])

        msg.submit(interact, [msg, chatbot, full_response], [msg, chatbot, full_response, latest_response])
        submit_btn.click(interact, [msg, chatbot, full_response], [msg, chatbot, full_response, latest_response])

        new_thread_btn.click(new_thread, [],[])

        tts_language_dropdown.change(
            tts_utils.update_voice_dropdown, [tts_language_dropdown], [tts_voice_dropdown], api_name=False
        )

        audio_mic.start_recording(
            asr_utils.start_recording, [audio_mic, asr_language_dropdown, state], [msg, state], api_name=False,
        )
        audio_mic.stop_recording(asr_utils.stop_recording, [state], [state], api_name=False)
        audio_mic.stream(
            asr_utils.transcribe_streaming, [audio_mic, asr_language_dropdown, state], [msg, state], api_name=False
        )
        audio_mic.clear(lambda: "", [], [msg], api_name=False)

        
        latest_response.change(
            tts_utils.text_to_speech,
            [latest_response, tts_language_dropdown, tts_voice_dropdown],
            [output_audio],
            api_name=False,
        )

        # TODO: how to stop the audio 

    demo.queue().launch(
        server_name="0.0.0.0", 
        server_port=server_port,
        favicon_path="ui_assets/css/faviconV2.png",
        allowed_paths=[
            "ui_assets/fonts/NVIDIASansWebWOFFFontFiles/WOFF2/NVIDIASans_W_Rg.woff2",
            "ui_assets/fonts/NVIDIASansWebWOFFFontFiles/WOFF2/NVIDIASans_W_Bd.woff2",
            "ui_assets/fonts/NVIDIASansWebWOFFFontFiles/WOFF2/NVIDIASans_W_It.woff2",
        ]
    )