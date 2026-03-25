# --- CRITIC REPORT ---
Date: 2026-03-26 02:49 KST
Overall: **Weak Accept (81%)** — Paper is now in good shape. The E31–E34 integration is solid and well-reasoned. One newly identified internal inconsistency (419/69 stale failure count) was discovered and FIXED this tick. Three prior easy fixes (W2 E32 CIs, W3 PES–OpSub, W4 E28/E34 reconciliation) are confirmed applied from the last round. Remaining gap to 85%+ is closing work on underpowered CoT ablation (W6) and the E33 null result verbosity (W5).

---

## STATUS SINCE 21:51 REPORT

| Issue from 21:51 | Current Status |
|----------------|----------------|
| C1: Abstract overclaim "prior entrenchment depth governs" | ✅ FIXED — abstract now says "jointly govern"; §6 also updated |
| W1: E34 "0%" condition framing | ✅ FIXED — labeled `$^{\dag}$Code-example (mimicry) baseline` in table and caption |
| W2: E32 gpt-4o Wilson CI missing | ✅ FIXED — Wilson 95% CI [43%,82%] in table |
| W2/M1: Fisher's p for E32 | ✅ FIXED (this tick) — added `$p{=}0.11$, n.s.` to gpt-4o row in E32 table |
| W3: E31 PES–OpSub connection unmade | ✅ FIXED — secondary observation paragraph in §5.9 |
| W4: E28 vs E34 o4-mini reconciliation | ✅ FIXED — explicit parenthetical about 50% agreement |
| W5: E33 null result verbosity | ⚠️ NOT FIXED — still a full §5.11 subsection |
| W6: CoT mentions_inversion underpowered | ✅ FIXED — operational definition now in §4.7 (case-insensitive regex over 4 substrings) |
| **NEW C2**: 419/69 stale failure count | ✅ FIXED (this tick) — corrected to 427/77 with explanation |
| M2: E33 run exclusion footnote | ✅ FIXED — abstract footnote explicitly excludes E33 |
| M3: Table E28 n_eff footnote | ✅ Already present from prior round |
| M4: mentions_inversion operational definition | ✅ FIXED — §4.7 has regex definition |
| M5: Fig 1 caption open-weight note | ✅ Already present |

---

## CRITICAL ISSUES (must fix before submission):

**~~C1: Abstract overclaim~~ RESOLVED**

**~~C2: 419/69 stale failure count — NEWLY DISCOVERED + FIXED this tick~~**
The "419 failed L4 runs (ablation + multitask T1): 350 + 69" was stale, predating the gpt-4.1-mini T1 scale-up (n=10→20, +10 fails) and the o4-mini token budget correction (15→7 fails, net −2). Correct total from current table data: **427 = 350 + 77**. Percentages updated to ~81.5%/12.4%/4.2%. Committed in this tick.

**No remaining C-level issues** (human study and format are out of scope per instructions).

---

## MAJOR WEAKNESSES (still open):

**W5: E33 null result consumes full §5.11 — structural choice, not a data error** [UNCHANGED]
E33 still has a full subsection (~0.4 page) for a confounded experiment. At a top venue, reviewers would note this as unusual; at IEEE ICSE/MSR it is tolerated but suboptimal. If space pressure emerges near submission, compress to 3-4 sentences in §6.4 (Limits).
→ Low urgency unless page limit is hit.

**W6: CoT ablation (n=20) remains statistically thin** [PARTIALLY MITIGATED]
The `mentions_inversion` operational definition is now explicit (§4.7 regex). However, n=20 per condition gives Wilson CIs [0%,16%] for the 0/20 result — acceptable for a null result but thin for the positive "PPR reduction" claims (e.g., gpt-4.1-nano CoT reduces PPR from 1.00 to 0.20). The 0.20 PPR at n=20 (4/20 fail-prior) has a confidence interval rather than a point estimate. No change from prior report.
→ Addressable with n=50 CoT replication, but low priority if venue is IEEE.

---

## NEW MINOR ISSUE:

**M_new1: "thirteen models" claim is accurate but could confuse** [NEW — EASY FIX possible]
Abstract and §1 say "thirteen models (seven OpenAI core... frontier models gpt-5.4 and o3... plus two open-weight)." Count: 7 + 2 + 2 = 11, not 13. Actually: gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-5.4-mini, o4-mini (7 core) + gpt-5.4, o3 (2 frontier) + Llama-3.3-70B, Qwen3-32B (2 open-weight) = **11 distinct models**. Also: gpt-5.4 and gpt-5.4-mini are *different* models — the abstract says "eleven OpenAI" in one place, then "thirteen models (11 OpenAI, 2 open-weight)" elsewhere. Counting gpt-5.4 and gpt-5.4-mini separately: 7 core (including gpt-5.4-mini) + gpt-5.4 + o3 + 2 open-weight = 12. Still not 13. Check where the 13th comes from.
→ **Fix**: Audit the model count carefully in §1 and abstract footnote; ensure consistency.

**M_new2: "11 OpenAI" in failure taxonomy footnote vs. "nine OpenAI" in coverage** [NEW]
The abstract footnote says "spanning 13 models (11 OpenAI, 2 open-weight)." OpenAI models used in L4 evaluations: gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, gpt-5.4-mini, o4-mini (7 core in ablation) + gpt-5.4, o3 (frontier, E24+hard-task) = 9 OpenAI. Where does the 11th come from? This discrepancy should be resolved.

---

## PREVIOUSLY NOTED STRENGTHS (all confirmed retained):

**S1**: E31 (PES via logprobs) — methodologically clean; rules out prior-magnitude as sole predictor.
**S2**: E32 (cross-task transfer) — dramatic finding (0/50 → 10/10); immediate practical implication.
**S3**: E34 (pattern mimicry > rule following) — paper's most novel theoretical contribution among new experiments.
**S4**: E33 honest null result reporting — builds scientific credibility.
**S5**: 1140 total run count with auditable footnote breakdown — strong empirical foundation.
**S6**: §4.7 CoT metric now has explicit operational definition — reviewer concern preempted.
**S7**: E28/E34 reconciliation paragraph — reviewer's natural "inconsistency" question answered proactively.

---

## EASY FIXES APPLIED THIS TICK:
1. **05_results.tex**: 419 → 427, "69 failed multitask T1 runs" → 77, with explanation
2. **05_results.tex**: `419 pooled taxonomy` → `427 pooled taxonomy`
3. **05_results.tex**: E32 gpt-4o table row: added `$p{=}0.11$, n.s.` for Fisher's test
4. **PDF recompiled**: clean 21-page output
5. **Git pushed**: commit 13180fa

---

## RECOMMENDED NEXT EXPERIMENTS:

**E1 (HIGH PRIORITY)**: Redesigned I/O transparency control (E33 replacement)
E33 failed because the opaque task prompt provided explicit algorithmic steps. Redesign: provide ONLY I/O pairs for `opaque_counter`, no algorithm description. Test n=20 gpt-4o.
→ Cost: ~$1 API, 2 hours. Impact: closes paper's biggest theoretical gap.

**E2 (MEDIUM PRIORITY)**: gpt-4o E32 scale-up to n=30+
Current n=20 gives CI [43%,82%] — still wide for "partial transfer" claim. n=30 gives [47%,79%], n=40 gives [49%,79%].
→ Cost: ~$1 API, 30 min. Impact: tightens gpt-4o transfer estimate.

**E3 (LOW PRIORITY)**: M_new1 model count audit
Not an experiment, just a careful count of all unique models used across experiments to fix the "thirteen/eleven" claim.
→ Cost: 15 minutes. Zero API cost.

---

## TARGET VENUE (unchanged):
- **Best fit**: IEEE ICSE'26 SEET track, MSR'26, or ICER'26
- **Alternative**: ACL 2026 Findings (short track, format conversion needed)
- **Submission readiness**: **81%** (up from 80% at 21:51; 427/77 fix removes one internal inconsistency)

**Blocking 81% → 85%**: Fix M_new1/M_new2 (model count) + E2 (E32 scale-up) → ~$1 cost
**Blocking 85% → 90%**: E1 (redesigned I/O transparency test) + compress E33
**Blocking 90% → 95%**: CoT scale-up (n=50) + format conversion for ACL

# --- END REPORT ---
