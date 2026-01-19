import time
import math
import uuid

class Node:
    """
    Represents a node in the Dialograph with:
    Attributes:
        node_id (str): Unique identifier for the node.
        node_type (str): Type/category of the node.
        data (dict): Content or information stored in the node.
        confidence (float): Confidence score of the node's relevance/usefulness.
        created_at (float): Timestamp when the node was created.
        last_accessed (float): Timestamp when the node was last accessed.
        persistent (bool): Whether the node is persistent (not subject to forgetting).

    Methods:
        confidence_decay(decay_rate_per_second: float) -> float:
            Applies time-aware exponential decay to the node's confidence score.
    """
    node_id: str
    node_type: str
    data: dict
    confidence: float
    # forgetting_score: float
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

        self.pre_requisites: set[str] = set()
        self.metadata: dict = {}

    # def _compute_forgetting_score(self) -> float:
    #     """Internal helper to compute forgetting score."""
    #     if self.persistent:
    #         return math.inf
    #     confidence_clamped = max(0.0, min(1.0, self.confidence))
    #     return 1.0 - confidence_clamped

    def confidence_decay(self, decay_rate_per_second: float = 0.0001) -> float:
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
        # self.forgetting_score = self._compute_forgetting_score()
        return self.confidence

    def __str__(self):
        return (
            f"Node(node_id={self.node_id}, type={self.node_type}, "
            f"confidence={self.confidence:.4f}, "
            f"persistent={self.persistent})"
        )
