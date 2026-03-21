# Examples

- `sample.py` : 기본 roundtrip 데모
- `protected_literals.py` : 문자열/주석 보호 검증
- `triple_quote_stress.py` : triple-quote 스트레스 케이스
- `case-c2.tsv` : alias preset (C-2)

## Quick check
```bash
cd ocaml-confusion-lang
dune exec confusionlang -- validate examples/case-c2.tsv
dune exec confusionlang -- roundtrip examples/case-c2.tsv examples/sample.py
```
