from dataclasses import dataclass, field
import time

@dataclass
class EdgeState:
    """
    Represents a directed edge between two nodes in the dialogue graph.
    Tracks relation type, strength, timestamps, and optional metadata.
    """
    relation: str                 # e.g., "supports", "elicits", "contradicts"
    strength: float               # confidence / weight of relation (0.0 - 1.0)
    created_at: float = field(default_factory=time.time)
    last_used: float = field(default_factory=time.time)
    metadata: dict = field(default_factory=dict)
    
    # Core methods
    def touch(self):
        """Update usage timestamp when edge is traversed."""
        self.last_used = time.time()

    def decay(self, rate: float = 0.01):
        """
        Decay edge strength over time based on inactivity.
        """
        time_elapsed = time.time() - self.last_used
        decay_amount = rate * time_elapsed
        self.strength = max(0.0, self.strength - decay_amount)

    def reinforce(self, amount: float = 0.1):
        """
        Strengthen edge after successful traversal.
        Caps strength at 1.0.
        """
        self.strength = min(1.0, self.strength + amount)
        self.touch()

    # Emotion-based updates
    def happy(self):
        """Happy emotion strengthens edge more."""
        self.reinforce(amount=0.2)
    
    def sad(self):
        """Sad emotion weakens edge slightly."""
        self.strength *= 0.9
        self.touch()
    
    def angry(self):
        """Angry emotion weakens edge more."""
        self.strength *= 0.8
        self.touch()
    
    def surprised(self):
        """Surprised emotion gives minor boost."""
        self.reinforce(amount=0.05)
    
    def neutral(self):
        """Neutral emotion gives small default reinforcement."""
        self.reinforce(amount=0.05)


    # Helper methods
    def update_metadata(self, key, value):
        """Update metadata for this edge."""
        self.metadata[key] = value

    def info(self):
        """Return a summary of the edge state."""
        return {
            "relation": self.relation,
            "strength": round(self.strength, 3),
            "last_used": self.last_used,
            "metadata": self.metadata
        }



# Example usage / testing
if __name__ == "__main__":
    edge = EdgeState(relation="supports", strength=0.5)
    
    print("Initial:", edge.info())
    
    # Simulate emotions
    edge.happy()
    print("After happy:", edge.info())
    
    edge.sad()
    print("After sad:", edge.info())
    
    edge.angry()
    print("After angry:", edge.info())
    
    edge.decay(rate=0.01)
    print("After decay:", edge.info())
