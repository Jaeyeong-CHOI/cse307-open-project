# Evaluation Comparison

- base: `docs/research/results/prompt-batch-v1-120.gpt4o.2026-03-23.json`
- candidate: `docs/research/results/prompt-batch-v1-120-contextpack.gpt4o.2026-03-24.json`

## Summary
- base avg score: 18.167
- cand avg score: 23.917
- delta avg score: +5.750
- base nonzero score: 30
- cand nonzero score: 35
- delta nonzero score: +5
- base passed: 2
- cand passed: 3
- delta passed: +1

## Top violations (candidate)
- original keyword used: for: 68
- original keyword used: return: 30
- original keyword used: if: 27
- original keyword used: def: 23
- original keyword used: in: 21
- python parse failed after normalization: invalid syntax (<unknown>, line 2): 19
- python parse failed after normalization: invalid syntax (<unknown>, line 1): 13
- python parse failed after normalization: invalid syntax (<unknown>, line 3): 13
- python parse failed after normalization: invalid syntax (<unknown>, line 6): 10
- missing alias for in: no, use exact python original grammer: 9
