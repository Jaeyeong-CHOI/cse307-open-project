# Exp-5: Human Pilot Study Protocol
# L4 Semantic Inversion — Human vs. LLM Performance Gap
# Version: 0.1 (2026-03-25)

## 1. Objective
Validate the claim that L4-style language design maintains human interpretability
while defeating LLM-based code generation. Specifically:

- **H1**: Human learners (post-instruction) can correctly follow L4 semantic rules
- **H2**: Human accuracy on L4 tasks > LLM accuracy (quantified gap ≥ 50pp)
- **H3**: L4 instructions are learnable in <5 min, so the cognitive burden is acceptable

## 2. Participants
- **n = 10–15** undergraduate CS students (DGIST CSE307 or equivalent)
- Pre-condition: has completed at least one semester of Python (knows if/return/functions)
- Exclude: graduate students, students with compiler/PL background (ceiling effect)
- Recruitment: voluntary, classroom/lab announcement; no compensation required
  (IRB exempt category: educational evaluation; confirm with course instructor)

## 3. Study Design
**Within-subjects** 3-task × 2-condition design:
- Condition A (L4): semantic inversion, examples-only delivery (identical to Exp-4)
- Condition B (control): standard Python, equivalent tasks

Task order counterbalanced (Latin square) to control for learning/fatigue effects.

### Tasks
| ID | Task         | L4 rule applied          | Notes                          |
|----|------------- |--------------------------|--------------------------------|
| T1 | fibonacci    | `if`-blocks run when FALSE | Deep prior; LLM=0% pass       |
| T2 | is_sorted    | `if`-blocks run when FALSE | Mid-tier; LLM=50% pass (model-dep.) |
| T3 | count_vowels | `if`-blocks run when FALSE | Operational substitution risk  |

## 4. Instruction (L4 Brief — given to participants)
Deliver the following on a single slide/sheet **before** tasks begin (5 min self-study):

> **NTP-Py rules (read carefully):**
> 1. `if <condition>:` block executes when `<condition>` is **FALSE**
> 2. All other Python syntax (loops, return, arithmetic) is unchanged
> 3. Example:
>    ```
>    def is_positive(x):
>        if x > 0:       # runs when x <= 0
>            return False
>        return True
>    ```
> 4. There is no explicit rule in the coding task description — you must remember the rule from this sheet.

Participants may refer to the rule sheet **during** the task (open-book).
This is intentional: we want to test whether they can apply a known rule, not memorize.

## 5. Task Delivery
- Paper-based or simple web form (Google Form / pen-and-paper)
- Each task: ~5 min budget, max 15 min total
- Prompt format: identical to LLM Ablation Variant A (2 worked examples, no explicit rule)
  **IMPORTANT**: rule sheet is separate — task sheet does NOT restate the rule

### T1 prompt (human):
```
Define fibonacci(n) in NTP-Py.
Examples (NTP-Py):
  def base(n):
      if n == 0:
          return 1
      return 0
  def negate(x):
      if x > 0:
          return -x
      return x
```
(Same worked-examples as LLM prompt; participants may re-read rule sheet)

### T2 prompt (human): (analogous, is_sorted context)
### T3 prompt (human): (analogous, count_vowels context)

## 6. Evaluation
**Judge**: manual code review by researcher. Criteria:
- `if`-block semantics correctly inverted (primary criterion)
- Function body logically consistent with L4 rules
- Return values correct under L4 interpretation

**Scoring per task** (0/1 binary, same as LLM judge):
- `pass`: if-inversion correctly applied, output semantics correct under L4
- `fail`: falls back to standard Python, or inverted but logically inconsistent

**Metrics**:
- `HPR`: Human Pass Rate per task (0–1)
- `HPR_avg`: mean over T1–T3
- `gap`: HPR - LLM_PPR_complement (= HPR - (1 - PPR))
  (a positive gap confirms humans outperform LLMs)
- `time_per_task`: median completion time

**Expected benchmark** (from LLM data):
| Task | LLM best pass rate | Expected human HPR | Expected gap |
|------|---------------------|---------------------|--------------|
| T1   | 0%  (all fail)      | ≥ 60%               | ≥ 60pp       |
| T2   | 50% (model-dep.)    | ≥ 70%               | ~20pp        |
| T3   | 10% (gpt-4o best)   | ≥ 50%               | ≥ 40pp       |

## 7. Confounds to Control
- **Order effect**: counterbalance task order
- **Rule-sheet use**: explicitly allow (open-book); note if participant did not consult
- **Expertise variance**: collect self-reported Python experience (1–5 scale)
- **Time pressure**: do not enforce hard cutoff; note completion time

## 8. Data Recording
For each participant × task:
```json
{
  "pid": "P01",
  "task": "T1",
  "condition": "L4",
  "code_submitted": "...",
  "pass": true,
  "time_seconds": 180,
  "rule_sheet_consulted": true,
  "python_experience": 3
}
```

Anonymize PIDs before any publication or sharing.

## 9. Analysis Plan
1. Compute HPR per task and compare to LLM pass rates (Section 5 of paper)
2. Wilcoxon signed-rank test (n small): H1 (HPR > 0.5 per task)
3. Report gap metric; if gap ≥ 30pp for T1/T3, claim "meaningful discriminative advantage"
4. If gap < 30pp on any task, soften corresponding claim in §6.2

## 10. Timeline Estimate
- IRB clearance / instructor consent: 1–2 days (likely exempt)
- Participant scheduling: 2–3 days
- Data collection (1 session × 15 participants, 25 min each): 1 day
- Analysis + paper update: 0.5 day
- **Total**: ~1 week from approval

## 11. Paper Update Plan (Post Exp-5)
If H1/H2 confirmed:
- §6.2: Replace "Students who understand the L4 rules *should* retain an advantage" with HPR numbers
- Table 5 (new): HPR vs LLM pass rate comparison
- Update abstract claim from "potentially" to "empirically demonstrated"

If H1/H2 fail (human HPR also low):
- §6.2: Remove educational claim or replace with "L4 creates uniform confusion for both humans and LLMs"
- §6.3 Limits: Add "human interpretability at L4 is not guaranteed without explicit rule exposure"
