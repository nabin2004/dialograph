import networkx as nx

class Dialograph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()

    def add_node(self, node_id, **attrs):
        self.graph.add_node(node_id, **attrs)

    def add_edge(self, src, dst, **attrs):
        self.graph.add_edge(src, dst, **attrs)
