# --- CRITIC REPORT ---
Date: 2026-03-25 11:31 KST
Overall: **Weak Accept** — Substantial experimental work, three-failure-mode taxonomy, and the o4-mini CoT dissociation story are genuinely interesting. However, a **critical data integrity bug in Figure 2** (bar chart values contradict Table 1 for 5 of 7 models) must be fixed before any submission, and the paper continues to lack the human baseline that every senior reviewer will demand.

---

## CRITICAL ISSUES (must fix before submission)

**C1: Figure 2 (L1 KLR bar chart) shows values that directly contradict Table 1 for 5 of 7 models — this is a data integrity error**
- The bar chart plots: gpt-4o-mini=0.52, gpt-4.1=1.00, gpt-4.1-mini=1.00, gpt-4.1-nano=1.00, o4-mini=1.00
- Table 1 reports: gpt-4o-mini ctx-pack=0.26, gpt-4.1 ctx-pack=0.30, gpt-4.1-mini ctx-pack=0.21, gpt-4.1-nano ctx-pack=0.38, o4-mini ctx-pack=0.27
- The value 0.52 for gpt-4o-mini does not appear anywhere in Table 1 (baseline=0.42, ctx-pack=0.26)
- The gpt-4.1 family at KLR=1.00 is **opposite** to the paper's narrative (§5.1 says ctx-pack reduces KLR to 0.21–0.30)
- A reviewer who glances at the figure and reads the table will conclude the paper has fabricated or confused data
- **Fix (10 min)**: Update the bar chart coordinates to match ctx-pack values from Table 1. For gpt-4o and gpt-5.4-mini (baseline condition), keep as-is. Update caption to state: "ctx-pack condition shown where measured; baseline for gpt-4o and gpt-5.4-mini." Exact fix applied below.

**C2: No human baseline — educational motivation is entirely unvalidated (carried from prior reports, still blocking)**
- The paper claims L4 provides "meaningful resistance for programming education." Every top-tier reviewer will ask: "Can humans solve L4 tasks given the rule sheet? If not, this is useless as an assessment." 
- Without Exp-5 (human pilot), the paper's core claim reduces to "LLMs fail a specific puzzle" — which is publishable at a workshop, not ACL/EMNLP main.
- **Fix**: Run informal human pilot (n=10, DGIST undergrads, 1 session each). Protocol already designed at `docs/research/human-pilot/`. Even 3–5 qualitative "think-aloud" examples would transform the discussion from speculative to evidenced.
- **Status**: This has appeared in C3 (09:08), C3 (06:xx), and now C2. It is the single highest-leverage action remaining.

**C3: IEEEtran format is wrong for all stated target venues (ACL/EMNLP/NeurIPS/ICML)**
- The paper compiles with `\documentclass[conference,10pt]{IEEEtran}`. ACL uses acl_natbib; EMNLP uses the same; NeurIPS uses its own template; ICML uses its own.
- This is a cosmetic fix but it affects: (a) page count estimate, (b) column width for figure/table sizing, (c) citation format, (d) first impression when reviewers open the PDF.
- **Fix**: Convert to ACL 2026 template (`acl_natbib.sty`) now. The `main_acl.tex` stub exists in the repo — complete it. The sooner this is done, the less painful it will be.

---

## MAJOR WEAKNESSES (top-tier requires addressing)

**W1: Open-weight model coverage is insufficient for a "general LLM property" claim**
- The paper now includes Llama-3.3-70B and Qwen3-32B preliminary results (L1 + L4 Variant A, n=20). This is an improvement. But n=20, single variant, and Groq inference only.
- For top-tier acceptance, n=20 on a single variant does not support "pattern blindness generalizes beyond OpenAI." It supports "pattern blindness is observed in two additional models at pilot scale."
- **Fix**: Scale open-weight L4 ablation to at least n=50 across all 5 variants (same as the main OpenAI models). If Groq rate limits are an issue, use Together.ai or Ollama locally. 2–3 hours of work.
- The Qwen3-32B KLR=1.00 result is interesting but unexplained — does it fail to follow instructions generally, or specifically resist alias substitution? A 5-prompt L3 test would disambiguate.

**W2: gpt-4.1-mini T2 (is_sorted) 20/20 pass vs. gpt-4.1 T2 1/50 is the paper's most surprising finding but is not sufficiently explained**
- Fisher's exact p<0.0001 is reported correctly. But the mechanism is unaddressed. Why does the "larger" model (gpt-4.1) fail where the "mini" variant succeeds? 
- The paper says "fine-tuning or RLHF choices appear to play a larger role than raw scale" — but this is a post-hoc rationalization without evidence.
- **Fix**: Add a short hypothesis subsection (2–3 sentences) in §6 (Discussion) distinguishing possible mechanisms: (a) RLHF over-alignment in gpt-4.1 may cause stronger prior entrenchment; (b) different instruction-tuning data for mini variants. Explicitly label it as a hypothesis, not a finding.

**W3: The "reasoning–generation dissociation" (CoT ablation) is a strong finding but is isolated to n=20 per condition on only 2 models**
- The finding is clear and well-stated. But with 4 conditions × 2 models at n=20, this is pilot-level. A reviewer will note that the finding rests on 80 total CoT runs.
- **Fix**: Extend CoT ablation to gpt-4.1-nano and o4-mini (n=20 each), yielding 160 total runs. gpt-4.1-nano is particularly interesting because it has L3 20/20 (follows explicit rule) but L4 0/50 (PPR=1.0) — the CoT test would determine if reasoning can partially bridge this gap.
- Expected cost: ~$2–5 in API calls.

**W4: Table 3 PPR variance across variants for gpt-4.1-mini (B=0.00 vs. E=1.00) is unexplained and suspicious**
- Variant B (3ex-extra, gpt-4.1-mini PPR=0.00): the model passes all 10 runs.
- Variant D (2ex-swapped, gpt-4.1-mini PPR=0.00): the model passes all 10 runs.
- Variant E (3ex-diff-domain, gpt-4.1-mini PPR=1.00): the model fails all 10 runs.
- This 1.00 swing across variants of the same model is a 4σ effect at n=10. A reviewer will ask: what structural property of variant E causes complete failure while variants B/D cause complete success? The paper acknowledges high variance but doesn't analyze the cause.
- **Fix**: Add a per-variant analysis in §5.3 or Appendix §10 explaining what differs between variants B/D (gpt-4.1-mini succeeds) and variant E (fails). If variant E uses a different domain for examples, does that mean domain shift defeats pattern extraction? This is actually an interesting finding if analyzed.

**W5: The failure taxonomy (§5.5) relies on 419 "failed L4 runs" but includes both ablation and multi-task T1 — the population definition is unclear**
- 350 ablation runs + 69 failed T1 multi-task runs = 419. But the multi-task prompt is "partially-annotated L4," not "strict example-only L4." Mixing these two populations in a taxonomy analysis is methodologically problematic.
- The 4.3% Type-III (operational substitution) rate in the pooled taxonomy may be an artifact of diluting the multi-task T3 data (where operational substitution is 94% for gpt-4o) with the ablation data.
- **Fix**: Report the failure taxonomy separately for (a) strict example-only ablation (350 runs) and (b) partially-annotated multi-task (345 runs), and note whether the failure mode distributions differ. This is a 30-minute analysis of existing JSON data.

---

## MINOR ISSUES

**M1**: §5.1 (L1 results) says the figure shows "L1 Keyword Leakage Rate (KLR) by model" but the figure caption does not specify delivery condition. After the bar chart fix (C1), the caption must clarify which condition is plotted for each model.

**M2**: §5.2 (L2) says "all four evaluated models adopted L2 syntax fully (SIR=0.0, n=20 each)" — but the experiments section says L2 was only run for gpt-4o, gpt-4.1-mini, gpt-4.1-nano (E17). The fourth model listed would be gpt-4o-mini (pilot n=5). So n=20 is incorrect for gpt-4o-mini. Fix: either exclude gpt-4o-mini from this claim or label it as pilot (n=5).

**M3**: Abstract "seven OpenAI model families (GPT-4o through o4-mini)" — with the addition of Llama-3.3-70B and Qwen3-32B, the abstract undercounts the model coverage. Update to "seven OpenAI and two open-weight models (nine total)."

**M4**: §6.2 (Educational implications) says "o4-mini achieves 8/15 only under the partially-annotated multi-task prompt (not under the strict example-only condition)" — this is correct but needs to acknowledge the n=15 limitation. 8/15 has a Wilson 95% CI of [33%, 77%]. At best, it's a noisy partial success.

**M5**: The footnote about gpt-5.4-mini var-E (n_eff=2) was previously flagged as M2 in the 09:08 report and marked as fixed (Table 3 now shows N/A). Confirm this is correct in the PDF — the TeX code in Table 3 still shows `N/A$^\dagger$` for var E with a separate footnote. ✅ Appears resolved.

**M6**: §9 (Reproducibility Protocol) lists scripts but not Python/package versions. Add a single line: `Python 3.x, openai==x.y.z, groq==x.y.z` so someone can replicate without version-hunting.

**M7**: The paper describes the title as hedged ("toward LLM-Resistant") — good. But the abstract still says "defeats LLM next-token-prediction (NTP) priors" which is strong. The paper's own data shows only *current models* fail L4; the abstract should hedge: "defeats current-generation LLM NTP priors."

**M8**: Figure 3 (L3 vs. L4 contrast, Panel A/B) — the comment markers `\%` in the lstlisting code will render as percent signs in PDF. Double-check that the rendered figure shows the correct code comment style (`#` for Python comments, not `%`).

---

## STRENGTHS

**S1**: The reasoning–generation dissociation (CoT ablation) is the paper's most novel finding. Models explicitly describe the inverted semantics in their chain-of-thought but still generate standard Python. This is a genuinely surprising and memorable result that will travel well at a poster session.

**S2**: The gpt-4.1-mini vs. gpt-4.1 T2 non-monotonic capacity finding (20/20 vs. 1/50, p<0.0001) is the kind of surprising within-family result that makes a paper interesting. It challenges simple "larger model = better" assumptions.

**S3**: Statistical rigor is strong for core findings: Wilson CIs throughout, Fisher's exact for key cross-model comparisons, explicit scale-up to n=50 to resolve n=10 artifacts. The operational substitution confirmation (94% at n=50, CI [83%,99%]) is solid.

**S4**: The L1/L4 open-weight preliminary extends the finding beyond OpenAI. Llama-3.3-70B KLR=0.23 vs. Qwen3-32B KLR=1.00 is an interesting cross-architecture finding that hints at instruction-tuning regime effects.

**S5**: Related work coverage is excellent — explicitly connects to CodeIF, MultiCodeIF, knowledge conflict, A-Not-B errors, and adversarial perturbation. The paper situates itself well in the existing literature.

**S6**: Experimental transparency is high: token budget correction for o4-mini is disclosed with full context, preliminary n=20 artifacts are explicitly identified, and all JSONs are committed to GitHub.

**S7**: The taxonomy (Figure 1) is clean and communicative. The 2-axis design space (perturbation depth × rule delivery) provides a useful framework for future work.

---

## RECOMMENDED NEXT EXPERIMENTS

**E1 [URGENT — single highest-leverage action]: Human pilot study (n≥10)**
- Run now. Protocol already designed. 4–6 hours.
- What it proves: humans with the rule sheet can solve L4 tasks (expected ~90% pass on T1), demonstrating human–LLM gap
- Without this: every reviewer will write "no human baseline, educational claim unvalidated"
- Upgrade from 58% → ~78% submission readiness

**E2 [HIGH]: Open-weight L4 full ablation (n=50, all 5 variants)**
- Llama-3.3-70B and/or Qwen2.5-Coder via Groq/Together
- What it proves: pattern blindness is a cross-architecture, not GPT-specific, failure mode
- Upgrade from "preliminary" to "confirmed" for open-weight coverage

**E3 [HIGH]: CoT ablation extension to gpt-4.1-nano and o4-mini (n=20 each)**
- 40 additional API calls, ~$3
- What it proves: reasoning-generation dissociation is robust; whether o4-mini CoT can partially overcome L4 in strict example-only condition
- Potential upgrade to the paper's discussion of reasoning model capabilities

**E4 [MEDIUM]: Variant E analysis for gpt-4.1-mini**
- Why does variant E (diff-domain examples) completely flip gpt-4.1-mini from PPR=0.00 to PPR=1.00?
- This is an analysis task on existing data (no new API calls needed)
- What it proves: domain sensitivity of pattern extraction — potential new finding

**E5 [MEDIUM]: Failure taxonomy split (ablation vs. multi-task)**
- Re-run `categorize_failures.py` on ablation-only and multi-task-only populations separately
- What it proves: whether operational substitution rate differs by prompt annotation level
- 30-minute analysis task, no new API calls

**E6 [LOW]: L4 example count scaling (1/2/3/5 examples, variant A structure)**
- What it proves: sample complexity curve for pattern extraction; is there a tipping point?
- Pedagogical relevance: how many examples do humans need vs. LLMs?

---

## TARGET VENUE

- **Best fit**: ACL 2026 Findings (NLP+Education or Model Analysis track)
- **With E1 (human study) + E2 (open-weight full)**: Upgrades to ACL 2026 main (borderline)
- **Fallback without E1**: EMNLP 2026 short paper (4 pages) or EDM 2026

**Submission readiness: 60%** — Δ+2 from prior 09:08 report (LaTeX precision fixes, E17–E21 log, minor text improvements)

Blocking issues in priority order:
1. **Figure 2 data error** (C1) — 10 min fix, MUST DO BEFORE NEXT PDF SHARE
2. **No human baseline** (C2) — 4–6 hours, MUST DO for ACL/EMNLP
3. **IEEEtran format** (C3) — 3 hours, do before October deadline
4. **Open-weight full coverage** (W1) — 2–3 hours
5. **CoT ablation extension** (W3) — 1–2 hours
6. **Failure taxonomy split** (W5) — 30 min

# --- END REPORT ---
