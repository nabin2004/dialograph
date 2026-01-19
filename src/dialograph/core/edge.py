from dataclasses import dataclass, field
import time
from typing import Dict, Optional, Literal
import uuid

RelationType = Literal["supports", "contradicts", "elicits", "influences", "depends_on"]
EmotionType = Literal["happy", "surprised", "neutral", "sad", "angry", "anxious", "excited"]


@dataclass
class Edge:
    """
    Represents a directed, time-aware relationship between two nodes in the dialogue graph.

    Each edge has:
    - source_node_id: ID of the node that initiates the relationship
    - target_node_id: ID of the node that receives the relationship
    - relation: the type of connection (supports, contradicts, elicits)
    - confidence: how important this connection is (0.0 - 1.0)
    - metadata: optional info like trauma, tags, or context
    """
    edge_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_node_id: str = field(default="")
    target_node_id: str = field(default="")


    relation: RelationType = "not_named"                        # e.g., "supports", "elicits", "contradicts"
    confidence: float = 0.5                       # [0.0, 1.0] long-term importance

    # Time tracking
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)

    # emotional_charge: float = 0.0           # [-1.0, +1.0]
    pending_reinforcement: Optional[float] = None

    def __post_init__(self):
        if not self.source_node_id or not self.target_node_id:
            raise ValueError("Edge requires source_node_id and target_node_id")
  
    def touch(self):
        """Mark edge as recently used."""
        self.last_used = time.time()


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

        return self.confidence



    # Learning & reinforcement
    def schedule_reinforcement(self, amount: float):
        """
        Schedule reinforcement without applying it immediately.
        Allows for delayed validation of whether action was successful.
        """
        if not -1.0 <= amount <= 1.0:
            raise ValueError(f"reinforcement amount must be in [-1.0, 1.0], got {amount}")
        self.pending_reinforcement = amount

    def apply_reinforcement(self, success: bool):
        """
        Apply or discard scheduled reinforcement based on outcome.
        
        Args:
            success: Whether the action using this edge was successful
        """
        if self.pending_reinforcement is None:
            return
            
        if success:
            self.strength = min(1.0, self.strength + self.pending_reinforcement)
        else:
            # Optional: slightly weaken on failure
            self.strength = max(0.0, self.strength - abs(self.pending_reinforcement) * 0.5)
            
        self.pending_reinforcement = None
        self.touch()

    def reinforce(self, amount: float = 0.1):
        """
        Directly strengthen edge (for immediate feedback).
        Use this when you don't need delayed reinforcement.
        """
        self.strength = min(1.0, self.strength + amount)
        self.touch()

    def weaken(self, amount: float = 0.1):
        """Directly weaken edge (for negative feedback)."""
        self.strength = max(0.0, self.strength - amount)
        self.touch()


    # Emotion handling
    def register_emotion(self, emotion: str, intensity: float = 1.0):
        """
        Register emotion without directly changing strength.
        Emotional charge affects importance temporarily.
        
        Args:
            emotion: Type of emotion (happy, sad, angry, etc.)
            intensity: Multiplier for emotional impact [0.0, 1.0]
        """
        emotion_map = {
            "happy": +0.3,
            "excited": +0.4,
            "surprised": +0.1,
            "neutral": 0.0,
            "anxious": -0.1,
            "sad": -0.2,
            "angry": -0.4,
        }
        
        delta = emotion_map.get(emotion.lower(), 0.0) * intensity
        self.emotional_charge = max(-1.0, min(1.0, self.emotional_charge + delta))
        self.metadata["last_emotion"] = emotion
        self.metadata["last_emotion_time"] = time.time()
        self.touch()

    def cool_down(self, rate: float = 0.05):
        """Gradually reduce emotional charge over time (return to neutral)."""
        if abs(self.emotional_charge) < 0.01:
            self.emotional_charge = 0.0
        elif self.emotional_charge > 0:
            self.emotional_charge = max(0.0, self.emotional_charge - rate)
        elif self.emotional_charge < 0:
            self.emotional_charge = min(0.0, self.emotional_charge + rate)

    # Importance calculation
    def importance_score(self, recency_weight: float = 0.3) -> float:
        """
        Compute dynamic importance score combining:
        - Base strength (70%)
        - Emotional charge (temporary boost/penalty)
        - Recency of usage (30% by default)
        
        Args:
            recency_weight: How much to weight recent usage [0.0, 1.0]
        
        Returns:
            Importance score in [0.0, 1.0+]
        """
        elapsed = time.time() - self.last_used
        
        # Recency decays exponentially (half-life of ~1 hour)
        recency_factor = 1.0 / (1.0 + elapsed / 3600.0)
        
        # Combine factors
        base_score = (1 - recency_weight) * self.strength + recency_weight * recency_factor
        emotional_boost = self.emotional_charge * 0.2  # emotions can add ±20%
        
        score = base_score + emotional_boost
        return max(0.0, score)  # Can exceed 1.0 during emotional spikes

    def should_prune(self, threshold: float = 0.1) -> bool:
        """
        Determine if this edge should be removed from graph.
        
        Args:
            threshold: Minimum strength to keep edge
        """
        return self.strength < threshold

    # Helper methods
    def update_metadata(self, key: str, value):
        """Update metadata for this edge."""
        self.metadata[key] = value

    def get_metadata(self, key: str, default=None):
        """Safely retrieve metadata."""
        return self.metadata.get(key, default)

    def age(self) -> float:
        """Get age of edge in seconds."""
        return time.time() - self.created_at

    def time_since_use(self) -> float:
        """Get time since last use in seconds."""
        return time.time() - self.last_used

    def info(self) -> Dict:
        """Return a human-readable summary of edge state."""
        return {
            "relation": self.relation,
            "strength": round(self.strength, 3),
            "emotional_charge": round(self.emotional_charge, 3),
            "pending_reinforcement": self.pending_reinforcement,
            "age_seconds": round(self.age(), 1),
            "time_since_use_seconds": round(self.time_since_use(), 1),
            "importance_score": round(self.importance_score(), 3),
            "should_prune": self.should_prune(),
            "metadata": self.metadata,
        }

    def __repr__(self) -> str:
        return f"Edge(relation='{self.relation}', strength={self.strength:.2f}, importance={self.importance_score():.2f})"



