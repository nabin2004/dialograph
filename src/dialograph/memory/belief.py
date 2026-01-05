

class BeliefState:
    proposition: str          # natural language or structured
    confidence: float = 0.8
    source: str | None = None
    last_verified: float 

    def weaken(self, amount: float = 0.1):
        raise NotImplementedError

    def strengthen(self, amount: float = 0.1):
        raise NotImplementedError
