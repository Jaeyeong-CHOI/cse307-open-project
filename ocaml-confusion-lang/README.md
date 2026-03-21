# ocaml-confusion-lang

OCaml 기반 Python 혼동 언어 연구용 최소 도구 체인 (초기 뼈대).

## 목표
- alias set의 1:1 충돌 여부를 자동 검증
- 이후 round-trip checker(혼동 언어 -> Python -> 실행 검증)로 확장

## 현재 지원
- `validate <alias_tsv>`: 필수 키 존재 + 중복 alias 감지
- `transform <alias_tsv> <source_file>`: Python -> 혼동 언어 치환
- `roundtrip <alias_tsv> <source_file>`: Python -> alias -> Python 복원 일치성 검사

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
```

## 다음 구현
1. 문자열/주석 보호 토크나이저
2. single-pass replace 엔진
3. round-trip equivalence checker
4. failure taxonomy 자동 라벨링
