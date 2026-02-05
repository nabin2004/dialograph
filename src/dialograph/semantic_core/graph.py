

from __unknown__ import SemanticEdge
class Dialograph:
    def __init__(self):
        self.semantic_nodes: Dict[str, SemanticNode] = {}
        self.semantic_edges: List[SemanticEdge] = []

        self.temporal_nodes: Dict[str, TemporalNodeState] = {}

    def add_node(self, node: SemanticNode):
        self.semantic_nodes[node.id] = node 
        self.temporal_nodes[node.id] = TemporalNodeState(
            node_id=node.id,
            created_at=datetime.now(),
            last_activated_at=datetime.now(),
            decay_score=1.0,
            confidence=1.0
        )

    def add_edge(self, edge: SemanticEdge):
        self.semantic_edges.append(edge)

    def activate(self, node_id: str, confidence: Optional[float] = None):
        state = self.temporal_nodes[node_id]
        state.last_activated_at = datetime.now()
        state.activation_count += 1
        state.decay_score = 1.0
        if confidence is not None:
            state.confidence = confidence

    def decay_all(self, lambda_: float = 0.01):
        now = datetime.now()
        for state in self.temporal_nodes.values():
            dt = (now - state.last_activated_at).total_seconds()
            state.decay_score *= exp(-lambda_ * dt)
