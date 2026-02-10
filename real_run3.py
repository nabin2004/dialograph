from dataclasses import dataclass
from datetime import datetime
from math import exp
from typing import Dict, List, Optional
import json
from pathlib import Path

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage


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
    def respond(self, node, state):
        return False, state.confidence, "confident-but-wrong"


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
# LLM Agent
# ============================================================

class DialographAgentLLM:
    def __init__(self, model_name="llama-3.1-8b-instant"):
        self.llm = ChatGroq(model=model_name)
        self.system = SystemMessage(content="You are a concise tutoring agent.")

    def next_action(self, instruction: str):
        messages = [
            self.system,
            HumanMessage(content=instruction)
        ]
        return self.llm.invoke(messages).content


# ============================================================
# Turn Logic
# ============================================================

def run_turn(
    graph,
    node_id,
    learner,
    agent,
    policies_on,
    graphs_on,
    log,
    turn_idx
):
    # ---------------- graphs OFF ----------------
    if not graphs_on:
        instruction = "Explain the topic clearly and briefly."
        response = agent.next_action(instruction)

        log.append({
            "turn": turn_idx,
            "node": None,
            "learner_correct": None,
            "learner_explanation": None,
            "policy": None,
            "action": "advance",
            "confidence": None,
            "retention": None,
            "memory_strength": None,
            "agent_instruction": instruction,
            "agent_response": response,
        })
        return "advance", node_id

    # ---------------- graphs ON ----------------
    state = graph.temporal_nodes[node_id]
    node = graph.semantic_nodes[node_id]

    graph.update_retention(node_id, turn_idx)

    correct, new_conf, explanation = learner.respond(node, state)
    update_memory_strength(state, correct, explanation)

    if policies_on:
        action, policy = policy_decision(state, correct, explanation)
    else:
        action, policy = no_policy_decision(correct)

    instruction = f"{action.upper()}: {node.content}"
    response = agent.next_action(instruction)

    graph.activate(node_id, new_conf, turn_idx)

    log.append({
        "turn": turn_idx,
        "node": node_id,
        "learner_correct": correct,
        "learner_explanation": explanation,
        "policy": policy,
        "action": action,
        "confidence": round(new_conf, 2),
        "retention": round(state.retention, 3),
        "memory_strength": round(state.memory_strength, 2),
        "agent_instruction": instruction,
        "agent_response": response,
    })

    if action == "advance":
        nxt = get_next_nodes(graph, node_id)
        return action, nxt[0] if nxt else node_id

    return action, node_id


# ============================================================
# Simulation + Metrics
# ============================================================

def run_simulation(graph, learner, policies_on, graphs_on, turns=12):
    agent = DialographAgentLLM()
    log = []
    current_node = "photosynthesis"

    for t in range(turns):
        action, current_node = run_turn(
            graph,
            current_node,
            learner,
            agent,
            policies_on,
            graphs_on,
            log,
            t,
        )

    return log


def compute_metrics(log):
    valid = [r for r in log if r["confidence"] is not None]

    if not valid:
        return {"turns": len(log)}

    return {
        "turns": len(log),
        "mean_confidence": round(sum(r["confidence"] for r in valid) / len(valid), 3),
        "mean_retention": round(sum(r["retention"] for r in valid) / len(valid), 3),
        "mean_memory_strength": round(sum(r["memory_strength"] for r in valid) / len(valid), 3),
        "mastery_rate": round(sum(1 for r in valid if r["confidence"] >= 0.8) / len(valid), 3),
        "advance_rate": round(sum(1 for r in log if r["action"] == "advance") / len(log), 3),
        "error_rate": round(sum(1 for r in valid if not r["learner_correct"]) / len(valid), 3),
    }


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    learners = [
        FragileCorrectLearner("fragile"),
        MisconceptionLearner("misconception"),
        OverconfidentGuesser("guesser"),
    ]

    conditions = [
        ("policies_off_graphs_off", False, False),
        ("policies_off_graphs_on", False, True),
        ("policies_on_graphs_on", True, True),
    ]

    log_dir = Path("simulation_logs")
    log_dir.mkdir(exist_ok=True)

    for learner in learners:
        for name, policies_on, graphs_on in conditions:
            graph = build_photosynthesis_graph() if graphs_on else None
            log = run_simulation(graph, learner, policies_on, graphs_on)
            metrics = compute_metrics(log)

            with open(log_dir / f"{learner.name}_{name}_log.json", "w") as f:
                json.dump(log, f, indent=2)

            with open(log_dir / f"{learner.name}_{name}_metrics.json", "w") as f:
                json.dump(metrics, f, indent=2)

            print(f"{learner.name} | {name} | metrics:", metrics)
