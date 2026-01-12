from enum import Enum
from typing import Optional, Tuple
from ..core.node import TemporalNode, MasteryLevel


class PedagogicalAction(Enum):
    """Actions the agent can take"""
    INTRODUCE = "introduce"  # First time showing concept
    PRACTICE = "practice"    # Reinforce existing concept
    REVIEW = "review"        # Remediate forgotten concept
    TEST = "test"            # Assess mastery
    WAIT = "wait"            # No action needed


class CurriculumPolicy:
    """
    Decides WHAT to teach and WHEN.
    Core of proactive behavior.
    """
    
    def __init__(self, review_threshold: float = 0.4, mastery_threshold: float = 0.8):
        self.review_threshold = review_threshold
        self.mastery_threshold = mastery_threshold
    
    def decide_next_action(
        self, 
        knowledge_graph: dict[str, TemporalNode]
    ) -> Tuple[PedagogicalAction, Optional[TemporalNode]]:
        """
        Proactive decision logic.
        Returns: (action, target_node)
        """
        
        # Priority 1: Review forgotten concepts (urgent)
        for node in knowledge_graph.values():
            if node.mastery == MasteryLevel.NEEDS_REVIEW:
                return PedagogicalAction.REVIEW, node
        
        # Priority 2: Practice concepts being learned
        practicing_nodes = [
            n for n in knowledge_graph.values() 
            if n.mastery == MasteryLevel.PRACTICING
        ]
        if practicing_nodes:
            # Focus on weakest concept
            weakest = min(practicing_nodes, key=lambda n: n.confidence)
            return PedagogicalAction.PRACTICE, weakest
        
        # Priority 3: Introduce new concepts (if prerequisites met)
        for node in knowledge_graph.values():
            if node.mastery == MasteryLevel.NOT_SEEN:
                if self._prerequisites_satisfied(node, knowledge_graph):
                    return PedagogicalAction.INTRODUCE, node
        
        # Priority 4: Test mastered concepts periodically
        mastered = [n for n in knowledge_graph.values() 
                   if n.mastery == MasteryLevel.MASTERED]
        if mastered and len(mastered) % 5 == 0:  # Every 5 mastered concepts
            return PedagogicalAction.TEST, mastered[0]
        
        # Nothing to do
        return PedagogicalAction.WAIT, None
    
    def _prerequisites_satisfied(
        self, 
        node: TemporalNode, 
        graph: dict[str, TemporalNode]
    ) -> bool:
        """Check if all prerequisites are mastered"""
        for prereq_id in node.prerequisites:
            prereq = graph.get(prereq_id)
            if not prereq:
                return False
            if prereq.mastery not in [MasteryLevel.MASTERED, MasteryLevel.PRACTICING]:
                return False
        return True
