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
    node_id: str
    created_at: datetime
    last_activated_at: datetime
    activation_count: int
    decay_score: float
    confidence: float


# ============================================================
# 3. DIALOGRAPH (OWNS EVERYTHING)
# ============================================================

class Dialograph:
    def __init__(self):
        self.semantic_nodes: Dict[str, SemanticNode] = {}
        self.semantic_edges: List[SemanticEdge] = []

        self.temporal_nodes: Dict[str, TemporalNodeState] = {}

    # ---- semantic registration ----
    def add_node(self, node: SemanticNode):
        self.semantic_nodes[node.id] = node
        self.temporal_nodes[node.id] = TemporalNodeState(
            node_id=node.id,
            created_at=datetime.now(),
            last_activated_at=datetime.now(),
            activation_count=0,
            decay_score=1.0,
            confidence=1.0
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


class LowConfidenceCondition(Condition):
    def __init__(self, threshold: float):
        self.threshold = threshold

    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        for node_id, state in graph.temporal_nodes.items():
            if state.confidence < self.threshold:
                matches.append({
                    "node_id": node_id,
                    "confidence": state.confidence
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
        avg_conf = sum(m["confidence"] for m in matches) / len(matches)
        return (1.0 - avg_conf) * self.confidence

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
        candidates = []

        for policy in self.policies:
            if policy.applies(graph):
                strength = policy.score(graph)
                if strength > 0:
                    candidates.append((policy, strength))

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: (x[0].priority, x[1]),
            reverse=True
        )
        return candidates[0][0]


# ============================================================
# 8. EXAMPLE USAGE (END-TO-END)
# ============================================================

if __name__ == "__main__":
    graph = Dialograph()

    graph.add_node(SemanticNode(
        id="concept_bayes",
        type="Concept",
        content="Bayes Theorem"
    ))

    graph.activate("concept_bayes", confidence=0.4)

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
        when=HighConfidenceWrongCondition(confidence=0.8),
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
        when=FastCorrectLowExplanationQuality(),
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
        when=HighConfidenceCorrectRepeated(times=2),
        do="ADVANCE_TOPIC",
        rather_than="ASK_MORE_PRACTICE",
        because="Repeated correct performance indicates mastery",
        priority=60,
        confidence=0.9
    )

    policy9 = DeclarativePolicy(
        id="cognitive_overload",
        when=LongLatencyIncorrectCondition(),
        do="REDUCE_COMPLEXITY",
        rather_than="ADD_HINTS",
        because="Excessive cognitive load impairs learning",
        priority=85,
        confidence=0.9
    )

    policy10 = DeclarativePolicy(
        id="transfer_ready",
        when=HighConfidenceVariedContextCorrect(),
        do="ASK_TRANSFER_QUESTION",
        rather_than="REPEAT_SIMILAR_PROBLEM",
        because="Varied success predicts readiness for transfer",
        priority=55,
        confidence=0.85
    )


    engine = PolicyEngine([
        compile_policy(policy1, policy2....)
    ])

    selected = engine.select(graph)

    if selected:
        print("ACTION:", selected.decide())
        print("WHY:", selected.explain(graph))
    else:
        print("ACTION: DEFAULT")
