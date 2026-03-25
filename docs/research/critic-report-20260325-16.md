# --- CRITIC REPORT ---
Date: 2026-03-25 16:09 KST
Overall: **Weak Accept** — Since the 13:42 report, the paper has addressed nearly every fixable issue (E24/E25/E26 experiments added, M1/M4/M5/M6/M7/W2/W3 fixed, Llama n=50 partial, Qwen n=50 full, hard-task confound caveat explicitly stated). The paper is now structurally sound and internally consistent. The two remaining blocking issues—C1 (human baseline absence) and C2 (IEEEtran format)—both require human action that cannot be automated. The paper is the best version it can be without human study data. The core contribution is clear, the experiments are rigorous at n=50 scale, and the failure-mode taxonomy is the most actionable finding in the current literature on LLM code assessment.

---

## CRITICAL ISSUES (must fix before submission)

**C1: No human baseline — the educational claim is still asserted, not evidenced**
- The paper's central pitch in §6.2 is that L4 creates a meaningful human–LLM asymmetry. Current text: "A student who reads the rule... can immediately apply it." This is presented as self-evidently true.
- A top-tier reviewer will ask: have you actually tested this? What if students also confuse themselves on L4 Fibonacci with inverted semantics? The answer "it follows from NTP mechanics" is not empirical evidence.
- The paper now hedges appropriately ("A formal human study (Exp-5, planned) is needed to quantify the exact human--LLM performance gap") which is honest, but this hedge is exactly what a reviewer uses to justify rejection.
- **Fix**: Run n≥5 pilot (DGIST undergrads, open-book rule sheet, T1 Fibonacci only, 15–20 min). Even qualitative evidence (5/5 humans pass T1 with rule sheet, vs. 0/50 LLMs) would transform this from an asserted gap to a measured one. Protocol already designed at `docs/research/human-pilot/pilot-protocol.md`.
- **Impact if unfixed**: For ACL/EMNLP main, this is likely a decisive rejection factor. For Findings or short paper, it weakens but doesn't kill the submission.

**C2: IEEEtran format for all ACL/EMNLP/NeurIPS target venues**
- `\documentclass[conference,10pt]{IEEEtran}` is incompatible with every listed target venue.
- The `main_acl.tex` stub exists but is not the compiled primary file.
- Page count estimates are unreliable: 12 pages under IEEEtran ≠ page count under ACL 2026 template.
- **Fix**: Before sharing externally or planning submission length, convert to ACL 2026 template. This is a 2–3 hour task.

---

## MAJOR WEAKNESSES (top-tier requires addressing)

**W1: Abstract sentence "thirteen models" creates verification burden for reviewers**
- The abstract claims "thirteen models" but the count reaches 13 only by combining: 7 core OpenAI, 2 frontier (gpt-5.4, o3), 2 open-weight (Llama, Qwen), plus gpt-5.4-mini (L1 baseline only) and possibly gpt-4o-mini. The counting is real but will trigger skepticism.
- Table 1 lists 12 rows including gpt-4o/gpt-4.1 families + Llama/Qwen. The abstract says "eleven OpenAI, 2 open-weight" = 13. Technically correct but the frontier models (gpt-5.4, o3) only appear in E24 (n=10 Fibonacci) and the hard-task battery. A reviewer who checks will find that gpt-5.4 L1 baseline uses gpt-5.4-mini (not gpt-5.4), and gpt-5.4 itself is only in hard-task + E24.
- **Fix**: Add one sentence: "Model coverage varies by experiment: 7 core models appear throughout; gpt-5.4 and o3 appear in §5.7 (hard-task) and E24 (Fibonacci); Llama-3.3-70B and Qwen3-32B appear in §5.8 (open-weight preliminary)." This sets expectations correctly.

**W2: Qwen3-32B L3 failure (E26) is a major negative finding under-emphasized in the Discussion**
- E26 shows Qwen3-32B fails L3 (0/5, PPR=0.80). This means the model cannot follow an **explicit** semantic inversion rule, let alone an implicit one. This is qualitatively different from every OpenAI model tested.
- The Discussion §6.4 mentions this in "Open-weight model failure modes" but the implication is not drawn out clearly: **Qwen3-32B cannot be used as a "resistant-to-LLM" assessment target at all**, because it fails even L3. You're not measuring L4 pattern blindness in Qwen; you're measuring a more basic failure.
- More importantly: if Qwen3-32B fails L3, then L4 resistance against Qwen is meaningless for the assessment use case—an assessment that blocks a model that can't even follow explicit rules is trivially too hard for the model but for the wrong reason.
- **Fix**: In §6.4 or the conclusion, explicitly state: "For open-weight models that fail L3 (e.g., Qwen3-32B), L4 resistance is vacuous for assessment purposes—the model is blocked at a more fundamental level. L4-style assessment design is most meaningful for models that pass L3 (instruction-following capable) but fail L4 (pattern extraction absent)." This sharpens the scope of the claim.

**W3: The CoT ablation has a critical internal inconsistency still not addressed**
- §5.6 says: "o4-mini: CoT reduces PPR from 0.95 to 0.65 and raises mentions_inversion to 35%."
- But §5.4 (Finding 5) says: "o4-mini achieves 8/15 on T1 under the partially-annotated prompt (after token budget correction)" — i.e., o4-mini can pass with partial annotation.
- The CoT ablation is Variant A (strict example-only). So: o4-mini with CoT at strict Variant A gets 1/20 (5%), but o4-mini with partial annotation (no CoT) gets 8/15 (53%). This contrast is interesting and important: **partial annotation is more effective than CoT instruction for o4-mini**. This deserves explicit discussion.
- Currently the paper discusses these results in separate sections without connecting them. A reviewer will ask: "If o4-mini can be tricked with partial annotation but not with CoT, what does this tell us about the nature of the failure?"
- **Fix**: In §6.1 or the CoT section, add: "Notably, o4-mini succeeds at 53% (8/15) under partial annotation (§5.4), yet only 5% (1/20) under CoT without partial annotation. This dissociation suggests that for reasoning models, partial rule disclosure (annotation cues) is a more effective pathway to inversion than meta-cognitive prompting alone. CoT may help dense models articulate the pattern, but does not provide the rule content itself."

**W4: Llama-3.3-70B per-variant data is too sparse to support the "context-sensitive prior reversion" claim**
- n_eff=5 per variant (due to 25/50 HTTP errors). The §5.8 text now reports per-variant PPR (Var. A=0.00, B=0.00, C=0.60, D=1.00, E=1.00) as evidence for "context-sensitive prior reversion."
- At n=5 per variant, confidence intervals are enormous. Wilson 95% CI for PPR=0.00 (0/5) is [0%, 43%]; for PPR=1.00 (5/5) it's [57%, 100%]. These overlap substantially.
- The claim "Llama applies standard control flow without inversion on Variants A/B (where I/O examples provide inversion cues) but reverts to strict Python prior on D/E" cannot be statistically supported at n=5 per variant.
- **Fix**: Add Wilson CIs to the per-variant Llama data. Change the language from "reveals a qualitatively different failure mode" to "suggests a potentially different failure mode, but n_eff=5 per variant precludes statistical claims; full replication is deferred." The current paper says "should be treated as preliminary" but doesn't show the CIs, leaving readers without the tools to evaluate the reliability.

---

## MINOR ISSUES

**M1: Abstract "915 total L4 evaluations" math needs verification**
- The abstract says "915 total L4 evaluations spanning 13 models (11 OpenAI, 2 open-weight)."
- Count: 350 (L4 ablation, 7 core models) + 20 (E24 gpt-5.4 + o3, Fibonacci) + 120 (hard-task, 4 models) + 345 (multi-task) + 160 (CoT ablation, 4 models, included in ablation?) = complex overlap. Does the CoT ablation count separately? The 160 CoT runs are on the same Variant A prompt as part of the ablation set.
- Also: "11 OpenAI" = gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-5.4-mini, o4-mini (7 core) + gpt-5.4, o3 (2 frontier) + ? = 9 or 11? If gpt-5.4 ≠ gpt-5.4-mini, then both appear. Verify the count.
- **Fix**: Add a footnote to the abstract: "L4 total excludes CoT ablation (160 runs, §5.6) to avoid double-counting. Counts verified against experiment log (§9)." Or adjust the number if CoT is counted.

**M2: Figure 1 (taxonomy figure) caption says "L4 (dark red) occupies the hardest cell" but L4 is colored green in the figure code**
- `fill=green!25` for L4 node; the caption says "dark red." Color–caption mismatch.
- **Fix**: Either change the figure fill to `fill=red!25` or update the caption to say "L4 (green) occupies the hardest cell (most resistant to LLM)." The green coding makes semantic sense (green = resistant from attacker's perspective) but "dark red" is wrong.

**M3: §5.7 (hard-task) and §6.1 (synthesis) both contain the hard-task confound caveat in almost identical language**
- §5.7: "This experiment differs from the strict L4 ablation in two respects, not one: (1) prior entrenchment depth and (2) I/O specification transparency."
- §6.1: "The hard-task extension differs from (1) in both prior depth and I/O transparency."
- There's near-verbatim overlap between these two passages.
- **Fix**: Shorten one of them to a forward/back reference. Either trim §5.7 and say "see §6.1 for synthesis," or trim §6.1 and say "as noted in §5.7."

**M4: The word "confusion language" in the abstract/keywords does not appear to be established terminology—no citation provided**
- The abstract says "designing a programming language" but the keywords include "confusion language." This term doesn't appear in the related work citations.
- If this is a new term being coined, it should be explicitly marked as such in the text.
- **Fix**: Add "(which we term a \emph{confusion language})" the first time the concept is introduced in §1 or §3, with a note that this is the authors' proposed terminology.

**M5: The E25 result (gpt-4.1 passes L3 T2 10/10) is mentioned in §6.3 but not in the experiment log §9**
- Status.md shows E25 was logged. But checking: the experiment log (§9) shows E25 as "L3-T2 diagnostic for gpt-4.1" — this should be confirmed present in the paper's §9 section. If it is there, this minor issue is resolved.
- **Fix**: Verify §9 experiment log includes E25 and E26 correctly.

**M6: Python version still needs confirmation in §9**
- The previous report flagged missing Python version. The status.md shows latexmk 4.87 was added (M6 fix). But "Python 3.x" with specific version number should be present.
- Check that openai, groq package versions are specified in §9.

---

## STRENGTHS

**S1**: E24 (gpt-5.4 and o3 on L4 Fibonacci, 0/10 each PPR=1.00) directly closes the most critical vulnerability from the 13:42 report. The core claim "L4 pattern blindness on prior-entrenched tasks holds for frontier models" is now empirically supported, not just inferred. This makes the paper reviewable without the reviewer falsifying it themselves.

**S2**: The E26 Qwen3-32B L3 diagnostic (0/5, PPR=0.80) adds a genuinely interesting negative result: general semantic meta-rule failure vs. L4-specific pattern blindness. The taxonomy is now richer — three failure modes plus the newly-characterized "Qwen-type" general instruction-following failure.

**S3**: E25 (gpt-4.1 passes L3 T2 10/10) provides exactly the mechanistic evidence needed to support the RLHF over-alignment hypothesis. The paper's strongest hypothesis is now backed by direct experiment: gpt-4.1 can follow explicit rules but fails to extract them from examples — isolation of pattern extraction as the failure mechanism.

**S4**: The paper now explicitly maps three L4 sub-conditions (strict ablation, partially-annotated multi-task, hard-task extension) to their evidentiary strength in §6.1. This is methodologically sophisticated and will pre-empt the most common reviewer complaint about conflating conditions.

**S5**: Failure taxonomy across 419 failed L4 runs (Type-I 83.1%, Type-II 12.6%, Type-III 4.3%) provides the first large-scale empirical characterization of how LLMs fail L4 tasks. This quantitative breakdown is directly useful for educational assessment design.

**S6**: The open-weight section now covers both n=50 ablation (Qwen, complete) and n=25 valid (Llama, partial with per-variant structure). The cross-family variance finding (KLR 0.23 vs 1.00) is the most practically actionable L1 finding for non-OpenAI educators.

**S7**: Statistical hygiene remains high throughout: Wilson CIs, Fisher's exact p-values, explicit scale-up from n=10 to n=50 to resolve preliminary artifacts (gpt-4o T3, gpt-4.1 T2). The paper consistently demonstrates that preliminary findings can be misleading at small n.

---

## RECOMMENDED NEXT EXPERIMENTS

**E1 [URGENT — 4–6 hours]: Human pilot study (n≥5, T1 Fibonacci, open-book rule sheet)**
- Protocol: `docs/research/human-pilot/pilot-protocol.md`
- What it proves: establishes the human baseline that the entire educational argument depends on
- Expected result: ~5/5 or 4/5 humans pass with rule sheet, confirming "humans can follow what LLMs can't extract"
- If humans also fail T1 with rule sheet: major finding, revise educational framing
- Cost: 5 × 20 min sessions = 100 person-minutes + coordination
- Transforms: submission readiness from 65% → 80%; enables ACL 2026 main submission

**E2 [MEDIUM — 1 hour]: Qwen3-32B full L3 ablation (n=20, Fibonacci + is_sorted)**
- E26 used n=5. At n=20, can distinguish "consistent failure" from sampling noise.
- What it proves: whether Qwen's L3 failure is systematic (general meta-rule failure) or a small-n artifact
- If confirmed at n=20: sharpens the "architecture-dependent failure taxonomy" claim in §6.4
- Cost: ~$2 in Groq API calls, 20 min

**E3 [MEDIUM — 1 hour]: Partial annotation gradient experiment**
- Currently the paper has: strict example-only (L4) vs. partially-annotated (multi-task L4) vs. explicit rule (L3)
- Missing: systematic test of annotation density. What PPR does o4-mini achieve with 25%, 50%, 75%, and 100% annotation density?
- What it proves: maps the L3↔L4 continuum and identifies the annotation threshold at which o4-mini's reasoning ability kicks in
- This would be the most novel finding for a reasoning-model-focused follow-up paper

**E4 [LOW — ongoing]: Execution-based judge for operational substitution**
- Current structural judge (47/50 detected) may miss novel arithmetic workarounds
- An execution-based judge (run model output on test cases, compare to oracle) would eliminate false negatives
- Not blocking but would strengthen the "operational substitution confirmed at 94%" claim

---

## TARGET VENUE

- **Best fit with human study (E1) completed**: ACL 2026 Findings or short paper — NLP+Education track; EMNLP 2026 main (student track / education application)
- **Without human study**: EDM 2026 (Educational Data Mining), ICER 2026 (Computing Education), or arXiv preprint + targeted venue later
- **Alternative**: NeurIPS 2026 Machine Learning for Education workshop — empirically strong, experimental rigor appreciated, human study less critical for workshop

**Submission readiness: 70%** — Δ+5 from 13:42 report

Progress since 13:42:
- E24 (gpt-5.4/o3 on Fibonacci) ✅ — closes the #1 blocking vulnerability
- E25 (gpt-4.1 L3 T2 10/10) ✅ — supports RLHF over-alignment hypothesis
- E26 (Qwen3-32B L3 diagnostic) ✅ — enriches failure taxonomy
- M1/M4/M5/M6/M7/W2/W3 — most fixed per git log
- Llama n=50 partial, Qwen n=50 full ✅

Remaining blocks in priority order:
1. **C1 (human baseline)** — 4–6 hours, mandatory for ACL/EMNLP main track, important for any venue
2. **C2 (IEEEtran format)** — 2–3 hours, needed before any submission
3. **W2 (Qwen L3 failure implications)** — 20 min writing
4. **W3 (CoT vs. partial annotation dissociation)** — 20 min writing
5. **W4 (Llama per-variant CIs)** — 10 min writing
6. **M1 (abstract "915" count verification)** — 10 min check
7. **M2 (figure color/caption mismatch)** — 5 min fix

# --- END REPORT ---
