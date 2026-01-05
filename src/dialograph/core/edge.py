from dataclasses import dataclass, field
import time


@dataclass
class EdgeState:
    relation: str                 # e.g. "supports", "elicits", "contradicts"
    strength: float               # confidence / weight of relation
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)

    def touch(self):
        """
        Update usage timestamp when edge is traversed.
        """
        pass 

    def decay(self, rate: float = 0.01):
        """
        Decay edge strength over time.
        """
        pass 

    def reinforce(self, amount: float = 0.1):
        """
        Strengthen edge after successful use.
        """
        pass 