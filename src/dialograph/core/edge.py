from dataclasses import dataclass, field
import time
import uuid
import math
from typing import Dict, Optional, Literal


RelationType = Literal["supports", "contradicts", "elicits", "causes", "depends_on"]
TruthStatus = Literal["observed", "inferred", "assumed"]
EmotionType = Literal["happy", "sad", "angry", "anxious", "excited", "neutral"]


@dataclass
class EdgeState:
    """
    Research-oriented, time-aware edge for proactive dialogue reasoning.

    Design goals:
    - Interpretable
    - Emotion-aware
    - Cost-sensitive
    - Safe
    """

    # Identity
    edge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str = ""
    target_node_id: str = ""

    # Semantics
    relation: RelationType = "supports"
    truth_status: TruthStatus = "assumed"

    # Core strength (long-term belief)
    strength: float = 0.5  # [0,1]

    # Decision-related
    expected_utility: float = 0.0     # benefit of acting on this edge
    risk: float = 0.0                 # [0,1]
    harm_potential: float = 0.0       # [0,1]

    # Emotion as a signal (temporary modulation)
    emotional_charge: float = 0.0     # [-1, +1]

    # Time
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)

    # Learning
    pending_reinforcement: Optional[float] = None

    # Metadata
    metadata: Dict = field(default_factory=dict)

    # Validation
    def __post_init__(self):
        if not self.source_node_id or not self.target_node_id:
            raise ValueError("Edge must have source and target nodes")
        if not 0.0 <= self.strength <= 1.0:
            raise ValueError("strength must be in [0,1]")
        if not -1.0 <= self.emotional_charge <= 1.0:
            raise ValueError("emotional_charge must be in [-1,1]")

    # Time dynamics
    def decay(self, base_rate: float = 0.01):
        """
        Differential decay:
        - Strong edges decay slower
        - Weak edges decay faster
        """
        elapsed = time.time() - self.last_used
        importance_factor = max(0.3, self.strength)
        decay_amount = base_rate * elapsed * (1.0 - importance_factor)
        self.strength = max(0.0, self.strength - decay_amount)

        # emotional cooldown
        self.cool_down(rate=0.05 * elapsed)

    def touch(self):
        self.last_used = time.time()

    # Emotion handling
    def register_emotion(self, emotion: EmotionType, intensity: float = 1.0):
        emotion_map = {
            "happy": +0.3,
            "excited": +0.4,
            "neutral": 0.0,
            "anxious": -0.1,
            "sad": -0.2,
            "angry": -0.4,
        }
        delta = emotion_map[emotion] * intensity
        self.emotional_charge = max(-1.0, min(1.0, self.emotional_charge + delta))
        self.metadata["last_emotion"] = emotion
        self.touch()

    def cool_down(self, rate: float = 0.05):
        if abs(self.emotional_charge) < 0.01:
            self.emotional_charge = 0.0
        elif self.emotional_charge > 0:
            self.emotional_charge -= rate
        else:
            self.emotional_charge += rate

    # Reinforcement
    def schedule_reinforcement(self, amount: float):
        self.pending_reinforcement = max(-1.0, min(1.0, amount))

    def apply_reinforcement(self, success: bool):
        if self.pending_reinforcement is None:
            return
        if success:
            self.strength = min(1.0, self.strength + self.pending_reinforcement)
        else:
            self.strength = max(0.0, self.strength - abs(self.pending_reinforcement) * 0.5)
        self.pending_reinforcement = None
        self.touch()

    # Proactive activation
    def importance_score(self, recency_weight: float = 0.3) -> float:
        elapsed = time.time() - self.last_used
        recency_factor = 1.0 / (1.0 + elapsed / 3600.0)

        base = (1 - recency_weight) * self.strength + recency_weight * recency_factor
        emotional_boost = 0.2 * self.emotional_charge

        return max(0.0, base + emotional_boost)

    def should_activate(self, threshold: float = 0.3) -> bool:
        """
        Simple, interpretable activation rule:
        importance × utility − risk
        """
        if self.harm_potential > 0.7:
            return False

        score = self.importance_score() * (1.0 + self.expected_utility) - self.risk
        return score >= threshold
