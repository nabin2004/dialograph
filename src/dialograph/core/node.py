import time
import math
import uuid

class Node:
    """
    Represents a node in the Dialograph with:
    - time-aware confidence decay
    - explicit forgetting score
    - optional persistence (never decays / never forgotten)
    """
    node_id: str
    node_type: str
    data: dict
    confidence: float
    forgetting_score: float
    created_at: float
    last_accessed: float
    persistent: bool

    def __init__(
        self,
        node_id: str,
        node_type: str,
        data: dict | None = None,
        confidence: float = 1.0,
        created_at: float | None = None,
        last_accessed: float | None = None,
        persistent: bool = False,
    ):
        self.node_id = node_id or str(uuid.uuid4())
        self.node_type = node_type
        self.data = data or {}
        self.confidence = confidence
        self.created_at = created_at or time.time()
        self.last_accessed = last_accessed or time.time()
        self.persistent = persistent

        # initialize forgetting score
        self.forgetting_score = self._compute_forgetting_score()

    def _compute_forgetting_score(self) -> float:
        """Internal helper to compute forgetting score."""
        if self.persistent:
            return math.inf
        confidence_clamped = max(0.0, min(1.0, self.confidence))
        return 1.0 - confidence_clamped

    def decay(self, decay_rate_per_second: float = 0.0001) -> float:
        """
        Time-aware exponential confidence decay.

        Args:
            decay_rate_per_second (float): fraction of confidence lost per second

        Returns:
            float: Updated confidence
        """
        if self.persistent:
            return self.confidence

        now = time.time()
        elapsed = now - self.last_accessed

        self.confidence *= (1.0 - decay_rate_per_second) ** elapsed
        self.last_accessed = now

        # keeps forgetting score in sync
        self.forgetting_score = self._compute_forgetting_score()
        return self.confidence

    def __str__(self):
        return (
            f"Node(node_id={self.node_id}, type={self.node_type}, "
            f"confidence={self.confidence:.4f}, forgetting_score={self.forgetting_score:.4f}, "
            f"persistent={self.persistent})"
        )
