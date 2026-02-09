"""
DIALOGRAPH POLICY SYSTEM - Updated Implementation
==================================================
This is the CORE policy system only - no chatbot integration.

Based on the paper's formal definitions:

DEFINITION (Dialograph State):
    State_t := (Graph, T_t)
    where:
    - Graph = (V, E) is the semantic graph of concepts and relationships
    - T_t: V → ℝᵏ is the temporal state function mapping concepts to state vectors
    - T_t(v) = ⟨c_t(v), f_t(v), r_t(v), d_t(v)⟩

DEFINITION (Action Space):
    Actions = {explain, ask_why, give_hint, quiz, review, advance}
    Abstract pedagogical intents (not surface realizations)

DEFINITION (Decision Policy):
    Policy π := (φ, a, ρ, ω)
    where:
    - φ: State_t → {0,1} is applicability condition
    - a ∈ Actions is the preferred action
    - ρ ∈ ℝ⁺ is static priority
    - ω ∈ [0,1] is dynamic confidence

POLICY SELECTION:
    π* = argmax_{πᵢ ∈ Πₜ} (ρᵢ · ωᵢ)
    where Πₜ = {πᵢ | φᵢ(State_t) = 1}

Key Updates from Original Code:
1. All 10 condition classes implemented (It had only LowConfidenceCondition)
2. Expanded TemporalNodeState with all learning signals
3. Added record_interaction() method to Dialograph
4. All policies properly defined with correct priorities
5. Policy selection uses paper's formula: π* = argmax(ρ · ω)
6. Working example at the bottom
"""

from dataclasses import dataclass
from datetime import datetime
from math import exp
from typing import Dict, List, Optional

# ============================================================
# 1. SEMANTIC LAYER (MEANING ONLY — NO TIME, NO USER STATE)
# ============================================================

@dataclass(frozen=True)
class SemanticNode:
    id: str
    type: str        # Concept, Skill, Question, etc.
    content: str


@dataclass(frozen=True)
class SemanticEdge:
    source: str
    target: str
    relation_type: str  # prerequisite_of, explains, etc.


# ============================================================
# 2. TEMPORAL LAYER (STATE OVER MEANING)
# ============================================================

@dataclass
class TemporalNodeState:
    """
    Temporal state vector T_t(v) as defined in paper, with practical extensions.
    
    Paper defines: T_t(v) = ⟨c_t(v), f_t(v), r_t(v), d_t(v)⟩
    - c_t: confidence (learner's estimated understanding)
    - f_t: interaction frequency
    - r_t: recency (last activation time)
    - d_t: decay (forgetting curve)
    
    Extended with error patterns and response characteristics to enable
    all 10 research-backed policies (not explicitly in paper's formalism
    but necessary for practical implementation).
    """
    node_id: str
    created_at: datetime
    last_activated_at: datetime  # r_t: recency
    activation_count: int         # f_t: interaction frequency
    decay_score: float            # d_t: decay/forgetting
    confidence: float             # c_t: learner confidence
    
    # PRACTICAL EXTENSIONS: Error patterns and response characteristics
    # (Required for policies like "Overconfident Error", "Guessing Behavior", etc.)
    error_count: int = 0
    correct_count: int = 0
    last_response_correct: Optional[bool] = None
    last_response_time_ms: Optional[float] = None
    consecutive_errors: int = 0
    consecutive_correct: int = 0
    explanation_quality_score: float = 0.0
    total_attempts: int = 0


# ============================================================
# 3. DIALOGRAPH (OWNS EVERYTHING)
# ============================================================

class Dialograph:
    def __init__(self):
        self.semantic_nodes: Dict[str, SemanticNode] = {}
        self.semantic_edges: List[SemanticEdge] = []
        self.temporal_nodes: Dict[str, TemporalNodeState] = {}
        
        # ADDED: Track current focus for policy evaluation
        self.current_focus_node: Optional[str] = None
        self.interaction_history: List[dict] = []

    # ---- semantic registration ----
    def add_node(self, node: SemanticNode):
        self.semantic_nodes[node.id] = node
        self.temporal_nodes[node.id] = TemporalNodeState(
            node_id=node.id,
            created_at=datetime.now(),
            last_activated_at=datetime.now(),
            activation_count=0,
            decay_score=1.0,
            confidence=0.5  # Start neutral instead of 1.0
        )

    def add_edge(self, edge: SemanticEdge):
        self.semantic_edges.append(edge)

    # ---- temporal updates ----
    def activate(self, node_id: str, confidence: Optional[float] = None):
        state = self.temporal_nodes[node_id]
        state.last_activated_at = datetime.now()
        state.activation_count += 1
        state.decay_score = 1.0
        if confidence is not None:
            state.confidence = confidence
        self.current_focus_node = node_id

    # ADDED: Critical method for updating state after learner interaction
    def record_interaction(self, node_id: str, correct: bool, 
                          response_time_ms: float, 
                          explanation_quality: float = 0.5):
        """
        Record a learner interaction and update temporal state.
        
        Args:
            node_id: The concept being practiced
            correct: Was the response correct?
            response_time_ms: How long did they take to respond?
            explanation_quality: Quality of explanation (0-1)
        """
        state = self.temporal_nodes[node_id]
        state.last_response_correct = correct
        state.last_response_time_ms = response_time_ms
        state.explanation_quality_score = explanation_quality
        state.total_attempts += 1
        
        if correct:
            state.correct_count += 1
            state.consecutive_correct += 1
            state.consecutive_errors = 0
            # Increase confidence when correct
            state.confidence = min(1.0, state.confidence + 0.15)
        else:
            state.error_count += 1
            state.consecutive_errors += 1
            state.consecutive_correct = 0
            # Decrease confidence when wrong
            state.confidence = max(0.0, state.confidence - 0.2)
        
        # Store in history for analytics
        self.interaction_history.append({
            "timestamp": datetime.now(),
            "node_id": node_id,
            "correct": correct,
            "response_time_ms": response_time_ms,
            "confidence": state.confidence
        })
        
        # Reactivate the node
        self.activate(node_id)

    def decay_all(self, lambda_: float = 0.01):
        now = datetime.now()
        for state in self.temporal_nodes.values():
            dt = (now - state.last_activated_at).total_seconds()
            state.decay_score *= exp(-lambda_ * dt)


# ============================================================
# 4. CONDITIONS (FORMAL "WHEN X HAPPENS")
# ============================================================

class Condition:
    def evaluate(self, graph: Dialograph) -> List[dict]:
        """
        Returns evidence matches.
        Empty list = condition not met.
        """
        raise NotImplementedError


# ORIGINAL:
class LowConfidenceCondition(Condition):
    """Fragile Knowledge: confidence below threshold"""
    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        if graph.current_focus_node:
            state = graph.temporal_nodes[graph.current_focus_node]
            if state.confidence < self.threshold:
                matches.append({
                    "node_id": graph.current_focus_node,
                    "confidence": state.confidence
                })
        return matches


# ADDED: The remaining 9 condition classes
class HighConfidenceWrongCondition(Condition):
    """Overconfident Error: high confidence but incorrect"""
    def __init__(self, confidence_threshold: float = 0.7):
        self.threshold = confidence_threshold
    
    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        if graph.current_focus_node:
            state = graph.temporal_nodes[graph.current_focus_node]
            if (state.confidence > self.threshold and 
                state.last_response_correct == False and
                state.total_attempts > 0):
                matches.append({
                    "node_id": graph.current_focus_node,
                    "confidence": state.confidence
                })
        return matches


class RepeatedWrongCondition(Condition):
    """Persistent Misconception: multiple consecutive errors"""
    def __init__(self, attempts: int = 2):
        self.attempts = attempts
    
    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        if graph.current_focus_node:
            state = graph.temporal_nodes[graph.current_focus_node]
            if state.consecutive_errors >= self.attempts:
                matches.append({
                    "node_id": graph.current_focus_node,
                    "errors": state.consecutive_errors
                })
        return matches


class FastIncorrectCondition(Condition):
    """Guessing Behavior: fast incorrect response"""
    def __init__(self, time_ms: float = 2000):
        self.time_threshold = time_ms
    
    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        if graph.current_focus_node:
            state = graph.temporal_nodes[graph.current_focus_node]
            if (state.last_response_correct == False and 
                state.last_response_time_ms and
                state.last_response_time_ms < self.time_threshold):
                matches.append({
                    "node_id": graph.current_focus_node,
                    "response_time": state.last_response_time_ms
                })
        return matches


class FastCorrectLowExplanationQuality(Condition):
    """Illusion of Mastery: correct but shallow understanding"""
    def __init__(self, time_ms: float = 3000, quality_threshold: float = 0.6):
        self.time_threshold = time_ms
        self.quality_threshold = quality_threshold
    
    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        if graph.current_focus_node:
            state = graph.temporal_nodes[graph.current_focus_node]
            if (state.last_response_correct == True and
                state.last_response_time_ms and
                state.last_response_time_ms < self.time_threshold and
                state.explanation_quality_score < self.quality_threshold):
                matches.append({
                    "node_id": graph.current_focus_node,
                    "explanation_quality": state.explanation_quality_score
                })
        return matches


class HighDecayCondition(Condition):
    """Forgetting Detected: decay score below threshold"""
    def __init__(self, threshold: float = 0.6):
        self.threshold = threshold
    
    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        # Only check current concept being taught (concept-specific)
        if graph.current_focus_node:
            state = graph.temporal_nodes[graph.current_focus_node]
            if state.decay_score < self.threshold and state.total_attempts > 0:
                matches.append({
                    "node_id": graph.current_focus_node,
                    "decay": state.decay_score
                })
        return matches


class ImprovingButIncorrectCondition(Condition):
    """Productive Struggle: improving confidence but still wrong"""
    def __init__(self):
        pass
    
    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        if graph.current_focus_node and len(graph.interaction_history) >= 2:
            recent = graph.interaction_history[-2:]
            state = graph.temporal_nodes[graph.current_focus_node]
            
            # Check if confidence is improving but still incorrect
            if (len(recent) >= 2 and
                recent[-1]["confidence"] > recent[-2]["confidence"] and
                state.last_response_correct == False):
                matches.append({
                    "node_id": graph.current_focus_node,
                    "improving": True
                })
        return matches


class HighConfidenceCorrectRepeated(Condition):
    """Mastery Achieved: multiple correct answers with high confidence"""
    def __init__(self, times: int = 2, confidence_threshold: float = 0.8):
        self.times = times
        self.threshold = confidence_threshold
    
    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        if graph.current_focus_node:
            state = graph.temporal_nodes[graph.current_focus_node]
            if (state.consecutive_correct >= self.times and 
                state.confidence >= self.threshold):
                matches.append({
                    "node_id": graph.current_focus_node,
                    "mastered": True
                })
        return matches


class LongLatencyIncorrectCondition(Condition):
    """Cognitive Overload: slow response and incorrect"""
    def __init__(self, time_ms: float = 10000):
        self.time_threshold = time_ms
    
    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        if graph.current_focus_node:
            state = graph.temporal_nodes[graph.current_focus_node]
            if (state.last_response_correct == False and
                state.last_response_time_ms and
                state.last_response_time_ms > self.time_threshold):
                matches.append({
                    "node_id": graph.current_focus_node,
                    "overloaded": True
                })
        return matches


class HighConfidenceVariedContextCorrect(Condition):
    """Transfer Readiness: consistent success across attempts"""
    def __init__(self, min_attempts: int = 3, confidence_threshold: float = 0.85):
        self.min_attempts = min_attempts
        self.threshold = confidence_threshold
    
    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        if graph.current_focus_node:
            state = graph.temporal_nodes[graph.current_focus_node]
            success_rate = state.correct_count / max(state.total_attempts, 1)
            if (state.total_attempts >= self.min_attempts and
                success_rate >= 0.8 and
                state.confidence >= self.threshold):
                matches.append({
                    "node_id": graph.current_focus_node,
                    "ready_for_transfer": True
                })
        return matches


# ============================================================
# 5. DECLARATIVE POLICY (WHAT HUMANS WRITE)
# ============================================================

@dataclass
class DeclarativePolicy:
    id: str
    when: Condition
    do: str
    rather_than: str
    because: str
    priority: int = 50
    confidence: float = 1.0


# ============================================================
# 6. COMPILED POLICY (WHAT THE SYSTEM EXECUTES)
# ============================================================

class CompiledPolicy:
    def __init__(self, p: DeclarativePolicy):
        self.id = p.id
        self.condition = p.when
        self.preferred_action = p.do
        self.avoided_action = p.rather_than
        self.because = p.because
        self.priority = p.priority
        self.confidence = p.confidence

    def applies(self, graph: Dialograph) -> bool:
        return len(self.condition.evaluate(graph)) > 0

    def score(self, graph: Dialograph) -> float:
        matches = self.condition.evaluate(graph)
        if not matches:
            return 0.0
        return self.confidence

    def decide(self) -> str:
        return self.preferred_action

    def explain(self, graph: Dialograph) -> str:
        matches = self.condition.evaluate(graph)
        return (
            f"Policy '{self.id}' fired on {len(matches)} items "
            f"because {self.because}"
        )


def compile_policy(p: DeclarativePolicy) -> CompiledPolicy:
    return CompiledPolicy(p)


# ============================================================
# 7. POLICY ENGINE (CONFLICT RESOLUTION)
# ============================================================

class PolicyEngine:
    def __init__(self, policies: List[CompiledPolicy]):
        self.policies = policies

    def select(self, graph: Dialograph) -> Optional[CompiledPolicy]:
        """
        Select policy using the formula from the paper:
        π* = argmax_{πᵢ ∈ Πₜ} (ρᵢ · ωᵢ)
        
        where:
        - Πₜ = set of applicable policies (φᵢ(State) = 1)
        - ρᵢ = static priority value
        - ωᵢ = dynamic policy confidence
        """
        candidates = []

        for policy in self.policies:
            if policy.applies(graph):  # φᵢ(State) = 1
                # Paper formula: score = ρᵢ · ωᵢ
                score = policy.priority * policy.confidence
                candidates.append((policy, score))

        if not candidates:
            return None

        # Select policy with maximum score
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]


# ============================================================
# 8. EXAMPLE USAGE (COMPLETE WORKING EXAMPLE)
# ============================================================

if __name__ == "__main__":
    
    print("=" * 70)
    print("EXAMPLE 1: MULTI-CONCEPT LEARNING (No Bias)")
    print("Student: Good at Math, Struggling with Social Skills")
    print("=" * 70)
    print()
    
    # Create graph with different concepts
    graph = Dialograph()
    
    # Math concept
    graph.add_node(SemanticNode(
        id="algebra",
        type="Concept",
        content="Algebra (Math)"
    ))
    
    # Social concept
    graph.add_node(SemanticNode(
        id="empathy",
        type="Concept",
        content="Empathy (Social Skills)"
    ))
    
    # Create policy engine
    policies = [
        DeclarativePolicy(
            id="fragile_knowledge",
            when=LowConfidenceCondition(threshold=0.5),
            do="ASK_EXPLANATION",
            rather_than="ADVANCE_TOPIC",
            because="Low confidence indicates fragile understanding",
            priority=80,
            confidence=0.9
        ),
        DeclarativePolicy(
            id="mastery_achieved",
            when=HighConfidenceCorrectRepeated(times=2, confidence_threshold=0.8),
            do="ADVANCE_TOPIC",
            rather_than="ASK_MORE_PRACTICE",
            because="Repeated correct performance indicates mastery",
            priority=60,
            confidence=0.9
        )
    ]
    engine = PolicyEngine([compile_policy(p) for p in policies])
    
    # Scenario 1: Teaching Algebra (student is good at math)
    print("📚 TEACHING: Algebra")
    graph.activate("algebra")
    
    # Student does well
    graph.record_interaction("algebra", correct=True, response_time_ms=2000, explanation_quality=0.9)
    graph.record_interaction("algebra", correct=True, response_time_ms=1800, explanation_quality=0.85)
    
    print(f"   Confidence: {graph.temporal_nodes['algebra'].confidence:.2f}")
    
    selected = engine.select(graph)
    if selected:
        print(f"   → POLICY: {selected.id}")
        print(f"   → ACTION: {selected.decide()}")
    print()
    
    # Scenario 2: Teaching Empathy (student struggles)
    print("📚 TEACHING: Empathy (Social Skills)")
    graph.activate("empathy")
    
    # Student struggles
    graph.record_interaction("empathy", correct=False, response_time_ms=5000, explanation_quality=0.3)
    
    print(f"   Confidence: {graph.temporal_nodes['empathy'].confidence:.2f}")
    
    selected = engine.select(graph)
    if selected:
        print(f"   → POLICY: {selected.id}")
        print(f"   → ACTION: {selected.decide()}")
    print()
    
    print("✅ RESULT: Agent adapts to EACH concept independently!")
    print("   - Math: Advanced (ADVANCE_TOPIC)")
    print("   - Social: Basic (ASK_EXPLANATION)")
    print()
    print("=" * 70)
    print()
    
    # Original test
    print("=" * 70)
    print("EXAMPLE 2: SINGLE CONCEPT TESTING")
    print("=" * 70)
    print()
    
    # Create graph
    graph2 = Dialograph()

    # Add a concept
    graph2.add_node(SemanticNode(
        id="concept_bayes",
        type="Concept",
        content="Bayes Theorem"
    ))

    # Set it as current focus
    graph2.activate("concept_bayes")

    # CORRECTED: Define all 10 policies with proper condition classes
    policy1 = DeclarativePolicy(
        id="fragile_knowledge",
        when=LowConfidenceCondition(threshold=0.5),
        do="ASK_EXPLANATION",
        rather_than="ADVANCE_TOPIC",
        because="Low confidence indicates fragile understanding",
        priority=80,
        confidence=0.9
    )

    policy2 = DeclarativePolicy(
        id="overconfident_error",
        when=HighConfidenceWrongCondition(confidence_threshold=0.7),
        do="CONFRONT_MISCONCEPTION",
        rather_than="GIVE_HINT",
        because="High confidence errors indicate entrenched misconceptions",
        priority=90,
        confidence=0.95
    )

    policy3 = DeclarativePolicy(
        id="persistent_misconception",
        when=RepeatedWrongCondition(attempts=2),
        do="CONCEPTUAL_CONTRAST",
        rather_than="REPEAT_EXPLANATION",
        because="Repeated errors require restructuring, not repetition",
        priority=85,
        confidence=0.9
    )

    policy4 = DeclarativePolicy(
        id="guessing_behavior",
        when=FastIncorrectCondition(time_ms=2000),
        do="SLOW_DOWN_AND_EXPLAIN",
        rather_than="MARK_INCORRECT",
        because="Fast incorrect responses indicate disengaged guessing",
        priority=70,
        confidence=0.85
    )

    policy5 = DeclarativePolicy(
        id="illusion_of_mastery",
        when=FastCorrectLowExplanationQuality(time_ms=3000, quality_threshold=0.6),
        do="ASK_WHY_QUESTION",
        rather_than="MARK_MASTERED",
        because="Fluency without depth predicts poor transfer",
        priority=75,
        confidence=0.9
    )

    policy6 = DeclarativePolicy(
        id="forgetting_detected",
        when=HighDecayCondition(threshold=0.6),
        do="RETRIEVAL_PRACTICE",
        rather_than="INTRODUCE_NEW_CONCEPT",
        because="Reactivation before forgetting improves retention",
        priority=85,
        confidence=0.95
    )

    policy7 = DeclarativePolicy(
        id="productive_struggle",
        when=ImprovingButIncorrectCondition(),
        do="GIVE_HINT",
        rather_than="GIVE_SOLUTION",
        because="Guided struggle promotes deeper learning",
        priority=65,
        confidence=0.8
    )

    policy8 = DeclarativePolicy(
        id="mastery_achieved",
        when=HighConfidenceCorrectRepeated(times=2, confidence_threshold=0.8),
        do="ADVANCE_TOPIC",
        rather_than="ASK_MORE_PRACTICE",
        because="Repeated correct performance indicates mastery",
        priority=60,
        confidence=0.9
    )

    policy9 = DeclarativePolicy(
        id="cognitive_overload",
        when=LongLatencyIncorrectCondition(time_ms=10000),
        do="REDUCE_COMPLEXITY",
        rather_than="ADD_HINTS",
        because="Excessive cognitive load impairs learning",
        priority=85,
        confidence=0.9
    )

    policy10 = DeclarativePolicy(
        id="transfer_ready",
        when=HighConfidenceVariedContextCorrect(min_attempts=3, confidence_threshold=0.85),
        do="ASK_TRANSFER_QUESTION",
        rather_than="REPEAT_SIMILAR_PROBLEM",
        because="Varied success predicts readiness for transfer",
        priority=55,
        confidence=0.85
    )

    # Compile all policies
    engine2 = PolicyEngine([
        compile_policy(policy1),
        compile_policy(policy2),
        compile_policy(policy3),
        compile_policy(policy4),
        compile_policy(policy5),
        compile_policy(policy6),
        compile_policy(policy7),
        compile_policy(policy8),
        compile_policy(policy9),
        compile_policy(policy10)
    ])

    # Simulate learner interactions
    print("TESTING POLICY SYSTEM")
    print("=" * 70)
    print()

    # Test 1: Low confidence triggers fragile knowledge policy
    print("TEST 1: Learner has low confidence (0.3)")
    graph2.temporal_nodes["concept_bayes"].confidence = 0.3
    selected = engine2.select(graph2)
    if selected:
        print(f"  ✓ ACTION: {selected.decide()}")
        print(f"  ✓ WHY: {selected.explain(graph2)}")
    print()

    # Test 2: Record a wrong answer quickly (guessing)
    print("TEST 2: Learner answers incorrectly in 1500ms (guessing)")
    graph2.record_interaction("concept_bayes", correct=False, response_time_ms=1500)
    selected = engine2.select(graph2)
    if selected:
        print(f"  ✓ ACTION: {selected.decide()}")
        print(f"  ✓ WHY: {selected.explain(graph2)}")
    print()

    # Test 3: Record another wrong answer (persistent misconception)
    print("TEST 3: Learner answers incorrectly again (persistent error)")
    graph2.record_interaction("concept_bayes", correct=False, response_time_ms=4000)
    selected = engine2.select(graph2)
    if selected:
        print(f"  ✓ ACTION: {selected.decide()}")
        print(f"  ✓ WHY: {selected.explain(graph2)}")
    print()

    # Test 4: Correct answer with high confidence
    print("TEST 4: Learner gets it right, confidence increases")
    graph2.record_interaction("concept_bayes", correct=True, response_time_ms=3000, explanation_quality=0.8)
    graph2.record_interaction("concept_bayes", correct=True, response_time_ms=2500, explanation_quality=0.85)
    selected = engine2.select(graph2)
    if selected:
        print(f"  ✓ ACTION: {selected.decide()}")
        print(f"  ✓ WHY: {selected.explain(graph2)}")
    else:
        print("  ✓ No intervention needed - learner is doing well")
    print()

    # Show final state
    state = graph2.temporal_nodes["concept_bayes"]
    print("=" * 70)
    print("FINAL LEARNER STATE:")
    print(f"  Confidence: {state.confidence:.2f}")
    print(f"  Total attempts: {state.total_attempts}")
    print(f"  Correct: {state.correct_count}, Errors: {state.error_count}")
    print(f"  Consecutive correct: {state.consecutive_correct}")
    print("=" * 70)