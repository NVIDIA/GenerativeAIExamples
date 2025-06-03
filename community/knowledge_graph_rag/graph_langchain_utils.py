# community/knowledge_graph_rag/graph_langchain_utils.py
import logging
from typing import Any, Dict, List, Optional, Tuple

from langchain_community.chains.graph_qa.base import GraphQAChain # Updated import
from langchain.chains.llm import LLMChain
from langchain_core.language_models.base import BaseLanguageModel
from langchain_core.prompts.prompt import PromptTemplate
from langchain_community.graphs import NetworkxEntityGraph # NetworkxEntityGraph from community
# Removed import for standalone get_entity_knowledge

# For compatibility with older langchain versions if BaseCallbackManager is used by GraphQAChain
try:
    from langchain_core.callbacks.manager import CallbackManagerForChainRun
except ImportError:
    from langchain.callbacks.manager import CallbackManagerForChainRun # This might also need community if version is very new


logger = logging.getLogger(__name__)

# Define a default prompt for the GPUGraphQAChain
DEFAULT_PROMPT_TEMPLATE = """
You are an expert Question/Answering system that is acting as a domain expert.
Use the following context to answer the question at the end.
If you don't know the answer, just say that you don't know, don't try to make up an answer.

Context:
{context}

Question: {question}
Helpful Answer:
"""
DEFAULT_PROMPT = PromptTemplate(
    input_variables=["context", "question"], template=DEFAULT_PROMPT_TEMPLATE
)

DEFAULT_ENTITY_EXTRACTION_TEMPLATE = """
You are an expert at identifying key entities from a user's question.
Extract all proper nouns and significant noun phrases from the question that could correspond to entities in a knowledge graph.
Return the entities as a comma-separated list. If no specific entities are found, return an empty string.

Question: {question}
Entities:
"""
DEFAULT_ENTITY_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["question"], template=DEFAULT_ENTITY_EXTRACTION_TEMPLATE
)


class NXCugraphEntityGraph(NetworkxEntityGraph):
    """Networkx entity graph index.
       Wraps a cugraph.MultiGraph object or a NetworkX graph intended for cugraph backend.
    """

    def __init__(self, graph: Any):
        """Initialize with a cugraph.MultiGraph or networkx.MultiDiGraph instance."""
        self.graph = graph


    def get_triples(self) -> List[Tuple[str, str, str]]:
        """Get all triples stored in the graph."""
        triples = []
        for u, v, data in self.graph.edges(data=True):
            # Assuming relation is stored in 'predicate' or 'relation_name' attribute of the edge
            relation = data.get('predicate', data.get('relation_name', ''))
            if relation: # Ensure there is a relation
                triples.append((str(u), str(relation), str(v)))
        return triples

    def add_triple(self, triple: Tuple[str, str, str]) -> None:
        """Add a triple to the graph."""
        # Ensure nodes exist
        if not self.graph.has_node(triple[0]):
            self.graph.add_node(triple[0])
        if not self.graph.has_node(triple[2]):
            self.graph.add_node(triple[2])
        # Add edge with relation type
        # Storing relation in 'predicate' for consistency with some notebook examples
        self.graph.add_edge(triple[0], triple[2], predicate=triple[1])

    def delete_triple(self, triple: Tuple[str, str, str]) -> None:
        """Delete a triple from the graph if it exists."""
        if self.graph.has_edge(triple[0], triple[2]):
            edges_to_remove = []
            # For MultiDiGraph, graph.edges() might return multiple edges if keys are different.
            # We need to check all edges between triple[0] and triple[2].
            if self.graph.is_multigraph():
                for u, v, key, data in self.graph.edges(nbunch=[triple[0]], data=True, keys=True):
                    if u == triple[0] and v == triple[2] and data.get('predicate') == triple[1]:
                        edges_to_remove.append((u,v,key))
                for u,v,key in edges_to_remove:
                    self.graph.remove_edge(u,v,key=key)
            else: # Not a multigraph
                # Check if the specific edge (based on predicate) exists
                data = self.graph.get_edge_data(triple[0], triple[2])
                if data and data.get('predicate') == triple[1]:
                     self.graph.remove_edge(triple[0], triple[2])


    def get_number_of_nodes(self) -> int:
        """Returns the number of nodes in the graph"""
        return self.graph.number_of_nodes()

    def get_number_of_edges(self) -> int:
        """Returns the number of edges in the graph"""
        return self.graph.number_of_edges()

    def get_neighbors(self, node: str, relationship_type: Optional[str] = None) -> List[str]:
        """Get neighbors of a node, optionally filtered by relationship type."""
        neighbors = set()
        if self.graph.has_node(node):
            # Iterate over outbound and inbound edges if graph is directed
            # For NetworkX MultiDiGraph
            if self.graph.is_directed():
                for u, v, data in self.graph.out_edges(node, data=True):
                    relation = data.get('predicate', data.get('relation_name', ''))
                    if relationship_type is None or relation == relationship_type:
                        neighbors.add(str(v))
                for u, v, data in self.graph.in_edges(node, data=True):
                    relation = data.get('predicate', data.get('relation_name', ''))
                    if relationship_type is None or relation == relationship_type:
                        neighbors.add(str(u))
            else: # Undirected graph
                 for _, neighbor_node, data in self.graph.edges(node, data=True):
                    relation = data.get('predicate', data.get('relation_name', ''))
                    if relationship_type is None or relation == relationship_type:
                        neighbors.add(str(neighbor_node))
        return list(neighbors)

    def get_entity_knowledge(self, entity: str, depth: int = 1) -> List[str]:
        """Get information about an entity by calling the parent's method."""
        # Assuming the parent NetworkxEntityGraph (from langchain_community.graphs)
        # now has this method, or provides similar functionality.
        # The original NetworkxEntityGraph had a get_entity_knowledge method.
        return super().get_entity_knowledge(entity, depth=depth)


class GPUGraphQAChain(GraphQAChain):
    """Question-answering chain over a graph, potentially using GPU-accelerated components."""

    def __init__(
        self,
        graph: NXCugraphEntityGraph,
        qa_chain: LLMChain,
        entity_extraction_chain: LLMChain,
        **kwargs: Any,
    ):
        """Initialize with graph, QA chain, and entity extraction chain."""
        super().__init__(
            graph=graph,
            qa_chain=qa_chain,
            entity_extraction_chain=entity_extraction_chain,
            **kwargs
        )

    @classmethod
    def from_llm(
        cls,
        llm: BaseLanguageModel,
        graph: NXCugraphEntityGraph, # Expecting our custom graph wrapper
        qa_prompt: PromptTemplate = DEFAULT_PROMPT, # Renamed for clarity
        entity_extraction_prompt: PromptTemplate = DEFAULT_ENTITY_EXTRACTION_PROMPT,
        **kwargs: Any,
    ) -> "GPUGraphQAChain":
        """Initialize from LLM, creating both QA and entity extraction chains."""
        qa_chain = LLMChain(llm=llm, prompt=qa_prompt)
        entity_extraction_chain = LLMChain(llm=llm, prompt=entity_extraction_prompt)
        return cls(
            graph=graph,
            qa_chain=qa_chain,
            entity_extraction_chain=entity_extraction_chain,
            **kwargs
        )

    def _call(
        self,
        inputs: Dict[str, Any],
        run_manager: Optional[CallbackManagerForChainRun] = None,
    ) -> Dict[str, str]:
        """Extract entities from query, get relations from graph, then answer query."""
        _run_manager = run_manager or CallbackManagerForChainRun.get_noop_manager()
        callbacks = _run_manager.get_child()

        query = inputs[self.input_key]

        # Heuristic to extract potential entities from the query for context gathering
        # This is a simplified approach. A more robust solution might involve an NER step.
        potential_entities = [word for word in query.split() if word[0].isupper()] # Basic check for proper nouns

        # Gather context from the graph based on potential entities
        # Or use a broader context if no specific entities are identified
        context_triples_str_list = []
        if potential_entities:
            for entity in potential_entities:
                # Check if entity exists as a node (case-sensitive)
                # The graph nodes are expected to be strings (entity names or IDs)
                if self.graph.graph.has_node(entity):
                     entity_knowledge = self.graph.get_entity_knowledge(entity, depth=1)
                     context_triples_str_list.extend(entity_knowledge)
                # Try case-insensitive match if direct match fails (example)
                # This requires iterating nodes if entity names are not normalized.
                # For now, we assume entity names in query match graph nodes.

        # If no specific entity context, or to augment, get some general graph triples
        if not context_triples_str_list:
            # Fallback to a limited number of general graph triples if no entity-specific context
            all_triples = self.graph.get_triples()
            context_triples_str_list = [f"({s}, {r}, {o})" for s, r, o in all_triples[:20]] # Limit context

        # Remove duplicates while preserving order (Python 3.7+)
        context_str = "\n".join(list(dict.fromkeys(context_triples_str_list)))

        if not context_str:
             context_str = "No relevant information found in the graph for this query."


        # QA over the graph context
        result = self.qa_chain(
            {"question": query, "context": context_str},
            callbacks=callbacks, # Pass callbacks to the qa_chain
        )
        return {self.output_key: result[self.qa_chain.output_key]}
