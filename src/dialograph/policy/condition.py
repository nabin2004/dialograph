class Condition:
    def evaluate(self, graph: Dialograph) -> List[dict]:
        """
        Returns evidence matches.
        Empty list = condition not met.
        """
        raise NotImplementedError


class LowConfidenceCondition(Condition):
    def __init__(self, threshold: float):
        self.threshold = threshold

    def evaluate(self, graph: Dialograph) -> List[dict]:
        matches = []
        for node_id, state in graph.temporal_nodes.items():
            if state.confidence < self.threshold:
                matches.append({
                    "node_id": node_id,
                    "confidence": state.confidence
                })
        return matches


