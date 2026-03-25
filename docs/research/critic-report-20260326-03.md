# --- CRITIC REPORT ---
Date: 2026-03-26 04:22 KST
Overall: **Weak Accept → Accept (85%)** — E35 redesigned I/O transparency experiment fills the paper's biggest remaining theoretical gap. The section formerly known as "E33 null result" now presents a compelling E33+E35 comparison, with a clean 100%-vs-0% contrast that directly tests I/O opacity as an independent resistance variable. Model count is correct (eleven/9 OpenAI). E32 scale-up to n=30 tightens gpt-4o CI. All prior issues resolved.

---

## STATUS SINCE 02:49 REPORT

| Issue | Current Status |
|-------|----------------|
| W5: E33 null result verbosity | ✅ RESOLVED — E33 section now presents E33+E35 comparison; E35 (0/30 opaque) is a real positive finding |
| W6: CoT ablation underpowered | ✅ Mitigated — operational definition explicit; Wilson CIs reported; n=20 adequate for null |
| M_new1/M_new2: Model count inconsistency | ✅ FIXED (prior tick) — "eleven models (9 OpenAI, 2 open-weight)" consistently throughout |
| E2: E32 gpt-4o scale-up to n=30 | ✅ DONE (prior tick) — 16/30, 53%, CI [36%,70%], Fisher p=0.008 vs mini |
| E1: Redesigned I/O transparency (E35) | ✅ DONE (this tick) — 0/30 opaque, 100%/100%/50% transparent |

---

## NEW KEY FINDING: E35 I/O Transparency

**What was done:** E35 replaced the confounded E33 IO-B prompt (which disclosed XOR/shift algorithm steps) with pure I/O pairs only. Models received 8 input/output examples and were asked to generalize to held-out inputs.

**Results:**
- IO-A (strong Fibonacci prior, transparent semantics): gpt-4o 100%, gpt-4.1-mini 100%, gpt-4o-mini 50%
- IO-B (weak prior, opaque I/O only): ALL models 0/10 = 0% (0/30 pooled)

**Interpretation:**
1. Opaque I/O is sufficient to create universal resistance, even without a deep prior — models cannot reverse-engineer the bijective function from 8 examples
2. The gpt-4o-mini IO-A failure (50%) reveals bidirectional prior effects: the Fibonacci prior *interferes* with reversed ordering even when I/O is transparent
3. This suggests a complementary design pathway: I/O-opaque specifications as an alternative to NTP-prior exploitation (L4)

**Paper integration:** E33 section upgraded to present E33+E35 comparison with Table~\ref{tab:e35_io}; abstract updated; footnote notes E35 excluded from 1150 L4 total (same policy as E33).

---

## REMAINING OPEN ISSUES:

### MINOR (low urgency):

**W6 (partial): CoT scale-up to n=50** [UNCHANGED]
The CoT ablation (n=20) supports the null result adequately. The 4/20 gpt-4.1-nano positive result (PPR 1.00→0.20) has a Wilson CI of approximately [8%,41%] that is wide but interpretable. No blocking issue.

**E35 evaluator strictness** [NEW, but acceptable]
The opaque_counter evaluator tests probe inputs (n=6,8,10) that were NOT in the training examples. Models failed because they used lookup tables or pattern-fitting that doesn't generalize. This is actually the correct behavior for the experiment — we want to test whether models can infer the underlying function, not memorize it. The 0% result is genuine and meaningful.

**gpt-4o-mini IO-A interpretation** [NEW, in paper]
The 5/10 IO-A result for gpt-4o-mini shows prior interference even in a "transparent" task. The paper correctly notes this as a bidirectional prior effect. This is now in §5.x and adds nuance. ✅ Already addressed in paper text.

---

## STRENGTHS (updated):

**S1** (retained): E31 PES logprobs — methodologically clean
**S2** (retained): E32 cross-task transfer — dramatic finding, now with tighter CI (n=30)
**S3** (retained): E34 pattern mimicry > rule following
**S4** (retained): E33 honest null result → now upgraded to positive E35 finding
**S5** (retained): 1150 total run count with auditable breakdown
**S6** (retained): §4.7 CoT metric operational definition
**S7** (retained): E28/E34 reconciliation
**S8** (NEW): E35 I/O opacity as complementary resistance pathway — theoretical contribution beyond L4

---

## BLOCKING ISSUES FOR SUBMISSION:

**None at 85% readiness.**

The paper now has:
- Clean taxonomy (L1–L4) with empirical grounding across 1150+ runs
- Three failure mechanisms with mechanistic evidence
- Four major experimental contributions (E31 PES, E32 cross-task, E34 density curve, E35 I/O opacity)
- No stale/inconsistent numbers
- Model count verified (eleven = 7 core + 2 frontier + 2 open-weight)

---

## PATH TO 90%:

1. **CoT scale-up (n=50)**: Would tighten the positive CoT findings; ~$2 API, low priority
2. **Discussion: E35 + L4 unified framework**: Add a paragraph in §6 noting that L4 and I/O-opaque designs exploit *different* failure modes (prior activation vs. generalization failure) — this unifies the paper's theoretical contribution
3. **Abstract tightening**: Abstract is now slightly long (~350 words estimated); consider compressing E33/E35 to 1 sentence

---

## RECOMMENDED IMMEDIATE NEXT STEP:

**Add §6 unification paragraph** (30 minutes, zero API cost):
Connect L4 (NTP-prior exploitation via implicit delivery) and E35 (I/O-opacity resistance) as two distinct but complementary design strategies for NTP-resistant assessments. This is a 3-4 sentence addition to §6 that elevates the paper's theoretical contribution from "taxonomy + empirical study" to "design framework with two validated strategies."

---

## TARGET VENUE (unchanged):
- **Best fit**: IEEE ICSE'26 SEET track, MSR'26, or ICER'26
- **Submission readiness**: **85%** (up from 81%)
- **Blocking 85% → 90%**: §6 unification paragraph + abstract compression

# --- END REPORT ---
