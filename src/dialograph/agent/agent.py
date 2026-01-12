from datetime import datetime, timedelta
from typing import Optional
from ..core.graph import Graph
from ..core.node import TemporalNode, MasteryLevel
from .policy import CurriculumPolicy, PedagogicalAction


class DialographAgent:
    """
    Main agent class: proactive, curriculum-aware dialogue.
    Integrates graph memory + temporal dynamics + policy.
    """
    
    def __init__(self, name: str, graph: Graph = None):
        self.name = name
        self.graph = graph or Graph()
        self.policy = CurriculumPolicy()
        self.current_time = datetime.now()
        self._knowledge_nodes: dict[str, TemporalNode] = {}
    
    def add_concept(
        self, 
        concept_id: str, 
        label: str, 
        prerequisites: list[str] = None
    ) -> TemporalNode:
        """Add learning concept to curriculum graph"""
        node = TemporalNode(concept_id, label, prerequisites or [])
        self._knowledge_nodes[concept_id] = node
        self.graph.add_node(node)
        
        # Add prerequisite edges
        for prereq_id in (prerequisites or []):
            if prereq_id in self._knowledge_nodes:
                self.graph.add_edge(prereq_id, concept_id, "prerequisite")
        
        return node
    
    def advance_time(self, days: int = 1):
        """Simulate time passing - triggers forgetting"""
        self.current_time += timedelta(days=days)
        for node in self._knowledge_nodes.values():
            node.decay_confidence(self.current_time)
    
    def act(self) -> str:
        """
        Proactive action - agent decides what to do.
        This is the KEY method: not reactive to user input.
        """
        action, target = self.policy.decide_next_action(self._knowledge_nodes)
        
        if action == PedagogicalAction.INTRODUCE:
            target.mastery = MasteryLevel.INTRODUCED
            target.confidence = 0.3
            target.last_reviewed = self.current_time
            prereqs = ', '.join(target.prerequisites) if target.prerequisites else 'none'
            return f"Introducing: {target.label}\n   Prerequisites: {prereqs}"
        
        elif action == PedagogicalAction.REVIEW:
            days_ago = (self.current_time - target.last_reviewed).days
            return f"Let's review: {target.label}\n   (Confidence: {target.confidence:.1%}, last seen {days_ago} days ago)"
        
        elif action == PedagogicalAction.PRACTICE:
            return f"Practice time: {target.label}\n   (Confidence: {target.confidence:.1%})"
        
        elif action == PedagogicalAction.TEST:
            return f"Quick check: {target.label}\n   (Let's verify your mastery)"
        
        else:
            return "All concepts mastered! Take a break or try advanced material."
    
    def respond(self, user_input: str = None) -> str:
        """
        Alias for act() - maintains compatibility.
        In Dialograph, the agent acts proactively regardless of input.
        """
        return self.act()
    
    def record_interaction(self, concept_id: str, success: bool):
        """Record learning outcome for a concept"""
        if concept_id in self._knowledge_nodes:
            node = self._knowledge_nodes[concept_id]
            node.update_after_interaction(success, self.current_time)
    
    def get_curriculum_status(self) -> str:
        """Display current learning state"""
        lines = [f"Curriculum Status ({self.name}):\n"]
        for node in self._knowledge_nodes.values():
            status = (
                f"  • {node.label}: {node.mastery.name} "
                f"(conf: {node.confidence:.1%}, reviews: {node.review_count})"
            )
            lines.append(status)
        return "\n".join(lines)
