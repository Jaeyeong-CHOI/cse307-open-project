# ocaml-confusion-lang

OCaml 기반 Python 혼동 언어 연구용 최소 도구 체인 (초기 뼈대).

## 목표
- alias set의 1:1 충돌 여부를 자동 검증
- 이후 round-trip checker(혼동 언어 -> Python -> 실행 검증)로 확장

## 현재 지원
- `validate <alias_tsv>`: 필수 키 존재 + 중복 alias 감지
- `transform <alias_tsv> <source_file>`: Python -> 혼동 언어 치환
- `roundtrip <alias_tsv> <source_file>`: Python -> alias -> Python 복원 일치성 검사
- `roundtrip-report <alias_tsv> <source_file> <out_json>`: roundtrip 결과 JSON 리포트 저장

## Alias TSV 형식
`<python_keyword>\t<alias_phrase>`

필수 키:
- in, def, for, return, if, elif

## 실행 예시
```bash
cd ocaml-confusion-lang
dune exec confusionlang -- validate examples/case-c2.tsv
dune exec confusionlang -- transform examples/case-c2.tsv examples/sample.py
dune exec confusionlang -- roundtrip examples/case-c2.tsv examples/sample.py
# 문자열/주석 보호 확인용
dune exec confusionlang -- roundtrip examples/case-c2.tsv examples/protected_literals.py
# 결과 JSON 저장 (repo 루트 docs/results 권장)
dune exec confusionlang -- roundtrip-report examples/case-c2.tsv examples/sample.py ../docs/results/roundtrip-sample.json
```

## 다음 구현
1. ~~문자열/주석 보호 토크나이저~~ ✅ (single/double/triple quote + line comment 보호)
2. single-pass replace 엔진 고도화 (현재는 코드 span별 fold)
3. ~~roundtrip 결과 JSON 리포트 저장~~ ✅ (`roundtrip-report`)
4. round-trip equivalence checker 강화 (AST/토큰 단위 비교)
5. failure taxonomy 자동 라벨링
