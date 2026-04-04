# Formal mechanics: temporal state, policies, and navigation (`real_run3.py`)

This note answers reproducibility concerns: **exact equations**, **pseudocode**, and **conflict resolution** as implemented in the simulation script `real_run3.py` (not hand-wavy “Ebbinghaus-inspired” prose alone).

Math below uses standard LaTeX. Render with a Markdown engine that supports math (e.g. MkDocs + Arithmatex, Pandoc, or a LaTeX preprint).

---

## 1. State variables (active node \(v\) at turn \(\tau \in \mathbb{Z}_{\ge 0}\))

For each semantic node \(v\), temporal state is

\[
\mathbf{s}_v = \bigl(c_v,\, n_v,\, \tau^{\mathrm{last}}_v,\, S_v,\, R_v\bigr),
\]

where:

| Symbol | Code field | Role |
|--------|------------|------|
| \(c_v \in [0,1]\) | `confidence` | Reported learner confidence (epistemic / calibration proxy) |
| \(n_v \in \mathbb{Z}_{\ge 0}\) | `activation_count` | Number of times \(v\) has been activated |
| \(\tau^{\mathrm{last}}_v\) | `last_activated_turn` | Turn index of last activation **before** the current turn’s updates |
| \(S_v > 0\) | `memory_strength` | Scale in the exponential decay (larger \(\Rightarrow\) slower forgetting in \(R_v\)) |
| \(R_v \in (0,1]\) | `retention` | Decay-based accessibility **before** re-activation this turn |

**Initialization** when a node is added (`add_node`):  
\(c_v \leftarrow 0.4\), \(n_v \leftarrow 0\), \(\tau^{\mathrm{last}}_v \leftarrow 0\), \(S_v \leftarrow 1.5\), \(R_v \leftarrow 1.0\).

---

## 2. Temporal state updates

### 2.1 Retention decay (exact formula)

At the **start** of a graph-on turn for active node \(v\) at global turn \(\tau\), if temporal updates are enabled (`temporal_on`):

\[
\Delta t_v = \tau - \tau^{\mathrm{last}}_v,
\qquad
R_v \;\leftarrow\; \exp\!\left(-\,\frac{\Delta t_v}{S_v}\right).
\]

This is exponential decay in **discrete turn lag** \(\Delta t_v\), with time constant \(S_v\) in **turns** (not wall-clock seconds in this script). Same functional form as a continuous-time Ebbinghaus-style curve \(e^{-t/S}\), with \(t\) instantiated as \(\Delta t_v\).

**Reference (code):** `Dialograph.update_retention` uses `dt = current_turn - state.last_activated_turn` and `retention = exp(-dt / memory_strength)`.

### 2.2 Memory-strength dynamics (piecewise update)

After the learner produces \((y, c^{\mathrm{new}}_v, \eta)\) with correctness \(y \in \{\mathrm{true},\mathrm{false}\}\) and explanation tag \(\eta \in \{\texttt{shallow},\texttt{fluent},\texttt{confident-but-wrong},\ldots\}\), if temporal updates are enabled:

\[
S_v \;\leftarrow\;
\begin{cases}
0.9\,S_v, & y = \mathrm{false}, \\[4pt]
S_v + 0.3, & y = \mathrm{true} \;\wedge\; \eta = \texttt{shallow}, \\[4pt]
S_v + 0.6, & y = \mathrm{true} \;\wedge\; \eta = \texttt{fluent}, \\[4pt]
S_v, & \text{otherwise (correct but other } \eta \text{)}.
\end{cases}
\]

Then **clamp**:

\[
S_v \;\leftarrow\; \mathrm{clip}(S_v,\, 0.5,\, 8.0).
\]

**Reference:** `update_memory_strength`.

### 2.3 Activation and confidence write-back

After the policy chooses an action and the LLM step runs, `activate` executes:

\[
n_v \leftarrow n_v + 1,\qquad
\tau^{\mathrm{last}}_v \leftarrow \tau,\qquad
c_v \leftarrow c^{\mathrm{new}}_v\ \ (\text{if provided}).
\]

**Order of operations in one turn** (graph-on, `temporal_on`):  
(1) update \(R_v\) via §2.1 → (2) sample learner → (3) update \(S_v\) via §2.2 → (4) policy / action → (5) LLM → (6) activate §2.3.

When `temporal_on` is false, steps (1) and (3) are skipped; \(R_v,S_v\) stay at their previous values (up to activation still incrementing \(n_v\) and updating \(c_v\)).

---

## 3. Policy composition, prioritization, and conflict resolution

### 3.1 Rule priority \(\rho\) and selection weights \(\omega\)

Dialograph policies are a **fixed ordered list** of rules \(\{\mathcal{R}_\rho\}_{\rho=1}^{K}\). Each rule \(\mathcal{R}_\rho\) is a predicate \(P_\rho(\mathbf{s}_v, y, \eta)\) mapped to an action \(a_\rho\) and a label \(\ell_\rho\).

**Conflict resolution:** **first-match wins** (deterministic, no continuous blending). Define one-hot weights

\[
\omega_\rho =
\begin{cases}
1, & \rho = \min\{\rho' : P_{\rho'} = \text{true}\}, \\
0, & \text{otherwise}.
\end{cases}
\]

Then

\[
a^\star = \sum_{\rho=1}^{K} \omega_\rho\, a_\rho,
\qquad
\ell^\star = \sum_{\rho=1}^{K} \omega_\rho\, \ell_\rho
\quad
(\text{only one term nonzero}).
\]

If no predicate holds before the fallback, the last rule always fires (default `advance`). This is the precise sense in which **\(\rho\) is priority** and **\(\omega\) is the deterministic winner indicator**—not a learned mixture.

### 3.2 Predicate list (matches `policy_decision` order)

Let \(c=c_v\), \(n=n_v\), \(R=R_v\), \(S=S_v\). Below, rules are listed in **ascending \(\rho\)** (evaluated top-to-bottom in code).

| \(\rho\) | Predicate \(P_\rho\) | Action \(a_\rho\) | Label \(\ell_\rho\) |
|----------|------------------------|-------------------|---------------------|
| 1 | \(c < 0.6 \land y\) | `ask_why` | Fragile Knowledge |
| 2 | \(\neg y \land c > 0.7\) | `challenge` | Overconfident Error |
| 3 | \(\neg y \land n > 2\) | `restructure` | Persistent Misconception |
| 4 | \(y \land \eta \in \{\texttt{fluent},\texttt{shallow}\}\) | `elicit_explanation` | Guessing / Low Engagement |
| 5 | \(\eta = \texttt{shallow}\) | `give_hint` | Illusion of Mastery |
| 6 | \(R < 0.3\) | `review` | Forgetting / Spaced Reactivation |
| 7 | \(\neg y\) | `give_hint` | Productive Struggle |
| 8 | \(y \land c \ge 0.7 \land S > 2.0\) | `advance` | Mastery-Based Advancement |
| 9 | \(c < 0.4\) | `simplify` | Cognitive Overload |
| 10 | \(y \land S > 3.0\) | `transfer` | Transfer Readiness |
| 11 | (fallback, always true) | `advance` | Default Policy |

**Remarks for reproducibility**

- **Overlap by design:** several predicates can be true simultaneously; **only the smallest \(\rho\)** with \(P_\rho=\text{true}\) is used. For example, \(\rho=4\) and \(\rho=5\) can both match when \(y\) and \(\eta=\texttt{shallow}\); \(\rho=4\) wins.
- **No policy** ablation (`policy_mode = none`):  
  \[
  a^\star = \begin{cases} \texttt{advance}, & y, \\ \texttt{give_hint}, & \neg y. \end{cases}
  \]

---

## 4. “Retrieval” and navigation (no learned scoring in this script)

There is **no** separate retrieval model that ranks arbitrary nodes by embedding similarity. **Navigation** after `advance` is purely graph topology:

\[
\mathrm{Succ}(v) = \bigl[ u : (v \to u) \in E \bigr]
\]

ordered as edges appear in `graph.semantic_edges`. The next node is

\[
v^+ =
\begin{cases}
\mathrm{Succ}(v)[0], & \mathrm{Succ}(v) \neq \emptyset \;\wedge\; \text{navigation enabled}, \\
v, & \text{otherwise}.
\end{cases}
\]

So “retrieval scoring” in the reviewer sense is **degenerate**: first outgoing prerequisite edge wins (deterministic). If you need a scored retrieval extension for a paper, define a separate function \(f(u \mid v, \mathbf{s})\) and replace \(v^+\) by \(\arg\max_{u \in \mathrm{Succ}(v)} f(u \mid v,\mathbf{s})\)—that is **not** present in `real_run3.py` today.

---

## 5. Pseudocode: one graph-on turn

```
Input: graph G, active node v, turn τ, learner L, temporal_on, policy_mode, navigation_on
State s ← G.temporal_nodes[v]

if temporal_on:
    Δt ← τ - s.last_activated_turn
    s.retention ← exp(-Δt / s.memory_strength)

(y, c_new, η) ← L.respond(semantic_node(v), s)

if temporal_on:
    update_memory_strength(s, y, η)   // §2.2

if policy_mode == dialograph:
    (action, label) ← first_matching_rule(s, y, η)   // §3.2
else if policy_mode == none:
    (action, label) ← (advance if y else give_hint, None)
else:
    KT.update(y); action ← KT.decide(); label ← "SimpleKT"

instruction ← UPPER(action) + ": " + content(v)
response ← LLM(instruction)

activate(G, v, c_new, τ)   // §2.3

if action == advance and navigation_on:
    Succ ← outgoing_targets(G, v)
    v_next ← Succ[0] if Succ non-empty else v
else:
    v_next ← v

return (action, v_next)
```

---

## 6. KT baseline (external temporal controller)

For completeness, the **SimpleKT** baseline maintains scalar mastery \(m \in (0,1)\). After observing correctness \(y\):

\[
m \leftarrow
\begin{cases}
m + 0.1\,(1-m), & y, \\
m - 0.1\,m, & \neg y,
\end{cases}
\qquad
m \leftarrow \mathrm{clip}(m,\,0.01,\,0.99).
\]

Decision (threshold policy):

\[
\text{action} =
\begin{cases}
\texttt{review}, & m < 0.5, \\
\texttt{practice}, & 0.5 \le m < 0.8, \\
\texttt{advance}, & m \ge 0.8.
\end{cases}
\]

---

## 7. Suggested citation in text

You can point reviewers here and state explicitly:

- Retention uses **\(R \leftarrow \exp(-\Delta t / S)\)** with turn lag \(\Delta t\) and learnable scale \(S\) updated by correctness/explanation (§2).
- Policies are **ordered first-match rules** with formal priority \(\rho\) and winner indicators \(\omega_\rho\) (§3).
- Navigation is **deterministic first successor** along prerequisite edges (§4), not latent retrieval.

This separates *what the code does* from optional future extensions (e.g. weighted policy mixtures or learned retrieval).
