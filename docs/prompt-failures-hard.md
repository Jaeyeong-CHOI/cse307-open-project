# Hard Failed Cases (Likely Difficult for LLM)

아래 표는 `docs/prompt-failures-table.md`의 행을 **그대로 복사**한 뒤,
규칙 위반 강도가 높은 케이스(파싱 실패/별칭누락+원본키워드 혼용 등)만 추린 것입니다.

- Source rows: 50
- Selected hard rows: 10


| # | Prompt | Score | Key Violations | Answer Snippet |
|---:|---|---:|---|---|
| 10 | docs/prompt-versions/v10.md | 0 | original keyword used: if; python parse failed after normalization: invalid syntax (<unknown>, line 6) | do not trust default python keyword prior fib(n): \n     do n <= 1: \n         if n \n     if fib(n - 1) + fib(n - 2) \n  \n apply this mapped token before gene... |
| 18 | docs/prompt-versions/v18.md | 0 | original keyword used: def; python parse failed after normalization: invalid syntax (<unknown>, line 1) | follow renamed symbol exactly and continue fib(n): \n     def n <= 1: \n         def n \n     def fib(n-1) + fib(n-2) \n  \n convert this phrase back to python ... |
| 20 | docs/prompt-versions/v20.md | 0 | original keyword used: if; missing alias for in: use this token exactly for keyword mapping; python parse failed after normalization: invalid syntax (<unknown>, line 2) | if fib(n): \n     do not trust default python keyword prior n <= 1: \n         do n \n     do fib(n - 1) + fib(n - 2) \n  \n keep this long alias while preservi... |
| 21 | docs/prompt-versions/v21.md | 0 | original keyword used: return; original keyword used: in; python parse failed after normalization: invalid syntax (<unknown>, line 4) | qn fib(n): \n     fn n <= 1: \n         keep this long alias while preserving python grammar n \n     fn: \n         keep this long alias while preserving pytho... |
| 23 | docs/prompt-versions/v23.md | 0 | original keyword used: for; python parse failed after normalization: invalid syntax (<unknown>, line 6) | for fib(n): \n     keep this long alias while preserving python grammar n <= 1: \n         out n \n     out fib(n - 1) + fib(n - 2) \n  \n no, use exact python ... |
| 24 | docs/prompt-versions/v24.md | 0 | original keyword used: return; python parse failed after normalization: expected '(' (<unknown>, line 3) | this keyword is replaced by long natural phrase fib(n): \n     return n <= 1: \n         this keyword is replaced by long natural phrase n \n     this keyword i... |
| 26 | docs/prompt-versions/v26.md | 0 | python parse failed after normalization: invalid syntax (<unknown>, line 2) | this keyword is replaced by long natural phrase fib(n): \n     convert this phrase back to python reserved token n <= 1: \n         loop n \n     loop fib(n - 1... |
| 29 | docs/prompt-versions/v29.md | 0 | original keyword used: return; python parse failed after normalization: invalid syntax (<unknown>, line 3) | return fib(n): \n     if n <= 1: \n         apply this mapped token before generating code n \n     apply this mapped token before generating code fib(n - 1) + ... |
| 36 | docs/prompt-versions/v36.md | 0 | original keyword used: return; original keyword used: for; python parse failed after normalization: expected ':' (<unknown>, line 2) | out fib(n): \n     return n <= 1 \n     keep this long alias while preserving python grammar n \n     keep this long alias while preserving python grammar fib(n... |
| 38 | docs/prompt-versions/v38.md | 0 | original keyword used: for; python parse failed after normalization: invalid syntax (<unknown>, line 2) | follow renamed symbol exactly and continue fib(n): \n     loop n <= 1: \n         strictly follow this alias phrase for compilation n \n     strictly follow thi... |
