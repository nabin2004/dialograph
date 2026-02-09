from dataclasses import dataclass

@dataclass
class TemporalNodeState:
    node_id: str
    created_at: datetime
    last_activated_at: datetime
    activation_count: int = 0
    decay_score: float = 1.0
    confidence: float = 1.0
