# NL-DSL v0.1 (자연어 기반, 다의 토큰 해석형)

## 1) 목표
자연어처럼 보이지만, 실제 해석은 형식 규칙으로 결정되는 과제 언어를 정의한다.
핵심은 모델의 표면 독해 의존성을 줄이고, 해석 로그 기반 검증을 가능하게 하는 것이다.

---

## 2) 해석 파이프라인
입력 문장을 다음 순서로 해석한다.

1. **토큰 추출**: longest-match 사전 매칭
2. **문맥 태그 적용**: 섹션/모드/seed
3. **의미 결정**: 우선순위 규칙에 따라 sense 확정
4. **AST 구성**
5. **평가 및 로그 출력**

---

## 3) 의미 결정 우선순위
동일 토큰이 여러 의미를 가질 때, 아래 순서로 결정한다.

1. 섹션 태그 (`[계산]`, `[검증]`, `[제약]`)
2. 모드 태그 (`@mode:eval`, `@mode:type`)
3. 최근 재정의 (`define token ...`)
4. seed 사전 (학생별 변형)
5. 기본 사전

---

## 4) 다의 토큰 사전 (초안)
| 토큰 | 기본 의미 | 대체 의미(문맥 의존) |
|---|---|---|
| 그리고 | CONSTRAINT_MERGE | SEQ_EVAL |
| 또는 | ALT_BRANCH | SET_UNION |
| 먼저 | PRIORITY_UP | PRE_STEP |
| 가능하면 | SOFT_REQUIRE | GREEDY_SELECT |
| 단 | OVERRIDE_PREV | GUARD_START |
| 적어도 | LOWER_BOUND | MIN_CARDINALITY |
| 제외하고 | EXCEPT_FILTER | NEG_GUARD |
| 그대로 | IDENTITY_OP | FREEZE_ENV |
| 다만 | CONTEXT_SWITCH | WEAK_CONSTRAINT |
| 즉 | REWRITE_RULE | EQUIV_ASSERT |

> 주의: 표면 한국어 의미로 판단하지 말고, 해석 우선순위 규칙을 따른다.

---

## 5) 문법 스켈레톤
```bnf
Doc     ::= Header* Clause+
Header  ::= Section | Mode | Def
Section ::= "[계산]" | "[검증]" | "[제약]"
Mode    ::= "@mode:eval" | "@mode:type"
Def     ::= "define token" Tok "as" Sense
Clause  ::= Phrase (Connector Phrase)*
Connector ::= "그리고" | "또는" | "단" | "다만"
Phrase  ::= Predicate | Constraint | Action
```

---

## 6) 예시
### 입력
```text
[제약]
@mode:eval
A를 만족하고 그리고 B를 가능하면 적용한다. 단 C는 제외하고 유지한다.
```

### 해석 로그(예시)
```json
[
  {"token":"그리고","sense":"CONSTRAINT_MERGE","rule":"Section[제약] > Mode[eval]"},
  {"token":"가능하면","sense":"SOFT_REQUIRE","rule":"default"},
  {"token":"단","sense":"OVERRIDE_PREV","rule":"default"},
  {"token":"제외하고","sense":"EXCEPT_FILTER","rule":"default"}
]
```

---

## 7) 채점 규칙 (권장)
- 제출물 = (정답 출력, 해석 로그, 토큰-의미 매핑표)
- 정답만 맞아도 로그 불일치면 실패
- 로그 일치 + 정답 일치 시 통과

배점 예시:
- 출력 정합성 40
- 해석 로그 정합성 40
- 오류 분석/수정 노트 20

---

## 8) 운영 포인트
- 학생별 seed로 토큰 사전을 일부 재배치
- hidden 문항에 부정/이중부정/담화표지 토큰 집중
- 오탐 방지를 위해 랜덤 구두 확인(짧게) 병행
