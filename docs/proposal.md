# Project Proposal — TraceLang + GuardLab

## 1. Problem Statement
Current assignment workflows are increasingly vulnerable to AI-assisted cheating and code sharing. Most grading systems only check final outputs, which makes it easy to bypass learning by submitting generated code.

## 2. Objective
Design a small programming language and assignment environment where successful submission requires both:
1) correct outputs, and
2) valid execution traces consistent with language semantics and assignment constraints.

## 3. Approach
### TraceLang (Language)
A compact functional language with explicit trace emission points.

- Base constructs: integer, boolean, if, let, functions
- Trace primitive: `emit(tag, value)`
- Runtime emits canonical trace events (evaluation steps, branching decisions)

### GuardLab (Environment)
- Per-student seeded assignment instances
- Containerized execution (Docker) for reproducibility
- Verifier checks output correctness and trace integrity

## 4. Why It Is Cheating-Resistant
- Seeded variation prevents direct copy reuse across students
- Output-only mimicry fails if trace constraints are not satisfied
- Hidden tests + trace policies reduce LLM “one-shot solve” success

## 5. Evaluation Plan
Compare two grading settings on identical tasks:
- Baseline: output-only grading
- Proposed: output + trace-aware grading

Metrics:
- pass rate of copied/adapted submissions
- pass rate of LLM-generated submissions
- false rejection rate for honest solutions

## 6. Expected Outcome
A practical blueprint for assignment systems that preserve learning integrity while still giving students meaningful automated feedback.
