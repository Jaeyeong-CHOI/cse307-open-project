# Evaluation Comparison

- base: `docs/research/results/prompt-batch-v1-120-legacy.gpt4o-mini.2026-03-24.json`
- candidate: `docs/research/results/prompt-batch-v1-120-contextpack.gpt4o-mini.2026-03-24.json`

## Summary
- base avg score: 3.750
- cand avg score: 6.500
- delta avg score: +2.750
- base nonzero score: 7
- cand nonzero score: 10
- delta nonzero score: +3
- base passed: 0
- cand passed: 0
- delta passed: +0

## Top violations (candidate)
- original keyword used: for: 53
- original keyword used: if: 33
- python parse failed after normalization: invalid syntax (<unknown>, line 1): 33
- python parse failed after normalization: invalid syntax (<unknown>, line 2): 28
- original keyword used: return: 27
- original keyword used: def: 21
- python parse failed after normalization: invalid syntax (<unknown>, line 6): 18
- original keyword used: in: 18
- missing alias for in: use this token exactly for keyword mapping: 12
- missing loop: for i in range(7): print(i, fib(i)): 10
