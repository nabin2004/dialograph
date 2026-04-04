# Simulation metrics (`real_run3.py`)

This document describes the **evaluation layer** for the photosynthesis tutoring simulation: what each metric means, how it is computed from the per-turn log, and how to use outputs for comparisons (e.g. policies on vs off, learner archetypes).

For **equations, policy priority (\(\rho\)), winner indicators (\(\omega\)), decay formulas, and turn pseudocode** aligned with the same script, see [Formal mechanics (`real_run3`)](real_run3_formal_mechanics.md).

## Per-turn log schema

Each entry appended in `run_turn()` is a dictionary with (among others):

| Field | Meaning |
|--------|---------|
| `turn` | 0-based turn index |
| `condition` | Run id from `SimulationRunConfig.name` (e.g. `full_dialograph`, `llm_baseline`) |
| `node` | Active semantic node id, or `None` for the LLM-only baseline (no graph) |
| `learner_correct` | Simulated learner correctness; always set for graph runs and for the LLM baseline |
| `confidence` | Learner confidence after the turn |
| `action` | Chosen tutor action (`advance`, `give_hint`, `review`, `practice`, `explain`, …) |
| `policy` | Dialograph policy name, `KT_heuristic` / `KT_BKT` / `KT_DKT_style`, `LLM_tutor_baseline`, or `None` (no-policy ablation) |
| `kt_mastery` | Latent **belief** scalar after the turn for any KT controller (`SimpleKT`, `BKT`, `DKTStyle`); else `null` |
| `temporal_on` | Whether retention / memory-strength updates were enabled for this condition |

Metrics are **pure functions** of this log; they do not call the LLM.

## Conditions, ablations, and external baselines

Runs are configured with `SimulationRunConfig` and `run_simulation(learner, config, ...)`. The default batch matches a typical reviewer-facing grid:

| Config name | Graph | Temporal (retention + memory strength) | Decision layer |
|-------------|-------|----------------------------------------|----------------|
| `full_dialograph` | Full multinode | On | Dialograph policies |
| `no_policy` | Full multinode | On | Naive: advance if correct else hint |
| `no_temporal` | Full multinode | **Off** | Dialograph policies |
| `single_node` | One node only (no navigation) | On | Dialograph policies |
| `llm_baseline` | **Off** | Off (no graph memory) | Scripted tutor: `llm_baseline_decision` (hint / ask / explain) |
| `kt_heuristic_baseline` | Full multinode | On | **SimpleKT** — heuristic scalar mastery (legacy “toy” KT for contrast) |
| `kt_bkt_baseline` | Full multinode | On | **BKT** — one-skill Bayesian Knowledge Tracing (fixed \(p_{\mathrm{learn}}, p_{\mathrm{slip}}, p_{\mathrm{guess}}\)) |
| `kt_dkt_style_baseline` | Full multinode | On | **DKTStyle** — untrained scalar latent with gated updates (DKT-*style*, not a trained LSTM) |

**How to frame comparisons (paper):**

- **LLM baseline** — isolates *decision structure + graph + memory* vs raw generation with a minimal reactive script (not “always explain”).
- **KT baselines** — temporal belief updates **without** Dialograph’s declarative cognitive policies; cite **BKT** as the classical interpretable reference and **DKTStyle** as a lightweight stand-in for deep KT (make clear it is **not** dataset-trained DKT).
- **GKT / graph KT** — you can **discuss in related work** without implementing; Dialograph’s differentiator is explicit **pedagogical policies** on top of temporal state, not SOTA graph-KT parameter fitting.
- **Ablations** — isolate policies, temporal updates, and graph navigation without claiming a third-party SOTA system.

Prefer cautious language, e.g. that Dialograph *shows* lower premature advancement or higher stability under simulation, rather than absolute “outperforms all baselines” unless backed by stats.

### Knowledge-tracing controllers (code reference)

| Class | `policy_mode` | Role |
|-------|----------------|------|
| `SimpleKT` | `kt` | Heuristic \(m\): cheap control path for ablations. |
| `BKT` | `kt_bkt` | Standard BKT **equations** (Bayesian observe + learn); parameters not fitted to logs. |
| `DKTStyle` | `kt_dkt_style` | Scalar \(h\) with LSTM-like gated nudges; **not** trained on sequences. |

Each exposes `.belief` (logged as `kt_mastery`) and `decide()` → `review` / `practice` / `advance` with thresholds documented in [Formal mechanics](real_run3_formal_mechanics.md).

### `mean_kt_mastery`

In `compute_metrics`, mean of per-turn `kt_mastery` (the controller’s **belief** scalar) when present; otherwise `null`. See also [Paper: KT positioning & claims](paper_addendum_kt_positioning.md).


## LLM backend (OpenRouter)

`DialographAgentLLM` uses **OpenRouter**’s OpenAI-compatible API (`https://openrouter.ai/api/v1`).

| Environment variable | Purpose |
|----------------------|---------|
| `OPENROUTER_API_KEY` | **Required** for live runs |
| `OPENROUTER_MODEL` | Optional; defaults to `openai/gpt-4o-mini`. Use any [OpenRouter model id](https://openrouter.ai/models) (e.g. `anthropic/claude-3.5-haiku`, `meta-llama/llama-3.3-70b-instruct`). |
| `OPENROUTER_HTTP_REFERER` | Optional site URL for OpenRouter rankings |
| `OPENROUTER_APP_TITLE` | Optional app name (default `Dialograph real_run3`) |

You can also pass `model_name=` or `api_key=` when constructing `DialographAgentLLM`.

## Simulation horizon

`run_simulation(..., turns=...)` defaults to **`DEFAULT_SIMULATION_TURNS` (50)** so curves and stability estimates have enough length for analysis. Override `turns=` for shorter smoke tests or longer runs.

## Time-aware metrics

### `learning_curve`

- **Definition:** For each graph-on step where `learner_correct` is not `None`, appends cumulative accuracy `correct_so_far / (i + 1)` where `i` is the index in the **full** log.
- **Use:** Visualize whether correctness trends up over time; compare conditions on the same horizon.

### `sliding_accuracy_k3`

- **Definition:** For each turn index `i`, accuracy over the last `k` turns (default `k = 3`) among entries with non-null `learner_correct`; entries with no scorable steps in the window are `null` in JSON.
- **Use:** Reduces noise from a single lucky or unlucky step; better for reporting “local” performance than raw per-turn correctness.

## Paper-oriented metrics

### `concept_stability_by_node` and `concept_stability_summary`

- **By node:** For each `node` id, fraction of turns (with non-null `learner_correct`) where the learner was correct.
- **Summary:** `mean`, `min`, and `max` over nodes with at least one scored turn.
- **Use:** Answers whether performance is **consistent across concepts** or concentrated on one node (possible guessing or imbalance).

### `time_to_mastery_turn`

- **Definition:** Smallest turn index `i` such that confidence is at least **`MASTERY_CONFIDENCE_THRESHOLD` (0.8)** for **`MASTERY_STREAK_LEN` (3)** consecutive graph-on rows (rows with non-null confidence). If never satisfied, `null` in JSON.
- **Use:** A scalar “speed to criterion” comparable across policies and learners.

### `premature_advancement_rate`

- **Definition:** Among turns with `action == "advance"`, the fraction where `confidence` is missing or strictly below **`PREMATURE_ADVANCE_CONFIDENCE` (0.7)**.
- **Use:** Measures whether the controller advances when the learner is still poorly calibrated; lower is generally better for safe progression.

### `intervention_effectiveness`

- **Definition:** Restrict to turns whose `action` is one of: `ask_why`, `give_hint`, `challenge`, `restructure` (see `INTERVENTION_ACTIONS` in code). For each such turn with both current and **next** turn having non-null confidence, count whether next-turn confidence **strictly increases**. Report successes / eligible interventions, or `0.0` if there were no eligible pairs.
- **Use:** Evidence that interventions co-occur with **immediate** confidence gains (a simple proxy; causal claims need tighter design).

## Legacy scalar metrics (ablations)

These remain useful for tables and baselines:

- `mean_confidence`, `mean_retention`, `mean_memory_strength`
- `mastery_rate` — fraction of graph-on turns with confidence ≥ 0.8
- `advance_rate` — fraction of all turns with `action == "advance"`
- `error_rate` — fraction of graph-on turns with `learner_correct` false

When the log has no graph-on rows (`valid` empty), legacy means are written as `null`; time-series and rates still return where defined.

## Simulated learner: `MisconceptionLearner`

Previously always incorrect, which made learning and policy effects hard to observe. The updated learner samples correctness with probability `min(0.1 + 0.1 * activation_count, 0.6)` using a **reproducible RNG** (`rng_seed` optional; default derived from learner name). That yields **improvement with practice** while staying mistake-prone early on.

## Output files

Running `real_run3.py` as a script writes JSON under `simulation_logs/`:

- `*_log.json` — full trace
- `*_metrics.json` — output of `compute_metrics(log)` including arrays for curves

For publication-style claims, prefer comparing **premature advancement**, **concept stability summary**, **time to mastery**, and **intervention effectiveness** across conditions rather than only scalar means over short runs.

## Constants (tuning)

Defined at module top in `real_run3.py`:

| Constant | Role |
|-----------|------|
| `DEFAULT_SIMULATION_TURNS` | Default episode length |
| `OPENROUTER_BASE_URL` | OpenRouter API base (override only if needed) |
| `DEFAULT_OPENROUTER_MODEL` | Fallback model id if `OPENROUTER_MODEL` is unset |
| `INTERVENTION_ACTIONS` | Actions counted for intervention effectiveness |
| `MASTERY_CONFIDENCE_THRESHOLD` / `MASTERY_STREAK_LEN` | Time-to-mastery criterion |
| `PREMATURE_ADVANCE_CONFIDENCE` | Threshold for “low confidence” advances |
| `SLIDING_ACCURACY_WINDOW` | Window size `k` for sliding accuracy |

Adjust these in one place so sweeps and ablations stay consistent.
