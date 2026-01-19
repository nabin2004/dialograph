# dialograph

**Dialograph** is a lightweight Python library for representing, evolving, and traversing dialogue memory as a temporal graph.
It is designed for **proactive dialogue agents**, where reasoning over user preferences, beliefs, and strategies matters more than raw generation.

At its core, Dialograph wraps a dynamic graph structure around typed dialogue memories and provides clean hooks for retrieval, scoring, and long-term evolution.

---

## Core Concepts

### Nodes

Nodes represent dialogue memory units such as:

* user preferences
* beliefs / facts
* dialogue strategies

Each node carries a **state object** (e.g. `PreferenceState`, `BeliefState`) with confidence and temporal metadata.

### Edges

Edges represent relations between memory units:

* semantic relations (supports, contradicts, elicits)
* dialogue flow dependencies
* strategy activation paths

Edges are directional, weighted, and time-aware.

### Time

Dialograph maintains an internal time counter that allows:

* decay of confidence
* forgetting
* recency-based retrieval

---

## Project Structure

```text
dialograph/
├── core/               # graph primitives
│   ├── graph.py        # Dialograph wrapper
│   ├── node.py         # node state definitions
│   └── edge.py         # edge state definitions
│
├── memory/             # typed dialogue memory
│   ├── preference.py
│   ├── belief.py
│   └── strategy.py
│
├── traversal/          # retrieval and scoring
│   ├── retrieve.py
│   └── score.py
│
├── utils/              # persistence & visualization
│   ├── io.py
│   └── visualize.py
```

---

## Installation

For development:
```bash
git clone https://github.com/nabin2004/dialograph.git
```

```bash
cd dialograph
```

```bash
uv venv
```
```bash
source .venv/bin/activate
```

```bash
uv pip install -e .
```

---

## Quick Example

```python
from dialograph import Node, Edge, Dialograph, draw

graph = Dialograph()

# Nabin Eats Rice.
n1 = Node(node_id='n1',node_type='personal_details',data={"value":"Nabin"})
n2 = Node(node_id='n2',node_type="object", data={"value":"Rice"})
n3 = Node(node_id='n3',node_type='personal_details',data={"value":"Football"})
n4 = Node(node_id='n4',node_type='person',data={"value":"R. Feynman"})
n5 = Node(node_id='n5',node_type='subject',data={"value":"Quantum Physics"})


e1 = Edge(edge_id='e1', source_node_id='n1', target_node_id='n2', relation='eats')
e2 = Edge(edge_id='e2', source_node_id='n1', target_node_id='n4', relation='knows')
e3 = Edge(edge_id='e3', source_node_id='n1', target_node_id='n3', relation='plays')
e4 = Edge(edge_id='e4', source_node_id='n1', target_node_id='n5', relation='interested')
e5 = Edge(edge_id='e5', source_node_id='n4', target_node_id='n5', relation='famousFor')


graph.add_node(n1)
graph.add_node(n2)
graph.add_node(n3)
graph.add_node(n4)
graph.add_node(n5)

graph.add_edge(e1)
graph.add_edge(e2)
graph.add_edge(e3)
graph.add_edge(e4)
graph.add_edge(e5)

draw(graph)
```

---

## Intended Use Cases

* Proactive dialogue systems
* Emotional support agents
* Preference elicitation
* Strategy planning and reuse
* Dialogue memory research

---

## Status

This project is **under active development**.
APIs may evolve, but core abstractions are expected to remain stable.

---

## Roadmap

* [ ] Path-based retrieval
* [ ] Forgetting thresholds
* [ ] Graph serialization
* [ ] 3D / interactive visualization
* [ ] LLM-facing retrieval API

---

## License

MIT License.

---

## Citation

If you use Dialograph in academic work, please cite the corresponding paper (coming soon).

```
- How can an agent use past interactions to proactively adapt its dialog strategies over time, without relying on opaque embedding-only retrieval or heavy ontologies?

- We're not retrieving facts, we're retrieving how to act.
```
