# --- CRITIC REPORT ---
Date: 2026-03-26 14:37 KST
Overall: **Weak Accept (91%)** — Two easy fixes applied (PPR=0.00 accuracy bug, multi-task temperature disclosure). One structural weakness flagged (PES two-model limitation) and one future-work gap surfaced (confusion language formal spec). No new blocking issues.

---

## STATUS SINCE REPORT-13 (12:49 KST)

| Item | Status |
|------|--------|
| New commits since report-13 | ✅ 3 (E28→E34 collapse, PDF rebuild) |
| New JSON results to integrate | ❌ None |
| Blocking issues | ❌ None |
| PDF compiles clean | ✅ 21 pages, 0 errors |

---

## FIXES APPLIED THIS TICK

### Fix-A: PPR=0.00 accuracy bug (§5 ablation text)
**Before:** "certain variants achieving full inversion while others revert completely"
**Problem:** gpt-4.1-mini variants B/D have PPR=0.00 but pass rate = 0/10 — PPR=0.00 means zero canonical-prior outputs (Type-II partial-attempt failures), NOT successful inversions. "Full inversion" is factually incorrect here.
**Fix:** Replaced with: "certain variants producing zero canonical-prior outputs (PPR=0.00 on Variants B and D; these are Type-II partial-attempt failures, not successful inversions) while others revert completely (PPR=1.00)"

### Fix-B: Multi-task temperature disclosure (§4)
**Before:** Temperature not stated for multi-task experiment (345 runs).
**Fix:** Added "Temperature=0 for all models except o4-mini (temperature=1, API requirement)" to multi-task experiment paragraph.

---

## CRITICAL ISSUES

**None.** All prior blockers resolved. No new critical issues found.

---

## MAJOR WEAKNESSES

### W1: PES (E31) Limited to Two Models — Claim Outpaces Evidence (HIGH priority)
**Location:** §5 §\ref{sec:e31_pes}, Table 4
**Issue:** The PES analysis uses only gpt-4o and gpt-4.1-mini. Yet §5 and §6 use PES data to make cross-model conclusions: "both fib and merge_sort have PES≥0.9996, yet only fib resists L4 — ruling out a simple prior-magnitude explanation." The claim is valid for these two models, but the headline result (PES-vs-resistance dissociation) has not been measured for gpt-4.1, gpt-4.1-nano, gpt-5.4-mini, or o4-mini. A reviewer will ask: "Could the resistance difference be PES-driven for models you didn't measure?"
**Fix:** Add qualifying sentence in §5: "Note: PES is measured for gpt-4o and gpt-4.1-mini only; gpt-4o-mini is excluded (markdown token emission). PES values for remaining models (gpt-4.1, gpt-4.1-nano, gpt-5.4-mini, o4-mini) are unmeasured; the PES-vs-resistance dissociation should be interpreted as a model-pair finding, not a universal result."
**Estimated effort:** ~15 min

### W2: Temperature Inconsistency Across Experiments Not Consolidated (MEDIUM priority)
**Issue:** The paper uses three temperature regimes across experiments:
- L4 ablation + multi-task + CoT + L3/L2: temp=0 (deterministic)
- E32 (Cross-task transfer) + E33/E34/E35: temp=0.7
- o4-mini (all experiments): temp=1 (API constraint)

The inconsistency is noted for o4-mini in §6 (Limits), and temp is disclosed per-experiment in the appendix. However, §5's multi-task section previously lacked temperature disclosure (fixed in Fix-B above). The remaining gap: readers doing quick reads of §5 main text will not immediately see why E32/E34 results (temp=0.7) differ in variance profile from the main ablation (temp=0). The §6 Limits section should consolidate this in one place.
**Fix:** Add one sentence in §6 Limits consolidating the three temperature regimes and noting which conclusions are most robust (temp=0 deterministic).
**Estimated effort:** ~10 min

### W3: "Confusion Language" Formal Spec Absent (MEDIUM priority)
**Issue:** The paper proposes "confusion language" as a novel concept (introduced terminology in §3), but never provides a minimal formal syntax specification or grammar. Reviewers familiar with DSL literature (ConCodeEval, L2CEval cited in related work) will note that no grammar/BNF/example syntax definition is given. For IEEE MSR/ICSE this is less critical than for a PL venue, but it weakens the "language design" framing.
**Fix (pragmatic):** In §3, add a footnote or ≤2-sentence inline note clarifying that a "confusion language" does not require a new grammar — it reuses Python surface syntax with a redefined semantic mapping, and the L2 extension (`:define ... ->` syntax) is the only syntactic deviation tested. This pre-empts the reviewer complaint without requiring a full grammar spec.
**Estimated effort:** ~15 min

---

## REMAINING WEAKNESSES (from prior reports, not yet addressed)

None. All prior weaknesses (W1–W5 from reports 12-13) have been resolved.

---

## STRENGTHS (unchanged)

- Statistical rigor: Wilson CIs, Fisher's exact, n_eff accounting throughout
- Three-failure-mode taxonomy: crisp, evidenced, actionable for assessment design
- E32 control condition (0/10 non-inverted examples) directly rules out cross-task priming
- PES (E31) adds mechanistic dimension; dissociation from hard-task resistance is a genuine finding
- E34 annotation density result is novel and counterintuitive (code-example mimicry > verbal rule)
- CoT–reasoning dissociation (models articulate rule but still generate canonical Python) is citable
- Related work is comprehensive: instruction-following, knowledge-conflict, adversarial code, education all covered
- E28→E34 convergence (both experiments agree at 50% density for o4-mini) strengthens replication claim
- Cross-venue framing is clean: theoretical taxonomy (L1-L4) + practical recipe for educators

---

## QUICK WINS REMAINING (path to 92%+)

| Item | Effort | Value |
|------|--------|-------|
| W1: PES two-model qualifier sentence in §5 | 15 min | +0.5% |
| W2: §6 Limits temperature consolidation sentence | 10 min | +0.5% |
| W3: §3 confusion language footnote | 15 min | +0.5% |

---

## TARGET VENUE

- **Best fit:** IEEE ICSE (SEET track), MSR Education track, or ICER
- **Submission readiness: 91%**

### Path to 93%+:
Apply W1 + W2 + W3 above (~40 min total)

# --- END REPORT ---
