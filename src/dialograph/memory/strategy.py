

class StrategyState:
    name: str                     # e.g. "empathize_then_suggest"
    description: str
    success_rate: float = 0.5
    usage_count: int = 0
    last_used: float 

    def record_outcome(self, success: bool):
        raise NotImplementedError