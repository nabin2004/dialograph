from dataclasses import dataclass
from datetime import datetime
from math import exp
from typing import Dict, List, Optional, Any
import json
from pathlib import Path

# LangChain imports
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
        SemanticNode("chloroplast", "concept", "Organelle of photosynthesis"),
        SemanticNode("thylakoid", "concept", "Site of light reactions"),
        SemanticNode("stroma", "concept", "Calvin cycle location"),
        SemanticNode("light_reactions", "process", "ATP and NADPH production"),
        SemanticNode("photosystem_ii", "component", "Electron excitation"),
        SemanticNode("electron_transport_chain", "process", "Proton gradient"),
        SemanticNode("photosystem_i", "component", "NADPH production"),
        SemanticNode("calvin_cycle", "process", "Carbon fixation"),
        SemanticNode("carbon_fixation", "subprocess", "CO2 incorporation"),
        SemanticNode("reduction_phase", "subprocess", "Sugar production"),
        SemanticNode("regeneration_phase", "subprocess", "RuBP regeneration"),
    ]
    for n in nodes:
        g.add_node(n)

    edges = [
        SemanticEdge("photosynthesis", "light_reactions", "prerequisite"),
        SemanticEdge("light_reactions", "photosystem_ii", "prerequisite"),
        SemanticEdge("photosystem_ii", "electron_transport_chain", "prerequisite"),
        SemanticEdge("electron_transport_chain", "photosystem_i", "prerequisite"),
        SemanticEdge("photosynthesis", "calvin_cycle", "prerequisite"),
        SemanticEdge("calvin_cycle", "carbon_fixation", "prerequisite"),
        SemanticEdge("carbon_fixation", "reduction_phase", "prerequisite"),
        SemanticEdge("reduction_phase", "regeneration_phase", "prerequisite"),
    ]
    for e in edges:
        g.add_edge(e)

    return g


def get_next_nodes(graph: Dialograph, node_id: str) -> List[str]:
    return [
        e.target
        for e in graph.semantic_edges
        if e.source == node_id and e.relation_type == "prerequisite"
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
    else:
        state.memory_strength += 0.1
    state.memory_strength = max(0.5, min(state.memory_strength, 8.0))

# ============================================================
# Policies
# ============================================================

def policy_decision(state: TemporalNodeState, correct: bool, explanation: str):
    if state.retention < 0.3:
        return "review", "Forgetting Recovery Policy"
    if not correct:
        return "challenge_misconception", "Contradiction Policy"
    if state.confidence < 0.6:
        return "ask_why", "Fragile Knowledge Policy"
    if explanation == "shallow":
        return "give_hint", "Illusion of Mastery Policy"
    return "advance", "Mastery Advancement Policy"

def no_policy_decision(correct: bool):
    return ("advance", None) if correct else ("give_hint", None)

# ============================================================
# Real LLM Agent (LangChain Dialograph Agent)
# ============================================================

class DialographAgentLLM:
    """
    Uses LangChain ChatGroq to respond based on the conversation.
    """

    def __init__(self, model_name="llama-3.1-8b-instant", top_k=5):
        self.llm = ChatGroq(model=model_name)
        self.memory_nodes: List[str] = []
        self.top_k = top_k
        self.system_msg = SystemMessage(content="You are a helpful tutor assistant.")

    def next_action(self, conversation: List[Dict[str, str]]) -> str:
        # add top memory nodes
        memory = "\n".join(self.memory_nodes[: self.top_k])
        last_message = conversation[-1]["content"] if conversation else "Hello"

        messages = [
            self.system_msg,
            HumanMessage(
                content=f"User said: {last_message}\nMemory:\n{memory}\nRespond as assistant."
            ),
        ]
        response = self.llm.invoke(messages)
        # update memory
        self.memory_nodes.append(last_message)
        return response.content

# ============================================================
# Simulation
# ============================================================

def action_to_instruction(action: str, node: SemanticNode) -> str:
    if action == "ask_why":
        return f"Explain {node.content}"
    if action == "give_hint":
        return f"Hint: {node.content}"
    if action == "challenge_misconception":
        return f"That is incorrect about {node.content}"
    if action == "review":
        return f"Let us review {node.content}"
    return "Proceed."

def run_turn(graph, node_id, learner, agent, policies_on, convo, log, turn_idx):
    state = graph.temporal_nodes[node_id]
    node = graph.semantic_nodes[node_id]

    graph.update_retention(node_id, turn_idx)
    correct, new_conf, explanation = learner.respond(node, state)
    update_memory_strength(state, correct, explanation)

    if policies_on:
        action, policy = policy_decision(state, correct, explanation)
    else:
        action, policy = no_policy_decision(correct)

    instruction = action_to_instruction(action, node)
    convo.append({"role": "system", "content": instruction})

    assistant_response = agent.next_action(convo)
    convo.append({"role": "assistant", "content": assistant_response})

    # --- Print assistant response so you can see it ---
    print(f"Turn {turn_idx} assistant says: {assistant_response}")

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
        "log_message": assistant_response,
    })

    return action


def run_simulation(graph, learner, policies_on):
    agent = DialographAgentLLM()
    convo, log = [], []
    current_node = "photosynthesis"

    for turn_idx in range(12):
        action = run_turn(graph, current_node, learner, agent, policies_on, convo, log, turn_idx)
        if action == "advance":
            nxt = get_next_nodes(graph, current_node)
            if nxt:
                current_node = nxt[0]

    return log

# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    learners = [
        FragileCorrectLearner("fragile"),
        MisconceptionLearner("misconception"),
        OverconfidentGuesser("guesser"),
    ]

    log_dir = Path("simulation_logs")
    log_dir.mkdir(exist_ok=True)

    for learner in learners:
        for policies_on in [True, False]:
            g = build_photosynthesis_graph()
            key = f"{learner.name}_{'on' if policies_on else 'off'}"
            print("\nRunning simulation:", key)

            log = run_simulation(g, learner, policies_on)

            # Print to console
            for row in log:
                print(row)

            # Save to JSON file
            log_file = log_dir / f"{key}_log.json"
            with open(log_file, "w") as f:
                json.dump(log, f, indent=2)

            print(f"Saved log to {log_file}")
