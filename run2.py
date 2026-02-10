from dataclasses import dataclass
from datetime import datetime
from math import exp
from typing import Dict, List, Optional, Any

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
    decay_score: float
    confidence: float


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
            decay_score=1.0,
            confidence=0.4,
        )

    def add_edge(self, edge: SemanticEdge):
        self.semantic_edges.append(edge)

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
# Graph Builder
# ============================================================

def build_photosynthesis_graph() -> Dialograph:
    g = Dialograph()

    nodes = [
        SemanticNode("photosynthesis", "concept",
                     "Process converting light energy to chemical energy"),
        SemanticNode("chloroplast", "concept",
                     "Organelle where photosynthesis occurs"),
        SemanticNode("thylakoid", "concept",
                     "Membrane sacs for light reactions"),
        SemanticNode("stroma", "concept",
                     "Fluid matrix for Calvin cycle"),
        SemanticNode("light_reactions", "process",
                     "Light-dependent ATP and NADPH production"),
        SemanticNode("photosystem_ii", "component",
                     "Initiates electron transport"),
        SemanticNode("electron_transport_chain", "process",
                     "Creates proton gradient"),
        SemanticNode("photosystem_i", "component",
                     "Produces NADPH"),
        SemanticNode("calvin_cycle", "process",
                     "Carbon fixation"),
        SemanticNode("carbon_fixation", "subprocess",
                     "CO2 incorporation"),
        SemanticNode("reduction_phase", "subprocess",
                     "Reduction using ATP and NADPH"),
        SemanticNode("regeneration_phase", "subprocess",
                     "Regenerates RuBP"),
    ]

    for n in nodes:
        g.add_node(n)

    edges = [
        SemanticEdge("photosynthesis", "chloroplast", "prerequisite"),
        SemanticEdge("chloroplast", "thylakoid", "component_of"),
        SemanticEdge("chloroplast", "stroma", "component_of"),

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
    return sorted(
        e.target
        for e in graph.semantic_edges
        if e.source == node_id and e.relation_type == "prerequisite"
    )


# ============================================================
# Simulated Learners
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
# Policies
# ============================================================

def policy_decision(state: TemporalNodeState, correct: bool, explanation: str):
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
# Agent (Dialogue Realizer)
# ============================================================

class Agent:
    def next_action(self, conversation: List[Dict[str, str]]) -> str:
        raise NotImplementedError


class DummyDialographAgent(Agent):
    def next_action(self, conversation: List[Dict[str, str]]) -> str:
        return conversation[-1]["content"]


def action_to_instruction(action: str, node: SemanticNode) -> str:
    if action == "ask_why":
        return f"Explain {node.content}."
    if action == "give_hint":
        return f"Here is a hint about {node.content}."
    if action == "challenge_misconception":
        return f"That is incorrect. Reconsider {node.content}."
    if action == "advance":
        return f"Good. Let us move forward."
    return "Continue."


# ============================================================
# Simulation Loop
# ============================================================

def run_turn(
    graph: Dialograph,
    node_id: str,
    learner: SimulatedLearner,
    agent: Agent,
    policies_on: bool,
    conversation: list,
    log: list,
):
    node = graph.semantic_nodes[node_id]
    state = graph.temporal_nodes[node_id]

    correct, new_conf, explanation = learner.respond(node, state)

    if policies_on:
        action, policy = policy_decision(state, correct, explanation)
    else:
        action, policy = no_policy_decision(correct)

    instruction = action_to_instruction(action, node)
    conversation.append({"role": "system", "content": instruction})
    tutor_text = agent.next_action(conversation)
    conversation.append({"role": "assistant", "content": tutor_text})

    graph.activate(node_id, confidence=new_conf)

    log.append({
        "node": node_id,
        "action": action,
        "policy": policy,
        "confidence": round(new_conf, 2),
        "correct": correct,
    })

    return action


def run_simulation(graph, learner, policies_on: bool):
    agent = DummyDialographAgent()
    conversation = []
    log = []

    current_node = "photosynthesis"

    for _ in range(12):
        action = run_turn(
            graph,
            current_node,
            learner,
            agent,
            policies_on,
            conversation,
            log,
        )

        if action == "advance":
            next_nodes = get_next_nodes(graph, current_node)
            if next_nodes:
                current_node = next_nodes[0]

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

    results: Dict[str, Any] = {}

    for learner in learners:
        for policies_on in [True, False]:
            graph = build_photosynthesis_graph()
            key = f"{learner.name}_{'on' if policies_on else 'off'}"
            results[key] = run_simulation(graph, learner, policies_on)

    for k, v in results.items():
        print("\n", k)
        for row in v:
            print(row)
