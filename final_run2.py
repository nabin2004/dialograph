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

def build_photosynthesis_graph():
    g = Dialograph()
    nodes = [
        SemanticNode("photosynthesis", "concept",
                     "Photosynthesis converts light energy into chemical energy"),
        SemanticNode("light_reactions", "process",
                     "Light reactions produce ATP and NADPH"),
        SemanticNode("photosystem_ii", "component",
                     "Photosystem II excites electrons"),
        SemanticNode("electron_transport_chain", "process",
                     "Electron transport creates a proton gradient"),
        SemanticNode("photosystem_i", "component",
                     "Photosystem I produces NADPH"),
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


def get_next_nodes(graph, node_id):
    return [e.target for e in graph.semantic_edges if e.source == node_id]


# ============================================================
# Learners (produce utterances + correctness)
# ============================================================

class SimulatedLearner:
    def __init__(self, name):
        self.name = name

    def respond(self, node, state):
        raise NotImplementedError


class FragileCorrectLearner(SimulatedLearner):
    def respond(self, node, state):
        text = f"I think {node.content}, but I might be missing details."
        return text, True, min(state.confidence + 0.05, 0.9), "shallow"


class MisconceptionLearner(SimulatedLearner):
    def respond(self, node, state):
        text = f"{node.content} happens because plants absorb sugar from soil."
        return text, False, state.confidence, "confident-but-wrong"


class OverconfidentGuesser(SimulatedLearner):
    def respond(self, node, state):
        correct = state.activation_count % 2 == 0
        text = f"This is obvious. {node.content}."
        return text, correct, 0.8, "fluent"


# ============================================================
# Memory Update
# ============================================================

def update_memory_strength(state, correct, explanation):
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
# Tutor LLM (no hidden state)
# ============================================================

class DialographAgentLLM:
    def __init__(self, model_name="llama-3.1-8b-instant"):
        self.llm = ChatGroq(model=model_name)
        self.system = SystemMessage(
            content="You are a tutoring assistant. Be concise, corrective, and pedagogical."
        )

    def respond(self, tutor_prompt: str):
        messages = [
            self.system,
            HumanMessage(content=tutor_prompt),
        ]
        return self.llm.invoke(messages).content


# ============================================================
# Turn Logic (atomic dialogue step)
# ============================================================

def run_turn(graph, node_id, learner, agent,
             policies_on, graphs_on, convo, log, turn):

    # -------- Learner --------
    if graphs_on:
        state = graph.temporal_nodes[node_id]
        node = graph.semantic_nodes[node_id]
        graph.update_retention(node_id, turn)

        learner_text, correct, new_conf, explanation = learner.respond(node, state)
        update_memory_strength(state, correct, explanation)
        activated_nodes = [node_id]
    else:
        learner_text = "Okay."
        correct = new_conf = explanation = None
        activated_nodes = []

    convo.append({"role": "user", "content": learner_text})

    # -------- Policy --------
    if graphs_on and policies_on:
        action, policy = policy_decision(state, correct, explanation)
    elif graphs_on:
        action, policy = no_policy_decision(correct)
    else:
        action, policy = "advance", None

    # -------- Tutor --------
    tutor_prompt = f"""
Learner said:
{learner_text}

Correct: {correct}
Explanation type: {explanation}
Activated nodes: {activated_nodes}
Policy: {policy}
Action: {action}

Respond as a tutor.
""".strip()

    tutor_text = agent.respond(tutor_prompt)
    convo.append({"role": "assistant", "content": tutor_text})

    # -------- Graph update --------
    if graphs_on:
        graph.activate(node_id, new_conf, turn)

    # -------- Logging --------
    log.append({
        "turn": turn,
        "node": node_id if graphs_on else None,
        "learner_utterance": learner_text,
        "learner_correct": correct,
        "learner_explanation": explanation,
        "activated_nodes": activated_nodes,
        "policies_on": policies_on,
        "graphs_on": graphs_on,
        "policy": policy,
        "action": action,
        "tutor_prompt": tutor_prompt,
        "tutor_response": tutor_text,
        "confidence": round(new_conf, 2) if new_conf is not None else None,
        "retention": round(state.retention, 3) if graphs_on else None,
        "memory_strength": round(state.memory_strength, 2) if graphs_on else None,
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
            graph, current_node, learner, agent,
            policies_on, graphs_on, convo, log, t
        )

        if graphs_on and action == "advance":
            nxt = get_next_nodes(graph, current_node)
            if nxt:
                current_node = nxt[0]

    return log, convo


def compute_metrics(log):
    usable = [r for r in log if r["confidence"] is not None]
    if not usable:
        return {"turns": len(log)}

    return {
        "turns": len(log),
        "mean_confidence":
            round(sum(r["confidence"] for r in usable) / len(usable), 3),
        "mean_retention":
            round(sum(r["retention"] for r in usable) / len(usable), 3),
        "mean_memory_strength":
            round(sum(r["memory_strength"] for r in usable) / len(usable), 3),
        "advance_rate":
            round(sum(1 for r in log if r["action"] == "advance") / len(log), 3),
        "misconception_rate":
            round(sum(1 for r in usable if not r["learner_correct"]) / len(usable), 3),
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

    out = Path("simulation_logs")
    out.mkdir(exist_ok=True)

    for learner in learners:
        for name, policies_on, graphs_on in conditions:
            graph = build_photosynthesis_graph() if graphs_on else None
            log, convo = run_simulation(graph, learner, policies_on, graphs_on)
            metrics = compute_metrics(log)

            json.dump(log, open(out / f"{learner.name}_{name}_log.json", "w"), indent=2)
            json.dump(convo, open(out / f"{learner.name}_{name}_conversation.json", "w"), indent=2)
            json.dump(metrics, open(out / f"{learner.name}_{name}_metrics.json", "w"), indent=2)

            print(learner.name, name, metrics)
