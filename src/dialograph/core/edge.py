from dataclasses import dataclass, field
import time
import uuid
from typing import Dict, Optional, Literal

RelationType = Literal[
    "supports",
    "contradicts",
    "elicits",
    "influences",
    "depends_on",
]

EmotionType = Literal[
    "happy",
    "surprised",
    "neutral",
    "sad",
    "angry",
    "anxious",
    "excited",
]


@dataclass
class Edge:
    """
    Represents a directed relationship between two nodes.

    Conceptual model:
    - strength: learned structural importance (does NOT decay with time)
    - recency: availability based on recent usage
    - emotional_charge: temporary modulation of importance
    """

    edge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str = field(default="")
    target_node_id: str = field(default="")

    relation: RelationType = "supports"

    # Learned importance (structural, long-term)
    strength: float = 0.5  # [0.0, 1.0]

    # Time tracking
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)

    # Emotional modulation
    emotional_charge: float = 0.0  # [-1.0, +1.0]

    # Reinforcement handling
    pending_reinforcement: Optional[float] = None

    metadata: Dict = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def __post_init__(self):
        if not self.source_node_id or not self.target_node_id:
            raise ValueError("Edge requires source_node_id and target_node_id")

        self.strength = max(0.0, min(1.0, self.strength))
        self.emotional_charge = max(-1.0, min(1.0, self.emotional_charge))

    # ------------------------------------------------------------------
    # Usage / recency
    # ------------------------------------------------------------------

    def touch(self):
        """Mark edge as recently used."""
        self.last_used = time.time()

    def recency_factor(self, now: Optional[float] = None) -> float:
        """
        Recency-based availability.
        Fast decay early, slower later.
        """
        now = now or time.time()
        elapsed = max(0.0, now - self.last_used)

        # Smooth hyperbolic decay (~1 hour scale)
        return 1.0 / (1.0 + elapsed / 3600.0)

    # ------------------------------------------------------------------
    # Learning & reinforcement
    # ------------------------------------------------------------------

    def schedule_reinforcement(self, amount: float):
        """
        Schedule reinforcement in [-1.0, +1.0].
        Applied later based on success.
        """
        if not -1.0 <= amount <= 1.0:
            raise ValueError("reinforcement amount must be in [-1.0, 1.0]")
        self.pending_reinforcement = amount

    def apply_reinforcement(self, success: bool):
        """
        Apply or discard scheduled reinforcement.
        """
        if self.pending_reinforcement is None:
            return

        if success:
            self.strength = min(1.0, self.strength + self.pending_reinforcement)
        else:
            self.strength = max(
                0.0,
                self.strength - abs(self.pending_reinforcement) * 0.5,
            )

        self.pending_reinforcement = None
        self.touch()

    def reinforce(self, amount: float = 0.1):
        """Immediate positive reinforcement."""
        self.strength = min(1.0, self.strength + max(0.0, amount))
        self.touch()

    def weaken(self, amount: float = 0.1):
        """Immediate negative reinforcement."""
        self.strength = max(0.0, self.strength - max(0.0, amount))
        self.touch()

    # ------------------------------------------------------------------
    # Emotion handling (temporary modulation)
    # ------------------------------------------------------------------

    def register_emotion(self, emotion: EmotionType, intensity: float = 1.0):
        """
        Register emotion affecting importance temporarily.
        """
        emotion_map = {
            "happy": 0.3,
            "excited": 0.4,
            "surprised": 0.1,
            "neutral": 0.0,
            "anxious": -0.1,
            "sad": -0.2,
            "angry": -0.4,
        }

        delta = emotion_map.get(emotion, 0.0) * max(0.0, min(1.0, intensity))
        self.emotional_charge = max(-1.0, min(1.0, self.emotional_charge + delta))

        self.metadata["last_emotion"] = emotion
        self.metadata["last_emotion_time"] = time.time()
        self.touch()

    def cool_down(self, rate: float = 0.05):
        """Decay emotional charge back to neutral."""
        if abs(self.emotional_charge) < rate:
            self.emotional_charge = 0.0
        elif self.emotional_charge > 0:
            self.emotional_charge -= rate
        else:
            self.emotional_charge += rate

    # ------------------------------------------------------------------
    # Importance & pruning
    # ------------------------------------------------------------------

    def importance_score(self, now: Optional[float] = None) -> float:
        """
        Final importance used in retrieval.

        importance =
            strength
            × recency_factor
            × (1 + emotional_charge * 0.2)
        """
        recency = self.recency_factor(now)
        emotional_boost = 1.0 + self.emotional_charge * 0.2

        score = self.strength * recency * emotional_boost
        return max(0.0, score)

    def should_prune(self, threshold: float = 0.05) -> bool:
        """
        Suggest edge removal if structurally weak.
        """
        return self.strength < threshold

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------

    def age(self) -> float:
        return time.time() - self.created_at

    def time_since_use(self) -> float:
        return time.time() - self.last_used

    def info(self) -> Dict:
        return {
            "relation": self.relation,
            "strength": round(self.strength, 3),
            "recency": round(self.recency_factor(), 3),
            "emotional_charge": round(self.emotional_charge, 3),
            "importance_score": round(self.importance_score(), 3),
            "age_seconds": round(self.age(), 1),
            "time_since_use_seconds": round(self.time_since_use(), 1),
            "should_prune": self.should_prune(),
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return (
            f"Edge("
            f"relation={self.relation}, "
            f"strength={self.strength:.2f}, "
            f"importance={self.importance_score():.2f}"
            f")"
        )
