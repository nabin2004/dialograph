from dataclasses import dataclass, field

class PreferenceState:
    """
    Docstring for PreferenceState
    """
    key: str
    value: str | float
    confidence: float   
    last_accessed: float
    last_updated: float

    def __init__(self, key: str, value: str | float, confidence: float):
        pass 

    def reinforce(self, amount: float = 0.1):
        pass

    def decay(self, decay_rate: float = 0.01):
        pass