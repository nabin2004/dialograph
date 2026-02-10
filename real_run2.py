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
        SemanticNode("photosynthesis", "concept", "Light energy to chemical energy"),
        SemanticNode("light_reactions", "process", "ATP and NADPH production"),
        SemanticNode("photosystem_ii", "component", "Electron excitation"),
        SemanticNode("electron_transport_chain", "process", "Proton gradient"),
        SemanticNode("photosystem_i", "component", "NADPH production"),
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
    return [
        e.target
        for e in graph.semantic_edges
        if e.source == node_id
    ]


# ============================================================
# Learners
# ============================================================

class SimulatedLearner:
    def __init__(self, name: str):
        self.name = name

    def respond(self, node, state):
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

def policy_decision(state, correct, explanation):
    if state.retention < 0.3:
        return "review", "Forgetting Recovery"
    if not correct:
        return "challenge", "Contradiction"
    if state.confidence < 0.6:
        return "ask_why", "Fragile Knowledge"
    if explanation == "shallow":
        return "give_hint", "Illusion of Mastery"
    return "advance", "Mastery"


def no_policy_decision(correct):
    return ("advance", None) if correct else ("give_hint", None)


# ============================================================
# LLM Agent
# ============================================================

class DialographAgentLLM:
    def __init__(self, model_name="llama-3.1-8b-instant"):
        self.llm = ChatGroq(model=model_name)
        self.system = SystemMessage(content="You are a helpful tutor.")

    def next_action(self, conversation):
        last = conversation[-1]["content"]
        msg = [
            self.system,
            HumanMessage(content=f"{last}")
        ]
        return self.llm.invoke(msg).content


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
    convo,
    log,
    turn_idx
):
    if not graphs_on:
        convo.append({"role": "system", "content": "Proceed."})
        response = agent.next_action(convo)
        convo.append({"role": "assistant", "content": response})

        log.append({
            "turn": turn_idx,
            "node": None,
            "action": "advance",
            "policy": None,
            "confidence": None,
            "retention": None,
            "memory_strength": None,
            "correct": None,
            "log_message": response,
        })
        return "advance"

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
    convo.append({"role": "system", "content": instruction})
    response = agent.next_action(convo)
    convo.append({"role": "assistant", "content": response})

    graph.activate(node_id, new_conf, turn_idx)

    log.append({
        "turn": turn_idx,
        "node": node_id,
        "action": action,
        "policy": policy,
        "confidence": round(new_conf, 2),
        "retention": round(state.retention, 3),
        "memory_strength": round(state.memory_strength, 2),
        "correct": correct,
        "log_message": response,
    })

    return action


# ============================================================
# Simulation + Metrics
# ============================================================

def run_simulation(graph, learner, policies_on, graphs_on, turns=12):
    agent = DialographAgentLLM()
    convo, log = [], []
    current_node = "photosynthesis"

    for t in range(turns):
        action = run_turn(
            graph,
            current_node,
            learner,
            agent,
            policies_on,
            graphs_on,
            convo,
            log,
            t
        )

        if graphs_on and action == "advance":
            nxt = get_next_nodes(graph, current_node)
            if nxt:
                current_node = nxt[0]

    return log


def compute_metrics(log):
    filtered = [r for r in log if r["confidence"] is not None]

    if not filtered:
        return {"turns": len(log)}

    return {
        "turns": len(log),
        "mean_confidence": round(sum(r["confidence"] for r in filtered) / len(filtered), 3),
        "mean_retention": round(sum(r["retention"] for r in filtered) / len(filtered), 3),
        "mean_memory_strength": round(sum(r["memory_strength"] for r in filtered) / len(filtered), 3),
        "mastery_rate": round(sum(1 for r in filtered if r["confidence"] >= 0.8) / len(filtered), 3),
        "advance_rate": round(sum(1 for r in log if r["action"] == "advance") / len(log), 3),
        "misconception_rate": round(sum(1 for r in filtered if not r["correct"]) / len(filtered), 3),
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
