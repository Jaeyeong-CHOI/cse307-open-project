# --- CRITIC REPORT ---
Date: 2026-03-25 18:56 KST
Overall: **Weak Accept (76%)** — Paper has made substantial progress since 17:52 report. Core experimental claims are now well-supported with appropriate statistical rigor (n=50 per model, Wilson CIs, Fisher's exact). The remaining blockers are C1 (no human baseline) and C2 (format). One new structural concern (C3) identified this tick: the multi-task experiment description in §4 still says "identical shared prompt header (two worked examples with inverted semantics, no explicit rule)—the same prompt structure as Ablation Variant A" but Table 4 caption and §5.4 correctly warn these are partially-annotated. This §4/§5 inconsistency is subtle but a top-tier reviewer would catch it.

---

## STATUS SINCE 17:52 REPORT

| Issue from 17:52 | Current Status |
|----------------|----------------|
| C1: Human pilot | ❌ Still unstarted (requires human action) |
| C2: IEEEtran → ACL format | ❌ Still pending (requires human action) |
| E3: Annotation density gradient (o4-mini) | ❌ Not run (new high-value experiment) |
| All automated fixes from prior ticks | ✅ Confirmed committed |

---

## CRITICAL ISSUES (must fix before submission):

**C1: No human baseline study** [UNCHANGED — HUMAN REQUIRED]
The central educational claim — "L4 defeats LLMs while humans can still solve it" — is entirely unverified empirically. The paper currently states this follows "directly from mechanics of NTP-based generation" without experiment. A top-tier PC member will write: *"The authors claim practical utility for programming education, but present zero evidence that human students can actually solve L4 tasks. The paper has no human participant data whatsoever. Without Exp-5, this is an interesting AI evaluation paper with speculative educational implications — not an educational technology contribution."*
→ **Fix**: Run n≥5 DGIST undergrad pilot on T1 Fibonacci (open-book, rule sheet provided). Protocol is at `docs/research/human-pilot/pilot-protocol.md`. Even 5 humans (all passing) vs 0/50 LLMs is a dramatic, publishable contrast.

**C2: IEEEtran format for ACL/EMNLP target** [UNCHANGED — HUMAN REQUIRED]
The paper uses IEEEtran but appears to target ACL/EMNLP venues (the paper cites ACL-style papers, uses ACL bib keys, `main_acl.tex` stub exists). A submission in the wrong format is desk-rejected. At 12 pages (IEEEtran), the ACL equivalent is likely ~14-16 pages, which would exceed 8-page ACL long paper limit or 4-page Findings/short limits.
→ **Fix**: Convert to ACL 2026 template before any submission planning. Budget 2-3 hours.

**C3: §4 Multi-task experiment description contradicts §5.4 protocol warning** [NEW — AUTOMATABLE]
§4.5 (L4 Multi-task Generalization Experiment) states: *"Both use the identical shared prompt header (two worked examples with inverted semantics, no explicit rule)—the same prompt structure as Ablation Variant A."* But §5.4 and Table 4 correctly clarify that this experiment uses *partially-annotated* prompts with inline comments. The §4 description misleads readers into believing multi-task uses the same strict protocol as ablation. A reviewer comparing §4 to Table 4's bold warning ("NOT directly comparable to Table 3") will flag an internal inconsistency.
→ **Fix**: Update §4.5 to explicitly state the inline comment annotation, consistent with §5.4.

---

## MAJOR WEAKNESSES (top-tier requires addressing):

**W1: Open-weight results are pilot-scale and architecturally sparse** [UNCHANGED CONCERN]
Llama-3.3-70B and Qwen3-32B are the only non-OpenAI models. Both have fundamental limitations: Llama has n_eff=5 per variant (Groq rate limits), Qwen fails even at L3. The paper is currently 78% an OpenAI API evaluation paper, 22% a research contribution. A reviewer will note that architecture/fine-tuning claims based on 2 models are speculative. Mistral, Gemini, Claude would all strengthen generalizability claims.
→ **Address**: Either tone down "architecture governs compliance" to "preliminary evidence suggests..." (already partially done) OR add one more open-weight model (Mistral-7B on Groq is fast/cheap). Current framing is acceptable at workshop level; main track would benefit from more diversity.

**W2: Confound between prior entrenchment depth and I/O transparency is unresolved** [PARTIALLY ADDRESSED]
The hard-task conclusion ("prior entrenchment depth governs resistance") co-varies with I/O specification transparency. The paper correctly flags this in §5.7 and §6.1. However, no experiment separates these. A PC member will argue: *"The hard task results are entirely explained by I/O transparency — the model reads 'merge_sort([3,1,4,2]) → [4,3,2,1]' and trivially infers descending order. This has nothing to do with prior depth. You haven't isolated your proposed mechanism."*
→ **Address**: Design one experiment that holds I/O transparency constant while varying prior depth. E.g., use Fibonacci-adjacent tasks with explicit I/O pairs (a hard but prior-entrenched version) vs. easy tasks with only code examples (shallow prior, low I/O transparency). Even n=10 would address this concern.

**W3: The "reasoning-generation dissociation" finding needs tighter framing** [PARTIALLY ADDRESSED]
The CoT ablation shows models articulate the inversion rule but generate wrong code. This is framed as a "dissociation." But a skeptical reviewer will note: (a) n=20 per condition at n=4 models is small, (b) "mentions_inversion" is a text-match metric on the reasoning chain — not a verified measurement of semantic understanding, (c) the dissociation could simply reflect that CoT prompting induces parroting of the prompt. The current finding is interesting but underpowered.
→ **Address**: At minimum, clarify what "mentions_inversion=100%" means operationally (exact substring match? semantic match?). Better: scale to n=50 for gpt-4o CoT ablation to establish statistical confidence.

**W4: The "operational substitution" failure mode needs an execution-based judge** [ACKNOWLEDGED, NOT FIXED]
The paper correctly identifies that the structural judge for operational substitution "may miss novel arithmetic transformations." At 94% detection rate (47/50), this is reported honestly. But a reviewer will note: T3 (count_vowels) operational substitution is only confirmed for gpt-4o at n=50; the "confirmed as a third failure mode" claim rests on a single model's extended evaluation.
→ **Address**: Run T3 for at least one additional model to n=50 to confirm generalizability of the operational substitution mode. Or implement an execution-based judge for T3 specifically (it's a simple function — run the generated code and check outputs against ground truth).

---

## MINOR ISSUES:

**M1: §4.5 multi-task n-count inconsistency** 
The §4 text says "255 initial runs" and §5.4 says "345 total multi-task runs" but neither clearly accounts for the gpt-5.4-mini addition (30 runs, bringing to 355 per status.md). The paper abstract says 345 runs; status.md mentions 355 and then 395 after o4-mini T2/T3 extension. The reader tracking these numbers through the text will get confused.
→ **Fix**: Audit all multi-task run counts and make them consistent through abstract, §4, §5, Table 4 caption.

**M2: gpt-4.1-mini variant B PPR=0.00 anomaly unexplained**
Table 3 shows gpt-4.1-mini gets PPR=0.00 on variant B (3 extra examples) and PPR=0.00 on variant D (2ex-swapped), but PPR=1.00 on variant E (different domain). The paper mentions this in the "domain-shift anomaly" paragraph. But variant A also shows PPR=0.10 (better than E at 1.00). The proposed hypothesis (in-domain example alignment) doesn't cleanly explain why variant A (2ex-baseline, in-domain) only gets 0.10 while variant B (3ex, in-domain) gets 0.00. More examples → lower PPR makes sense, but this should be stated explicitly.
→ **Fix**: Add one sentence clarifying that example count and domain jointly modulate extraction quality in this model.

**M3: The §6 discussion contains two near-identical paragraphs on L4 condition clarification**
§6.1 has a paragraph "Clarifying which results belong to which L4 condition" that substantially overlaps with the Note box in §5.4. This redundancy costs space and reads as self-defensive rather than analytical.
→ **Fix**: Consolidate. Keep the §5.4 protocol note (it's appropriately placed at the results section). In §6.1, reduce to 1-2 sentences pointing readers to §5.4 for protocol details.

**M4: Figure 1 (taxonomy) has inconsistent cell sizing**
The "not studied" cells use `minimum width=1.8cm` while studied cells use `minimum width=1.6cm`. This creates visual misalignment in the grid. Minor but noticeable in a polished PDF.
→ **Fix**: Unify to 1.8cm or use fixed column widths.

**M5: Abstract run-count needs verification** 
Abstract says "910 total L4 evaluations spanning 13 models." Per the footnote: 350 + 75 + 20 + 120 + 345 = 910. But status.md mentions 910 total. The abstract footnote breakdown needs to reconcile with multi-task = 345 or 355 or 395 (conflicting numbers in status.md).
→ **Fix**: Lock down the canonical multi-task run count, then verify the 910 total via the footnote arithmetic.

**M6: "confusion language" terminology needs Wikipedia/prior-work disambiguation**
The paper coins "confusion language" as its proposed terminology (now correctly noted as proposed in §3). However, this term might be confused with obfuscation languages (brainfuck, etc.) or esolang literature. A brief 1-sentence disambiguation would preempt reviewer confusion.
→ **Fix**: Add in §3.2: "We distinguish confusion languages from esoteric languages (e.g., brainfuck), which aim for human uninterpretability; confusion languages retain full human interpretability while selectively targeting LLM NTP priors."

---

## STRENGTHS:
**S1**: Three failure modes (prior dominance, pattern blindness, operational substitution) are well-defined, empirically distinguished, and practically actionable for assessment design.
**S2**: The n=50 scale-up for all 7 core OpenAI models with Wilson CIs represents genuine statistical rigor — rare in this type of paper.
**S3**: E24 (gpt-5.4 and o3 on strict Fibonacci) is a decisive experiment that closes the "frontier models might work" objection. The result (0/10, PPR=1.00 for both) is clean.
**S4**: The CoT ablation "reasoning-generation dissociation" is a genuinely interesting finding — models verbalize the rule but generate wrong code. This deserves its own paper someday.
**S5**: The Qwen3-32B L3 failure (confirmed at n=20) is an important architectural finding — the L3/L4 taxonomy reveals qualitatively different model capability classes.
**S6**: The gpt-4.1-mini vs. gpt-4.1 T2 anomaly (non-monotonic capacity, confirmed via Fisher's exact p<0.0001) is surprising and theoretically interesting.
**S7**: Related work coverage is thorough: CodeIF, MultiCodeIF, knowledge conflict papers (Xie et al., Wu et al., Zhang et al.) are all cited and connected to the findings.

---

## RECOMMENDED NEXT EXPERIMENTS:

**E1 (HIGH PRIORITY): Human pilot study — T1 Fibonacci open-book, n=5**
→ Proves: humans can solve L4 when given the rule; LLM-human gap is real and large
→ Cost: ~100 person-minutes + coordination; no API cost
→ Paper impact: transforms educational claim from speculative to empirical; likely +10% submission readiness

**E2 (HIGH PRIORITY): Annotation density gradient for o4-mini**
→ Design: 0% / 25% / 50% / 75% / 100% annotation on T1 Fibonacci (n=10 per level, 50 total runs)
→ Proves: where exactly is the L3↔L4 boundary for reasoning models? Maps the phase transition
→ Cost: ~$2-3 API, 1 hour
→ Paper impact: resolves the "partial annotation is the vulnerability" claim quantitatively

**E3 (MEDIUM PRIORITY): Confound isolation — prior depth vs. I/O transparency**
→ Design: Create a "hard Fibonacci" variant with explicit I/O pairs but same recursive structure (shallow prior + transparent I/O). Compare to standard Fibonacci (deep prior + opaque code examples).
→ Proves (or disproves): whether prior entrenchment or I/O transparency is the driver of hard-task success
→ Cost: ~$2-3 API, 1-2 hours design + 1 hour run
→ Paper impact: resolves W2 (the main theoretical weakness)

**E4 (MEDIUM PRIORITY): T3 execution-based judge for gpt-4.1-mini at n=30**
→ Design: Run T3 count_vowels for a second model (gpt-4.1-mini) to n=30; implement Python subprocess judge checking actual function outputs
→ Proves: operational substitution is a cross-model phenomenon, not gpt-4o-specific
→ Cost: ~$1 API, 2 hours (judge implementation)

**E5 (LOW PRIORITY): gpt-4.1-mini variant-level analysis deep dive**
→ Design: Run 5 additional variants for gpt-4.1-mini at n=20 each with systematic domain-match/mismatch factorial
→ Proves: domain-shift anomaly is replicable; isolates example domain as causal variable

---

## TARGET VENUE:
- **Best fit right now**: ACL 2025 Findings (short/findings track) or EMNLP 2025 industry track
- **Stretch goal**: ACL 2026 main track (requires C1 + C2 + W2 resolution)
- **Submission readiness**: **76%** (unchanged from 17:52 report; no new experiments run)

**Blocking 76% → 80%**: Complete C1 (human pilot) — can be done TODAY with minimal overhead
**Blocking 80% → 85%**: Complete E2 (annotation density) + fix §4.5 inconsistency (C3)
**Blocking 85% → 90%**: Complete C2 (format) + E3 (confound isolation)
**Blocking 90% → 95%**: Resolve W2 experimentally + scale CoT ablation to n=50

# --- END REPORT ---
