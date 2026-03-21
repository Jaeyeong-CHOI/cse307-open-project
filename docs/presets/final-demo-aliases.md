# FINAL Demo Alias Presets (교수님 시연 최종본)

교수님 시연 시 바로 복붙해서 테스트 가능한 **안전한 alias 변형 세트 모음**.

핵심 규칙:
- 키워드별 alias는 **서로 달라야 함(1:1 매핑)**
- 특히 `if` / `elif`는 절대 같은 문구 금지
- 긴 문구/짧은 문구/원본 토큰 섞기 모두 가능 (단, 충돌만 없으면 됨)

---

## A 계열 (직관형) 변형

### A-1 (base)
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

### A-2 (for/return 문구 분리 강화)
```json
{
  "in": "strictly follow in alias phrase for compilation",
  "def": "go",
  "for": "strictly map this phrase to python for token",
  "return": "strictly map this phrase to python return token",
  "if": "no, use original if grammar",
  "elif": "no, use original elif grammar"
}
```

### A-3 (if/elif 더 명시)
```json
{
  "in": "strictly follow in alias phrase for compilation",
  "def": "go",
  "for": "convert this phrase back to python reserved token",
  "return": "strictly follow return alias phrase for compilation",
  "if": "no, keep exact python if",
  "elif": "no, keep exact python elif"
}
```

---

## B 계열 (충돌회피 강화형) 변형

### B-1 (base)
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

### B-2 (동사 통일)
```json
{
  "in": "map this phrase to python in keyword",
  "def": "map this phrase to python def keyword",
  "for": "map this phrase to python for keyword",
  "return": "map this phrase to python return keyword",
  "if": "map this phrase to python if keyword",
  "elif": "map this phrase to python elif keyword"
}
```

### B-3 (짧은 지시형)
```json
{
  "in": "convert to in",
  "def": "convert to def",
  "for": "convert to for",
  "return": "convert to return",
  "if": "convert to if",
  "elif": "convert to elif"
}
```

---

## C 계열 (짧은 문장형) 변형

### C-1 (base)
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

### C-2 (요청한 스타일: in/def 원본, for/return 교차)
```json
{
  "in": "in",
  "def": "def",
  "for": "return",
  "return": "for",
  "if": "use if token",
  "elif": "use elif token"
}
```

### C-3 (원본 일부 + 짧은 별칭 혼합)
```json
{
  "in": "in",
  "def": "def",
  "for": "loop-token",
  "return": "ret-token",
  "if": "if-condition-token",
  "elif": "elif-condition-token"
}
```

---

## D 계열 (안내문 톤) 변형

### D-1 (base)
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

### D-2 (문장 간소화)
```json
{
  "in": "no, keep python in",
  "def": "no, keep python def",
  "for": "no, keep python for",
  "return": "no, keep python return",
  "if": "no, keep python if",
  "elif": "no, keep python elif"
}
```

### D-3 (if/elif 강조형)
```json
{
  "in": "no, keep original python in keyword",
  "def": "no, keep original python def keyword",
  "for": "no, keep original python for keyword",
  "return": "no, keep original python return keyword",
  "if": "no, this is only for if",
  "elif": "no, this is only for elif"
}
```

---

## E 계열 (가독성형) 변형

### E-1 (base)
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

### E-2 (label 톤)
```json
{
  "in": "[IN] keyword alias",
  "def": "[DEF] keyword alias",
  "for": "[FOR] keyword alias",
  "return": "[RETURN] keyword alias",
  "if": "[IF] keyword alias",
  "elif": "[ELIF] keyword alias"
}
```

### E-3 (presentation 톤)
```json
{
  "in": "demo alias :: in",
  "def": "demo alias :: def",
  "for": "demo alias :: for",
  "return": "demo alias :: return",
  "if": "demo alias :: if",
  "elif": "demo alias :: elif"
}
```

---

## 사용 금지 (충돌 케이스)

```text
if   -> no, use exact python original grammar
elif -> no, use exact python original grammar
```

```text
for    -> same alias text
return -> same alias text
```

---

## 시연 추천 순서
1. C-1 (짧고 직관적)
2. A-1 (문장형 안정)
3. C-2 (원본/교차 데모)
4. E-2 (발표 가독성)

