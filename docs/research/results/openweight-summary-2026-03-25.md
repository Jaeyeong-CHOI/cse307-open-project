# Open-Weight Model Results Summary (2026-03-25)

Models evaluated via Groq API: Llama-3.3-70B-versatile, Qwen3-32B

## L1: Keyword Leakage Rate (KLR) and Partial Structural Score (PSS)

Context-pack delivery, v1-v20 (n=20 per model).

| Model | Type | Delivery | KLR | PSS | Pass |
|-------|------|----------|-----|-----|------|
| Llama-3.3-70B | open-weight | ctx-pack | 0.233 | 0.337 | 0/20 |
| Qwen3-32B | open-weight | ctx-pack | 1.000 | 0.000 | 0/20 |
| gpt-4.1-mini (ref) | proprietary | ctx-pack | 0.21 | 0.37 | 0/20 |
| gpt-4o-mini (ref) | proprietary | ctx-pack | 0.26 | 0.32 | 0/20 |
| o4-mini (ref) | proprietary | ctx-pack | 0.27 | 0.41 | 0/20 |

**Findings:**
- Llama-3.3-70B (KLR=0.233) is competitive with the best proprietary models (gpt-4.1-mini ctx-pack KLR=0.21), showing comparable alias compliance.
- Qwen3-32B (KLR=1.000) shows complete prior dominance -- every alias slot leaked the original Python keyword. This is worse than any OpenAI model tested.

## L4: Semantic Inversion Ablation (Variant A only, n=20)

| Model | Type | n | Pass | PPR | Notes |
|-------|------|---|------|-----|-------|
| Llama-3.3-70B | open-weight | 20 | 0/20 | 0.05 | Low PPR but still 0% pass |
| Qwen3-32B | open-weight | 18* | 0/18 | 1.00 | Complete prior dominance |
| gpt-4o (ref) | proprietary | 10 | 0/10 | 0.40 | Variant A only |
| gpt-4.1-mini (ref) | proprietary | 10 | 0/10 | 0.10 | Variant A only |
| o4-mini (ref) | proprietary | 10 | 0/10 | 0.80 | Variant A only |

*Qwen3-32B: 2 HTTP errors (rate limiting) out of 20 runs.

**Findings:**
- Both open-weight models confirm pattern blindness (0% pass rate), consistent with all proprietary models.
- Llama-3.3-70B has very low PPR (0.05) -- it rarely defaults to standard Python prior but still fails to invert semantics. This suggests a different failure mode: the model generates non-standard code that is neither standard Python nor correctly inverted.
- Qwen3-32B shows PPR=1.0 (complete prior dominance), similar to gpt-4.1 and gpt-4.1-nano among proprietary models.

## Key Takeaway

Pattern blindness at L4 generalizes beyond OpenAI proprietary models to open-weight architectures. Both Llama-3.3-70B and Qwen3-32B fail to extract semantic inversion from examples alone, confirming the robustness of this finding across model families.
