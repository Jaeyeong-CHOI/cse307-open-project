# Evaluation Comparison

- base: `docs/research/results/prompt-batch-v1-120-legacy.gpt54-mini.2026-03-24.json`
- candidate: `docs/research/results/prompt-batch-v1-120.gpt54-mini.2026-03-23.json`

## Summary
- base avg score: 9.083
- cand avg score: 6.583
- delta avg score: -2.500
- base nonzero score: 19
- cand nonzero score: 16
- delta nonzero score: -3
- base passed: 0
- cand passed: 0
- delta passed: +0

## Top violations (candidate)
- original keyword used: for: 88
- original keyword used: if: 86
- original keyword used: in: 84
- original keyword used: return: 74
- original keyword used: def: 59
- python parse failed after normalization: invalid syntax (<unknown>, line 2): 16
- python parse failed after normalization: expected '(' (<unknown>, line 2): 15
- python parse failed after normalization: invalid syntax (<unknown>, line 1): 14
- missing alias for in: convert this phrase back to python reserved token: 11
- missing alias for in: keep this long alias while preserving python grammar: 10
