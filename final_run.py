from dataclasses import dataclass
from math import exp
from pathlib import Path
from typing import Dict, List
import json
import statistics

from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

# ============================================================
# Global Parameters
# ============================================================

TIME_COMPRESSION = 5.0  # 1 dialog turn ≈ 5 time units (accelerated forgetting)

# ============================================================
# Core Structures
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
    activation_count: int = 0
    confidence: float = 0.4
    last_turn: int = 0
    memory_strength: float = 1.5
    retention: float = 1.0

# ============================================================
# Dialograph
# ============================================================

class Dialograph:
    def __init__(self):
        self.nodes: Dict[str, SemanticNode] = {}
        self.edges: List[SemanticEdge] = []
        self.state: Dict[str, TemporalNodeState] = {}

    def add_node(self, node: SemanticNode):
        self.nodes[node.id] = node
        self.state[node.id] = TemporalNodeState(node_id=node.id)

    def add_edge(self, edge: SemanticEdge):
        self.edges.append(edge)

    def update_retention(self, node_id, turn):
        s = self.state[node_id]
        dt = (turn - s.last_turn) * TIME_COMPRESSION  # ✅ explicit acceleration
        s.retention = exp(-dt / s.memory_strength)

    def activate(self, node_id, confidence, turn):
        s = self.state[node_id]
        s.activation_count += 1
        s.last_turn = turn
        if confidence is not None:
            s.confidence = confidence

# ============================================================
# Graph Builders
# ============================================================

def build_graph():
    g = Dialograph()
    g.add_node(SemanticNode(
        "photosynthesis", "concept",
        "Photosynthesis converts light energy into chemical energy"
    ))
    g.add_node(SemanticNode(
        "light_reactions", "process",
        "Light reactions produce ATP and NADPH"
    ))
    g.add_edge(SemanticEdge(
        "photosynthesis", "light_reactions", "prerequisite"
    ))
    return g

def next_nodes(g, nid):
    return [e.target for e in g.edges if e.source == nid]

# ============================================================
# Learners
# ============================================================

class Learner:
    def __init__(self, name): self.name = name
    def respond(self, node, state): raise NotImplementedError

class FragileLearner(Learner):
    def respond(self, node, state):
        return (
            f"I think {node.content}, but I might be missing details.",
            True,
            min(state.confidence + 0.05, 0.9),
            "shallow",
        )

class MisconceptionLearner(Learner):
    def respond(self, node, state):
        return (
            f"{node.content} happens because plants absorb sugar from soil.",
            False,
            state.confidence,
            "confident_wrong",
        )

class GuesserLearner(Learner):
    """A learner that guesses randomly with low confidence."""
    import random

    def respond(self, node, state):
        correct = self.random.choice([True, False])
        conf = self.random.uniform(0.3, 0.6)  # uncertain guesses
        expl = "shallow" if correct else "confident_wrong"
        text = f"I guess that {node.content}" if correct else f"I think {node.content} but maybe wrong"
        return text, correct, conf, expl

# ============================================================
# Memory Update
# ============================================================

def update_memory(state, correct, explanation):
    if not correct:
        state.memory_strength *= 0.9
    elif explanation == "shallow":
        state.memory_strength += 0.3
    else:
        state.memory_strength += 0.6
    state.memory_strength = max(0.5, min(state.memory_strength, 8.0))

# ============================================================
# Policies
# ============================================================

def policy(state, correct, explanation):
    if correct and state.confidence < 0.6:
        return "ask_why", "Fragile Knowledge"
    if not correct and state.confidence > 0.7:
        return "challenge", "Overconfident Error"
    if not correct and state.activation_count > 2:
        return "restructure", "Persistent Misconception"
    if correct and explanation == "shallow":
        return "probe", "Illusion of Mastery"
    if correct and state.memory_strength > 2.0:
        return "advance", "Mastery-Based Advancement"
    return "hint", "Productive Struggle"

# ============================================================
# Tutor LLM
# ============================================================

class Tutor:
    def __init__(self):
        self.llm = ChatGroq(model="llama-3.1-8b-instant")
        self.sys = SystemMessage("You are a concise tutoring assistant.")

    def reply(self, prompt):
        return self.llm.invoke([self.sys, HumanMessage(prompt)]).content

# ============================================================
# Single Episode
# ============================================================

def run_episode(learner, policies_on, turns=12):
    g = build_graph()
    tutor = Tutor()

    node = "photosynthesis"
    turns_log, convo = [], []

    for t in range(turns):
        s = g.state[node]
        g.update_retention(node, t)

        text, correct, conf, expl = learner.respond(g.nodes[node], s)
        update_memory(s, correct, expl)

        action, pol = policy(s, correct, expl) if policies_on else ("advance", None)

        tutor_msg = tutor.reply(
            f"Learner: {text}\nCorrect: {correct}\nPolicy: {pol}\nAction: {action}"
        )

        g.activate(node, conf, t)

        turns_log.append({
            "turn": t,
            "node": node,
            "correct": correct,
            "confidence": round(conf, 3),
            "retention": round(s.retention, 3),
            "memory_strength": round(s.memory_strength, 3),
            "policy": pol,
            "action": action,
        })

        convo.append({"user": text, "assistant": tutor_msg})

        if action == "advance":
            nxt = next_nodes(g, node)
            if nxt:
                node = nxt[0]

    return turns_log, convo

# ============================================================
# Metrics (with policy diagnostics)
# ============================================================

def compute_metrics(turns):
    n = len(turns)
    return {
        "turns": n,
        "mean_confidence": statistics.mean(t["confidence"] for t in turns),
        "mean_retention": statistics.mean(t["retention"] for t in turns),
        "mean_memory_strength": statistics.mean(t["memory_strength"] for t in turns),
        "advance_rate": sum(t["action"] == "advance" for t in turns) / n,
        "misconception_rate": sum(not t["correct"] for t in turns) / n,
        "policy_activation_rate": sum(t["policy"] is not None for t in turns) / n,
    }

# ============================================================
# Experiment Runner
# ============================================================

def run_experiments():
    root = Path("experiments")
    summary = root / "summary"
    summary.mkdir(parents=True, exist_ok=True)

    learners = [
        FragileLearner("fragile"),
        MisconceptionLearner("misconception"),
    ]

    conditions = {
        "policies_on": True,
        "policies_off": False,
    }

    all_rows = []

    for learner in learners:
        for cname, pol_on in conditions.items():
            for run in range(5):
                base = root / learner.name / cname / f"run_{run}"
                base.mkdir(parents=True, exist_ok=True)

                turns, convo = run_episode(learner, pol_on)
                metrics = compute_metrics(turns)

                # Save individual run files
                json.dump(turns, open(base / "turns.json", "w"), indent=2)
                json.dump(convo, open(base / "conversation.json", "w"), indent=2)
                json.dump(metrics, open(base / "metrics.json", "w"), indent=2)

                all_rows.append({
                    "learner": learner.name,
                    "condition": cname,
                    "run": run,
                    **metrics
                })

    # ✅ Save master table
    summary_file = summary / "metrics_all_runs.json"
    json.dump(all_rows, open(summary_file, "w"), indent=2)

    # ✅ Compute aggregated metrics per learner/condition
    aggregated = {}
    for learner_name in set(r["learner"] for r in all_rows):
        aggregated[learner_name] = {}
        for cond in set(r["condition"] for r in all_rows):
            runs = [r for r in all_rows if r["learner"]==learner_name and r["condition"]==cond]
            agg = {}
            for key in ["mean_confidence","mean_retention","mean_memory_strength",
                        "advance_rate","misconception_rate","policy_activation_rate"]:
                vals = [r[key] for r in runs]
                agg[key] = {
                    "mean": round(statistics.mean(vals),3),
                    "std": round(statistics.stdev(vals),3) if len(vals)>1 else 0.0
                }
            aggregated[learner_name][cond] = agg

    json.dump(aggregated, open(summary / "metrics_aggregated.json", "w"), indent=2)


if __name__ == "__main__":
    run_experiments()
