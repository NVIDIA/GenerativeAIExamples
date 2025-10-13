"""
This file overwrites a number of functions within classes from Langchain.
This allows us to use the gpu-enabled nx-cugraph class.
"""

from langchain.chains import GraphQAChain
from langchain_community.graphs.networkx_graph import NetworkxEntityGraph, get_entities
from typing import Optional, Any, List
import nx_cugraph as nxcg
import re

"""
We define the NXCugraphEntityGraph class that overwrides the NetworkxEntityGraph class.
This is mainly so that we dont get errors with our QA chain.
"""
class NXCugraphEntityGraph(NetworkxEntityGraph):

    def __init__(self, graph: Optional[Any] = None) -> None:

        # Call the parent constructor.
        super().__init__()

        """Create a new graph."""
        if graph is not None:
            if not isinstance(graph, nxcg.DiGraph):
                raise ValueError("Passed in graph is not of correct shape")
            self._graph = graph
        else:
            self._graph = nxcg.DiGraph()

    def get_entity_knowledge(self, entity: str, depth: int = 1) -> List[str]:
        """Get information about an entity."""

        entity = re.sub(r'[^a-zA-Z0-9_ ,\n]', '', entity).replace(" ","_")
        
        if not self._graph.has_node(entity):
            return []

        results = []
        for src, sink in nxcg.bfs_edges(self._graph, entity, depth_limit=depth):
            relation = self._graph[src][sink]
            results.append(f"source: {src} sink: {sink} detail: {relation}")
        print(f"Query edges: {results}")
        return results
    
"""
We define the GpuGraphQAChain, which replaces the GraphQAChain from langchain.
Mainly this just allows us to use NXCugraphEntityGraphs instead of NetworkxEntityGraphs.
"""

from typing import Any, Dict, List, Optional
from langchain.chains.llm import LLMChain
from pydantic import Field
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import BasePromptTemplate
from langchain_core.callbacks.manager import CallbackManagerForChainRun

class GPUGraphQAChain(GraphQAChain):

    graph: NXCugraphEntityGraph = Field(exclude=True)

    @classmethod
    def from_llm(
        cls,
        llm: BaseLanguageModel,
        graph: NXCugraphEntityGraph,
        verbose: bool = True,
        **kwargs: Any
    ) -> 'GPUGraphQAChain': 

        gqac = super().from_llm(llm=llm, graph=graph, verbose=verbose, **kwargs)

        gqac.graph = graph

        return gqac