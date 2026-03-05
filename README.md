# TraceLang + GuardLab (CSE307 Open Project)

Cheating-resistant assignment language and programming environment.

## Motivation
Traditional programming assignments are vulnerable to:
- AI-generated direct solutions
- Code sharing / superficial rewriting
- Output-only grading that ignores reasoning process

This project proposes a **process-aware** grading model: students submit both output and execution traces.

## Core Idea
- **TraceLang**: a tiny language with required trace events
- **GuardLab**: an assignment environment with per-student seeded variants
- **Verifier**: validates output + trace consistency

## High-level Architecture
1. **Generator**: creates student-specific assignment instances from a common template
2. **Interpreter**: executes TraceLang and emits structured trace
3. **Verifier**: checks semantic correctness and trace constraints
4. **Feedback**: reports first failing trace step

## MVP Scope
- Minimal TraceLang grammar (arithmetics, let, if, function)
- `emit(tag, value)` trace primitive
- Seed-based test/constraint variation
- CLI verifier for output+trace

## Repo Structure
- `docs/proposal.md` – one-page project proposal
- `docs/design.md` – design details and evaluation plan
- `src/` – prototype OCaml skeleton
- `demo/` – demonstration scenarios

## Next Steps
1. Finalize TraceLang syntax and semantics
2. Implement parser/interpreter skeleton in OCaml
3. Build verifier with hidden tests + trace checks
4. Prepare demo and evaluation results

## Web Demo
A lightweight demo UI is included in `web/index.html`.

Run locally:
```bash
cd web
python3 -m http.server 8080
# then open http://localhost:8080
```

The demo showcases:
- seeded assignment variant generation
- output + trace-aware verification logic

## OCaml ↔ Web Bridge (Demo)
Generate a sample submission JSON from OCaml stub and load it in the web UI:
```bash
./scripts/generate_sample_submission.sh
# then upload demo/submission.json in the browser
```

## GitHub Pages
A workflow is included at `.github/workflows/pages.yml`.
After enabling Pages in repo settings, web demo will deploy from `web/`.
