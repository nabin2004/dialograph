# 2AI 2026 reviewer feedback — status tracker (Paper ID 180)

**Paper:** Dialograph: A decision-theoretic framework for proactive educational dialogue using temporal graphs  

This document maps **reviewer concerns** to **what is already implemented** in the repository (especially `real_run3.py` and docs) versus **what still belongs in the paper, experiments, or future work**.  

**Draft for authors — not committed to git by default;** update as the camera-ready or rebuttal evolves.

---

## Snapshot: Reviewer 1 vs Reviewer 2

| Reviewer | Overall | Core empirical ask |
|----------|---------|---------------------|
| **R1** | Accept (minor revision) | Longer horizon, stronger metrics, external baselines (LLM-only, KT). |
| **R2** | Reject | Same empirical gaps **plus** writing quality, formal reproducibility (equations, ρ/ω, pseudocode), related-work differentiation, scope clarity. |

Much of R1’s empirical checklist is now **addressed in code and simulation docs**. R2’s **writing, related work, and paper-only formal sections** still need **manuscript** work even when the repo already contains the technical content.

---

## R1 — Detailed feedback (Q6) and status

### 1. “Experimental horizon is short (five turns)”

| Status | **Done (in repo)** |
|--------|-------------------|
| Addressed in simulation code | Default **`DEFAULT_SIMULATION_TURNS = 50`** in `real_run3.py` (not 5). Batch runs use this unless you pass `turns=` to `run_simulation`. |

| Still to do | **Paper / experiments** |
|-------------|---------------------------|
| Manuscript | Replace any “five turns” (or short-horizon) description with the **actual** protocol: e.g. 50 turns, or report both 30- and 50-turn sweeps if you want to match an earlier plan. |
| Optional | Log **wall-clock / API cost** so longer runs are defensible. |

---

### 2. “Metrics are internal proxies, not externally validated learning outcomes”

| Status | **Partially done (in repo)** |
|--------|------------------------------|
| Stronger **simulation metrics** | `compute_metrics()` in `real_run3.py` adds **time-structured** and **policy-relevant** measures: learning curve, sliding-window accuracy, per-node concept stability (+ summary), time-to-mastery, premature-advancement rate, intervention effectiveness, mean KT mastery when applicable; legacy scalars retained. |
| Documentation | `docs/real_run3_metrics.md` defines each metric and how it is computed from the log. |

| Still to do | **Paper / validation** |
|-------------|-------------------------|
| External validity | Reviewers still want **human studies** or **standardized benchmarks** if you claim real learning outcomes. Simulated learners remain **proxies**. |
| Writing | Frame honestly: “simulated learners and session-level metrics” vs “validated learning gains.” |

---

### 3. “Baseline comparison limited to policy-ablated same system; add LLM-only tutor and knowledge tracing”

| Status | **Done (in repo)** |
|--------|-------------------|
| **LLM-only tutor (fairer baseline)** | `llm_baseline`: no graph, no Dialograph policies; **`llm_baseline_decision(correct, turn_idx)`** → `give_hint` / `ask_question` / `explain` with structured prompts (`LLM_BASELINE_TOPIC`). Logged as `policy: LLM_tutor_baseline`. |
| **KT baselines** | **`SimpleKT`** (`kt_heuristic_baseline`), **`BKT`** (`kt_bkt_baseline`, classical observe+learn with fixed hyperparameters), **`DKTStyle`** (`kt_dkt_style_baseline`, untrained latent stand-in for deep KT). Logged as `KT_heuristic`, `KT_BKT`, `KT_DKT_style`; see [Paper: KT positioning](paper_addendum_kt_positioning.md). |
| **Extra ablations** | `no_policy`, **`no_temporal`** (no retention / memory-strength updates), **`single_node`** (one node, no prerequisite navigation), plus **`full_dialograph`**. |
| Batch | `if __name__ == "__main__"` runs learners × conditions and writes `simulation_logs/*.json`. |
| How to run | `docs/real_run3_experiments.md`. |

| Still to do | **Paper** |
|-------------|-----------|
| Tables / figures | Summarize **metrics by condition** (e.g. premature advancement, stability, time-to-mastery) in the paper. |
| Statistics | Optional: seeds, CIs, multiple runs — not automated in the script beyond `MisconceptionLearner` RNG seed. |
| “Standard KT” | **BKT** and **DKT-style** baselines are now in code; **GKT** remains related-work positioning unless you add a trained model. See [paper addendum](paper_addendum_kt_positioning.md). |

---

## R2 — Detailed feedback and status

### 1. Typos, grammar, formatting, redundancy (abstract vs intro)

| Status | **Not done in repo** |
|--------|----------------------|
| | Full **proofread and LaTeX cleanup** are **manuscript** tasks. No automated fix in this repository. |

**To do:** Editorial pass; unify author list and PDF cut-off issues; shorten redundant abstract/intro overlap.

---

### 2. “Temporal updates, ρ/ω, retrieval scoring, policy mechanics lack equations, pseudocode, algorithms”

| Status | **Done (in docs + code alignment)** |
|--------|--------------------------------------|
| Formal write-up | **`docs/real_run3_formal_mechanics.md`**: retention \(R \leftarrow e^{-\Delta t/S}\), memory-strength piecewise update, **ordered rules with priority ρ and winner indicators ω** (first-match), **navigation** as first successor edge (no learned retrieval score), **turn pseudocode**, **KT baselines** (heuristic, BKT, DKT-style) in §6. |
| Implementation | Matches `Dialograph.update_retention`, `update_memory_strength`, `policy_decision`, `get_next_nodes`, `run_turn` order in `real_run3.py`. |

| Still to do | **Paper** |
|-------------|-----------|
| Integration | **Lift** (or cite) the formal mechanics doc into the paper’s Preliminaries / Appendix so reviewers see it in the **submission PDF**, not only the repo. |
| Retrieval | If the **paper** claims “policy-aware retrieval” beyond first-edge navigation, either **extend code** with explicit scoring or **narrow the claim** to match `get_next_nodes` behavior. |

---

### 3. “Quantitative metrics, baselines, ablations, user studies”

| Status | **Partially done** |
|--------|---------------------|
| Quantitative **simulation** | Metrics + baselines + ablations as in R1 §3 (`real_run3.py`, `docs/real_run3_metrics.md`). |
| User studies | **Not done** — requires human protocol, ethics, data. |

**To do:** Paper section with **numbers** from `simulation_logs/*_metrics.json`; optional pilot user study if feasible.

---

### 4. “Differentiate from temporal KT (GNN-KT) and proactive dialogue (e.g. DPDP)”

| Status | **Not done in repo** |
|--------|----------------------|
| | **Related work** and **positioning** paragraphs are **paper** work. The codebase does not replace a literature comparison. |

**To do:** Explicit comparison table: what Dialograph adds (declarative cognitive policies, graph + temporal state separation, etc.) vs cited systems.

---

### 5. “Framework is general-purpose in repo but paper focuses on education — clarify LLM realization and noisy inputs”

| Status | **Partially reflected in code** |
|--------|----------------------------------|
| | `real_run3.py` shows **LLM as utterance realization** (`DialographAgentLLM`, instruction `ACTION: node.content`). Simulated learners stand in for **noisy/calibrated behavior** but are not “real user noise” models. |

| Still to do | **Paper** |
|-------------|-----------|
| | One subsection: **general Dialograph** (`src/dialograph`) vs **education instantiation** (`real_run3`); **where** LLM sits; **limitations** on robustness to ASR/NLP errors. |

---

### 6. “Expand Preliminaries with formal definitions (e.g. decay, policy matching)”

| Status | **Done in repo (draft material)** |
|--------|-----------------------------------|
| | Same as R2 §2: **`docs/real_run3_formal_mechanics.md`**. |

| Still to do | **Paper** |
|-------------|-----------|
| | Copy or adapt into **Preliminaries / Appendix**; keep notation consistent with the PDF. |

---

### 7. “Quantitative results (simulated) and real-user pilot; fix typos and complete sections”

| Status | |
|--------|--|
| Simulated results | **Runnable** via `real_run3.py` → JSON metrics; **paper** needs aggregated tables/plots. |
| Real-user pilot | **Not done.** |
| Typos / complete sections | **Manuscript** only. |

---

## Quick checklist (for rebuttal or revision letter)

| Item | Repo / docs | Paper manuscript |
|------|-------------|------------------|
| Longer horizon | Done (50 turns default) | Update text + any figures |
| Richer metrics | Done (`compute_metrics`, metrics doc) | Report in results |
| LLM-only baseline | Done (`llm_baseline`) | Describe + table |
| KT baselines | Done (`SimpleKT`, `BKT`, `DKTStyle`; see paper addendum) | Methods text + limits (BKT not fitted; DKTStyle not trained) |
| Ablations (temporal, single-node, no-policy) | Done | Describe + table |
| Formal decay, policy order, pseudocode | Done (`real_run3_formal_mechanics.md`) | Integrate into PDF |
| Related work (GNN-KT, DPDP, etc.) | — | **To do** |
| Proofreading, formatting, redundancy | — | **To do** |
| Human study / external validation | — | Optional / future |

---

## File index (where “how” lives)

| Artifact | Role |
|----------|------|
| `real_run3.py` | Simulation, metrics, baselines, ablations, OpenRouter agent |
| `docs/real_run3_experiments.md` | How to run experiments and env vars |
| `docs/real_run3_metrics.md` | Metric definitions, log schema, condition table |
| `docs/real_run3_formal_mechanics.md` | LaTeX-friendly formal spec (decay, ρ/ω, navigation, pseudocode, KT §6) |
| `docs/paper_addendum_kt_positioning.md` | Paper wording: KT vs Dialograph, limits, related work |
| `docs/how_to_build_docs.md` | MkDocs build/serve |
| `simulation_logs/` (generated) | Per-run JSON logs and metrics (not usually committed) |

---

*Last updated: tracking document for 2AI 2026 Paper 180; align dates and outcomes with your actual rebuttal.*
