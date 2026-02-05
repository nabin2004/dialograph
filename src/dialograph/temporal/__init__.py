from dataclasses import dataclass

@dataclass
class TemporalNodeState:
    node_id: str
    created_at: datetime
    last_activated_at: datetime
    activation_count: int
    decay_score: float
    confidence: float
