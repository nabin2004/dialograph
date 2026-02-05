# Semantic Layer
@dataclass(frozen=True)
class SemanticNode:
    id: str 
    type: str # Concept, Skill, Question, Misconception, Answer, Hint, Feedback
    content: str 

@dataclass(frozen=True)
class SemanticEdge:
    source: str 
    target: str 
    relation_type: str # prerequisite_of, explains, contradicts, reinforces, derived_from 


## Temporal Layer

@dataclass 
class TemporalNodeState:
    node_id: str 
    created_at: datetitme 
    last_activation_at: datetime 
    activation_count: int 
    decay_score: float 
    confidence: float 


## Graph Container
class Dialograph:
    def __init__(self):
        self.semantic_nodes = {}
        self.semantic_edges = []

        self.temporal_nodes = {}
        self.temporal_edges = {}

        self.policies = []

    def activate_node(self, node_id: str):
        state = self.temporal_nodes[node_id]
        state.last_activated_at = now()
        state.activation_count += 1
        state.decay_score = 1.0

    def decay_all(self):
        for state in self.temporal_nodes.values():
            dt = now() - state.last_activated_at
            state.decay_score *= exp(-LAMBDA * dt)


class DecisionPolicy:
    def applies(self, graph: Dialograph) -> bool:
        raise NotImplementedError

    def decide(self, graph: Dialograph) -> str:
        raise NotImplementedError

"""
Nodes = what exists
Temporal state = what happened
Policies = what to do
LLM = how to say it
"""

##############################################
# Decision Policy
#############################################

# when condition X happens
class GraphPattern:
    pass 

## You should do Y rather than Z
preferred_action = Y
avoided_action = Z

# because B 
explain()


##########################################
@dataclass
class DeclarativePolicy:
    id: str
    when: "Condition"
    do: str
    rather_than: str
    because: str
    priority: int = 50
    confidence: float = 1.0


class Condition:
    def evaluate(self, graph) -> list[dict]:
        """
        Returns matches. Empty list = condition not met.
        """
        raise NotImplementedError

class LowConfidence(Condition):
    def __init__(self, threshold: float):
        self.threshold = threshold

    def evaluate(self, graph):
        matches = []
        for node_id, state in graph.temporal_nodes.items():
            if state.confidence < self.threshold:
                matches.append({
                    "node_id": node_id,
                    "confidence": state.confidence
                })
        return matches
