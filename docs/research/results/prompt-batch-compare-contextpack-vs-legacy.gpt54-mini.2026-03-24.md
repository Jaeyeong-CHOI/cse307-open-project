# Evaluation Comparison

- base: `docs/research/results/prompt-batch-v1-120-legacy.gpt54-mini.2026-03-24.json`
- candidate: `docs/research/results/prompt-batch-v1-120-contextpack.gpt54-mini.2026-03-24.json`

## Summary
- base avg score: 9.083
- cand avg score: 21.667
- delta avg score: +12.583
- base nonzero score: 19
- cand nonzero score: 32
- delta nonzero score: +13
- base passed: 0
- cand passed: 3
- delta passed: +3

## Top violations (candidate)
- original keyword used: for: 66
- original keyword used: if: 38
- original keyword used: return: 31
- original keyword used: def: 22
- original keyword used: in: 22
- python parse failed after normalization: invalid syntax (<unknown>, line 2): 21
- python parse failed after normalization: invalid syntax (<unknown>, line 1): 16
- python parse failed after normalization: invalid syntax (<unknown>, line 6): 12
- python parse failed after normalization: expected ':' (<unknown>, line 2): 11
- missing alias for in: no, use exact python original grammer: 9
