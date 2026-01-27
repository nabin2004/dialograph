import networkx as nx
import pickle
import time
from typing import Dict, List, Tuple, Optional

from dialograph.core.node import Node
from dialograph.core.edge import Edge


class Dialograph:
    """
    Time-aware directed multigraph for dialog memory and reasoning.

    - Nodes store beliefs and memory availability (Ebbinghaus)
    - Edges store learned structural relations
    - NetworkX handles topology only
    """

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.nodes: Dict[str, Node] = {}
        self.edges: Dict[str, Edge] = {}

    # ------------------------------------------------------------------
    # Node handling
    # ------------------------------------------------------------------

    def add_node(self, node: Node):
        if node.node_id in self.nodes:
            raise ValueError(f"Node {node.node_id} already exists")

        self.nodes[node.node_id] = node
        self.graph.add_node(node.node_id)

    def get_node(self, node_id: str) -> Node:
        return self.nodes[node_id]

    # ------------------------------------------------------------------
    # Edge handling
    # ------------------------------------------------------------------

    def add_edge(self, edge: Edge):
        if edge.edge_id in self.edges:
            raise ValueError(f"Edge {edge.edge_id} already exists")

        if edge.source_node_id not in self.nodes:
            raise ValueError("Source node does not exist")

        if edge.target_node_id not in self.nodes:
            raise ValueError("Target node does not exist")

        self.edges[edge.edge_id] = edge

        self.graph.add_edge(
            edge.source_node_id,
            edge.target_node_id,
            key=edge.edge_id,
        )

    def get_edge(self, edge_id: str) -> Edge:
        return self.edges[edge_id]

    def get_edges(self, src: str, dst: str) -> List[Edge]:
        if not self.graph.has_edge(src, dst):
            return []

        return [
            self.edges[key]
            for key in self.graph[src][dst].keys()
        ]

    def outgoing_edges(self, node_id: str) -> List[Edge]:
        edges = []
        for _, dst, key in self.graph.out_edges(node_id, keys=True):
            edges.append(self.edges[key])
        return edges

    # ------------------------------------------------------------------
    # Retrieval (Tier 1: neighbors)
    # ------------------------------------------------------------------

    def retrieve_neighbors(
        self,
        source_node_id: str,
        top_k: int = 5,
        context_match_fn=None,
        now: Optional[float] = None,
    ) -> List[Tuple[float, Node, Edge]]:
        """
        Retrieve neighboring nodes scored by:
        node.confidence × node.availability × edge.importance
        """
        now = now or time.time()
        results = []

        for edge in self.outgoing_edges(source_node_id):
            node = self.get_node(edge.target_node_id)

            context_match = (
                context_match_fn(node) if context_match_fn else 1.0
            )

            score = (
                node.retrieval_score(now)
                * edge.importance_score(now)
                * context_match
            )

            results.append((score, node, edge))

        results.sort(key=lambda x: x[0], reverse=True)
        return results[:top_k]

    # ------------------------------------------------------------------
    # Temporal views
    # ------------------------------------------------------------------

    def subgraph_at_time(self, t: float) -> nx.MultiDiGraph:
        """
        Snapshot of graph structure at time t.
        """
        g = nx.MultiDiGraph()

        for node in self.nodes.values():
            if node.created_at <= t:
                g.add_node(node.node_id)

        for edge in self.edges.values():
            if edge.created_at <= t:
                g.add_edge(
                    edge.source_node_id,
                    edge.target_node_id,
                    key=edge.edge_id,
                )

        return g

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: str):
        """
        Persist full dialograph state.
        """
        data = {
            "nodes": self.nodes,
            "edges": self.edges,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str):
        """
        Load dialograph state.
        """
        with open(path, "rb") as f:
            data = pickle.load(f)

        self.nodes = data["nodes"]
        self.edges = data["edges"]

        self.graph = nx.MultiDiGraph()
        for node_id in self.nodes:
            self.graph.add_node(node_id)

        for edge in self.edges.values():
            self.graph.add_edge(
                edge.source_node_id,
                edge.target_node_id,
                key=edge.edge_id,
            )
