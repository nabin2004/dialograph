# ============================================================
# COMPILED POLICY (WHAT THE SYSTEM EXECUTES)
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


