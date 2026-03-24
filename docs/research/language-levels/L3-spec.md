# L3 Language Specification: Anti-Prior Confusion Language

**Design revision date:** 2026-03-24
**Reason for L2 failure:** L2 syntax was fully adopted when explicitly explained. LLMs follow explicit structural rules well. The real research challenge is designing a language that defeats priors even WITH instruction.

## New Design Principle

> **The language must look like Python at the surface but systematically violate Python execution semantics in ways that NTP priors predict incorrectly.**

This is different from L2 (which just had different syntax).
L3 is semantically confusing: it LOOKS like Python but means different things.

## L3 Core Design

### 1. Operator Reversal with Python-like Surface
```
# Looks like Python but REVERSED semantics
if n >= 1:   # means: n <= 1 (condition inverted)
    return n
```

### 2. Keyword Homoglyphs (visually similar but semantically wrong)
```
# `def` → `dеf` (cyrillic е instead of latin e)
# `return` → `retuгn` (cyrillic г)
# Looks identical in most fonts but is different token
```

### 3. Indentation-Semantics Inversion
```
# In L3: OUTER block executes if condition is FALSE
# INNER block executes if condition is TRUE
# This directly inverts Python's if-block semantics
if n <= 1:
    # This runs when n > 1 (inverted!)
    return fib(n-1) + fib(n-2)
return n  # This runs when n <= 1 (inverted!)
```

### 4. Token Alias Maximizing NTP Confusion
Pick aliases that are:
- Common Python words but in wrong syntactic positions
- The WRONG word that NTP would predict at that slot
```
# Python predicts `return` after function body
# L3 uses `emit` (low probability in that position)
# But also uses `if` as a function call, `for` as assignment
```

## Research Hypothesis (Revised)

**H1 (revised):** LLMs with instruction following can adopt explicit L2. The harder challenge is semantic confusion in L3 where surface form matches Python but semantics invert.

**H2:** Homoglyph attacks on Python keywords create persistent confusion even when explicitly told the rule.

**H3:** Semantic inversion (same syntax, opposite meaning) defeats LLMs more than syntactic inversion.

## Experiment Design

### Condition Matrix
| Condition | Language | Context | Expected KLR |
|---|---|---|---|
| A | L1 (token swap) | baseline | ~42% |
| B | L1 (token swap) | context-pack | ~26% |
| C | L2 (syntax inversion) | explicit rules | ~0% (L2 adopts easily) |
| D | L3 (semantic inversion) | explicit rules | ~30-50% (hypothesis) |
| E | L3 (semantic inversion) | baseline | ~70-90% (hypothesis) |

### Key metric: Semantic Correctness Rate (SCR)
Even if model uses the right token, does it produce the right logic?
SCR = fraction of outputs that are semantically correct under L3 rules.
