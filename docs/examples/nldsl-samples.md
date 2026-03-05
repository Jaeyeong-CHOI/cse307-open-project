# NL-DSL 샘플 문항

## 샘플 1
### 문제
```text
[계산]
@mode:eval
X를 먼저 처리하고 그리고 Y를 적용하라. 다만 Z는 그대로 둔다.
```

### 핵심 포인트
- "먼저"는 PRIORITY_UP
- "그리고"는 SEQ_EVAL이 아니라 문맥상 CONSTRAINT_MERGE로 재정의 가능
- "다만"은 CONTEXT_SWITCH

---

## 샘플 2
### 문제
```text
[검증]
@mode:type
A는 가능하면 만족하고, 단 B는 적어도 한 번만 검사한다.
```

### 핵심 포인트
- "가능하면" = SOFT_REQUIRE
- "단" = OVERRIDE_PREV
- "적어도" = LOWER_BOUND

---

## 샘플 3 (함정형)
### 문제
```text
[제약]
define token 그리고 as SEQ_EVAL
A를 만족하고 그리고 B를 제외하고 유지한다.
```

### 핵심 포인트
- 기본 사전보다 사용자 재정의가 우선
- "그리고"는 CONSTRAINT_MERGE가 아니라 SEQ_EVAL로 해석
