from pages.knowledge_base import knowledge_base
from pages.multimodel_assistant import multimodal_assistant, create_conv, query_embedder, retriever
from taipy.gui import Gui 


def on_init(state):
    state.conv.update_content(state, create_conv(state))

pages = {
    "Multimodal_Assistant": multimodal_assistant,
    "Knowledge_Base": knowledge_base
}

if __name__ == "__main__":
    gui = Gui(pages=pages)
    conv = gui.add_partial("")
    gui.run(title="Multimodal Assistant",
            dark_mode=False,
            debug=True,
            host='0.0.0.0',
            margin="0px")