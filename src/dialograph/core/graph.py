import networkx as nx
import json
import pickle
from dialograph.core.node import Node
from dialograph.core.edge import Edge

class Dialograph:
    """
    A time-aware directed multigraph for tracking state changes over time.
    Built on NetworkX's MultiDiGraph to support multiple edges between nodes.
    """
    
    def __init__(self):
        """Initialize an empty Dialograph with time tracking."""
        self.graph = nx.MultiDiGraph()
        
        self.nodes: dict[str, Node] = {}
        self.edges: dict[str, Edge] = {}

        self.time = 0
    
    def step(self):
        """
        Increment the internal time counter.
        Useful for tracking temporal evolution of the graph.
        """
        self.time += 1
        return self.time
    
    def add_node(self, node, **attrs):  #attrs any other attributes like label, value, status
        if node.node_id in self.nodes:
            raise ValueError(f"Node {node.node_id} already exists in the graph")
        self.nodes[node.node_id] = node
        self.graph.add_node(node.node_id)

    def get_node(self, node_id: str):
        return self.nodes[node_id]

    def add_edge(self, edge):
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
            key=edge.edge_id
        )

    def get_edges(self, src: str, dst: str):
        result = []
        if self.graph.has_edge(src, dst):
            for key in self.graph[src][dst]:
                result.append(self.edges[key])
        return result

    def subgraph_at_time(self, t: float):
        g = nx.MultiDiGraph()

        for node in self.nodes.values():
            if node.created_at <= t:
                g.add_node(node.node_id)

        for edge in self.edges.values():
            if edge.created_at <= t:
                g.add_edge(
                    edge.source_node_id,
                    edge.target_node_id,
                    key=edge.edge_id
                )
        return g

    def update_node(self, node):
        pass 

    def update_edge(self, edge):
        pass

    def save(self, path: str):
        data = {
            "nodes": self.nodes,
            "edges": self.edges,
            "time": self.time,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load(self, path: str):
        pass 