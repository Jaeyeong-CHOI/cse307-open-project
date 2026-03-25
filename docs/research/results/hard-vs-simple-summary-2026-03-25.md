# Hard-Task vs Simple-Task L4 Comparison (2026-03-25)

## Hypothesis
Harder tasks (merge_sort, binary_search, BFS) with longer code and deeper Python priors
will show STRONGER pattern blindness than simple tasks (fib, is_sorted, count_vowels).

## Results

### Simple Tasks (L4 example-only, inverted if-semantics)
| Model         | T1-fib | T2-sorted | T3-vowels |
|---------------|--------|-----------|-----------|
| gpt-4o        | 0/10   | 10/10     | 0/50      |
| gpt-4o-mini   | 0/10   | 0/10      | 0/10      |
| gpt-4.1       | 0/10   | 1/50      | 0/10      |
| gpt-4.1-mini  | 0/20   | 20/20     | 0/20      |
| gpt-4.1-nano  | 0/10   | 0/10      | 0/10      |
| gpt-5.4-mini  | 0/10   | 0/10      | 0/10      |
| o4-mini       | 8/15   | 0/20      | 0/20      |

### Hard Tasks (L4 example-only, behavioral I/O examples)
| Model    | H1-mergesort | H2-binsearch | H3-bfs | Overall |
|----------|-------------|-------------|--------|---------|
| gpt-4o   | 4/10 (40%)  | 10/10 (100%)| 10/10 (100%)| 80%  |
| gpt-5.4  | 10/10 (100%)| 10/10 (100%)| 10/10 (100%)| 100% |
| o3       | 10/10 (100%)| 10/10 (100%)| 10/10 (100%)| 100% |
| o4-mini  | 10/10 (100%)| 10/10 (100%)| 10/10 (100%)| 100% |

## Key Finding: Hypothesis REJECTED

Hard tasks show dramatically LESS pattern blindness (80-100% pass) compared to simple
tasks (0% pass for most models). The reversal is explained by a critical methodological
difference:

**Simple tasks (original L4):** Examples embed an IMPLICIT semantic rule (if-block runs
when condition is FALSE). The model must extract this unstated rule from code examples
that superficially look like standard Python.

**Hard tasks (this experiment):** Examples show explicit I/O behavior (descending sort,
inverted presence/absence). The model can directly implement the shown behavior as a
specification without needing to extract a hidden semantic rule.

## Interpretation

Pattern blindness is NOT about task complexity. It is specifically about the gap between:
1. Following explicit behavioral specifications (I/O examples) -- models can do this
2. Extracting implicit semantic rules from code examples -- models cannot do this

When the "inversion" is expressed as clear I/O examples, models comply even when the
behavior contradicts their Python prior. When the same inversion is embedded as an
implicit rule in code structure, models are blind to it.

This finding sharpens the pattern blindness construct: the failure mode is
**rule extraction from implicit code patterns**, not inability to produce
prior-contradicting behavior when directly specified.

## Models Tested
- gpt-5.4 (latest dense model): 30/30 (100%)
- o3 (reasoning model): 30/30 (100%)
- o4-mini (reasoning model): 30/30 (100%)
- gpt-4o (baseline): 24/30 (80%)

## Note on gpt-5.4-pro
gpt-5.4-pro returned 404 (model not available). Substituted o4-mini.
