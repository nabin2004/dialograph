from dataclasses import dataclass

@dataclass(frozen=True)
class Node:
    id: str 
    type: str 
    content: str 


