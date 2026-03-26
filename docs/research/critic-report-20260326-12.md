# --- CRITIC REPORT ---
Date: 2026-03-26 12:15 KST
Overall: **Weak Accept (88%)** — Paper is internally consistent and numerically verified. Two structural gaps fixed this tick: stale §3 open-weight threat text and missing §4 experiment subsections for E25–E27/E31–E35.

---

## STATUS SINCE REPORT-10 (10:01 KST)

| Item | Status |
|------|--------|
| New commits since report-10 | ✅ 1 (this tick: §3+§4 structural fix) |
| New JSON results to integrate | ❌ None |
| Blocking issues | ❌ None |
| PDF compiles clean | ✅ 22 pages, 0 errors |

---

## FIXES APPLIED THIS TICK

### F1: §3 Stale Open-Weight Threat Text (Easy fix — applied)
**Before:** §3 Threats to Validity stated open-weight evaluation is "reported at n=20, Variant A only." This was stale — Qwen3-32B completed 50/50 full replication and Llama-3.3-70B achieved 25/50 valid runs.
**Fix:** Updated both the Construct and External threat bullets to accurately reflect the extended run status and residual limitation (Llama n_eff=5/variant still underpowered).

### F2: §4 Missing Experiment Subsections for E25–E27, E31, E32, E33/E35, E34 (Easy fix — applied)
**Before:** §4 Experiments contained subsections for E24 and E28 but had no protocol descriptions for E25–E27 (L3 diagnostics), E31 (PES via logprobs), E32 (cross-task transfer), E33/E35 (I/O transparency), and E34 (multi-model annotation density). These 5 experiment families are fully described and tabled in §5 but invisible in §4, creating a §4→§5 structural gap.
**Fix:** Added 5 new subsections to §4 (E25–E27, E31, E32, E33/E35, E34) with brief protocol descriptions and cross-references to corresponding §5 results sections.

---

## CRITICAL ISSUES

**None.** All number cross-verifications from report-10 confirmed clean. No new data to integrate.

---

## MAJOR WEAKNESSES (Remaining — not fixed this tick)

### W1: §3 "Models Evaluated" list is incomplete (Medium effort)
§4 lists only the 7 core OpenAI models. The paper also evaluates gpt-5.4, o3 (hard-task + E24), Llama-3.3-70B, and Qwen3-32B. A reviewer will immediately notice the model list is a subset.
**Action:** Add a "Additional Models" sub-item or note: *gpt-5.4, o3 (hard-task extension/E24); Llama-3.3-70B, Qwen3-32B (open-weight, via Groq API).*

### W2: E28 vs. E34 Section Overlap / Redundancy (Cosmetic, low priority)
§5 has both §E28 (o4-mini only, 40 runs) and §E34 (3-model, 150 runs) as separate subsections. E28 is now subsumed by E34's richer data. A reviewer might ask why E28 is a standalone section rather than being folded into E34 as the "o4-mini pilot."
**Action (optional):** Collapse E28 into E34 as a "pilot study" paragraph, or add a clear forward pointer at the top of E28 directing readers to E34 for the full analysis.

### W3: gpt-4.1-mini T1 PPR anomaly under-explained (Minor)
Table 3 shows gpt-4.1-mini PPR=0.38 overall (lowest of all models). §5 explains variant-level non-monotonicity, but the introductory sentence "PPR values range from 0.38 to 1.0" without caveating that 0.38 is a statistical artifact of variant-averaging (individual variants span 0.00–1.00) could mislead a reader into thinking gpt-4.1-mini is the "most resistant" model when it is not in the sense the reader expects.
**Action:** Add one clarifying parenthetical in §5.4 intro: "(gpt-4.1-mini's 0.38 overall PPR reflects variant heterogeneity, not a uniformly lower prior pull; see variant-level values in Table 3)."

### W4: Hard-task I/O transparency confound — never explicitly resolved (Medium effort)
§5 and §6 correctly note the prior-depth/I/O-transparency confound for hard tasks and label it a hypothesis. However, E35 only tests opaque I/O on a *different* task (opaque_counter), not on the hard tasks themselves. A reader asking "does IO-transparency explain hard-task success?" cannot answer this from current data.
**Action (future work, but should be stated explicitly in §6 Limits):** Add one sentence: "E35 establishes I/O opacity as sufficient for resistance on a separate task; whether removing I/O transparency from the hard tasks (H1–H3) would recover resistance remains untested and is the most direct experiment to resolve the confound."

### W5: Llama-3.3-70B open-weight section is structurally disordered
The "context-sensitive prior reversion" hypothesis for Llama is introduced in §5 Open-Weight, then repeated almost verbatim in §6 Discussion §6.3. The two occurrences duplicate rather than build on each other.
**Action:** In §6.3, replace the duplicated hypothesis description with a one-sentence forward reference to the §5 description, then add one new sentence on implications.

---

## STRENGTHS

### S1: Statistical rigor is exemplary for a venue paper
Wilson CIs throughout, Fisher's exact p-values for all binary comparisons, explicit n_eff accounting for HTTP errors, temperature caveats for o4-mini. This is publication-ready statistical hygiene.

### S2: Three-failure-mode taxonomy is the paper's strongest conceptual contribution
Prior dominance / Pattern blindness / Operational substitution is clearly differentiated, evidenced at distinct n-sizes, and the failure taxonomy cross-check (419/427 pool) is clean.

### S3: E32 control condition is a genuine strength
0/10 control (non-inverted examples → no transfer) directly rules out cross-task priming as confound. This is methodologically careful and reviewers will appreciate it.

### S4: PES (E31) adds a mechanistic dimension
Logprobs-based prior measurement is a smart addition. The PES vs. L4 outcome dissociation (fib ≈ merge_sort PES yet opposite resistance) advances the theoretical framing beyond behavioral results alone.

### S5: E34 annotation density result inverts naive expectation
The "code example (0% verbal) > full explicit rule (100%)" finding is genuinely surprising and directly extends E32's cross-task contamination insight. Well motivated and clearly presented.

### S6: Related work is comprehensive and well-scoped
MultiCodeIF explicit/implicit asymmetry cited as closest prior; Lampinen A-Not-B errors cited for pattern blindness analogy; Khan et al. (77% accuracy drop) cited as closest educational prior. The research gap paragraph is crisp.

---

## TARGET VENUE (IEEE format retained)

- **Best fit:** IEEE ICSE (SEET track), MSR Education track, or ICER (CS Education Research)
- **Alternative:** ACL Findings workshop (NLP+Education angle — but would require format change)
- **Submission readiness: 88%**

### Path to 90%+:
1. Fix W1 (model list, ~10 min) → +0.5%
2. Fix W3 (gpt-4.1-mini PPR clarification, ~5 min) → +0.5%
3. Address W4 in §6 Limits (one sentence, ~5 min) → +0.5%
4. Collapse E28 into E34 intro (W2, ~20 min) → +0.5%

None of these require new experiments. Pure writing fixes.

# --- END REPORT ---
