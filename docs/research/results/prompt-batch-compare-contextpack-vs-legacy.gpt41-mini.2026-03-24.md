# Evaluation Comparison

- base: `docs/research/results/prompt-batch-v1-120.gpt41-mini.2026-03-23.json`
- candidate: `docs/research/results/prompt-batch-v1-120-contextpack.gpt41-mini.2026-03-24.json`

## Summary
- base avg score: 10.750
- cand avg score: 8.500
- delta avg score: -2.250
- base nonzero score: 24
- cand nonzero score: 12
- delta nonzero score: -12
- base passed: 0
- cand passed: 1
- delta passed: +1

## Top violations (candidate)
- original keyword used: for: 60
- original keyword used: if: 31
- python parse failed after normalization: invalid syntax (<unknown>, line 1): 31
- original keyword used: return: 27
- python parse failed after normalization: invalid syntax (<unknown>, line 2): 26
- original keyword used: def: 20
- python parse failed after normalization: invalid syntax (<unknown>, line 6): 12
- python parse failed after normalization: invalid syntax (<unknown>, line 3): 11
- python parse failed after normalization: expected ':' (<unknown>, line 2): 9
- missing alias for in: no, use exact python original grammer: 9
