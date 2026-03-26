# --- CRITIC REPORT ---
Date: 2026-03-27 02:30 KST
Overall: **Weak Accept (92%)** — Major rigor upgrade since last cycle (9 commits: L1 factorial n=300, E34 per-cell CIs, E32 Fisher p, L2/L3 caveats). One easy bug fixed this run: undefined `\ref{sec:judge_validation}` (missing label in §4). PDF now 0 undefined refs, 15 pages.

---

## STATUS SINCE REPORT-16 (18:45 KST)

| Item | Status |
|------|--------|
| New commits since report-16 | ✅ 9 commits (9a60e67→9e42476) |
| New JSON results to integrate | ❌ None |
| Blocking issues | 🔧 1 (fixed this run: undefined ref `sec:judge_validation`) |
| PDF compiles clean | ✅ 15 pages, 0 errors, 0 undefined refs (after fix) |

---

## BUG FIXED THIS RUN

### ✅ F1: Undefined `\ref{sec:judge_validation}` — FIXED
**Location:** §5 L3 section, line 162  
**Issue:** `\ref{sec:judge_validation}` referenced throughout paper but `\label{sec:judge_validation}` was absent from `04_experiments.tex`. Caused LaTeX undefined-reference warning every compile.  
**Fix applied:** Added `\label{sec:judge_validation}` to `\subsection{Judge Validation}` in `04_experiments.tex`.  
**PDF:** Recompiled; 0 undefined refs confirmed.

---

## CRITICAL ISSUES

**None.** Compiles 0 errors, 15 pages, all references resolve.

---

## REMAINING WEAKNESSES

### W1: Judge manual validation log missing from repository (MEDIUM)
**Location:** §4 Judge Validation + paper claim "Full validation data is in the repository"  
**Issue:** Paper states "Full validation data is in the repository" but `docs/research/results/judge-manual-validation-50runs.json` does not exist. The 96% (48/50) claim is internally consistent and plausible, but reviewers who check the repo will find the claim unsubstantiated. The rigor audit already flags this as "HUMAN NEEDED."  
**Fix:** Either (a) locate and commit the validation log, or (b) change "Full validation data is in the repository" → "Validation details available on request." Option (b) is a 2-minute edit.  
**Estimated effort:** 2 min (text) or ~20 min (log file recovery/commit)  
**Impact:** Reproducibility credibility. Reviewer might flag paper's own claim as false.

### W2: E34 MAT interpretation is logically problematic (MEDIUM)
**Location:** Table caption `tab:e34_density`, MAT column  
**Issue:** MAT is defined as "lowest level where pass rate > 50%" but Table IV shows:
- `gpt-4.1-mini` MAT = "0%" (8/10 = 80% at 0%, but 0% is a code-example condition, qualitatively distinct from verbal annotation)
- `o4-mini` MAT = "0%" (7/10 = 70% at 0%)
- `gpt-4o` MAT = "None" (max 50% at 100%, not > 50%)  

The 0% level is explicitly flagged as "qualitatively distinct from verbal annotation (25–100%)" — yet the MAT column reports it as if it answers the annotation density question. A reviewer will ask: "What is the MAT *within the verbal annotation range* (25–100%)?" The honest answer is: None for all models (no level achieves >50% in that range). The current MAT column is misleading because it merges two qualitatively different conditions.  
**Fix:** Change MAT column values for gpt-4.1-mini and o4-mini from "0%†" to "None (verbal)" or add a footnote "†No level in verbal range (25–100%) exceeds 50%; mimicry baseline excluded." (3-min edit)  
**Estimated effort:** 3 min  
**Impact:** Prevents reviewer objection about misleading claim.

### W3: L1 factorial uses single model (gpt-4o) — generalizability claim is understated (LOW)
**Location:** §5.1 factorial subsection  
**Issue:** The factorial conclusion "L1 resistance is alias-strategy-dependent, not universal" is based on gpt-4o only. The paper acknowledges this implicitly (gpt-4o, ctx-pack) but does not caveat that other models may show different Type-A/B/C orderings (e.g., gpt-4.1-mini shows lower baseline KLR, which might compress the type effect). A reviewer may ask whether the Type C KLR=0.00 result holds cross-model.  
**Fix (optional):** Add sentence: "The alias-type effect is characterized for \texttt{gpt-4o} only; cross-model replication of the Type-C ceiling is recommended before drawing model-independent conclusions."  
**Estimated effort:** 2 min  
**Impact:** Prevents scope overclaiming on the factorial finding.

### W4: Total evaluation count (1,140+) may be understated or inconsistent (LOW)
**Location:** §1 Introduction, contribution 4  
**Issue:** "1,140+ evaluations" is a claim that should be cross-checkable from reported n values. Quick tally: L1 pilot (120×models) + L1 ctx-pack (20×4) + L1 factorial (300×3=900) + L2 (20×3+5) + L3 (~60) + L4 ablation (50×7=350) + L4 frontier E24 (10×2) + multi-task (345) + CoT (160) + hard-task (120) + E31 (1-token logprob, negligible) + E32 (30+10+10=50) + E33/E35 (10×3×2=60) + E34 (150) + E25-E27 (~35) = well over 2,000+ if pilot L1 is included. The "1,140+" claim appears to count only non-pilot evaluations, but the boundary is not stated.  
**Fix (optional):** Change "1,140+" to a more defensible count or add "(excluding L1 pilot runs)" clarifier. Alternatively, change to "2,000+" if including factorial and pilot.  
**Estimated effort:** 5 min  
**Impact:** Minor — reviewers rarely count. But claim should be internally consistent.

---

## STRENGTHS (cumulative, unchanged from prior report)

- **Statistical rigor:** Wilson CIs throughout, Fisher's exact (E32 p=0.0023, L3 gpt-4o-mini p<0.0001), n_eff accounting
- **L1 factorial design:** n=300/type, seed-controlled, selection-bias-corrected — genuinely rigorous
- **E34 per-cell CIs:** All 15 cells have Wilson 95% CIs; exploratory caveat explicit
- **Three-failure-mode taxonomy:** crisp, evidenced, actionable
- **Judge validation:** 96% (48/50) + label now resolves properly
- **GitHub URL:** abstract — reproducibility-forward
- **L2/L3 caveats:** prompt-bank variance, judge unvalidated notes added
- **CoT–reasoning dissociation:** publishable standalone finding
- **E35 I/O opacity:** 0/30 clean result, good epistemic hedging
- **E34 mimicry > rule-following finding:** counter-intuitive, well-hedged
- **Educational scope caveat, temperature disclosure, confusion language footnote**
- **Related work:** 14 subsections covering spec gaming, adversarial code, prompt injection analogies

---

## QUICK WINS REMAINING

| Item | Effort | Value |
|------|--------|-------|
| W1: Fix repo claim (text) | 2 min | +1% reproducibility |
| W2: Fix MAT column interpretation | 3 min | +2% rigor/clarity |
| W3: Add factorial cross-model caveat | 2 min | +1% scope accuracy |
| W4: Clarify 1140+ count boundary | 5 min | +0.5% consistency |

**Total: ~12 min for +4.5% submission readiness**

---

## TARGET VENUE

- **Best fit:** IEEE ICSE (SEET track), MSR Education track, or ICER
- **Submission readiness: 92%** (up from 91% after undefined ref fix)

### Path to 94%:
W2 (MAT fix, 3 min) + W1 (repo claim text, 2 min) + W3 (factorial caveat, 2 min) = ~7 min. Brings rigor/consistency above typical bar for workshop-track acceptance. W4 is cosmetic.

# --- END REPORT ---
