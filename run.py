

class SimulatedLearner:
    def __init__(self, name: str):
        self.name = name
        self.misconception = False

    def respond(self, node: SemanticNode, state: TemporalNodeState):
        raise NotImplementedError


class FragileCorrectLearner(SimulatedLearner):
    """Learner A"""
    def respond(self, node, state):
        correct = True
        confidence = max(0.2, state.confidence + 0.05)
        explanation_depth = "shallow"
        return correct, confidence, explanation_depth

class MisconceptionLearner(SimulatedLearner):
    """Learner B"""
    def respond(self, node, state):
        correct = False
        confidence = state.confidence  # stays high
        explanation_depth = "confident-but-wrong"
        return correct, confidence, explanation_depth

class OverconfidentGuesser(SimulatedLearner):
    """Learner C"""
    def respond(self, node, state):
        correct = state.activation_count % 2 == 0
        confidence = 0.8
        explanation_depth = "fluent"
        return correct, confidence, explanation_depth


def policy_decision(state: TemporalNodeState, correct: bool, explanation: str):
    if not correct:
        return "challenge_misconception", "Contradiction Policy"

    if state.confidence < 0.6:
        return "ask_why", "Fragile Knowledge Policy"

    if explanation == "shallow":
        return "give_hint", "Illusion of Mastery Policy"

    return "advance", "Mastery Advancement Policy"


def no_policy_decision(correct: bool):
    if correct:
        return "advance", None
    return "give_hint", None


def run_turn(
    graph: Dialograph,
    node_id: str,
    learner: SimulatedLearner,
    policies_on: bool,
    log: list
):
    node = graph.semantic_nodes[node_id]
    state = graph.temporal_nodes[node_id]

    correct, new_conf, explanation = learner.respond(node, state)

    if policies_on:
        action, policy = policy_decision(state, correct, explanation)
    else:
        action, policy = no_policy_decision(correct)

    graph.activate(node_id, confidence=new_conf)

    log.append({
        "node": node_id,
        "confidence": round(new_conf, 2),
        "correct": correct,
        "explanation": explanation,
        "action": action,
        "policy": policy
    })

    return action


PATH = ["photosynthesis", "light_reactions", "calvin_cycle"]


def run_simulation(graph, learner, policies_on):
    log = []
    current_idx = 0

    for _ in range(12):
        node_id = PATH[current_idx]
        action = run_turn(graph, node_id, learner, policies_on, log)

        if action == "advance" and current_idx < len(PATH) - 1:
            current_idx += 1

    return log


learners = [
    FragileCorrectLearner("fragile"),
    MisconceptionLearner("misconception"),
    OverconfidentGuesser("guesser")
]

results = {}

for learner in learners:
    for policies_on in [True, False]:
        g = Dialograph()
        # add nodes + edges here
        key = f"{learner.name}_{'on' if policies_on else 'off'}"
        results[key] = run_simulation(g, learner, policies_on)
