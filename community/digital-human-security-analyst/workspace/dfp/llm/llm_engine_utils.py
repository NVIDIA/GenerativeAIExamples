from morpheus.llm import LLMEngine
from morpheus.llm import LLMContext
from morpheus.llm.nodes.extracter_node import ExtracterNode
from morpheus.llm.nodes.llm_generate_node import LLMGenerateNode
from morpheus.llm.nodes.prompt_template_node import PromptTemplateNode
from morpheus.llm.services.llm_service import LLMService
from morpheus.llm.services.nemo_llm_service import NeMoLLMService
from morpheus.llm.task_handlers.simple_task_handler import SimpleTaskHandler


from dfp.llm.nim_task_handler import NIMTaskHandler
# from dfp.llm.nim_llm_service import NIMChatService
from dfp.llm.retriever_context_node import RetrieverContextNode
# from dfp.llm.nemo_retriever_client import RetrieverClient
from dfp.llm.chat_nvidia_service import ChatNVIDIAChatService



def build_engine_llm_service(prompt_template: str, llm_service: str = "NIM", output_column:str = "response"):

    llm_service_cls: type[LLMService] = None

    if llm_service == "NemoLLM":
        llm_service_cls = NeMoLLMService
        model_name = "gpt-43b-002"
    elif llm_service == "NIM":
        llm_service_cls = ChatNVIDIAChatService 
        model_name = "meta/llama-3.1-405b-instruct"
        base_url =  "https://integrate.api.nvidia.com/v1" 
    else:
        raise ValueError(f"Invalid LLM service: {llm_service}")

    service = llm_service_cls()
    my_llm_client = service.get_client(model_name=model_name, base_url=base_url)
    
    engine = LLMEngine()

    engine.add_node("extracter", node=ExtracterNode())

    engine.add_node("prompts",
                    inputs=['/extracter'],
                    node=PromptTemplateNode(template=prompt_template, template_format="jinja"))

    engine.add_node("completion", inputs=["/prompts"], node=LLMGenerateNode(llm_client=my_llm_client))
    
    if output_column != "response":
        engine.add_task_handler(inputs=["/completion"], handler=NIMTaskHandler(output_col_name=output_column))
    else:
        engine.add_task_handler(inputs=["/completion"], handler=SimpleTaskHandler())

    return engine

def build_engine_rag_context(retriever_client_cyber_enrichment):
    engine = LLMEngine()
    

    engine.add_node("query_extracter", node=ExtracterNode())

    engine.add_node("rag_contexts",
                    inputs=['/query_extracter'],
                    node=RetrieverContextNode(retriever_client_cyber_enrichment))

    engine.add_task_handler(inputs=["/rag_contexts"], handler=NIMTaskHandler(output_col_name="rag_context"))

    return engine