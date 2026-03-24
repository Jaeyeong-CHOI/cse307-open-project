# Research Direction v2.0 — Instruction-Prior Conflict Analysis

**Decision date:** 2026-03-24
**Decision status:** ACTIVE (previous direction partially deprecated)
**Rationale:** Previous approach reduced to 0-pass metric collapse. Direction shifted to failure mechanism analysis with interpretable continuous metrics.

---

## New Research Question

> When model instruction (transformed syntax rules) directly conflicts with pretrained language priors (Python dominance), what structural factors determine the degree of reversion?

This reframes from "does LLM comply?" → "WHERE and WHY does prior override instruction?"

---

## Why this is stronger

| Old framing | New framing |
|---|---|
| "does model follow alias?" | "at which syntactic positions does prior win?" |
| binary pass/fail | continuous violation profile |
| expected result (obvious) | structure of failure (novel) |
| infra paper | behavior analysis paper |

---

## Critical Decision: Deprecate Binary Pass

Binary pass is removed as primary metric. Reasons:
1. All models score 0. No discrimination power.
2. Zero information about HOW failure occurs.
3. Cannot compare model families.

Replaced by:

### Primary Metrics (all continuous)
- **KLR** (Keyword Leakage Rate): fraction of outputs that use original Python keywords instead of aliases, per keyword token class.
- **ACR** (Alias Compliance Rate): fraction of alias slots correctly filled.
- **PSS** (Partial Structural Score): weighted sum of partial credit per sub-component (0.0–1.0 scale).
- **PIR** (Prior Influence Rate): derived metric: KLR / (KLR + ACR). High PIR → prior dominates.

### Sub-component weights (PSS)
| Component | Weight |
|---|---|
| Alias compliance (no leakage) | 0.40 |
| Normalization parse success | 0.25 |
| Core logic skeleton | 0.25 |
| Format/loop fidelity | 0.10 |

---

## Experiment Plan (v2)

### Exp-1: Prior Influence by Keyword Class
- For each keyword (if/for/in/return/def), compute KLR independently.
- Hypothesis: function-definition keywords (def) leak more than control-flow (for/if).
- Why: def is higher-frequency and less context-dependent.

### Exp-2: Alias Difficulty Level (L1–L4)
| Level | Design | Expected KLR |
|---|---|---|
| L1 | similar-sounding alias (e.g., `fore`) | low |
| L2 | unrelated short token (e.g., `xk`) | medium |
| L3 | anti-prior phrase (e.g., "do not use for here") | high |
| L4 | conflicting alias (e.g., `if` maps to `return`) | very high |
- Key finding: where is the "breaking point" on the difficulty axis?

### Exp-3: Prompt Strategy Ablation
| Strategy | Description |
|---|---|
| S0 | No context (legacy) |
| S1 | Context-pack (alias + banned list) |
| S2 | Few-shot (1-2 examples using aliases) |
| S3 | Self-rewrite instruction |
- Measure delta-KLR and delta-ACR per strategy.

### Exp-4: Task Complexity
Expand beyond fib to:
- nested control-flow task
- multi-function composition
- stateful iteration
- real-bug-fix style
- Measure: does harder task increase or decrease prior dominance?

### Exp-5: Human baseline (small-scale)
- n=5–10 participants given same alias rules + same task
- Record: error type, time-to-solve, voluntary reversion
- Question: Is this LLM-specific or general cognitive challenge?

---

## Ablation Required Before Submission
1. S0 vs S1 vs S2 vs S3 (prompt strategy) × model family × alias difficulty
2. Per-keyword KLR table (heatmap-ready)
3. PSS distribution histogram per model
4. Prior Influence Rate (PIR) ranking across conditions

---

## Paper Structure (v2)

1. Introduction: prior-vs-instruction conflict framing
2. Related Work: instruction following, alignment, constrained generation
3. Method: confusion language design, KLR/ACR/PSS/PIR metrics
4. Experiments: Exp 1–4 (human if available)
5. Analysis: where/when/why prior wins
6. Discussion: implications for alignment, safety, instruction robustness
7. Conclusion: "LLM instruction compliance is structurally limited by pretrained language priors—here is the failure map"

---

## Implementation Roadmap

- [ ] `scripts/partial_judge.py`: new judge returning KLR/ACR/PSS/PIR per sample
- [ ] `scripts/analyze_violation_structure.py`: position + keyword class analysis
- [ ] `scripts/alias_difficulty_gen.py`: generate L1–L4 alias variants
- [ ] multi-task benchmark design + prompt templates (10+ tasks)
- [ ] paper v3: rewrite abstract + RQ + results sections
- [ ] optional: human experiment protocol doc

---

## Self-evaluation: Is this NeurIPS/ICLR quality?

| Criterion | Status |
|---|---|
| Novel research question | YES (prior-vs-instruction conflict is underexplored) |
| Continuous interpretable metrics | IN PROGRESS |
| Multi-model, multi-task ablation | PLANNED |
| Strong baseline comparison | NEEDS ADDITION |
| Human baseline | PLANNED |
| Clear failure mechanism | PARTIALLY DONE |
| Related work coverage | WEAK (need to expand) |

**Honest assessment:** This direction CAN reach top-tier with 2–3 more experiment rounds. The raw insight (prior dominates instruction even under explicit prohibition) is real and publishable IF properly characterized.
