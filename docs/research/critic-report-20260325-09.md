# --- CRITIC REPORT ---
Date: 2026-03-25 09:08 KST
Overall: **Weak Accept** — Significant progress since 04:35 report. Core data integrity issue (C2) from prior report is resolved; statistical rigor improved (Wilson CIs, Fisher's exact added); n equalization largely complete. The paper now has a genuine, well-documented empirical contribution. Key blockers for top-tier acceptance: (1) no human study (educational claim still unvalidated), (2) OpenAI-only model coverage, (3) IEEEtran format mismatch, (4) PSS metric needs cleaner handling, (5) Table 4 is dense to the point of illegibility. With these addressed, this is a credible ACL Findings or EMNLP submission.

---

## CRITICAL ISSUES (must fix before submission)

**C1: Table 4 (L4 multi-task) is unreadable — 7 models × 3 tasks = 21 rows with heterogeneous n, excessive footnote clutter**
- The current table has four different footnote symbols, two dagger symbols, and four distinct n values (10/15/20/50) scattered across rows. A reviewer at a glance cannot extract the main message.
- The footnote for o4-mini's token budget correction (`$^\S$`) is critical context but is buried 4 lines into a 200-word footnote block. This will get missed.
- **Fix**: Split Table 4 into (a) a compact summary view (model × task: pass/n, bolding notable cells) plus (b) a companion table or appendix showing exact PPR per condition. Move footnote detail to the appendix (Section 10). The main table should communicate the key patterns in ~8 rows.

**C2: "Partially-annotated L4" in multi-task vs. "pure example-only L4" in ablation — this is two different experiments, but Table 3 and Table 4 appear in the same Results section without enough signal to a reader that these are NOT comparable**
- Table 3 (L4 ablation) uses strict example-only delivery. Table 4 (multi-task) uses a partially-annotated prompt with inline comments. A reader seeing o4-mini pass 8/15 in Table 4 and 0/50 in Table 3 without reading the §4 text carefully will conclude the tables contradict each other.
- The paper does address this in §4 and the Table 4 caption, but the caption is ~120 words. That's too long for a table caption and reviewers will skim it.
- **Fix**: Add a bold warning in Table 4 header: "‡ Partially-annotated prompt; not directly comparable to Table 3 (strict example-only)." Consider a section break between §5.3 (L4 ablation) and §5.4 (multi-task) that explicitly states the prompt protocol change. This is currently a paper clarity issue that could cause a reviewer to think there's a data integrity problem.

**C3: No human baseline — the paper's stated motivation ("programming education") is entirely unvalidated**
- The abstract says: "educational utility requires further validation via human study." The introduction frames the entire paper around "how can instructors meaningfully assess student understanding?" but provides zero human data.
- A top-tier ACL/EMNLP reviewer will write: "The paper's motivation is programming education, but there is no human study showing L4 tasks are solvable by humans. Without this, the paper's contribution is a demonstration that LLMs fail a particular puzzle — which is interesting but does not constitute an educational intervention."
- **Fix**: Run the human pilot (protocol already designed: `docs/research/human-pilot/pilot-protocol.md`). Even n=10 informal data (e.g., 10 DGIST undergrads, informal consent) would transform this paper. If IRB timeline prevents formal study, at minimum add an appendix with 2-3 qualitative examples of a human attempting L4 with the rule sheet, showing they can solve it.
- **Estimated effort**: 4-6 hours to collect informal data. This single addition upgrades submission readiness from ~58% to ~80%.

---

## MAJOR WEAKNESSES (top-tier requires addressing)

**W1: OpenAI-only model coverage is a fatal weakness at any top-tier venue in 2026**
- Seven models, all OpenAI. Not a single open-weight model (Llama, Qwen, Mistral, DeepSeek-Coder). This is the single most predictable reviewer objection.
- The paper acknowledges this in Threats to Validity ("open-weight model replication is future work") but top-tier reviewers will not accept this for a paper claiming "pattern blindness is a general LLM property."
- **How to address**: Run L4 ablation variant A on at least 2 open-weight models (Llama-3.1-70B and Qwen2.5-Coder-32B recommended — both accessible via local inference or API). Even n=20 per model would support a claim of generalization. If API budget is constrained, use Groq or Together.ai for free/cheap inference.
- **Time estimate**: 2-3 hours of script work + API calls.

**W2: The "scale does not predict compliance" claim (gpt-5.4-mini KLR=0.67 > gpt-4o KLR=0.37) is confounded and weakly supported**
- These two models have different model families, RLHF training regimes, and corpus compositions. Comparing their KLR values and concluding "scale doesn't predict compliance" is like comparing apples to oranges. The paper says "possibly due to stronger code-generation training" but this is speculative.
- At n=120 vs n=20 (gpt-5.4-mini baseline at n=120, but gpt-4.1/gpt-4.1-nano only at n=20), even the within-family comparison is on unequal footing. Table 1 caption notes this but it creates an asymmetric comparison.
- **How to address**: Frame L1 finding (1) as "model-family-specific compliance patterns" rather than "scale doesn't predict compliance." Qualify with the training corpus hypothesis as a stated, not demonstrated, mechanism.

**W3: PSS metric is in Table 1 as primary data but has no validation**
- The §3 Metrics section now correctly calls PSS "exploratory" and "heuristic" — this is better than the previous version. But PSS still appears in Table 1 as a co-equal column with KLR. A reviewer will ask: why report it at all if it's exploratory and the weights are heuristic?
- PSS adds visual noise to Table 1 and invites skepticism about metric selection bias.
- **How to address**: Move PSS column to an appendix table. In Table 1, report only KLR (the validated metric). Mention PSS in a single sentence in §3 with a pointer to the appendix. This simplifies the paper's primary results and reduces reviewer skepticism.

**W4: L2 and L3 results (Table 2) are presented with tiny n (n=5 for L2/L3, n=10 for L3-gpt-4o)**
- Table 2 reports 5/5, 0/5, 10/10, 10/10, 0/5. These are pilot-level results. 5/5 pass rate has a 95% Wilson CI of [57%, 100%] — it's consistent with a 57% true pass rate.
- The paper currently presents these with no CIs. For a top-tier venue, n=5 results in a primary table is not acceptable without explicit pilot labeling.
- **How to address**: Either (a) expand L2/L3 to n≥20 for all conditions (2-3 hours of API calls), OR (b) add Wilson CIs to Table 2, relabel the table as "pilot evaluation" in the caption, and move it to an appendix. Option (a) is stronger.

**W5: The token budget correction for o4-mini (max_completion_tokens: 400→5000) is a significant methodological change that needs more prominent treatment**
- Currently disclosed in a footnote (`$^\S$`). But this correction changes o4-mini from 0/45 (strongest finding for pattern blindness generalization) to 8/15 T1 (nuanced finding about reasoning under partial annotation). This is not a minor footnote — it's a finding revision.
- **How to address**: Promote this to a dedicated paragraph in §5.4, not a footnote. Title it something like "Corrected o4-mini result: partial annotation enables reasoning-model extraction." Clearly state: (1) original run was misconfigured, (2) corrected result, (3) implication. This transparency strengthens the paper's credibility rather than weakening it — reviewers respect methodological honesty.

**W6: Figure 1 (taxonomy) has two empty cells labeled "---" with no explanation**
- The paper says "Token/Implicit and Syntax/Implicit" cells are gray and labeled "---". The caption says "L4 (dark red) occupies the hardest cell." But a reviewer will ask: why don't these cells exist? Token-level implicit delivery (e.g., showing examples with aliased tokens without stating the alias rules) seems like a plausible L1.5 condition worth considering.
- **How to address**: Add a 2-sentence note in §3 (Method / Taxonomy subsection) explaining that these cells are theoretically possible but not studied, with a brief hypothesis about expected behavior (e.g., "Token/Implicit would likely fail more completely than L1-Explicit due to even weaker contextual cues"). This preempts a reviewer objection.

---

## MINOR ISSUES

**M1**: IEEEtran format is wrong for all target venues (ACL/EMNLP/NeurIPS/ICML). This must be fixed before submission. ACL Anthology template is ~3 hours of reformatting work. Do this now to avoid deadline-day scramble. *(Carried over from prior report — still unresolved.)*

**M2**: Table 3 footnote: "gpt-5.4-mini var-E: 8 HTTP errors; n_eff=2" — a cell with n=2 should be reported as N/A or excluded, not as PPR=1.0†. Even with the dagger, reporting PPR=1.0 on 2 samples is misleading. Change to "N/A (n_eff=2; excluded)" and exclude from PPR calculation for gpt-5.4-mini.

**M3**: Abstract says "all non-reasoning models fail T1 universally" — but gpt-4.1-nano shows PPR=0.20 on T1 (multi-task), meaning it exhibits some partial resistance/fragmentation, not pure prior dominance. This is a minor overclaim. Qualify: "all non-reasoning models fail T1 (0/10 to 0/20 pass rates)."

**M4**: §6.3 Limits says "Its detection in our structural judge is conservative (arithmetic heuristic patterns)" re: operational substitution. But the scale-up confirms 47/50 detection — this is actually high recall. Revise to say: "Our structural judge detects known patterns (\texttt{count -= 1; return -count}); novel arithmetic workarounds not matching these patterns may evade detection. An execution-based judge would provide exhaustive coverage."

**M5**: The title contains "LLM-Resistant" — better than the previous "LLM-Proof," but still strong. The paper shows resistance for current models on tested tasks; future models may solve L4. Consider: "Designing NTP-Prior-Aware Programming Languages for LLM-Resistant Coding Assessment" or add a hedge: "...toward LLM-Resistant Coding Assessment."

**M6**: §9 (reproducibility protocol) — the section title is "Reproducibility Protocol" but the content reads as an experiment log. Consider separating into (a) a short reproducibility section in the main paper with the key commands, and (b) moving the E1-E16 experiment log to appendix §10 or a separate file. The current structure conflates "how to reproduce" with "what we did when."

**M7**: `multicode2025` citation has arXiv:2507.00699 — this is a July 2025 preprint. Double-check that this preprint existed by March 2025. If not, replace with the actual MultiCodeIF paper identifier or remove the arXiv ID.

**M8**: The paper reports 350 L4 ablation runs and 355 multi-task runs in different places. Abstract only mentions 7 model families; it should also mention total scale (705 runs across L4) to establish empirical credibility at first read.

**M9**: gpt-4o-mini T1 multi-task footnote (`$^*$`) calls the failure mode "template fragmentation." This is a new, unnamed failure mode not in the Three Failure Modes section (§5.5). Either add it as a fourth mode (with caveat: observed in n=10) or explicitly label it as a variant of prior dominance in §5.5. Currently it appears in a footnote but not in the taxonomy — a reviewer will notice.

---

## STRENGTHS (updated)

**S1**: The o4-mini token budget correction story is now actually *more* interesting — reasoning models exploit partial annotation while dense models cannot. This nuance (partial annotation vs. pure example-only) is a genuine contribution. The before/after transparency is commendable.

**S2**: Statistical rigor is substantially improved: Wilson CIs on key cells, Fisher's exact p<0.0001 for gpt-4.1 T2 vs. gpt-4.1-mini, explicit n equalization at 50 per model for L4 ablation. This is no longer a weak-stats paper for the core L4 finding.

**S3**: The operational substitution scale-up (n=50, 94% rate, Wilson CI [83%,99%]) is now a solid finding. The "statistical artifact at n=10" admission is honest and credibility-building.

**S4**: The taxonomy Figure 1 is clean and communicates the 2D design space effectively. The gpt-4o L3 vs. L4 contrast figure (Panel A/B) remains the paper's clearest single illustration.

**S5**: Related work is comprehensive and well-connected. The explicit-implicit asymmetry framing (MultiCodeIF) is well-positioned.

**S6**: The within-family non-monotonic finding (gpt-4.1 T2 1/50 vs. gpt-4.1-mini 20/20, p<0.0001) is surprising and interesting — this is publishable on its own if framed properly.

**S7**: All experimental JSON data committed to GitHub with scripts — reproducibility is above average.

---

## RECOMMENDED NEXT EXPERIMENTS

**E1 [URGENT — highest leverage]: Human pilot study (n=10, informal, within-subjects T1/T2/T3)**
- Protocol already designed. Run this now.
- What it proves: H1 (human-LLM gap on L4), H2 (L4 does not confuse humans who know the rule)
- Expected result: ~80-100% human pass rate on T1 (given rule sheet), vs. 0% LLM — clean finding
- If even 5 participants succeed on T1, it transforms the paper's educational claim from speculative to evidenced

**E2 [HIGH]: Open-weight model replication (Llama-3.1-70B or Qwen2.5-Coder-32B, L4 ablation Variant A, n=20)**
- What it proves: pattern blindness is a general LLM property, not GPT-specific
- Run via Groq/Together.ai; ~2 hours + minimal cost
- One open-weight model result is enough to preempt the most predictable reviewer objection

**E3 [MEDIUM]: L2 and L3 expansion to n≥20 per condition**
- Current n=5 for L2/L3 is pilot-level. 2-3 hours of API calls.
- What it proves: L2 full adoption and L3 capacity threshold hold at statistically meaningful n
- Also: test L3 on gpt-4.1/gpt-4.1-nano — currently only gpt-4o and gpt-4.1-mini are reported for L3

**E4 [MEDIUM]: o4-mini L4 multi-task T2/T3 with corrected token budget (n≥20 each)**
- Currently only T1 was corrected. T2 and T3 for o4-mini were at n=15 with what conditions?
- What it proves: whether reasoning can also partially address T2 (is_sorted) under partial annotation
- This would resolve ambiguity in Finding (5) about reasoning-model behavior

**E5 [LOW but interesting]: L4 difficulty scaling — number of examples (1/2/3/5)**
- Vary examples in Variant A from 1 to 5 to find the tipping point
- What it proves: sample complexity curve for pattern blindness; informs pedagogical design

---

## TARGET VENUE

- **Best fit**: ACL 2026 Findings (NLP+Education or LLM Analysis track) or EMNLP 2026 short paper track
- **Stretch target**: ACL 2026 main — requires E1 (human study) + E2 (open-weight) + C1 (table readability) + M1 (template)
- **Fallback**: EDM 2026 (Educational Data Mining) — this paper would likely be accepted as-is; strong fit for the venue audience

**Submission readiness: 58%** — blocking issues:
1. No human baseline (C3) — educational claim unvalidated
2. OpenAI-only models (W1) — generalizability undemonstrated
3. IEEEtran format mismatch (M1) — wrong template for target venues
4. Table 4 legibility (C1) — dense, multi-footnote table will hurt reviewer comprehension
5. Table 3/4 comparison confusion risk (C2) — protocol change not prominent enough

**Δ from prior report (04:35)**: +16 percentage points (42% → 58%). The n equalization, statistical tests, and data integrity resolution are real improvements. The remaining gap is almost entirely human study + open-weight models + format.

# --- END REPORT ---
