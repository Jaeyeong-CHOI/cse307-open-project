# ocaml-confusion-lang

[![OCaml confusion-lang CI](https://github.com/Jaeyeong-CHOI/cse307-open-project/actions/workflows/ocaml-confusion-lang-ci.yml/badge.svg?branch=main)](https://github.com/Jaeyeong-CHOI/cse307-open-project/actions/workflows/ocaml-confusion-lang-ci.yml)
[최근 CI 실행 확인](https://github.com/Jaeyeong-CHOI/cse307-open-project/actions/workflows/ocaml-confusion-lang-ci.yml)

OCaml 기반 Python 혼동 언어 연구용 최소 도구 체인 (초기 뼈대).

## 목표
- alias set의 1:1 충돌 여부를 자동 검증
- 이후 round-trip checker(혼동 언어 -> Python -> 실행 검증)로 확장

## 현재 지원
- `validate <alias_tsv>`: 필수 키 존재 + 중복 alias 감지
- `transform <alias_tsv> <source_file>`: Python -> 혼동 언어 치환
- `roundtrip <alias_tsv> <source_file>`: Python -> alias -> Python 복원 일치성 검사
- `roundtrip-report <alias_tsv> <source_file> <out_json>`: roundtrip 결과 JSON 리포트 저장 (`first_diff`, `failure_taxonomy`, `ast_equivalent` 포함)
- `batch-roundtrip-report <alias_tsv> <manifest_txt> <out_json> [--include-diff]`: 여러 소스 파일에 대한 일괄 roundtrip JSON 요약 (`total_cases`, `ok_cases`, `mismatch_cases`, `cases[]`) 생성
  - `--include-diff` 사용 시 각 케이스에 `first_diff`, `first_token_diff` 포함
- `python3 scripts/batch_report_summary.py <batch_json> [-o output_md] [--csv-output output.csv] [--top-k-mismatches 5] [--include-diff-columns]`: batch JSON을 사람 친화적인 Markdown 요약으로 변환하고(선택) case-level CSV로 내보냄

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
# triple-quote 스트레스 케이스
dune exec confusionlang -- roundtrip examples/case-c2.tsv examples/triple_quote_stress.py
# 결과 JSON 저장 (repo 루트 docs/research/results 권장)
dune exec confusionlang -- roundtrip-report examples/case-c2.tsv examples/sample.py ../docs/research/results/roundtrip-sample.json
# manifest 기반 batch 리포트
dune exec confusionlang -- batch-roundtrip-report examples/case-c2.tsv examples/manifest-v1.txt ../docs/research/results/roundtrip-batch-v1.json
# mismatch 디버깅용 상세 diff 포함
dune exec confusionlang -- batch-roundtrip-report examples/case-c2.tsv examples/manifest-v1.txt ../docs/research/results/roundtrip-batch-v1.diff.json --include-diff
# batch 결과 Markdown 요약 생성
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json -o ../docs/research/results/roundtrip-batch-v1.diff.summary.md --csv-output ../docs/research/results/roundtrip-batch-v1.diff.csv --top-k-mismatches 10
# CSV에 diff 상세 컬럼(first_diff/first_token_diff)까지 포함
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json --csv-output ../docs/research/results/roundtrip-batch-v1.diff.with-diff.csv --include-diff-columns
```

## 다음 구현
1. ~~문자열/주석 보호 토크나이저~~ ✅ (single/double/triple quote + line comment 보호)
2. ~~single-pass replace 엔진 고도화 (현재는 코드 span별 fold)~~ ✅ (코드 span에서 keyword 매칭 1-pass 스캐너로 대체)
3. ~~roundtrip 결과 JSON 리포트 저장~~ ✅ (`roundtrip-report`)
4. ~~round-trip equivalence checker 강화 (토큰 단위 1차 비교)~~ ✅ (`token_equivalent`, `first_token_diff` 리포트 포함)
5. ~~failure taxonomy 자동 라벨링~~ ✅ (기초 휴리스틱 태그: `token_substitution_mismatch`, `line_count_mismatch`, `token_stream_mismatch` 등)
6. ~~AST 기반 비교기(정밀 단계) 추가~~ ✅ (`roundtrip-report`에 Python `ast.parse` 기반 `ast_equivalent`/`ast_parse_error` 기록)
7. ~~`dune runtest` 회귀 테스트(리포트 스키마 assertion) 추가~~ ✅ (`test_roundtrip_report_schema.py`)
8. ~~mismatch fixture 기반 `failure_taxonomy` assertion 확대~~ ✅ (`examples/collision-risk.tsv`, mismatch 케이스 검증)
9. ~~CI smoke에 `dune runtest` + `roundtrip-report` 검사 추가~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
10. ~~batch eval 스크립트 뼈대(`batch-roundtrip-report`) 추가~~ ✅ (manifest 기반 다중 소스 요약 리포트)
11. ~~CI에서 `batch-roundtrip-report` 스모크 + 결과 artifact 업로드~~ ✅ (`roundtrip-sample.ci.json`, `roundtrip-batch-v1.ci.json`)
12. ~~`batch-roundtrip-report` 상세 모드 옵션(`--include-diff`) 추가~~ ✅ (케이스별 `first_diff`/`first_token_diff` 선택 포함)
13. ~~CI smoke에 `--include-diff` 샘플 실행 + artifact 업로드 추가~~ ✅ (`roundtrip-batch-v1.include-diff.ci.json`)
14. ~~`batch-roundtrip-report --include-diff` 스키마 회귀 assertion 추가~~ ✅ (`test_roundtrip_report_schema.py`)
15. ~~`batch-roundtrip-report` 기본 모드 vs `--include-diff` 모드 스키마 차이 분리 assertion 추가~~ ✅ (`test_roundtrip_report_schema.py`)
16. ~~batch 결과 post-processing 스크립트(요약 표 생성) 초안 추가~~ ✅ (`scripts/batch_report_summary.py`)
17. ~~README 상단에 CI 배지/최근 실행 링크 노출~~ ✅
18. ~~whitespace/line-count drift 유도 fixture 추가로 taxonomy/배치 회귀 커버리지 확장~~ ✅ (`examples/batch-summary-fixture-whitespace-linecount.json`, `test_batch_report_summary.py`)
19. ~~summary 스크립트에 CSV export + top-k mismatch view 옵션 추가~~ ✅ (`--csv-output`, `--top-k-mismatches`)
20. ~~summary CSV에 optional diff 컬럼(`--include-diff-columns`) 추가~~ ✅ (`first_diff_*`, `first_token_diff_*`)
