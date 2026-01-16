# Dialograph

A time-aware directed multigraph for evolving dialogue, belief, and memory structures.

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
