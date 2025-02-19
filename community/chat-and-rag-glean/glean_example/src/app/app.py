import logging

import gradio as gr
from glean_example.src.app.css import css, theme
from glean_example.src.agent import agent
from typing import List
from pathlib import Path
from gradio_log import Log
import os

log_file = "/tmp/gradio_log.txt"
if Path(log_file).exists:
    os.remove(log_file)
    
Path(log_file).touch()

ch = logging.FileHandler(log_file)
ch.setLevel(logging.DEBUG)


logger = logging.getLogger("gradio_log")
logger.setLevel(logging.DEBUG)
for handler in logger.handlers:
    logger.removeHandler(handler)
logger.addHandler(ch)


def convert_to_langchain_history(history: List):
    if len(history) < 1:
        return []

    langchain_history = []
    for msg_pair in history:
        msg1, msg2 = msg_pair
        if msg1 == "user":
            langchain_history.append(("user", msg2))
        if msg1 != "user":
            langchain_history.append(("system", msg2))

    return langchain_history


def agent_predict(msg: str, history: List) -> str:
    history = convert_to_langchain_history(history)

    history.append(("user", msg))
    response = agent.invoke(input={"messages": history})
    return response["messages"][-1][1]


chatbot = gr.Chatbot(label="Ask away!", elem_id="chatbot", show_copy_button=True)

with gr.Blocks(theme=theme, css=css) as chat:
    chat_interface = gr.ChatInterface(
        fn=agent_predict,
        chatbot=chatbot,
        title="ACME Corp Help Agent",
        autofocus=True,
        fill_height=True,
    )

    Log(log_file=log_file)

# chat_interface.render()

if __name__ == "__main__":
    chat.queue().launch(share=False)
