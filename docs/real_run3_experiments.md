# Running experiments (`real_run3.py`)

This page describes how to run the **tutoring simulation experiments** at the repository root: batch conditions, learners, LLM calls via OpenRouter, and JSON outputs under `simulation_logs/`.

For what each metric means, see [Metrics & baselines](real_run3_metrics.md). For equations and turn logic, see [Formal mechanics](real_run3_formal_mechanics.md).

---

## Prerequisites

1. **Python environment** with project dependencies (from the repo root):

   ```bash
   uv sync
   ```

   The simulation uses **`langchain-openai`** (declared in `pyproject.toml`) to call OpenRouter’s OpenAI-compatible API.

2. **OpenRouter API key** — required for every LLM turn. Create a key at [openrouter.ai](https://openrouter.ai) and export it:

   ```bash
   export OPENROUTER_API_KEY="sk-or-..."
   ```

3. **Optional: model choice**

   ```bash
   export OPENROUTER_MODEL="openai/gpt-4o-mini"
   ```

   Use any [OpenRouter model id](https://openrouter.ai/models) you have access to (e.g. `anthropic/claude-3.5-haiku`, `meta-llama/llama-3.3-70b-instruct`).

4. **Optional OpenRouter headers** (for their rankings dashboard):

   ```bash
   export OPENROUTER_HTTP_REFERER="https://your-site.example"
   export OPENROUTER_APP_TITLE="Dialograph experiments"
   ```

---

## Run the default experiment batch

From the **repository root** (where `real_run3.py` lives):

```bash
uv run python real_run3.py
```

Or, with a shell that already has `OPENROUTER_API_KEY` set:

```bash
python real_run3.py
```

### What runs

- **Learners (3):** `fragile`, `misconception`, `guesser` (see `FragileCorrectLearner`, `MisconceptionLearner`, `OverconfidentGuesser` in `real_run3.py`).
- **Conditions (6):** `full_dialograph`, `no_policy`, `no_temporal`, `single_node`, `llm_baseline`, `kt_baseline`.
- **Turns per run:** `DEFAULT_SIMULATION_TURNS` (50 by default).

Each combination calls the LLM once per turn, so **full batch cost** scales with  
\(3 \times 6 \times 50 = 900\) completions (plus your chosen model’s pricing).

### Outputs

All files go to **`simulation_logs/`** (created automatically):

| File pattern | Content |
|--------------|---------|
| `{learner}_{condition}_log.json` | Per-turn trace (`condition`, `action`, `policy`, `confidence`, LLM instruction/response, …) |
| `{learner}_{condition}_metrics.json` | Result of `compute_metrics(log)` (curves, stability, premature advancement, …) |

Example: `misconception_full_dialograph_metrics.json`.

The script also **prints** a one-line summary per run to stdout.

---

## Reproducibility notes

- **Misconception learner:** RNG is seeded from the learner name unless you pass `MisconceptionLearner("name", rng_seed=...)`.
- **LLM:** OpenRouter responses are **not** deterministic unless the provider and model support fixed sampling and you configure it (not set in `real_run3.py` today). For strict reproducibility, log model id, temperature (if exposed later), and timestamps.

---

## Custom runs (Python API)

You can run a subset or change the horizon without editing the `if __name__ == "__main__"` block by importing from `real_run3`:

```python
from real_run3 import (
    MisconceptionLearner,
    SimulationRunConfig,
    run_simulation,
    compute_metrics,
    DialographAgentLLM,
)

learner = MisconceptionLearner("misconception", rng_seed=42)
cfg = SimulationRunConfig(
    "full_dialograph",
    graphs_on=True,
    policy_mode="dialograph",
    temporal_on=True,
    navigation_on=True,
)

agent = DialographAgentLLM()  # uses OPENROUTER_* env vars
log = run_simulation(learner, cfg, turns=30, agent=agent)
metrics = compute_metrics(log)
```

For **offline tests**, pass a mock agent with a `next_action(self, instruction: str) -> str` method instead of `DialographAgentLLM()`.

---

## Ablations and baselines (quick reference)

| `SimulationRunConfig.name` | Role |
|----------------------------|------|
| `full_dialograph` | Full system |
| `no_policy` | Graph + temporal, naive advance/hint only |
| `no_temporal` | No retention / memory-strength updates |
| `single_node` | One node, no prerequisite navigation |
| `llm_baseline` | No graph; scripted tutor + same simulated learner |
| `kt_baseline` | SimpleKT replaces Dialograph policies |

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| `OpenRouter API key missing` | `OPENROUTER_API_KEY` not set in the environment |
| `ModuleNotFoundError: langchain_openai` | Run `uv sync` from repo root |
| Very slow or rate limits | Reduce `turns`, fewer conditions, or a faster/cheaper model |
| Empty or sparse metrics for graph-off rows | Expected for fields that need `confidence` / `learner_correct`; LLM baseline still logs learner signals — see [metrics doc](real_run3_metrics.md) |

---

## Related

- [Building the docs](how_to_build_docs.md) — MkDocs for this documentation site.
