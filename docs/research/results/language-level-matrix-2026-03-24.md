# Language Level Difficulty Matrix — 2026-03-24 (Updated)

## Complete Results Table

| Model | L1 KLR ↓ | L2 SIR ↓ | L3 PPR ↓ (explicit) | L4 pattern noticed |
|---|---|---|---|---|
| gpt-4o-mini | 0.423 | 0.000 | **1.000 (FAILS)** | No (ignored examples) |
| gpt-4o | 0.366 | 0.000 | **0.000 (SUCCEEDS)** | No (ignored examples) |
| gpt-4.1-mini | 0.431 | N/A | **0.000 (SUCCEEDS)** | N/A |
| gpt-4.1-nano | 0.690 | N/A | N/A | N/A |
| gpt-5.4-mini | 0.670 | N/A | N/A | N/A |

## Level Definitions

| Level | Design | Difficulty rationale |
|---|---|---|
| L1 | Token alias substitution | Tests surface token prior |
| L2 | Syntax structure inversion | Tests structural prior |
| L3 | Semantic inversion (explicit rules) | Tests semantic reasoning with instruction |
| L4 | Semantic inversion (implicit, from examples) | Tests few-shot pattern extraction |

## Key Findings

### F1: L2 is not resistant — LLMs adopt new syntax easily
All tested models achieved SIR=0.0 when given explicit L2 rules.

### F2: L3 reveals a model capability threshold
- gpt-4o-mini cannot follow semantic inversion even when explicitly explained → **PPR=1.0**
- gpt-4o and gpt-4.1-mini CAN follow semantic inversion when explained → **PPR=0.0**

### F3: L4 (implicit) defeats even strong models via a different mechanism
gpt-4o completely ignores the inversion pattern in examples and writes standard Python.
This is NOT prior dominating — it's **pattern blindness**: the model doesn't notice the semantic anomaly in examples.

### F4: Two distinct failure modes discovered
1. **Prior Dominance (L1, L3 weak models)**: Model knows the rule but prior overrides
2. **Pattern Blindness (L4)**: Model doesn't extract the semantic rule from examples at all

## Theoretical Framework (emerging)

```
LLM language resistance spectrum:
L1 (token)  →  Partial resistance (prior sometimes wins)
L2 (syntax) →  No resistance (models adopt easily)
L3 (semantic, explicit) → Conditional resistance (capacity-dependent)
L4 (semantic, implicit) → High resistance via pattern blindness
```

Ideal LLM-resistant language: **Python surface + inverted semantics + no explicit rule given**

## Next Steps
- [ ] Run L4 with gpt-4o-mini, gpt-4.1-nano (expect pattern blindness too)
- [ ] Design L4-v2: add more examples to help model, see if pattern emerges
- [ ] Quantify SCR (Semantic Correctness Rate) for all levels
- [ ] Update paper with 4-level difficulty taxonomy
