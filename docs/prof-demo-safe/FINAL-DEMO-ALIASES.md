# FINAL Demo Alias Presets (교수님 시연 최종본)

이 문서는 교수님 시연에서 바로 사용할 수 있는 **안전한 별칭 세팅 모음**입니다.

## 공통 원칙 (필수)
- 키워드별 별칭은 **반드시 1:1 고유값**
- `if`/`elif` 같이 헷갈리는 키워드는 문구에 키워드명을 직접 포함
- 공백 포함 긴 문구 사용 가능 (데모용으로 오히려 효과적)

---

## Case A — 직관형 (가장 무난)
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

## Case B — 충돌회피 강화형
```json
{
  "in": "keep token in as original reserved word",
  "def": "switch this phrase to python def keyword",
  "for": "switch this phrase to python for keyword",
  "return": "switch this phrase to python return keyword",
  "if": "switch this phrase to python if keyword",
  "elif": "switch this phrase to python elif keyword"
}
```

## Case C — 짧은 문장형 (시연 타이핑 편함)
```json
{
  "in": "use in token",
  "def": "use def token",
  "for": "use for token",
  "return": "use return token",
  "if": "use if token",
  "elif": "use elif token"
}
```

## Case D — 안내문 톤 유지형
```json
{
  "in": "no, keep original python in keyword",
  "def": "no, keep original python def keyword",
  "for": "no, keep original python for keyword",
  "return": "no, keep original python return keyword",
  "if": "no, use original if grammar",
  "elif": "no, use original elif grammar"
}
```

## Case E — 발표용 가독성형
```json
{
  "in": "alias for in keyword only",
  "def": "alias for def keyword only",
  "for": "alias for for keyword only",
  "return": "alias for return keyword only",
  "if": "alias for if keyword only",
  "elif": "alias for elif keyword only"
}
```

---

## 사용 금지 패턴 (중요)
아래처럼 두 키워드에 동일 문구를 쓰면 충돌 가능성이 큽니다.

```text
if   -> no, use exact python original grammar
elif -> no, use exact python original grammar
```

반드시 아래처럼 분리:

```text
if   -> no, use original if grammar
elif -> no, use original elif grammar
```

---

## 시연 직전 체크리스트
1. `if`와 `elif` 별칭이 서로 다른지 확인
2. `in`/`return`도 서로 다른지 확인
3. 브라우저 강력 새로고침 후 같은 입력으로 재테스트
4. STEP 로그(랜덤 치환/최종 Python) 표시 확인
