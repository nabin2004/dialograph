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
from dialograph.core.graph import Dialograph
from dialograph.memory.preference import PreferenceState
from dialograph.core.edge import EdgeState

g = Dialograph()

g.add_node(
    "pref_movie",
    state=PreferenceState(
        key="movie_genre",
        value="sci-fi",
        confidence=0.9,
    )
)

g.add_node(
    "belief_stress",
    state=BeliefState(
        proposition="user is stressed about exams",
        confidence=0.7,
    )
)

g.add_edge(
    "belief_stress",
    "pref_movie",
    state=EdgeState(relation="influences")
)
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

