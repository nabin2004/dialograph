

class PolicyEngine:
    def __init__(self, policies: List[CompiledPolicy]):
        self.policies = policies

    def select(self, graph: Dialograph) -> Optional[CompiledPolicy]:
        candidates = []

        for policy in self.policies:
            if policy.applies(graph):
                strength = policy.score(graph)
                if strength > 0:
                    candidates.append((policy, strength))

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: (x[0].priority, x[1]),
            reverse=True
        )
        return candidates[0][0]

