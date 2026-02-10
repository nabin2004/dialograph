from dataclasses import dataclass
from math import exp
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import statistics
import random
from datetime import datetime

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
        dt = (turn - s.last_turn) * TIME_COMPRESSION  # explicit acceleration
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
    g.add_node(SemanticNode(
        "calvin_cycle", "process",
        "Calvin cycle uses ATP and NADPH to fix carbon dioxide into sugar"
    ))
    g.add_edge(SemanticEdge(
        "photosynthesis", "light_reactions", "prerequisite"
    ))
    g.add_edge(SemanticEdge(
        "light_reactions", "calvin_cycle", "prerequisite"
    ))
    return g

def next_nodes(g, nid):
    return [e.target for e in g.edges if e.source == nid]

# ============================================================
# Learners
# ============================================================

class Learner:
    def __init__(self, name): 
        self.name = name
        self.incorrect_responses = 0
        self.correct_responses = 0
        
    def respond(self, node, state): 
        raise NotImplementedError

class FragileLearner(Learner):
    def respond(self, node, state):
        self.correct_responses += 1
        return (
            f"I think {node.content}, but I might be missing details.",
            True,
            min(state.confidence + 0.05, 0.9),
            "shallow",
        )

class MisconceptionLearner(Learner):
    def __init__(self, name):
        super().__init__(name)
        self.misconceptions = [
            "Plants absorb sugar from soil through their roots.",
            "Photosynthesis happens only at night when plants sleep.",
            "The main product of photosynthesis is oxygen, not glucose."
        ]
    
    def respond(self, node, state):
        self.incorrect_responses += 1
        misconception = random.choice(self.misconceptions)
        return (
            f"I believe {node.content}, but actually {misconception}",
            False,
            state.confidence,
            "confident_wrong",
        )

class GuesserLearner(Learner):
    def __init__(self, name, guess_correct_prob=0.5):
        super().__init__(name)
        self.guess_correct_prob = guess_correct_prob
        self.guess_types = ["fluent", "shallow"]
    
    def respond(self, node, state):
        is_correct = random.random() < self.guess_correct_prob
        if is_correct:
            self.correct_responses += 1
            guess_type = random.choice(self.guess_types)
            if guess_type == "fluent":
                response = f"Yes, {node.content}. That's clear to me."
            else:  # shallow
                response = f"I guess {node.content}..."
            confidence = random.uniform(0.3, 0.6)  # Low confidence guessing
            return (response, True, confidence, guess_type)
        else:
            self.incorrect_responses += 1
            # Make a plausible but wrong guess
            wrong_responses = [
                f"I think it's about {random.choice(['respiration', 'digestion', 'reproduction'])}...",
                f"Maybe {node.content} but in reverse?",
                f"Not sure, perhaps it involves {random.choice(['sunlight', 'water', 'minerals'])} differently?"
            ]
            confidence = random.uniform(0.4, 0.7)  # Sometimes overconfident in wrong guesses
            return (random.choice(wrong_responses), False, confidence, "fluent")

# ============================================================
# Memory Update
# ============================================================

def update_memory(state, correct, explanation):
    if not correct:
        state.memory_strength *= 0.9
    elif explanation in ("shallow", "fluent"):
        state.memory_strength += 0.3
    else:
        state.memory_strength += 0.6
    state.memory_strength = max(0.5, min(state.memory_strength, 8.0))

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
# Tutor LLM
# ============================================================

class Tutor:
    def __init__(self):
        self.llm = ChatGroq(model="llama-3.1-8b-instant")
        self.sys = SystemMessage("You are a concise tutoring assistant.")

    def reply(self, prompt):
        return self.llm.invoke([self.sys, HumanMessage(prompt)]).content

# ============================================================
# Enhanced Logging System
# ============================================================

class ExperimentLogger:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.experiment_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
    def log_turn(self, turn_data: Dict, learner_name: str, condition: str, run_id: int):
        """Log individual turn data"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "experiment_id": self.experiment_timestamp,
            "learner": learner_name,
            "condition": condition,
            "run": run_id,
            **turn_data
        }
        return log_entry
    
    def log_conversation(self, convo_data: List[Dict], learner_name: str, condition: str, run_id: int):
        """Log conversation data"""
        convo_entry = {
            "timestamp": datetime.now().isoformat(),
            "experiment_id": self.experiment_timestamp,
            "learner": learner_name,
            "condition": condition,
            "run": run_id,
            "conversation": convo_data
        }
        return convo_entry
    
    def log_metrics(self, metrics: Dict, learner_name: str, condition: str, run_id: int):
        """Log metrics data"""
        metrics_entry = {
            "timestamp": datetime.now().isoformat(),
            "experiment_id": self.experiment_timestamp,
            "learner": learner_name,
            "condition": condition,
            "run": run_id,
            "metrics": metrics
        }
        return metrics_entry
    
    def log_learner_stats(self, learner: Learner, condition: str, run_id: int):
        """Log learner-specific statistics"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "experiment_id": self.experiment_timestamp,
            "learner": learner.name,
            "condition": condition,
            "run": run_id,
            "total_responses": learner.correct_responses + learner.incorrect_responses,
            "correct_responses": learner.correct_responses,
            "incorrect_responses": learner.incorrect_responses,
            "accuracy_rate": learner.correct_responses / max(1, learner.correct_responses + learner.incorrect_responses)
        }
        return stats

# ============================================================
# Single Episode with Enhanced Logging
# ============================================================

def run_episode(learner, policies_on, turns=12, logger=None, learner_name="", condition="", run_id=0):
    g = build_graph()
    tutor = Tutor()

    node = "photosynthesis"
    turns_log, convo = [], []
    
    # Track policy usage
    policy_usage = {}

    for t in range(turns):
        s = g.state[node]
        g.update_retention(node, t)

        text, correct, conf, expl = learner.respond(g.nodes[node], s)
        update_memory(s, correct, expl)

        if policies_on:
            action, pol = policy_decision(s, correct, expl)
        else:
            action, pol = no_policy_decision(correct)
        
        # Track policy usage
        if pol:
            policy_usage[pol] = policy_usage.get(pol, 0) + 1

        tutor_msg = tutor.reply(
            f"Learner: {text}\nCorrect: {correct}\nPolicy: {pol}\nAction: {action}\n"
            f"Confidence: {conf:.2f}, Retention: {s.retention:.2f}"
        )

        g.activate(node, conf, t)

        turn_data = {
            "turn": t,
            "node": node,
            "node_content": g.nodes[node].content,
            "learner_response": text,
            "correct": correct,
            "confidence": round(conf, 3),
            "retention": round(s.retention, 3),
            "memory_strength": round(s.memory_strength, 3),
            "activation_count": s.activation_count,
            "policy": pol,
            "policy_action": action,
            "explanation_type": expl,
            "tutor_response": tutor_msg[:200] + "..." if len(tutor_msg) > 200 else tutor_msg
        }

        if logger:
            turn_log = logger.log_turn(turn_data, learner_name, condition, run_id)
            turns_log.append(turn_log)
        else:
            turns_log.append(turn_data)

        convo.append({"user": text, "assistant": tutor_msg})

        if action == "advance":
            nxt = next_nodes(g, node)
            if nxt:
                node = nxt[0]

    return turns_log, convo, policy_usage

# ============================================================
# Enhanced Metrics (with policy diagnostics)
# ============================================================

def compute_metrics(turns, policy_usage=None):
    n = len(turns)
    if n == 0:
        return {}
    
    return {
        "turns": n,
        "mean_confidence": statistics.mean(t["confidence"] for t in turns),
        "mean_retention": statistics.mean(t["retention"] for t in turns),
        "mean_memory_strength": statistics.mean(t["memory_strength"] for t in turns),
        "advance_rate": sum(t["policy_action"] == "advance" for t in turns) / n,
        "misconception_rate": sum(not t["correct"] for t in turns) / n,
        "policy_activation_rate": sum(t["policy"] is not None for t in turns) / n,
        "unique_nodes_visited": len(set(t["node"] for t in turns)),
        "average_activation": statistics.mean(t["activation_count"] for t in turns) if n > 0 else 0,
        "policy_usage": policy_usage if policy_usage else {}
    }

# ============================================================
# Enhanced Experiment Runner
# ============================================================

def run_experiments():
    root = Path("experiments")
    summary = root / "summary"
    summary.mkdir(parents=True, exist_ok=True)
    
    # Initialize logger
    logger = ExperimentLogger(root)

    learners = [
        FragileLearner("fragile"),
        MisconceptionLearner("misconception"),
        GuesserLearner("guesser", guess_correct_prob=0.5)
    ]

    conditions = {
        "policies_on": True,
        "policies_off": False,
    }

    all_rows = []
    detailed_logs = []
    learner_stats = []

    for learner in learners:
        for cname, pol_on in conditions.items():
            for run in range(5):
                base = root / learner.name / cname / f"run_{run}"
                base.mkdir(parents=True, exist_ok=True)

                turns, convo, policy_usage = run_episode(
                    learner, pol_on, logger=logger, 
                    learner_name=learner.name, condition=cname, run_id=run
                )
                metrics = compute_metrics(turns, policy_usage)
                
                # Get learner statistics
                stats = logger.log_learner_stats(learner, cname, run)
                learner_stats.append(stats)

                # Save individual run files
                json.dump(turns, open(base / "turns_detailed.json", "w"), indent=2)
                json.dump(convo, open(base / "conversation.json", "w"), indent=2)
                json.dump(metrics, open(base / "metrics.json", "w"), indent=2)
                
                # Save policy usage separately
                json.dump(policy_usage, open(base / "policy_usage.json", "w"), indent=2)

                all_rows.append({
                    "learner": learner.name,
                    "condition": cname,
                    "run": run,
                    **metrics
                })
                
                detailed_logs.append({
                    "learner": learner.name,
                    "condition": cname,
                    "run": run,
                    "turns": turns,
                    "conversation": convo[:3]  # First 3 exchanges for quick review
                })

    # Save master table
    summary_file = summary / "metrics_all_runs.json"
    json.dump(all_rows, open(summary_file, "w"), indent=2)
    
    # Save detailed logs
    detailed_file = summary / "detailed_logs.json"
    json.dump(detailed_logs, open(detailed_file, "w"), indent=2)
    
    # Save learner statistics
    stats_file = summary / "learner_statistics.json"
    json.dump(learner_stats, open(stats_file, "w"), indent=2)

    # Compute aggregated metrics per learner/condition
    aggregated = {}
    policy_summary = {}
    
    for learner_name in set(r["learner"] for r in all_rows):
        aggregated[learner_name] = {}
        policy_summary[learner_name] = {}
        
        for cond in set(r["condition"] for r in all_rows):
            runs = [r for r in all_rows if r["learner"]==learner_name and r["condition"]==cond]
            agg = {}
            
            # Standard metrics
            for key in ["mean_confidence","mean_retention","mean_memory_strength",
                        "advance_rate","misconception_rate","policy_activation_rate",
                        "unique_nodes_visited","average_activation"]:
                if key in runs[0]:
                    vals = [r[key] for r in runs]
                    agg[key] = {
                        "mean": round(statistics.mean(vals),3),
                        "std": round(statistics.stdev(vals),3) if len(vals)>1 else 0.0,
                        "min": round(min(vals),3),
                        "max": round(max(vals),3)
                    }
            
            # Policy usage summary
            if cond == "policies_on":
                policy_counts = {}
                for run in runs:
                    for policy_name, count in run.get("policy_usage", {}).items():
                        policy_counts[policy_name] = policy_counts.get(policy_name, 0) + count
                policy_summary[learner_name][cond] = policy_counts
            
            aggregated[learner_name][cond] = agg

    json.dump(aggregated, open(summary / "metrics_aggregated.json", "w"), indent=2)
    json.dump(policy_summary, open(summary / "policy_summary.json", "w"), indent=2)
    
    # Generate a simple report
    generate_report(aggregated, policy_summary, summary)
    
    return all_rows, aggregated, policy_summary

def generate_report(aggregated, policy_summary, summary_path):
    """Generate a human-readable report"""
    report_lines = []
    report_lines.append("=" * 80)
    report_lines.append("EXPERIMENT REPORT")
    report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append("=" * 80)
    
    for learner_name, conditions in aggregated.items():
        report_lines.append(f"\n{'='*60}")
        report_lines.append(f"LEARNER: {learner_name.upper()}")
        report_lines.append(f"{'='*60}")
        
        for condition, metrics in conditions.items():
            report_lines.append(f"\nCondition: {condition}")
            report_lines.append("-" * 40)
            
            for metric_name, stats in metrics.items():
                if isinstance(stats, dict) and 'mean' in stats:
                    report_lines.append(f"  {metric_name}: {stats['mean']:.3f} ± {stats['std']:.3f}")
        
        if learner_name in policy_summary and "policies_on" in policy_summary[learner_name]:
            report_lines.append(f"\nPolicy Usage (policies_on condition):")
            report_lines.append("-" * 40)
            policies = policy_summary[learner_name]["policies_on"]
            for policy_name, count in sorted(policies.items(), key=lambda x: x[1], reverse=True):
                report_lines.append(f"  {policy_name}: {count}")
    
    report_text = "\n".join(report_lines)
    report_file = summary_path / "experiment_report.txt"
    with open(report_file, "w") as f:
        f.write(report_text)
    
    print(f"\nReport saved to: {report_file}")
    print(report_text)

# ============================================================
# Main Execution
# ============================================================

if __name__ == "__main__":
    print("Starting enhanced experiment with comprehensive logging...")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    all_rows, aggregated, policy_summary = run_experiments()
    
    print("\n" + "=" * 80)
    print("Experiment completed successfully!")
    print(f"Total runs: {len(all_rows)}")
    print(f"Learners tested: {list(set(r['learner'] for r in all_rows))}")
    print(f"Conditions tested: {list(set(r['condition'] for r in all_rows))}")
    print("Results saved to: experiments/summary/")
    print("=" * 80)