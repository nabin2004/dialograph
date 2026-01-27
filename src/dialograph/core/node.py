import time
import math
import uuid
from typing import Optional


class Node:
    """
    Represents a node in the Dialograph.

    Conceptual separation:
    - confidence: epistemic reliability (does NOT decay with time)
    - availability: memory accessibility (Ebbinghaus forgetting curve)
    - memory_strength: controls forgetting speed, grows with reinforcement
    """

    def __init__(
        self,
        node_id: Optional[str],
        node_type: str,
        data: Optional[dict] = None,
        confidence: float = 1.0,
        created_at: Optional[float] = None,
        last_accessed: Optional[float] = None,
        persistent: bool = False,
        memory_strength: float = 3600.0,  # baseline: ~1 hour
    ):
        self.node_id = node_id or str(uuid.uuid4())
        self.node_type = node_type
        self.data = data or {}

        # Epistemic belief strength (does NOT decay with time)
        self.confidence = max(0.0, min(1.0, confidence))

        # Time tracking
        self.created_at = created_at or time.time()
        self.last_accessed = last_accessed or self.created_at

        # Forgetting control
        self.memory_strength = max(memory_strength, 1.0)
        self.persistent = persistent

        # Optional graph helpers
        self.pre_requisites: set[str] = set()
        self.metadata: dict = {}

    # ------------------------------------------------------------------
    # Ebbinghaus forgetting curve
    # ------------------------------------------------------------------

    def availability(self, now: Optional[float] = None) -> float:
        """
        Memory availability based on Ebbinghaus forgetting curve.

        retention(t) = exp(-t / S)

        where:
        - t = time since last access
        - S = memory_strength
        """
        if self.persistent:
            return 1.0

        now = now or time.time()
        elapsed = max(0.0, now - self.last_accessed)

        S = max(self.memory_strength, 1e-6)
        return math.exp(-elapsed / S)

    # ------------------------------------------------------------------
    # Reinforcement / spaced repetition
    # ------------------------------------------------------------------

    def reinforce(self, amount: float = 0.2):
        """
        Reinforce memory via spaced repetition.

        Effects:
        - resets forgetting timer
        - increases memory_strength (slower future forgetting)
        - slightly boosts confidence (bounded)
        """
        now = time.time()
        self.last_accessed = now

        # Sublinear growth of memory strength
        growth = max(0.0, amount)
        self.memory_strength *= (1.0 + growth)

        # Hard cap to prevent immortal memories (~1 week)
        self.memory_strength = min(self.memory_strength, 7 * 24 * 3600)

        # Optional small confidence recovery
        self.confidence = min(1.0, self.confidence + 0.05)

    # ------------------------------------------------------------------
    # Retrieval helper
    # ------------------------------------------------------------------

    def retrieval_score(self, now: Optional[float] = None) -> float:
        """
        Score used during retrieval:
        belief reliability × memory availability
        """
        return self.confidence * self.availability(now)

    # ------------------------------------------------------------------
    # Debug / display
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"Node("
            f"id={self.node_id}, "
            f"type={self.node_type}, "
            f"confidence={self.confidence:.3f}, "
            f"availability={self.availability():.3f}, "
            f"memory_strength={self.memory_strength:.1f}, "
            f"persistent={self.persistent}"
            f")"
        )
