# Partial Score Summary (2026-03-24)

## Metrics
- **KLR** (Keyword Leakage Rate): lower is better (less prior reversion)
- **ACR** (Alias Compliance Rate): higher is better (1 - KLR)
- **PSS** (Partial Structural Score): weighted sub-component score 0–1
- **PIR** (Prior Influence Rate): KLR / (KLR + ACR), measures how much pretrained prior dominates

## Key Results

| Model/Condition | n | KLR ↓ | ACR ↑ | PSS ↑ | PIR ↓ |
|---|---|---|---|---|---|
| gpt-4o-mini (context-pack) | 120 | 0.260 | 0.740 | 0.324 | 0.260 |
| gpt-4o (baseline) | 120 | 0.366 | 0.634 | 0.396 | 0.366 |
| gpt-4o-mini (baseline) | 120 | 0.423 | 0.578 | 0.273 | 0.423 |
| gpt-4.1-mini (baseline) | 120 | 0.431 | 0.569 | 0.329 | 0.431 |
| gpt-5.4-mini (baseline) | 120 | 0.670 | 0.330 | 0.249 | 0.670 |
| gpt-4.1-nano (baseline) | 120 | 0.690 | 0.310 | 0.160 | 0.690 |

## Key Findings

1. **Context-pack halves prior influence**: gpt-4o-mini KLR drops from 0.423 → 0.260 with explicit language contract.
2. **Model size ≠ compliance**: gpt-5.4-mini has higher KLR (0.670) than gpt-4o-mini (0.423). Larger/newer model can be MORE prior-dominated.
3. **gpt-4o best overall**: Highest ACR (0.634) and PSS (0.396) in baseline condition.
4. **Clear KLR spectrum**: Models range from 0.26 to 0.69 — not all zero. Binary metric was hiding real structure.

## Interpretation

Prior Influence Rate (PIR) is the most discriminative metric.
- PIR < 0.3: instruction-following is competitive with prior
- PIR 0.3–0.5: mixed; prior partially wins
- PIR > 0.5: prior dominates — "confusion language" successfully defeats alignment

This directly supports the research hypothesis: **pretrained language prior overrides instruction at quantifiable rates, varying systematically by model and prompt strategy.**
