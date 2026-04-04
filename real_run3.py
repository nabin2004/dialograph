from dataclasses import dataclass
from datetime import datetime
from math import exp
import os
from typing import Any, Dict, List, Literal, Optional
import json
import random
from pathlib import Path

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Default horizon for paper-grade evaluation (graphs-on runs need enough turns to show learning).
DEFAULT_SIMULATION_TURNS = 50

INTERVENTION_ACTIONS = frozenset({"ask_why", "give_hint", "challenge", "restructure"})
MASTERY_CONFIDENCE_THRESHOLD = 0.8
MASTERY_STREAK_LEN = 3
PREMATURE_ADVANCE_CONFIDENCE = 0.7
SLIDING_ACCURACY_WINDOW = 3

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_OPENROUTER_MODEL = "openai/gpt-4o-mini"


# ============================================================
# Core Graph Structures
# ============================================================

@dataclass(frozen=True)
class SemanticNode:
    id: str
    type: str
    content: str


@dataclass(frozen=True)
class SemanticEdge:
    source: str
    target: str
    relation_type: str


@dataclass
class TemporalNodeState:
    node_id: str
    created_at: datetime
    last_activated_at: datetime
    activation_count: int
    confidence: float
    last_activated_turn: int
    memory_strength: float
    retention: float


# ============================================================
# Dialograph
# ============================================================

class Dialograph:
    def __init__(self):
        self.semantic_nodes: Dict[str, SemanticNode] = {}
        self.semantic_edges: List[SemanticEdge] = []
        self.temporal_nodes: Dict[str, TemporalNodeState] = {}

    def add_node(self, node: SemanticNode):
        self.semantic_nodes[node.id] = node
        self.temporal_nodes[node.id] = TemporalNodeState(
            node_id=node.id,
            created_at=datetime.now(),
            last_activated_at=datetime.now(),
            activation_count=0,
            confidence=0.4,
            last_activated_turn=0,
            memory_strength=1.5,
            retention=1.0,
        )

    def add_edge(self, edge: SemanticEdge):
        self.semantic_edges.append(edge)

    def update_retention(self, node_id: str, current_turn: int):
        state = self.temporal_nodes[node_id]
        dt = current_turn - state.last_activated_turn
        state.retention = exp(-dt / state.memory_strength)

    def activate(self, node_id: str, confidence: Optional[float], turn_idx: int):
        state = self.temporal_nodes[node_id]
        state.last_activated_at = datetime.now()
        state.activation_count += 1
        state.last_activated_turn = turn_idx
        if confidence is not None:
            state.confidence = confidence


# ============================================================
# Graph Builder
# ============================================================

def build_photosynthesis_graph() -> Dialograph:
    g = Dialograph()
    nodes = [
        SemanticNode("photosynthesis", "concept", "Convert light energy to chemical energy"),
        SemanticNode("light_reactions", "process", "Produce ATP and NADPH"),
        SemanticNode("photosystem_ii", "component", "Initial electron excitation"),
        SemanticNode("electron_transport_chain", "process", "Generate proton gradient"),
        SemanticNode("photosystem_i", "component", "Reduce NADP+ to NADPH"),
    ]
    for n in nodes:
        g.add_node(n)

    edges = [
        SemanticEdge("photosynthesis", "light_reactions", "prerequisite"),
        SemanticEdge("light_reactions", "photosystem_ii", "prerequisite"),
        SemanticEdge("photosystem_ii", "electron_transport_chain", "prerequisite"),
        SemanticEdge("electron_transport_chain", "photosystem_i", "prerequisite"),
    ]
    for e in edges:
        g.add_edge(e)

    return g


def get_next_nodes(graph: Dialograph, node_id: str) -> List[str]:
    return [e.target for e in graph.semantic_edges if e.source == node_id]


def build_single_node_graph() -> Dialograph:
    """One concept only — policies fire, but navigation cannot test multi-node structure."""
    g = Dialograph()
    n = SemanticNode(
        "photosynthesis",
        "concept",
        "Photosynthesis: convert light energy to chemical energy (full unit).",
    )
    g.add_node(n)
    return g


# ============================================================
# External baselines & run configuration
# ============================================================

PolicyMode = Literal["dialograph", "none", "kt", "kt_bkt", "kt_dkt_style"]

KT_POLICY_MODES = frozenset({"kt", "kt_bkt", "kt_dkt_style"})

KT_POLICY_LABELS: Dict[str, str] = {
    "kt": "KT_heuristic",
    "kt_bkt": "KT_BKT",
    "kt_dkt_style": "KT_DKT_style",
}


@dataclass(frozen=True)
class SimulationRunConfig:
    """
    Paper-oriented conditions: full system, ablations, and external baselines.

    ``llm_tutor_baseline``: no graph, no Dialograph policies, no graph memory —
    a naive tutor that only reacts via ``llm_baseline_decision`` (fairer than
    always saying \"explain\").
    """

    name: str
    graphs_on: bool
    policy_mode: PolicyMode = "dialograph"
    temporal_on: bool = True
    navigation_on: bool = True
    llm_tutor_baseline: bool = False

    def __post_init__(self) -> None:
        if self.llm_tutor_baseline and self.graphs_on:
            raise ValueError("llm_tutor_baseline requires graphs_on=False")


def llm_baseline_decision(correct: bool, turn_idx: int) -> str:
    """Naive tutor script: respond to correctness + periodic questioning."""
    if not correct:
        return "give_hint"
    if turn_idx % 3 == 0:
        return "ask_question"
    return "explain"


class SimpleKT:
    """
    Heuristic scalar “mastery” (not classical BKT/DKT). Kept for comparison;
    prefer ``BKT`` or ``DKTStyle`` for reviewer-facing KT baselines.
    """

    def __init__(self, mastery: float = 0.3):
        self.mastery = mastery

    @property
    def belief(self) -> float:
        return self.mastery

    def update(self, correct: bool) -> None:
        if correct:
            self.mastery += 0.1 * (1.0 - self.mastery)
        else:
            self.mastery -= 0.1 * self.mastery
        self.mastery = max(0.01, min(0.99, self.mastery))

    def decide(self) -> str:
        if self.mastery < 0.5:
            return "review"
        if self.mastery < 0.8:
            return "practice"
        return "advance"


class BKT:
    """
    One-skill Bayesian Knowledge Tracing (Bayesian update + learning transition).
    Interpretable baseline; not fitted to real data (fixed p_learn, p_slip, p_guess).
    """

    def __init__(
        self,
        p_init: float = 0.3,
        p_learn: float = 0.2,
        p_slip: float = 0.1,
        p_guess: float = 0.2,
    ):
        self.p_know = p_init
        self.p_learn = p_learn
        self.p_slip = p_slip
        self.p_guess = p_guess

    @property
    def belief(self) -> float:
        return self.p_know

    def update(self, correct: bool) -> None:
        if correct:
            num = self.p_know * (1.0 - self.p_slip)
            den = num + (1.0 - self.p_know) * self.p_guess
        else:
            num = self.p_know * self.p_slip
            den = num + (1.0 - self.p_know) * (1.0 - self.p_guess)
        if den <= 0.0:
            return
        self.p_know = num / den
        self.p_know = self.p_know + (1.0 - self.p_know) * self.p_learn
        self.p_know = max(0.01, min(0.99, self.p_know))

    def decide(self) -> str:
        if self.p_know < 0.5:
            return "review"
        if self.p_know < 0.8:
            return "practice"
        return "advance"


class DKTStyle:
    """
    Scalar latent state with the same update shape as a gated hidden unit (not trained).
    Credible “deep KT style” comparison without PyTorch or datasets.
    """

    def __init__(self, hidden: float = 0.5):
        self.hidden = hidden

    @property
    def belief(self) -> float:
        return self.hidden

    def update(self, correct: bool) -> None:
        if correct:
            self.hidden += 0.1 * (1.0 - self.hidden)
        else:
            self.hidden -= 0.1 * self.hidden
        self.hidden = max(0.0, min(1.0, self.hidden))

    def decide(self) -> str:
        if self.hidden < 0.4:
            return "review"
        if self.hidden < 0.7:
            return "practice"
        return "advance"


def make_kt_controller(policy_mode: PolicyMode):
    if policy_mode == "kt":
        return SimpleKT()
    if policy_mode == "kt_bkt":
        return BKT()
    if policy_mode == "kt_dkt_style":
        return DKTStyle()
    return None


# Fixed topic for LLM-only baseline (no semantic graph).
LLM_BASELINE_TOPIC = SemanticNode(
    "synthetic_topic",
    "concept",
    "Photosynthesis: light-dependent and light-independent reactions, ATP/NADPH, and carbon fixation.",
)


def _fresh_llm_baseline_state() -> TemporalNodeState:
    return TemporalNodeState(
        node_id=LLM_BASELINE_TOPIC.id,
        created_at=datetime.now(),
        last_activated_at=datetime.now(),
        activation_count=0,
        confidence=0.4,
        last_activated_turn=0,
        memory_strength=1.5,
        retention=1.0,
    )


# ============================================================
# Learners
# ============================================================

class SimulatedLearner:
    def __init__(self, name: str):
        self.name = name

    def respond(self, node: SemanticNode, state: TemporalNodeState):
        raise NotImplementedError


class FragileCorrectLearner(SimulatedLearner):
    def respond(self, node, state):
        return True, min(state.confidence + 0.05, 0.9), "shallow"


class MisconceptionLearner(SimulatedLearner):
    """
    Starts unreliable and improves with repeated activation so policies and
    metrics (e.g. intervention effectiveness, time-to-mastery) have a real signal.
    """

    def __init__(self, name: str, rng_seed: Optional[int] = None):
        super().__init__(name)
        seed = rng_seed if rng_seed is not None else (hash(name) & 0xFFFFFFFF) or 1
        self._rng = random.Random(seed)

    def respond(self, node, state):
        prob_correct = min(0.1 + 0.1 * state.activation_count, 0.6)
        correct = self._rng.random() < prob_correct
        return correct, state.confidence, "confident-but-wrong"


class OverconfidentGuesser(SimulatedLearner):
    def respond(self, node, state):
        correct = state.activation_count % 2 == 0
        return correct, 0.8, "fluent"


# ============================================================
# Memory Strength Update
# ============================================================

def update_memory_strength(state: TemporalNodeState, correct: bool, explanation: str):
    if not correct:
        state.memory_strength *= 0.9
    elif explanation == "shallow":
        state.memory_strength += 0.3
    elif explanation == "fluent":
        state.memory_strength += 0.6
    state.memory_strength = max(0.5, min(state.memory_strength, 8.0))


# ============================================================
# Policies
# ============================================================

# ============================================================
# Pedagogical Policies (from Table 3)
# ============================================================

def policy_decision(state, correct, explanation):
    """
    Returns (action, policy_name) based on learner state.
    Policies are layered from urgent/critical -> supportive -> advancement.
    """

    # --------------------------------------------------------
    # Fragile Knowledge: Teach from basics when confidence is low
    # Metacognitive calibration [9]
    if state.confidence < 0.6 and correct:
        return "ask_why", "Fragile Knowledge"

    # --------------------------------------------------------
    # Overconfident Error: Correct misconceptions directly
    # Dunning-Kruger effect [10]
    if not correct and state.confidence > 0.7:
        return "challenge", "Overconfident Error"

    # --------------------------------------------------------
    # Persistent Misconception: Restructure knowledge after repeated errors
    # Conceptual change theory [11]
    if not correct and state.activation_count > 2:
        return "restructure", "Persistent Misconception"

    # --------------------------------------------------------
    # Guessing / Low Engagement: Slow down and elicit explanation
    # Response-time modeling [12]
    if explanation in ("fluent", "shallow") and correct:
        return "elicit_explanation", "Guessing / Low Engagement"

    # --------------------------------------------------------
    # Illusion of Mastery: Request deeper explanation when shallow correctness occurs
    # Fluency illusion [9]
    if explanation == "shallow":
        return "give_hint", "Illusion of Mastery"

    # --------------------------------------------------------
    # Forgetting / Spaced Reactivation: Trigger retrieval practice
    # Forgetting curve [13]
    if state.retention < 0.3:
        return "review", "Forgetting / Spaced Reactivation"

    # --------------------------------------------------------
    # Productive Struggle: Provide hints for improving but incorrect learners
    # Productive failure [14]
    if not correct:
        return "give_hint", "Productive Struggle"

    # --------------------------------------------------------
    # Mastery-Based Advancement: Advance only after stable correct performance
    # Mastery learning [15]
    if correct and state.confidence >= 0.7 and state.memory_strength > 2.0:
        return "advance", "Mastery-Based Advancement"

    # --------------------------------------------------------
    # Cognitive Overload: Reduce complexity for struggling learners
    # Cognitive Load Theory [16]
    if state.confidence < 0.4:
        return "simplify", "Cognitive Overload"

    # --------------------------------------------------------
    # Transfer Readiness: Introduce new context or problems
    # Transfer taxonomy [17]
    if correct and state.memory_strength > 3.0:
        return "transfer", "Transfer Readiness"

    # --------------------------------------------------------
    # Default fallback
    return "advance", "Default Policy"


def no_policy_decision(correct):
    return ("advance", None) if correct else ("give_hint", None)


# ============================================================
# LLM Agent (OpenRouter — OpenAI-compatible API)
# ============================================================

class DialographAgentLLM:
    """
    Calls OpenRouter (https://openrouter.ai). Set ``OPENROUTER_API_KEY`` in the
    environment. Override the model with ``OPENROUTER_MODEL`` or pass
    ``model_name`` explicitly (OpenRouter model id, e.g. ``anthropic/claude-3.5-haiku``).
    Optional: ``OPENROUTER_HTTP_REFERER``, ``OPENROUTER_APP_TITLE`` for OpenRouter rankings.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        *,
        api_key: Optional[str] = None,
        base_url: str = OPENROUTER_BASE_URL,
    ):
        model = model_name or os.getenv("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL)
        key = api_key or os.getenv("OPENROUTER_API_KEY")
        if not key:
            raise ValueError(
                "OpenRouter API key missing: set environment variable OPENROUTER_API_KEY "
                "or pass api_key= to DialographAgentLLM."
            )
        headers: Dict[str, str] = {}
        referer = os.getenv("OPENROUTER_HTTP_REFERER")
        if referer:
            headers["HTTP-Referer"] = referer
        headers["X-Title"] = os.getenv("OPENROUTER_APP_TITLE", "Dialograph real_run3")
        self.llm = ChatOpenAI(
            model=model,
            api_key=key,
            base_url=base_url,
            default_headers=headers or None,
        )
        self.system = SystemMessage(content="You are a concise tutoring agent.")

    def next_action(self, instruction: str):
        messages = [self.system, HumanMessage(content=instruction)]
        return self.llm.invoke(messages).content


# ============================================================
# Turn Logic
# ============================================================

def run_turn(
    graph: Optional[Dialograph],
    node_id: str,
    learner: SimulatedLearner,
    agent: DialographAgentLLM,
    log: List[Dict[str, Any]],
    turn_idx: int,
    config: SimulationRunConfig,
    kt: Optional[Any],
    llm_state: Optional[TemporalNodeState],
) -> tuple[str, str]:
    base_log: Dict[str, Any] = {"turn": turn_idx, "condition": config.name}

    # ----- LLM-only tutor baseline (no graph, no Dialograph memory/policies) -----
    if config.llm_tutor_baseline:
        assert llm_state is not None
        correct, new_conf, explanation = learner.respond(LLM_BASELINE_TOPIC, llm_state)
        action = llm_baseline_decision(correct, turn_idx)
        instruction = f"{action.upper()}: {LLM_BASELINE_TOPIC.content}"
        response = agent.next_action(instruction)
        llm_state.activation_count += 1
        llm_state.last_activated_turn = turn_idx
        llm_state.confidence = new_conf

        log.append(
            {
                **base_log,
                "node": None,
                "learner_correct": correct,
                "learner_explanation": explanation,
                "policy": "LLM_tutor_baseline",
                "action": action,
                "confidence": round(new_conf, 2),
                "retention": None,
                "memory_strength": None,
                "kt_mastery": None,
                "temporal_on": False,
                "agent_instruction": instruction,
                "agent_response": response,
            }
        )
        return action, node_id

    assert graph is not None
    state = graph.temporal_nodes[node_id]
    node = graph.semantic_nodes[node_id]

    if config.temporal_on:
        graph.update_retention(node_id, turn_idx)

    correct, new_conf, explanation = learner.respond(node, state)

    if config.temporal_on:
        update_memory_strength(state, correct, explanation)

    if config.policy_mode == "dialograph":
        action, policy = policy_decision(state, correct, explanation)
    elif config.policy_mode == "none":
        action, policy = no_policy_decision(correct)
    elif config.policy_mode in KT_POLICY_MODES:
        assert kt is not None
        kt.update(correct)
        action = kt.decide()
        policy = KT_POLICY_LABELS[config.policy_mode]

    instruction = f"{action.upper()}: {node.content}"
    response = agent.next_action(instruction)

    graph.activate(node_id, new_conf, turn_idx)

    log.append(
        {
            **base_log,
            "node": node_id,
            "learner_correct": correct,
            "learner_explanation": explanation,
            "policy": policy,
            "action": action,
            "confidence": round(new_conf, 2),
            "retention": round(state.retention, 3),
            "memory_strength": round(state.memory_strength, 2),
            "kt_mastery": round(kt.belief, 4) if kt is not None else None,
            "temporal_on": config.temporal_on,
            "agent_instruction": instruction,
            "agent_response": response,
        }
    )

    if action == "advance" and config.navigation_on:
        nxt = get_next_nodes(graph, node_id)
        return action, nxt[0] if nxt else node_id

    return action, node_id


# ============================================================
# Simulation + Metrics
# ============================================================

def learning_curve(log: List[Dict[str, Any]]) -> List[float]:
    """Cumulative accuracy over full log indices (turns with no label are skipped)."""
    curve: List[float] = []
    correct_so_far = 0
    for i, r in enumerate(log):
        if r["learner_correct"] is not None:
            if r["learner_correct"]:
                correct_so_far += 1
            curve.append(correct_so_far / (i + 1))
    return curve


def sliding_accuracy(
    log: List[Dict[str, Any]], k: int = SLIDING_ACCURACY_WINDOW
) -> List[Optional[float]]:
    """k-turn windowed accuracy; stabilizes noisy learners."""
    acc: List[Optional[float]] = []
    for i in range(len(log)):
        window = log[max(0, i - k + 1) : i + 1]
        vals = [r["learner_correct"] for r in window if r["learner_correct"] is not None]
        if vals:
            acc.append(sum(vals) / len(vals))
        else:
            acc.append(None)
    return acc


def concept_stability(log: List[Dict[str, Any]]) -> Dict[str, float]:
    """Per-node fraction of correct responses; high spread → inconsistent knowledge."""
    per_node: Dict[str, List[Optional[bool]]] = {}
    for r in log:
        if r["node"] is None:
            continue
        per_node.setdefault(r["node"], []).append(r["learner_correct"])
    stability: Dict[str, float] = {}
    for node, vals in per_node.items():
        scored = [v for v in vals if v is not None]
        if scored:
            stability[node] = round(sum(1 for v in scored if v) / len(scored), 4)
    return stability


def time_to_mastery(
    log: List[Dict[str, Any]],
    threshold: float = MASTERY_CONFIDENCE_THRESHOLD,
    streak: int = MASTERY_STREAK_LEN,
) -> Optional[int]:
    """First turn index (0-based) where confidence stays ≥ threshold for `streak` consecutive graph-on rows."""
    count = 0
    for i, r in enumerate(log):
        c = r.get("confidence")
        if c is not None and c >= threshold:
            count += 1
            if count >= streak:
                return i
        elif c is not None:
            count = 0
    return None


def premature_advancement(
    log: List[Dict[str, Any]], low_confidence: float = PREMATURE_ADVANCE_CONFIDENCE
) -> float:
    """Share of advance actions taken when confidence is missing or below threshold."""
    bad = 0
    total = 0
    for r in log:
        if r["action"] != "advance":
            continue
        total += 1
        conf = r.get("confidence")
        if conf is None or conf < low_confidence:
            bad += 1
    return round(bad / total, 4) if total > 0 else 0.0


def intervention_effectiveness(log: List[Dict[str, Any]]) -> float:
    """Fraction of intervention turns followed by increased confidence (graph-on rows)."""
    improvements = 0
    interventions = 0
    for i in range(1, len(log)):
        prev, curr = log[i - 1], log[i]
        if prev["action"] not in INTERVENTION_ACTIONS:
            continue
        p_conf, c_conf = prev.get("confidence"), curr.get("confidence")
        if p_conf is None or c_conf is None:
            continue
        interventions += 1
        if c_conf > p_conf:
            improvements += 1
    return round(improvements / interventions, 4) if interventions > 0 else 0.0


def summarize_stability(stability: Dict[str, float]) -> Dict[str, float]:
    """Aggregate concept stability for compact JSON / tables."""
    if not stability:
        return {"mean": 0.0, "min": 0.0, "max": 0.0}
    vals = list(stability.values())
    return {
        "mean": round(sum(vals) / len(vals), 4),
        "min": round(min(vals), 4),
        "max": round(max(vals), 4),
    }


def run_simulation(
    learner: SimulatedLearner,
    config: SimulationRunConfig,
    turns: int = DEFAULT_SIMULATION_TURNS,
    agent: Optional[DialographAgentLLM] = None,
) -> List[Dict[str, Any]]:
    agent = agent or DialographAgentLLM()
    log: List[Dict[str, Any]] = []
    current_node = "photosynthesis"

    if config.llm_tutor_baseline:
        graph: Optional[Dialograph] = None
        llm_state = _fresh_llm_baseline_state()
    else:
        llm_state = None
        if not config.navigation_on:
            graph = build_single_node_graph()
        else:
            graph = build_photosynthesis_graph()

    kt = (
        make_kt_controller(config.policy_mode)
        if config.policy_mode in KT_POLICY_MODES and config.graphs_on
        else None
    )

    for t in range(turns):
        action, current_node = run_turn(
            graph,
            current_node,
            learner,
            agent,
            log,
            t,
            config,
            kt,
            llm_state,
        )

    return log


def compute_metrics(log: List[Dict[str, Any]]) -> Dict[str, Any]:
    valid = [r for r in log if r["confidence"] is not None]
    stability = concept_stability(log)
    curve = learning_curve(log)
    slide = sliding_accuracy(log)

    kt_vals = [r["kt_mastery"] for r in log if r.get("kt_mastery") is not None]

    out: Dict[str, Any] = {
        "turns": len(log),
        # Time-aware and paper-oriented
        "learning_curve": [round(x, 4) for x in curve],
        "sliding_accuracy_k3": [None if v is None else round(v, 4) for v in slide],
        "concept_stability_by_node": stability,
        "concept_stability_summary": summarize_stability(stability),
        "time_to_mastery_turn": time_to_mastery(log),
        "premature_advancement_rate": premature_advancement(log),
        "intervention_effectiveness": intervention_effectiveness(log),
        "advance_rate": round(sum(1 for r in log if r["action"] == "advance") / len(log), 3)
        if log
        else 0.0,
        "mean_kt_mastery": round(sum(kt_vals) / len(kt_vals), 4) if kt_vals else None,
    }

    if not valid:
        out["mean_confidence"] = None
        out["mean_retention"] = None
        out["mean_memory_strength"] = None
        out["mastery_rate"] = None
        out["error_rate"] = None
        return out

    out.update(
        {
            # Legacy scalars (ablations / baselines)
            "mean_confidence": round(sum(r["confidence"] for r in valid) / len(valid), 3),
            "mean_retention": round(sum(r["retention"] for r in valid) / len(valid), 3),
            "mean_memory_strength": round(
                sum(r["memory_strength"] for r in valid) / len(valid), 3
            ),
            "mastery_rate": round(
                sum(1 for r in valid if r["confidence"] >= MASTERY_CONFIDENCE_THRESHOLD)
                / len(valid),
                3,
            ),
            "error_rate": round(
                sum(1 for r in valid if not r["learner_correct"]) / len(valid), 3,
            ),
        }
    )
    return out


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    learners = [
        FragileCorrectLearner("fragile"),
        MisconceptionLearner("misconception"),
        OverconfidentGuesser("guesser"),
    ]

    # Graph | Temporal | Policy — reviewer-oriented grid (+ external baselines).
    conditions: List[SimulationRunConfig] = [
        SimulationRunConfig(
            "full_dialograph",
            graphs_on=True,
            policy_mode="dialograph",
            temporal_on=True,
            navigation_on=True,
        ),
        SimulationRunConfig(
            "no_policy",
            graphs_on=True,
            policy_mode="none",
            temporal_on=True,
            navigation_on=True,
        ),
        SimulationRunConfig(
            "no_temporal",
            graphs_on=True,
            policy_mode="dialograph",
            temporal_on=False,
            navigation_on=True,
        ),
        SimulationRunConfig(
            "single_node",
            graphs_on=True,
            policy_mode="dialograph",
            temporal_on=True,
            navigation_on=False,
        ),
        SimulationRunConfig(
            "llm_baseline",
            graphs_on=False,
            llm_tutor_baseline=True,
        ),
        SimulationRunConfig(
            "kt_heuristic_baseline",
            graphs_on=True,
            policy_mode="kt",
            temporal_on=True,
            navigation_on=True,
        ),
        SimulationRunConfig(
            "kt_bkt_baseline",
            graphs_on=True,
            policy_mode="kt_bkt",
            temporal_on=True,
            navigation_on=True,
        ),
        SimulationRunConfig(
            "kt_dkt_style_baseline",
            graphs_on=True,
            policy_mode="kt_dkt_style",
            temporal_on=True,
            navigation_on=True,
        ),
    ]

    log_dir = Path("simulation_logs")
    log_dir.mkdir(exist_ok=True)

    for learner in learners:
        for cfg in conditions:
            log = run_simulation(learner, cfg)
            metrics = compute_metrics(log)

            fname = f"{learner.name}_{cfg.name}"
            with open(log_dir / f"{fname}_log.json", "w") as f:
                json.dump(log, f, indent=2)

            with open(log_dir / f"{fname}_metrics.json", "w") as f:
                json.dump(metrics, f, indent=2)

            print(f"{learner.name} | {cfg.name} | metrics:", metrics)
