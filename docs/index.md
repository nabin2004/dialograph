# Dialograph

A time-aware directed multigraph for evolving dialogue, belief, and memory structures.

## Simulation evaluation

The script `real_run3.py` logs tutoring turns and exports **paper-oriented metrics**, plus **external baselines** (LLM-only tutor script, simple knowledge tracing) and **ablations** (no policy, no temporal updates, single-node graph). See [How to run experiments](real_run3_experiments.md), [Simulation metrics (`real_run3`)](real_run3_metrics.md), and [Formal mechanics (LaTeX / reproducibility)](real_run3_formal_mechanics.md).

## Quick example

```python
from dialograph import Dialograph, Node, Edge

g = Dialograph()

a = Node(node_id="a", node_type="intent")
b = Node(node_id="b", node_type="belief")

g.add_node(a)
g.add_node(b)

g.add_edge(
    Edge(
        source_node_id="a",
        target_node_id="b",
        relation="elicits"
    )
)
```
## Node

## Edge

## Graph
