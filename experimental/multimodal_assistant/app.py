from pages.knowledge_base import knowledge_base, uploaded_file_paths, change_config
from pages.multimodel_assistant import multimodal_assistant, create_conv, create_document_section, query_embedder, retriever
from taipy.gui import Gui, State, notify


def on_init(state):
    """Called when the user first opens the page"""
    state.conv.update_content(state, "")
    state.document_section.update_content(state, "")
    with state: 
        state['Multimodal_Assistant'].messages_dict = {}
        state['Multimodal_Assistant'].messages = [{"role": "assistant", "style": "assistant_message", "content": "Hi, what can I help you with?"}]
        state.conv.update_content(state, create_conv(state))
        state.document_section.update_content(state, create_document_section(state))

def on_exception(state: State, function_name: str, ex: Exception):
    """Called when an exception is raised in a function"""
    notify(state, "e", f"A problem occured in {function_name}")
    print(f"Exception in {function_name}:\n{ex}")
    notify(state, 'error', 'Reinitializing application in an attempt to solve the issue')
    change_config(state)
    on_init(state)

pages = {
    "Multimodal_Assistant": multimodal_assistant,
    "Knowledge_Base": knowledge_base
}

if __name__ == "__main__":
    gui = Gui(pages=pages)
    conv = gui.add_partial("") # conv is the chat between the assistant and the user
    document_section = gui.add_partial("")
    gui.run(title="Multimodal Assistant",
            dark_mode=False,
            debug=True,
            host='0.0.0.0',
            margin="0px")