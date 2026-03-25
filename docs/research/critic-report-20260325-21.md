# --- CRITIC REPORT ---
Date: 2026-03-25 21:51 KST
Overall: **Weak Accept (80%)** — E31–E34 substantially strengthen the paper's mechanistic claims. PES (E31) provides direct prior-magnitude evidence; cross-task transfer (E32) establishes prompt-level assessment implications; annotation density (E34) maps the mimicry-vs-rule-following boundary. The honest null result (E33) is appropriate transparency. Three new concerns identified this tick: (C1) abstract overclaim on "prior entrenchment depth governs resistance" conflicts with E31's own dissociation finding; (W_new1) E34's "0% density" condition is qualitatively different from 25–100% and from strict L4 ablation, making the "peak at 0%" headline finding potentially misleading; (W_new2) E32 reports no Wilson CIs or Fisher's test for the 6/10 partial-transfer result.

---

## STATUS SINCE 18:56 REPORT

| Issue from 18:56 | Current Status |
|----------------|----------------|
| C1: Human pilot | ✅ Reframed as design principle (not empirical blocker); §6.2 now explicitly argues the asymmetry follows from NTP mechanics |
| C2: IEEEtran format | ❌ Intentional; out of scope per instructions |
| C3: §4 multi-task description contradicts §5.4 | ✅ FIXED — §4.5 now explicitly states "partially-annotated L4 condition" with NOT directly comparable warning |
| W1: Open-weight pilot scale | ✅ Qwen3-32B E27 (n=20) + Llama full ablation (n_eff=25) added |
| W2: I/O transparency confound | ⚠️ PARTIALLY addressed — E31 shows equal PES for fib/merge_sort, E33 null result noted honestly; confound not fully isolated |
| W3: CoT ablation underpowered | ⚠️ Same concern; n=20 per condition, gpt-4o CoT not scaled to n=50 |
| M1/M3/M4/M5/M6: All minor fixes | ✅ All confirmed fixed in previous ticks |
| **NEW**: E31–E34 integrated | ✅ All four experiments in §5 with tables |

---

## CRITICAL ISSUES (must fix before submission):

**C1: Abstract overclaims "prior entrenchment depth governs resistance" — contradicted by E31** [NEW — EASY FIX]
The abstract states: *"prior entrenchment depth, not task difficulty, governs resistance."*
But E31 (§5.9) shows fib and merge_sort have near-identical PES (≥0.9996), yet diverge completely on L4 resistance. The paper itself concludes (correctly) that I/O transparency is the critical moderating variable—but the abstract still says "prior entrenchment depth governs resistance." This is a direct internal contradiction between the abstract claim and the paper's own E31 conclusion.
→ **Fix**: Change abstract to: *"prior entrenchment depth and I/O specification transparency jointly govern resistance; E31 shows that prior magnitude alone (PES ≥ 0.9996 for both resistant and non-resistant tasks) is insufficient to predict L4 failure."*

---

## MAJOR WEAKNESSES (top-tier requires addressing):

**W1: E34 "0% density" condition is qualitatively different — headline finding potentially misleading** [NEW — PARTIAL FIX POSSIBLE]
E34 reports "peak at 0% annotation density" as its headline. But the 0% condition includes an inverted *code* example (`if n >= 0:`), which is qualitatively different from both the strict L4 ablation (I/O examples, no explicit operators) and from the 25–100% conditions (verbal annotation). The paper acknowledges this in the caption ("includes an inverted code example; not comparable to strict L4 ablation"), but the "non-monotonic density curve with peak at 0%" framing suggests a continuous density gradient where 0% means "no annotation." A reviewer will flag: *"The 0% condition is a different intervention type — it should be either relabeled (e.g., 'code-example baseline') or excluded from the density curve, with the density gradient starting at 25%."*
The actual finding (code-example mimicry > verbal annotation) is interesting and well-argued; the framing is the issue.
→ **Address**: Relabel 0% as "code-example (mimicry)" in Table 6 / Figure description. Restructure E34 key finding as: "pattern mimicry via code examples outperforms verbal annotation across all density levels, and within the verbal annotation range (25–100%), pass rates are non-monotonic." This is more precise than the current framing.

**W2: E32 cross-task transfer (6/10 gpt-4o) reports no Wilson CIs — easy to fix** [NEW — EASY FIX]
Table E32 and the §5.10 text report gpt-4o 6/10 (60%) without a confidence interval. Wilson 95% CI for 6/10 is [29%, 88%] — very wide. A reviewer will note that the partial transfer claim for gpt-4o is statistically weak. The gpt-4.1-mini 10/10 result is strong (Wilson CI: [72%, 100%]), but the gpt-4o 6/10 result needs its CI reported.
→ **Fix**: Add Wilson 95% CIs to all three E32 results in table and text. Also note that gpt-4o 6/10 vs gpt-4.1-mini 10/10 is statistically marginal (Fisher's p ≈ 0.11).

**W3: E31 PES — gpt-4o T3 count_vowels PES=0.1606 ↔ operational substitution connection unmade** [NEW — EASY FIX]
Table E31 shows gpt-4o has PES=0.1606 for count_vowels (T3), while gpt-4.1-mini has PES=1.0000. The paper's main PES claim is "PES alone doesn't predict resistance." But there's a more interesting secondary finding hiding here: gpt-4o's *low* T3 PES may explain its operational substitution behavior — if the model has weak prior pull toward `return s.count(...)`, it is more likely to generate an arithmetic workaround rather than defaulting to the standard template. This PES–OpSub connection is unexploited.
→ **Fix**: Add 1–2 sentences in §5.9: *"A secondary observation: gpt-4o's low T3 PES (0.1606) contrasts with its operational substitution behavior on T3 at $n=50$ (94% OpSub). This may reflect that a weaker prior (lower PES) does not simply yield compliance; instead, the model explores alternative generation paths that still avoid the L4 inversion rule. The PES–OpSub relationship warrants future study."*

**W4: E28 vs. E34 o4-mini "inconsistency" needs explicit reconciliation** [PARTIALLY ADDRESSED — EASY FIX]
E28: o4-mini peaks at 50% density (6/10, using 8-example prompt with no 0% condition).
E34: o4-mini "peaks at 0%" (7/10 at code-example baseline), with 50%=6/10 and 75%=6/10.
The paper says they are "directionally consistent...though absolute levels differ due to prompt design differences." But a reader comparing Table E28 (peak at 50%) and Table E34 (peak at 0%) will see what looks like a contradiction. The reconciliation is actually simple: E28 didn't test a 0% condition; at 50%, both experiments agree (6/10). The "peak at 0%" in E34 is an artifact of including the code-example baseline.
→ **Fix**: Add a parenthetical in the reconciliation sentence: *"Both experiments agree at 50% density (E28: 6/10; E34: 6/10); E34's apparent 'peak at 0%' is due to the qualitatively distinct code-example baseline condition absent from E28's design."*

**W5: E33 null result consumes paper space with low evidential value** [DESIGN ISSUE — CANNOT FIX WITHOUT MAJOR REWRITE]
E33 is honestly reported as a failed experiment (procedural transparency defeats the isolation attempt). It occupies a full subsection (~1/3 page). A reviewer will note that a full subsection for a confounded null result is unusual; typically this goes in a footnote or "design decisions" paragraph.
→ **Partial fix**: If space is tight, compress E33 to 3-4 sentences noting the design flaw and planned redesign. Move to §6.4 (Limits) or §6.5 (Next steps) rather than having its own §5.11 subsection. Space savings could be used for CIs in E32.

**W6: Reasoning-generation dissociation CoT ablation (W3 from prior report) remains underpowered** [UNCHANGED]
n=20 per condition for CoT ablation. The "dissociation" finding (100% mentions_inversion but 0% pass) is compelling, but at n=20, Wilson CI on mentions_inversion=100% is [83%, 100%] — reasonably tight. The concern is the dissociation claim rests on text-match ("mentions_inversion"), which could be prompt parroting rather than semantic understanding. No change since last report.
→ **Address**: At minimum, clarify operational definition of mentions_inversion (exact substring match? Regex? Semantic?) in §4.7.

---

## MINOR ISSUES:

**M1: E32 statistical gaps**
No p-value for gpt-4o (6/10) vs. gpt-4.1-mini (10/10). Fisher's exact gives p ≈ 0.08 (one-sided) — not significant at α=0.05. This should be noted: the gpt-4o vs. gpt-4.1-mini cross-task transfer difference is not statistically distinguishable at n=10.
→ **Fix**: Add Fisher's p in E32 text.

**M2: E33 run count not in total**
E33 ran 60 evaluations (3 models × 2 tasks × n=10). These are not in the 1130 total (correctly excluded since they're not L4 evaluations). A brief footnote acknowledging E33's 60 runs are excluded from the count would preempt reviewer questions.
→ **Fix**: Add to §5.11 or abstract footnote: *"E33 (I/O transparency control, 60 runs) excluded from total as a confounded control experiment rather than an L4 evaluation proper."*

**M3: Table E28 n_eff discrepancy**
Table E28 shows n=10 per level but 100% row has 1 HTTP error (1 valid run lost), yet table shows "1" in pass column with n presumably 9. Table caption says "n=10 per level, 40 total runs" but actual valid runs = 39. Update caption to reflect n_eff or add a footnote.
→ **Fix**: Add `$^\dagger$1 HTTP error; $n_\mathrm{eff}=9$` to the 100% density row in Table E28.

**M4: "mentions_inversion" metric undefined operationally in §4**
§4.7 CoT ablation says "we additionally track whether the model's reasoning text mentions the inversion pattern" — no operational definition. Is this a regex? Manual annotation? Python substring match?
→ **Fix**: Add "(determined by substring match for 'inverted', 'opposite', or 'false when true')" or equivalent in §4.7.

**M5: Figure 1 bar chart shows open-weight models but legend omits them**
The L1 KLR bar chart (Fig. 1) shows Llama-3.3-70B and Qwen3-32B (marked with $^\star$) in the table but the TikZ bar chart only shows 7 models (gpt-4o through o4-mini). The open-weight models appear in Table 1 but not Fig. 1. A reviewer may wonder why the bar chart doesn't show these models. Either add them to the chart with a distinct color, or note in caption: "Open-weight models excluded from bar chart; see Table 1."
→ **Fix**: Add to Fig. 1 caption: "Open-weight models (\texttt{Llama-3.3-70B}, \texttt{Qwen3-32B}) appear in Table~\ref{tab:l1_results} only; bar chart shows OpenAI models for visual clarity."

---

## STRENGTHS (new since last report):

**S1**: E31 (PES via logprobs) is methodologically clean — it directly measures what the paper claims to care about (prior strength) and produces a clear null result (PES doesn't predict resistance). This strengthens the I/O transparency hypothesis by ruling out the prior-magnitude alternative.

**S2**: E32 (cross-task transfer) has immediate practical implications for instructors (prompt-level isolation requirement) and is clearly motivated by the prior findings. The result is dramatic: 0/50 → 10/10 with cross-task priming.

**S3**: E34's "pattern mimicry > rule following" finding is the paper's most novel theoretical contribution among the new experiments. It inverts the naive expectation and converges with E32 (code examples more effective than verbal rules). This deserves emphasis in the abstract.

**S4**: E33's honest null result reporting is a sign of scientific maturity. A confident researcher would have quietly dropped this; reporting the design flaw while specifying the redesign needed builds credibility.

**S5**: The 1130 total run count, with a complete footnote breakdown, is a genuine strength — reviewers can audit the claims.

**Previously noted strengths (S1–S7 from 18:56 report) remain intact.**

---

## RECOMMENDED NEXT EXPERIMENTS:

**E1 (ALREADY PARTIALLY DONE as E34, HIGH PRIORITY)**: Redesigned I/O transparency confound test
E33 failed due to procedural transparency. Redesign: IO-B should provide only I/O pairs for `opaque_counter` with no algorithm description. Test at n=20 with gpt-4o. This would finally isolate whether I/O transparency or prior depth drives the fib vs. merge_sort divergence.
→ Cost: ~$1 API, 2 hours
→ Paper impact: resolves the paper's biggest theoretical gap

**E2 (HIGH PRIORITY): E32 scale-up for gpt-4o (n=20)**
gpt-4o 6/10 has Wilson CI [29%, 88%] — too wide for the "partial transfer" claim. Scaling to n=20 would tighten to [30%, 70%] range. The 10/10 gpt-4.1-mini result is already definitive.
→ Cost: ~$0.50 API, 30 min
→ Paper impact: confirms or refutes partial transfer for gpt-4o

**E3 (MEDIUM PRIORITY): CoT mentions_inversion operational validation**
Hand-code 20 examples from CoT runs to validate the substring-match approach. If precision is high (>90%), the metric is defensible. If not, semantic classification is needed.
→ Cost: 1-2 hours human annotation (no API)
→ Paper impact: resolves W6

---

## TARGET VENUE (unchanged):
- **Best fit right now**: IEEE ICSE'26 SEET track, MSR'26, or ICER'26 (educational research in computing)
- **Alternative**: ACL 2026 Findings (short track, 4 pages) — requires format conversion
- **Submission readiness**: **80%** (up from 76% at 18:56; E31–E34 integration is solid; easy fixes below would push to 82%)

**Blocking 80% → 85%**: Fix C1 (abstract overclaim) + W2 (E32 CIs) + W3 (E31 PES-OpSub connection) — all EASY edits
**Blocking 85% → 90%**: E1 redesigned I/O transparency test + compress E33 to footnote
**Blocking 90% → 95%**: Resolve W6 (CoT metric validation) + E2 (E32 scale-up) + format conversion

# --- END REPORT ---
