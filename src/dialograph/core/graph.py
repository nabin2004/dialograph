import networkx as nx
import json
import pickle

class Dialograph:
    """
    A time-aware directed multigraph for tracking state changes over time.
    Built on NetworkX's MultiDiGraph to support multiple edges between nodes.
    """
    
    def __init__(self):
        """Initialize an empty Dialograph with time tracking."""
        self.graph = nx.MultiDiGraph()
        self.time = 0
    
    def step(self):
        """
        Increment the internal time counter.
        Useful for tracking temporal evolution of the graph.
        """
        self.time += 1
        return self.time
    
    def add_node(self, node_id, **attrs):  #attrs any other attributes like label, value, status
        """
        Add a node to the graph with optional attributes.
        Automatically adds a timestamp of when the node was created.
        
        Args:
            node_id: Unique identifier for the node
            **attrs: Arbitrary keyword arguments to store as node attributes
        """
        attrs['created_at'] = self.time
        self.graph.add_node(node_id, **attrs)
    
    def add_edge(self, src, dst, **attrs):
        """
        Add an edge from src to dst with optional attributes.
        Automatically adds a timestamp of when the edge was created.
        Returns the key of the newly created edge.
        
        Args:
            src: Source node ID
            dst: Destination node ID
            **attrs: Arbitrary keyword arguments to store as edge attributes
            
        Returns:
            key: The unique key for this edge (important for multigraphs)
        """
        attrs['created_at'] = self.time
        key = self.graph.add_edge(src, dst, **attrs)
        return key
    
    def update_node(self, node_id, **attrs):
        """
        Update attributes of an existing node.
        Adds an 'updated_at' timestamp to track modifications.
        
        Args:
            node_id: ID of the node to update
            **attrs: Attributes to update or add
            
        Raises:
            ValueError: If the node doesn't exist
        """
        if node_id not in self.graph:
            raise ValueError(f"Node {node_id} does not exist in the graph")
        
        attrs['updated_at'] = self.time
        self.graph.nodes[node_id].update(attrs)
    
    def update_edge(self, src, dst, key, **attrs):
        """
        Update attributes of an existing edge identified by src, dst, and key.
        Adds an 'updated_at' timestamp to track modifications.
        
        Args:
            src: Source node ID
            dst: Destination node ID
            key: Edge key (MultiDiGraph can have multiple edges between same nodes)
            **attrs: Attributes to update or add
            
        Raises:
            ValueError: If the edge doesn't exist
        """
        if not self.graph.has_edge(src, dst, key):
            raise ValueError(f"Edge ({src}, {dst}, {key}) does not exist in the graph")
        
        attrs['updated_at'] = self.time
        self.graph.edges[src, dst, key].update(attrs)
    
    def get_node_state(self, node_id):
        """
        Retrieve all attributes of a node.
        
        Args:
            node_id: ID of the node
            
        Returns:
            dict: Dictionary of node attributes
            
        Raises:
            ValueError: If the node doesn't exist
        """
        if node_id not in self.graph:
            raise ValueError(f"Node {node_id} does not exist in the graph")
        
        return dict(self.graph.nodes[node_id])
    
    def get_edge_state(self, src, dst, key):
        """
        Retrieve all attributes of an edge.
        
        Args:
            src: Source node ID
            dst: Destination node ID
            key: Edge key
            
        Returns:
            dict: Dictionary of edge attributes
            
        Raises:
            ValueError: If the edge doesn't exist
        """
        if not self.graph.has_edge(src, dst, key):
            raise ValueError(f"Edge ({src}, {dst}, {key}) does not exist in the graph")
        
        return dict(self.graph.edges[src, dst, key])
    
    def save(self, path: str):
        """
        Save the Dialograph to a file.
        Uses pickle for complete serialization including the time state.
        
        Args:
            path: File path where the graph will be saved
        """
        data = {
            'graph': self.graph,
            'time': self.time
        }
        with open(path, 'wb') as f:
            pickle.dump(data, f)
    
    def load(self, path: str):
        """
        Load a Dialograph from a file.
        Restores both the graph structure and the time state.
        
        Args:
            path: File path from which to load the graph
        """
        with open(path, 'rb') as f:
            data = pickle.load(f)
        
        self.graph = data['graph']
        self.time = data['time']