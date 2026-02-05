from dataclasses import dataclass

@dataclass(frozen=True)
class SemanticNode:
    id: str 
    type: str 
    content: str 


