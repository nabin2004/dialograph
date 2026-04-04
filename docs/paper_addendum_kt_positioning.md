# Paper addendum: knowledge tracing (KT) baselines and positioning

Use this note when revising the **2AI / camera-ready** manuscript: what the **code** implements, what to **write**, and what **not** to overclaim.

---

## What the repository implements (`real_run3.py`)


| Baseline (config `name`) | Controller | Credible for reviewers as…                                                                                                                                         |
| ------------------------ | ---------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `kt_heuristic_baseline`  | `SimpleKT` | Cheap heuristic; good as **internal** contrast only.                                                                                                               |
| `kt_bkt_baseline`        | `BKT`      | **Classical BKT** update (observe + learn) with **fixed** p_{\mathrm{learn}}, p_{\mathrm{slip}}, p_{\mathrm{guess}} — not fitted to your logs or a public dataset. |
| `kt_dkt_style_baseline`  | `DKTStyle` | **DKT-inspired** scalar dynamics **without** neural training or sequence data.                                                                                     |


Formal equations: [Formal mechanics §6](real_run3_formal_mechanics.md).

---

## Suggested **Related work** additions (no new code required)

- **BKT** — Corbett & Anderson-style Bayesian Knowledge Tracing; cite as the standard **interpretable** sequential learner model.
- **DKT** — Piech et al.; LSTM-based sequence modeling; your `DKTStyle` is a **deliberately minimal** stand-in—state that you compare to a **simplified** latent-state update, not a reproduced DKT experiment.
- **GKT / graph-based KT** — cite 1–2 graph KT papers; argue that they **jointly model concepts and time** but typically **do not** expose a **declarative, cognitively named policy layer** that maps state → tutorial **actions** the way Dialograph does (adjust wording to match your actual claims).

---

## Core positioning sentence (adapt for abstract / intro)

> Knowledge tracing models focus on **estimating** latent mastery from interaction sequences. Dialograph targets **pedagogical decision-making**: a **temporal graph** of concepts plus **explicit policy rules** that choose tutorial actions, with an LLM handling **surface realization**. We compare against **BKT** and a **DKT-style** scalar baseline that also map belief to coarse actions (`review` / `practice` / `advance`) so that differences reflect **policy and structure**, not only whether a latent trace exists.

---

## What to add in the **paper** (checklist)

1. **Methods (one subsection)**
  - Define BKT observe + learn step (copy from formal mechanics or standard BKT text).  
  - List fixed hyperparameters used in code (`p_init`, `p_learn`, `p_slip`, `p_guess`).  
  - Define `DKTStyle` as an **untrained** latent with gated updates; clarify **≠** trained DKT.
2. **Experiments**
  - Table or figure: **Dialograph (full)** vs **no_policy** vs **LLM baseline** vs **BKT** vs **DKTStyle** (and optional heuristic KT) on **simulation metrics** (e.g. premature advancement, concept stability, time-to-mastery, intervention effectiveness — see [metrics doc](real_run3_metrics.md)).  
  - State **simulated learners** and **horizon** (e.g. 50 turns).
3. **Limitations (honest)**
  - BKT parameters are **not** fit to data.  
  - `DKTStyle` is **not** SOTA deep KT.  
  - No replacement for **human** studies or **benchmark** datasets unless you add them later.
4. **Language to avoid**
  - “We implement DKT” / “we beat GKT” without qualification.  
  - Prefer: “BKT baseline with fixed parameters,” “DKT-style untrained latent,” “graph KT cited for related work.”

---

## Optional extensions (future work / appendix)

- Fit BKT (EM) on synthetic or real interaction sequences.  
- Plug a **pretrained** DKT or small GKT if you obtain compatible data.  
- Report **confidence intervals** over RNG seeds for `MisconceptionLearner`.

---

## Cross-links

- [Running experiments](real_run3_experiments.md)  
- [Metrics & baselines](real_run3_metrics.md)  
- [Formal mechanics (LaTeX)](real_run3_formal_mechanics.md)

