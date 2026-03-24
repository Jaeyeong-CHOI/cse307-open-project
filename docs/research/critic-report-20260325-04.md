# --- CRITIC REPORT ---
Date: 2026-03-25 04:35 KST
Overall: **Weak Reject** — Interesting mechanism taxonomy with real empirical signal, but critical gaps in experimental rigor (unequal n across models/conditions, single-task backbone, no human baseline) and several methodological issues that a top-tier PC would flag as fatal without revision.

---

## CRITICAL ISSUES (must fix before submission)

**C1: Drastically unequal n across model conditions — confounds all comparisons**
- L4 ablation: gpt-4o/gpt-4o-mini/gpt-4.1-mini/gpt-5.4-mini at n=50, but gpt-4.1/gpt-4.1-nano/o4-mini at n=20.
- L1 contextpack: gpt-4.1 family at n=20 vs. gpt-4o-mini baseline at n=120.
- L4 multitask: gpt-4.1-mini n=20/task, gpt-4o/gpt-4o-mini n=10/task, o4-mini n=15/task.
- **Fix**: Either equalize all conditions to n=20 (acceptable minimum) or explicitly power-analyze why n=20 is sufficient. Currently the paper compares PPR=1.0 (n=20) to PPR=0.70 (n=50) with no confidence intervals, making the comparison meaningless for a reviewer who wants to know if gpt-4.1 is "worse than" gpt-4o.

**C2: L1 KLR=1.00 for gpt-4.1/gpt-4.1-mini/gpt-4.1-nano/o4-mini is NOT reported in Table 1 — a critical discrepancy with the cron task brief**
- The cron task brief states: "L1 KLR (context-pack): gpt-4.1=1.00, gpt-4.1-mini=1.00, gpt-4.1-nano=1.00, o4-mini=1.00" but Table 1 in the paper shows gpt-4.1 ctx-pack KLR=0.30, gpt-4.1-mini ctx-pack=0.21, gpt-4.1-nano ctx-pack=0.38, o4-mini ctx-pack=0.27.
- **This is a data integrity crisis**: either the cron brief is wrong, or the paper table is stale/wrong. Whichever way, this must be reconciled immediately. If KLR=1.00 is the true result, the paper's central claim that "context-pack delivery consistently reduces KLR" is FALSE.
- **Fix**: Re-audit raw JSON files (l1-gpt41-contextpack-2026-03-25.json, etc.) against Table 1. Determine whether the "1.00" in the brief refers to L4 PPR (which would make more sense), not L1 KLR. Update table or brief. This single issue could constitute fabrication if not reconciled.

**C3: No statistical tests — zero confidence intervals, zero significance testing**
- All KLR/PPR comparisons are raw point estimates. For n=10 (L4 multitask gpt-4o T1), a 0/10 pass rate has a 95% CI of [0, 0.31] — it's consistent with 31% true pass rate.
- For n=5 (L2, L3 initial screening), results are anecdotal by any top-tier standard.
- **Fix**: Add at minimum: (1) 95% Wilson confidence intervals on all KLR/PPR values; (2) Fisher's exact test or chi-squared for key comparisons (e.g., gpt-4o T2 10/10 vs. gpt-4o-mini T2 0/10); (3) Explicitly note that L2/L3 results with n=5–10 are exploratory/pilot only and should not be presented as definitive.

**C4: The paper's core construct — "LLM resistance" — lacks a theoretical definition**
- What exactly is the threshold for "resistance"? KLR>0.5? PPR>0.9? Pass_rate=0? The paper switches between metrics (KLR for L1, PPR for L3/L4, pass_rate for multitask) without a unified resistance criterion.
- A reviewer will ask: "At what KLR is L1 'partially resistant' vs. 'not resistant'? Is 0.21 resistant?" The paper never answers this.
- **Fix**: Define a formal resistance criterion (e.g., "a language level provides *robust resistance* if PPR ≥ 0.9 and pass_rate = 0 across all tested models at n ≥ 30"). Apply consistently. This is the theoretical core — it must be crisp.

---

## MAJOR WEAKNESSES (top-tier requires addressing)

**W1: Single task backbone (Fibonacci) for L1–L3 is a severe generalization threat**
- The entire L1 experiment (n=120) uses only Fibonacci with varied aliases. KLR differences between models could be entirely explained by Fibonacci-specific Fibonacci priors, not general prior dominance.
- L3 likewise: semantic inversion tested only on `fib`. The L4 multi-task extension is a step in the right direction but covers only 3 tasks with small n.
- **How to address**: Add at minimum 2 more tasks for L1 baseline (e.g., `is_prime`, `factorial`). Report whether KLR patterns are consistent across tasks. If not, the claimed "prior dominance" mechanism is task-confounded.

**W2: gpt-5.4-mini (KLR=0.67) underperforms gpt-4o (KLR=0.37) — the "scale doesn't predict compliance" claim needs mechanistic explanation**
- This is presented as a finding but no explanation is offered beyond asserting it. Is gpt-5.4-mini more code-optimized? Does it have a different instruction-following training mix? Without a mechanism, this is a confounded observation not a finding.
- The comparison is also confounded: gpt-5.4-mini baseline vs. gpt-4o baseline — different training data, RLHF regime, and even model family lineage. Calling this a "scale" effect is unjustified.
- **How to address**: Either frame this as an anomaly requiring investigation rather than a finding, or provide model-card-level evidence for why gpt-5.4-mini has stronger code priors.

**W3: o4-mini's 1/20 L4 pass is presented as evidence that "chain-of-thought provides narrow advantage" — this is statistically unsupported**
- 1/20 is not significantly different from 0/20 (Fisher's exact p=1.0 vs. a zero-pass null). The pass was on variant E, which had n_eff=2 for gpt-5.4-mini (8 HTTP errors). The evidence is extremely weak.
- **How to address**: Re-run o4-mini at n=50 on variant E specifically to determine if the 1/20 result is reproducible. If it is, this becomes a genuine finding. If not, remove the claim.

**W4: L1 PSS metric is never validated as a meaningful measure**
- PSS (Partial Structural Score) uses weights (alias:0.4, parse:0.25, skeleton:0.25, format:0.1) that are explicitly called "heuristic" in the threats-to-validity section. Yet PSS values are reported in Table 1 as primary data.
- A reviewer will ask: "Why 0.4 for alias? What is the sensitivity analysis?" Without validation, PSS should either be removed or clearly labeled as exploratory/secondary.
- **How to address**: Report PSS as supplementary only, or validate the weights via human judgment on a random sample (even n=20 examples), or replace with a simpler metric (e.g., alias_compliance_rate).

**W5: Table 2 (L2–L4 summary) has n=5 for L2 and L3-gpt-4o-mini — too small to be in a primary results table**
- Five samples is not a result; it's a pilot. Reporting n=5 L2 results with "5/5" passes in a results table alongside n=50 ablation numbers is misleading.
- **How to address**: Move L2 n=5 and L3 n=5 to a pilot/appendix section. Label clearly. Or expand to n≥20.

**W6: The "operational substitution" failure mode (T3, gpt-4o) is observed in 1/10 samples — insufficient basis for naming a new failure mode**
- A single instance (`count -= 1; return -count`) is interesting but not a reproducible finding. The paper names it as one of three "distinct failure mechanisms" yet it is observed exactly once.
- **How to address**: Run gpt-4o T3 at n≥30 and report the rate of operational substitution. Only if it occurs at >10% rate (>3 instances) should it be named as a failure mode. Otherwise, relegate to an observation or footnote.

---

## MINOR ISSUES

**M1**: Table 1 caption says "Context-pack delivery consistently reduces KLR" — this is contradicted by gpt-4.1-mini where contextpack gives avg_score=-2.250 vs. legacy (from status.md). Resolve or qualify.

**M2**: The paper title "Inverting Python: Designing NTP-Prior-Resistant Programming Languages for LLM-Proof Coding Assessment" contains "LLM-Proof" — this is overclaiming. L4 is "LLM-resistant for current models on tested tasks." o4-mini already breaks through on variant E. Change to "LLM-Resistant" or "AI-Resistant."

**M3**: Section 4 mentions "AVRTG key path" — this is an internal implementation detail that should not appear in a published paper. Remove or replace with generic "authenticated API calls via environment variable."

**M4**: The paper uses IEEEtran conference format but targets ACL/EMNLP/NeurIPS (as stated in cron brief). IEEEtran is inappropriate for all three venues. If the target is ACL/EMNLP, reformat to ACL anthology style. If NeurIPS/ICML, use their LaTeX template.

**M5**: The `multicode2025` citation has arXiv:2507.00699 — this is a July 2025 paper being cited in a March 2025 submission. Temporal inconsistency. Verify this citation exists and is accessible.

**M6**: Section on "Threats to Validity" is in the Methods section. This should either be moved to Discussion or expanded significantly. Currently it's 4 lines and dismisses major threats too quickly.

**M7**: Figure 1 (taxonomy TikZ diagram) has two empty gray cells for Token/Implicit and Syntax/Implicit. These should either be labeled "Not studied" with a note on why, or the paper should acknowledge that implicit token/syntax levels are theoretically possible and provide hypotheses about their expected behavior.

**M8**: The paper reports gpt-5.4-mini variant E as "n_eff=2" due to 8 HTTP errors — this cell in Table 3 should be marked as invalid/excluded rather than reporting PPR=1.0 with a dagger footnote that many readers will miss.

**M9**: "Operational substitution" is defined in §Results before it appears in §Method. It should either be defined in §Method as a potential failure mode (with hypothesis that it would emerge) or moved as a post-hoc finding with appropriate epistemic hedging.

---

## STRENGTHS

**S1**: The L3/L4 contrast (same model, gpt-4o, succeeds at L3 but fails at L4) is a genuinely clean within-model experiment that isolates pattern blindness from prior dominance. This is the paper's strongest and most reproducible finding.

**S2**: The related work section is thorough and well-connected. The explicit-implicit asymmetry framing linking to MultiCodeIF is compelling and well-positioned.

**S3**: The taxonomy itself (two-axis design space: perturbation depth × rule delivery) is a useful conceptual contribution that organizes prior observations coherently. The Figure 1 TikZ diagram communicates it clearly.

**S4**: Reproducibility artifacts (JSON results, scripts, prompt banks) are committed to GitHub. This is above average for the field.

**S5**: The multi-task extension (T1/T2/T3) identifying task-dependent resistance is a meaningful contribution beyond single-task evaluation, and the T2 result (gpt-4o 10/10, gpt-4.1-mini 20/20) provides useful contrast showing L4 is not universally resistant.

**S6**: The finding that o4-mini (reasoning model) fails L4 despite chain-of-thought is non-obvious and interesting — it challenges a common assumption that extended reasoning resolves few-shot failures. With more data (see W3), this could be a strong contribution.

---

## RECOMMENDED NEXT EXPERIMENTS

**E1: Human pilot study (n≥15, within-subjects, T1/T2/T3)** → proves the educational core claim
- The entire paper's motivation is "LLM-resistant programming education." Without human data showing students can solve L4 tasks where LLMs cannot, the educational claim is entirely theoretical. This is the #1 priority. Even n=10 with informal results would be better than nothing.
- What it proves: human–LLM performance gap exists (H1), L4 does not also confuse humans (H2).

**E2: Equalized n=50 for all models in L4 ablation (gpt-4.1, gpt-4.1-nano, o4-mini)**
- Currently these three are at n=20. Bringing to n=50 enables direct statistical comparison with gpt-4o/gpt-4o-mini/gpt-4.1-mini.
- Also: re-run o4-mini variant E at n=50 to validate the 1/20 pass (see W3).

**E3: L1 multi-task baseline (is_prime, factorial, at least 2 tasks, n≥30 per task per model)**
- Tests whether KLR differences between models are Fibonacci-specific or general.
- What it proves: prior dominance is (or is not) task-invariant.

**E4: Open-source model replication (Llama-3 or Qwen-2.5-Coder)**
- All current results are GPT-family only. Top-tier reviewers will immediately flag "only closed models."
- What it proves: pattern blindness is a general LLM property, not a GPT-specific artifact.

**E5: Execution-based judge for operational substitution detection**
- Current judge is structural (checks if condition is inverted). Operational substitution achieves correct output without structural inversion.
- What it proves: the rate of operational substitution across models and tasks. If >10% on T3, it's a genuine failure mode worth naming.

**E6: L4 difficulty scaling — vary number of examples (1 / 2 / 3 / 5 / 10)**
- Currently fixed at 2–3 examples. Ablation over example count would reveal the tipping point at which models start extracting the inversion rule.
- What it proves: pattern blindness has a sample complexity curve; L4 resistance can be made more or less robust by controlling example count.

---

## TARGET VENUE

- **Best fit**: ACL 2026 Findings or EMNLP 2026 (NLP+Education or LLM Analysis track). Not suitable for NeurIPS/ICML without a stronger theoretical contribution or more rigorous experimental design. Could work for EDM (Educational Data Mining) 2026 as a full paper.
- **Stretch target**: ACL main — requires human study (E1), statistical tests (C3), and equalized n (C1).
- **Submission readiness**: **42%** — blocking issues:
  1. C2 (data integrity: KLR=1.00 discrepancy must be resolved immediately)
  2. C3 (zero statistical tests — unacceptable at any top-tier venue)
  3. C1 (unequal n — confounds comparisons)
  4. No human baseline (educational claim unsupported)
  5. Template mismatch (IEEEtran vs. ACL/NeurIPS)

# --- END REPORT ---
