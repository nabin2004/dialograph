import networkx as nx


class Dialograph:
    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.time = 0

    def step(self):
        pass 

    def add_node(self, node_id, **attrs):
        pass

    def add_edge(self, src, dst, **attrs):
        pass

    def update_node(self, node_id, **attrs):
        pass

    def add_edge(self, src, dst, **attrs):
        pass

    def update_edge(self, src, dst, key, **attrs):
        pass

    def get_node_state(self, node_id):
        pass

    def get_edge_state(self, src, dst, key):
        pass

    def save(self, path: str):
        pass

    def load(self, path: str):
        pass
