# --- CRITIC REPORT ---
Date: 2026-03-25 13:42 KST
Overall: **Weak Accept** — Compared to the 11:31 report, the paper has made substantial progress: Figure 2 data integrity issue resolved, CoT ablation extended to 4 models (160 runs), variant-E domain-shift analysis added, W5 taxonomy split noted, hard-task L4 extension adds a genuinely important boundary condition. However, the hard-task section introduces a new critical confound (C1 new), the absence of gpt-5.4/o3 on the core L4 Fibonacci ablation leaves the claim dangerously open (C2 new), and the human baseline absence remains the single blocking issue for top-tier acceptance.

---

## CRITICAL ISSUES (must fix before submission)

**C1: Hard-task L4 condition is NOT strictly equivalent to simple L4 Fibonacci — the "identical L4 delivery mode" claim is misleading**
- The paper states hard tasks use "2 worked I/O examples demonstrating the inverted behavior, with no explicit rule — identical L4 delivery mode."
- This is factually questionable. For Fibonacci, the inversion targets CONTROL FLOW semantics embedded in code structure (if-blocks execute when condition is FALSE). The inversion is invisible in I/O alone. For merge sort returning descending order, the 2 worked I/O examples make the semantic inversion trivially obvious: input [3,1,4,2] → output [4,3,2,1] requires zero inference about "semantic inversion" — any model can see the output is sorted descending.
- The paper itself acknowledges "A complementary methodological factor reinforces this effect: the hard-task prompts provide explicit I/O specifications (descending-sorted output, inverted return values, reversed traversal order), while the original L4 tasks embed an implicit semantic rule in code structure." This admission reveals the conditions ARE different in a way that confounds the prior-entrenchment hypothesis.
- A reviewer will ask: are gpt-5.4/o3/o4-mini succeeding because the prior is shallower, OR because the I/O examples for hard tasks effectively constitute explicit behavioral specifications? You cannot distinguish these explanations from the current data.
- **Fix**: Add an explicit caveat to §5.7 and Discussion §6.1 that the hard-task L4 condition differs from the simple L4 condition in TWO ways: (a) shallower prior, AND (b) more inferentially transparent I/O specification. Acknowledge that the prior-entrenchment hypothesis cannot be cleanly separated from I/O transparency effects without an additional experiment (e.g., test Fibonacci with I/O examples only, no code structure). Consider renaming to "Hard-Task L4 Extension (different delivery modality)" rather than claiming identical mode.

**C2: gpt-5.4 and o3 are ONLY tested on hard tasks — the paper never tests them on L4 Fibonacci (strict example-only). This leaves the central claim open for the latest models.**
- The paper's core claim: "L4 (semantic inversion, implicit): Effective against all tested models on prior-entrenched tasks (e.g., Fibonacci)."
- But gpt-5.4 and o3 were NOT tested on L4 Fibonacci under the strict example-only ablation. They appear only in the hard-task battery. The paper acknowledges: "Whether these models also overcome deep prior entrenchment (the original L4 Fibonacci task) remains an open question for future work."
- Every senior reviewer at ACL/EMNLP will immediately flag: "If gpt-5.4 or o3 can solve L4 Fibonacci, your entire resistance claim is false for frontier models."
- At n=10 per cell, this experiment costs <$5 in API calls and ~30 minutes. There is no reason NOT to run it.
- **Fix (URGENT — 30 min)**: Run L4 Fibonacci (Variant A, n=10) for gpt-5.4 and o3. If they succeed, the paper's conclusion needs significant revision (which is important to know now). If they fail, you remove a major vulnerability. Either outcome is informative. This should be E24 in the experiment log.

**C3: No human baseline — educational motivation entirely unvalidated (carried from all prior reports)**
- The paper now strengthens the human-LLM asymmetry framing (§6.2 and intro) and says "A student reasons about a rule; an LLM samples from a prior." This framing is compelling but entirely asserted, not measured.
- The planned Exp-5 (human study) is repeatedly cited as "needed." Every reviewer will penalize this.
- With the hard-task finding, the concern deepens: if capable models can solve hard-task L4 by reasoning about I/O examples, why can a human with the rule sheet also not be confused by the same L4 format? The paper doesn't address this.
- **Fix**: Run n≥5 pilot (DGIST undergrads, 30 min each, T1 only with rule sheet). Even qualitative think-alouds from 3 students would transform this claim from speculative to evidenced. Protocol is ready at `docs/research/human-pilot/pilot-protocol.md`.

**C4: IEEEtran format for all stated target venues (ACL/EMNLP/NeurIPS/ICML) — unchanged since first report**
- Still compiles with `\documentclass[conference,10pt]{IEEEtran}`. The `main_acl.tex` stub exists but is not the primary file.
- **Fix**: Convert to ACL 2026 template before any external sharing. The sooner the better, as page-count estimates under IEEEtran are unreliable for ACL submission planning.

---

## MAJOR WEAKNESSES (top-tier requires addressing)

**W1: Open-weight model coverage insufficient — still pilot-level (n=20, Variant A only)**
- Previous report flagged this. Qwen3-32B KLR=1.00 is interesting but unexplained. Does it follow instructions generally, or is this L1-specific? An L3 test (5 runs) would disambiguate.
- Llama-3.3-70B L4: 0/20, PPR=0.05 (described as "1/20 strict Python prior; remaining 19 applied standard control flow without inversion"). Wait — PPR=0.05 means 5% strict Python prior, but 95% "standard control flow without inversion"? This is a third failure mode distinct from both prior dominance AND pattern blindness. The paper should categorize Llama's dominant failure mode explicitly.
- **Fix**: (a) 5-run L3 test for Qwen3-32B to check if it can follow explicit rules at all. (b) Clarify Llama-3.3-70B's failure taxonomy (the 19/20 "standard control flow" is not pattern blindness in the same sense as the OpenAI models — what exactly is happening?).

**W2: The conclusion conflates two different "L4 failure mode" populations**
- Table 3 (L4 ablation, strict example-only, n=50 per model) covers 7 models.
- Table 4 (L4 multi-task, partially-annotated, mixed n) covers 7 models.
- Table 5 (L4 hard-task, I/O examples, n=10) covers 4 models, 3 of which aren't in Table 3.
- The Discussion §6.1 talks about "L4 resistance" as if the findings across these tables form a unified picture. They don't — they represent three increasingly different conditions. The paper handles this with protocol warnings, but the Discussion doesn't separate the takeaways clearly.
- **Fix**: Add a one-paragraph synthesis in §6.1 explicitly mapping which results belong to which condition and what inference is valid from each. Something like: "The strict example-only ablation (Table 3) provides the cleanest evidence that all 7 tested models exhibit pattern blindness. The partially-annotated multi-task results (Table 4) show task-dependent resistance with reasoning-model exceptions. The hard-task extension (Table 5) suggests prior entrenchment depth as a third design axis, but uses a different delivery modality."

**W3: The "prior entrenchment depth" hypothesis is plausible but not the only explanation for the hard-task results**
- The paper argues: Fibonacci has deep prior → models fail; merge sort/BFS have shallow priors → models succeed.
- But there is a simpler confound: the hard tasks specify the DESIRED BEHAVIOR in the I/O examples in a way that is unambiguous even without semantic rule understanding. A model that sees input/output [3,1,4,2]→[4,3,2,1] for merge sort can succeed by pattern-matching on the behavioral requirement, not by "extracting semantic inversion." This is essentially what operational substitution is — succeeding via behavioral spec without semantic rule adoption.
- In other words: gpt-5.4/o3 might be doing "operational substitution" on hard tasks (hitting the correct I/O spec) rather than genuine semantic inversion. The "pass" criterion may be too lenient for the hard-task condition.
- **Fix**: For hard tasks, verify that successful outputs actually implement the INVERTED SEMANTICS (e.g., merge sort with inverted comparison operator), not just produce the correct output via a different algorithmic approach. Add a semantic correctness check as a second judge criterion.

**W4: The gpt-4.1 vs. gpt-4.1-mini non-monotonic finding (T2 1/50 vs. 20/20) is now addressed with hypotheses in §6.3, but remains without any mechanistic evidence**
- The hypotheses (RLHF over-alignment, instruction-tuning regime) are clearly labeled as hypotheses. Good.
- However, a simple diagnostic would strengthen the claim: test gpt-4.1 on L3 (explicit rule) for T2 (is_sorted). If gpt-4.1 succeeds at L3 T2 but fails at L4 T2, the "over-alignment causes pattern extraction failure, not general rule-following failure" hypothesis is supported. If gpt-4.1 also fails L3 T2, the explanation is different.
- This is ~10 API calls and would directly sharpen the discussion.

---

## MINOR ISSUES

**M1**: Abstract still says "seven OpenAI families (GPT-4o through o4-mini), plus two open-weight models" — but gpt-5.4 and o3 appear in the hard-task section. These are two additional models not mentioned in the abstract's model count. The abstract should say "nine OpenAI models (including gpt-5.4 and o3 in the hard-task extension)" or restructure the model listing.

**M2**: §5.7 (hard-task): Table 5 reports gpt-4o at 80% (24/30 across H1/H2/H3). But the H1 (merge sort) result is 4/10. This means at n=10, confidence intervals for H1 are wide: Wilson 95% CI = [16%, 67%]. Four correct out of ten on a binary task is close to 50/50 chance. Add a Wilson CI footnote for H1 gpt-4o (4/10) to prevent over-interpreting this specific cell.

**M3**: §5.4 Finding (2) says "T1 (Fibonacci) is resistant for all non-reasoning models" but then lists o4-mini as "exception." However, the next finding (5) says "Reasoning partially mitigates pattern blindness under partial annotation" — these two findings partially overlap and create redundancy. Consider merging or clearly sequencing them.

**M4**: The CoT ablation now covers 4 models × 2 conditions × n=20 = 160 runs. The text in §5.6 still has some language from before the extension: "four models: gpt-4o, gpt-4.1-mini, gpt-4.1-nano, o4-mini" — this is correct now but the bullet list only shows data for gpt-4o and gpt-4.1-mini in detail, then gpt-4.1-nano and o4-mini. Make sure the o4-mini CoT finding (PPR 0.95→0.65, mentions_inversion=35%) is given equal prominence since it's the most interesting reasoning-model result.

**M5**: §5.6 says "CoT reduces PPR from 0.95 to 0.65 and raises mentions_inversion to 35%." — But o4-mini at no-CoT PPR=0.95 seems inconsistent with o4-mini overall PPR=0.92 in Table 3. Is the CoT ablation using Variant A only? Clarify which variant and condition was used for the CoT baseline. If the no-CoT condition here is a different setup from Table 3, this should be noted.

**M6**: Python package versions still not listed in §9 (Reproducibility). This was flagged as M6 in the previous report and still missing. Add: "Python 3.x, openai==x.y.z, groq==x.y.z, latexmk version" to §9.

**M7**: The term "L4" is used to refer to at least four distinct conditions in the paper: (a) strict example-only Fibonacci ablation, (b) partially-annotated multi-task, (c) hard-task I/O examples, and (d) the L3/L4 contrast in Figure 3. While each section notes the differences, the taxonomy header in Table 1 just says "Semantic inv. / Implicit" for L4 without distinguishing the sub-conditions. A brief "L4 conditions" note in the Method section or a table footnote would help readers track which L4 condition they're reading about.

---

## STRENGTHS

**S1**: The hard-task extension (§5.7) is the paper's most important new finding since the 11:31 report. "Prior entrenchment depth governs resistance" is a clean, teachable insight that elevates the contribution from "LLMs fail a puzzle" to "we understand *why* they fail and what task properties determine whether resistance holds." This is a finding that can anchor a conference talk.

**S2**: CoT ablation now covers 4 models × 160 runs. The reasoning–generation dissociation is now substantially more solid: gpt-4.1-nano (mentions 100%, PPR 1.00→0.20 with CoT) and o4-mini (mentions 35%, marginal 1/20 pass) fill in the story nicely. This is publishable as a standalone finding.

**S3**: Figure 2 (bar chart) was fixed — values now correctly reflect ctx-pack condition for all models. The C1 data integrity issue from the 11:31 report is resolved. ✓

**S4**: Variant-E domain-shift analysis in §5.4 is new and well-handled. The hypothesis is clearly labeled as hypothesis, not finding. The domain-shift mechanism (different semantic domain weakens pattern extraction signal) is coherent and provides a plausible account for gpt-4.1-mini B/D vs. E variance.

**S5**: The human-LLM asymmetry framing in §6.2 is now substantially stronger. "A student reasons about a rule; an LLM samples from a prior" is a memorable and accurate characterization that frames the educational contribution well.

**S6**: W5 from the previous report (failure taxonomy split note) is addressed with the population note at the end of §5.5. The limitation that T3 operational substitution is excluded from the 419-run pool is now explicitly stated. ✓

**S7**: Statistical rigor remains high: Wilson CIs throughout, Fisher's exact for key comparisons, scale-up from n=10 to n=50 to resolve artifacts. The paper's empirical hygiene is notably better than typical workshop papers in this space.

---

## RECOMMENDED NEXT EXPERIMENTS

**E1 [URGENT — 30 min, <$5]: Test gpt-5.4 and o3 on L4 Fibonacci (strict example-only, Variant A, n=10)**
- What it proves: whether the latest frontier models can crack the same L4 Fibonacci task that defeats all 7 current models
- If they fail → "L4 resistance holds even for frontier models on prior-entrenched tasks" — major strengthening of core claim
- If they succeed → "L4 resistance has already been broken by frontier models" — major finding that must be in the paper (and would redirect the contribution)
- CRITICAL: without this, any reviewer testing gpt-5.4 on L4 Fibonacci themselves could falsify your claim in review

**E2 [HIGH — 4-6 hours]: Human pilot study (n≥5, T1 only, with rule sheet)**
- Protocol designed at `docs/research/human-pilot/pilot-protocol.md`
- What it proves: humans with rule sheet achieve near-ceiling performance → validates educational framing
- Upgrade: 60% → ~78% submission readiness

**E3 [MEDIUM — 30 min]: Test gpt-4.1 on L3 T2 (explicit rule, is_sorted)**
- What it proves: whether gpt-4.1's T2 failure is about pattern extraction specifically (L4 fails, L3 succeeds) vs. general difficulty with inverted is_sorted semantics
- Would directly support the RLHF over-alignment hypothesis in §6.3

**E4 [MEDIUM — 30 min]: Test Qwen3-32B on L3 (explicit rule, Fibonacci, n=5)**
- What it proves: whether Qwen3-32B's KLR=1.00 reflects instruction-following failure generally or L1-specific alias resistance
- If Qwen3-32B passes L3 but fails L4: consistent with instruction-following capability without pattern extraction
- If Qwen3-32B fails L3: suggests Qwen doesn't follow semantic meta-rules at all — a different finding

**E5 [MEDIUM — 1 hour]: Semantic correctness verification for hard-task L4 successes**
- Re-judge a sample of successful hard-task runs to confirm they implement inverted semantics (not just produce correct I/O via operational substitution)
- What it proves: whether the "pass" rate in Table 5 reflects genuine semantic inversion or behavioral spec matching

---

## TARGET VENUE

- **Best fit with E1+E2 completed**: ACL 2026 Findings (NLP+Education or Model Analysis track)
- **With E1 alone (no human study)**: EMNLP 2026 short paper (4 pages) or EDM 2026
- **Current state without E1**: RISKY to submit anywhere — a reviewer running gpt-5.4 on L4 Fibonacci could falsify the central claim before the paper is published

**Submission readiness: 65%** — Δ+5 from 11:31 report (Figure 2 fixed, CoT extended, hard-task finding added, multiple minor issues resolved)

Blocking issues in priority order:
1. **E1 (gpt-5.4/o3 on L4 Fibonacci)** — 30 min, MUST DO before any sharing — either confirms or disconfirms core claim
2. **C1 (hard-task delivery mode confound)** — 30 min writing — clarify that hard-task L4 and simple L4 differ in BOTH prior depth AND I/O transparency
3. **C3 (human baseline)** — 4–6 hours, mandatory for ACL/EMNLP main
4. **C4 (IEEEtran format)** — 3 hours, before submission
5. **W1 (open-weight L4 full ablation)** — 2–3 hours
6. **M1 (abstract model count)** — 5 min fix

# --- END REPORT ---
