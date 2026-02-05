from dataclasses import dataclass

@dataclass(frozen=True)
class SemanticEdge:
    source: str 
    target: str 
    relation_type: str 
