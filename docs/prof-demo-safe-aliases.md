# Professor Demo Safe Alias Settings

교수님 앞 시연용으로 **충돌 없이 안정적으로 동작**하는 별칭 세팅만 모은 문서입니다.

핵심 원칙:
- 각 Python 키워드마다 **고유한 문구**를 사용한다.
- 의미가 비슷해도(예: `if`, `elif`) 같은 문구를 쓰지 않는다.
- `no, use original ...` 패턴을 쓸 때도 키워드명을 문구에 포함해 구분한다.

---

## ✅ Recommended Safe Set (Demo)

- `in` → `strictly follow in alias phrase for compilation`
- `def` → `go`
- `for` → `convert this phrase back to python reserved token`
- `return` → `strictly follow return alias phrase for compilation`
- `if` → `no, use original if grammar`
- `elif` → `no, use original elif grammar`

---

## 왜 이렇게 해야 하나?

`if`와 `elif`에 같은 별칭(예: `no, use exact python original grammar`)을 넣으면,
역치환 시 어떤 키워드로 복원해야 할지 모호해집니다.

이 원칙은 `in`/`return`처럼 다른 키워드에도 동일하게 적용됩니다.
즉, 시연용에서는 **모든 키워드 별칭을 1:1 고유값**으로 유지해야 합니다.

- `if` 전용: `no, use original if grammar`
- `elif` 전용: `no, use original elif grammar`

---

## 시연 전 체크리스트

1. `if` / `elif` / `for` / `return` 등 주요 키워드 별칭이 서로 겹치지 않는지 확인
2. 공백 포함 긴 문구 별칭이 정상 치환되는지 미리 테스트
3. 변환 로그에서 랜덤 치환 STEP이 표시되는지 확인
4. 브라우저 강력 새로고침 후 동일 결과 재확인

---

## Quick Copy (JSON style)

```json
{
  "in": "strictly follow in alias phrase for compilation",
  "def": "go",
  "for": "convert this phrase back to python reserved token",
  "return": "strictly follow return alias phrase for compilation",
  "if": "no, use original if grammar",
  "elif": "no, use original elif grammar"
}
```
