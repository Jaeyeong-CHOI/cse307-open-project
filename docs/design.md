# Design Notes

## Language Core
- Expr:
  - literals: int, bool
  - operators: +, -, *, <, ==
  - control: if-then-else
  - bindings: let x = e1 in e2
  - functions: fun x -> e / e1 e2
  - tracing: emit(tag, value)

## Trace Model
Event schema (JSON-like):
- `{ step, event, node, value, envHash }`

Key event types:
- `EvalStart(node)`
- `EvalEnd(node, value)`
- `BranchTaken(node, then|else)`
- `UserEmit(tag, value)`

## Assignment Variation
Given `(student_id, assignment_id, salt)`:
- derive seed = hash(...)
- generate parameterized constants/cases
- select subset of hidden tests

## Verification
1. run interpreter on student submission
2. compare observed output with expected output
3. validate trace policy:
   - required events exist
   - event order constraints hold
   - trace hash matches canonicalization rules

## Risks / Limits
- Over-constraining traces may penalize creative implementations
- Trace obfuscation could leak less than full semantics but still expose patterns
- Need careful balance between strictness and pedagogical flexibility
