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
- `python3 scripts/batch_report_summary.py <batch_json> [-o output_md] [--csv-output output.csv] [--json-output output.json] [--top-k-mismatches 5] [--include-diff-columns] [--mismatch-sort input|severity] [--taxonomy-weights weights.json] [--taxonomy-weight-profile profile_name] [--only-mismatches] [--fail-on-mismatch] [--fail-on-severity-total-ge N] [--fail-on-severity-avg-ge X]`: batch JSON을 사람 친화적인 Markdown 요약으로 변환하고(선택) case-level CSV/JSON으로 내보냄 (`mismatch_severity_total`, `mismatch_severity_avg` 위험 신호 지표 + `taxonomy_weight_source` 재현성 메타데이터 + `gates`(mismatch/severity gate 상태) 포함, `--only-mismatches`로 mismatch row만 필터링 가능, severity threshold 기반 CI gate 지원)
- `python3 scripts/batch_report_summary.py --list-taxonomy-profiles`: 내장 taxonomy weight profile 목록 출력 (`examples/weights/*.json`)

## Alias TSV 형식
`<python_keyword>\t<alias_phrase>`

필수 키:
- in, def, for, return, if, elif

## 실행 예시
```bash
cd ocaml-confusion-lang
dune exec ./main.exe -- validate examples/case-c2.tsv
dune exec ./main.exe -- transform examples/case-c2.tsv examples/sample.py
dune exec ./main.exe -- roundtrip examples/case-c2.tsv examples/sample.py
# 문자열/주석 보호 확인용
dune exec ./main.exe -- roundtrip examples/case-c2.tsv examples/protected_literals.py
# triple-quote 스트레스 케이스
dune exec ./main.exe -- roundtrip examples/case-c2.tsv examples/triple_quote_stress.py
# 결과 JSON 저장 (repo 루트 docs/research/results 권장)
dune exec ./main.exe -- roundtrip-report examples/case-c2.tsv examples/sample.py ../docs/research/results/roundtrip-sample.json
# manifest 기반 batch 리포트
dune exec confusionlang -- batch-roundtrip-report examples/case-c2.tsv examples/manifest-v1.txt ../docs/research/results/roundtrip-batch-v1.json
# mismatch 디버깅용 상세 diff 포함
dune exec confusionlang -- batch-roundtrip-report examples/case-c2.tsv examples/manifest-v1.txt ../docs/research/results/roundtrip-batch-v1.diff.json --include-diff
# batch 결과 Markdown 요약 생성
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json -o ../docs/research/results/roundtrip-batch-v1.diff.summary.md --csv-output ../docs/research/results/roundtrip-batch-v1.diff.csv --top-k-mismatches 10
# CSV에 diff 상세 컬럼(first_diff/first_token_diff)까지 포함
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json --csv-output ../docs/research/results/roundtrip-batch-v1.diff.with-diff.csv --include-diff-columns
# 머신 가공용 JSON 요약(payload) 동시 저장
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json --json-output ../docs/research/results/roundtrip-batch-v1.diff.summary.json
# task-set lineage(task_set_id/alias_set_id/manifest_path)를 요약 metadata에 포함
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json --json-output ../docs/research/results/roundtrip-batch-v1.diff.summary.with-lineage.json --task-set-json examples/task-set-v1.json
# mismatch 하이라이트를 severity 기반으로 정렬
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json -o ../docs/research/results/roundtrip-batch-v1.diff.summary.severity.md --mismatch-sort severity
# taxonomy severity 가중치를 외부 JSON으로 주입
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json -o ../docs/research/results/roundtrip-batch-v1.diff.summary.custom-weight.md --mismatch-sort severity --taxonomy-weights examples/taxonomy-weights-severity-alt.json
# 내장 profile 목록 확인
python3 scripts/batch_report_summary.py --list-taxonomy-profiles
# 내장 profile 이름으로 가중치 적용
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json -o ../docs/research/results/roundtrip-batch-v1.diff.summary.profile-v2.md --mismatch-sort severity --taxonomy-weight-profile v2-education-risk
# taxonomy profile schema lint (CI/local)
python3 scripts/validate_taxonomy_profiles.py
# summary JSON payload schema lint
python3 scripts/validate_summary_payload.py ../docs/research/results/roundtrip-batch-v1.diff.summary.json
# metric schema JSON lint
python3 scripts/validate_metric_schema.py examples/metric-schema-v1.json
# task set schema JSON lint
python3 scripts/validate_task_set.py examples/task-set-v1.json
# summary JSON -> metric snapshot 생성 (task-set lineage 자동 포함)
python3 scripts/generate_metric_snapshot.py ../docs/research/results/roundtrip-batch-v1.diff.summary.json -o ../docs/research/results/roundtrip-batch-v1.diff.metrics.json --task-set-id cse307-roundtrip-batch-v1 --prompt-condition strict --model gpt-5.3-codex --task-set-json examples/task-set-v1.json
# summary/task-set lineage 불일치 시 fail-fast
python3 scripts/generate_metric_snapshot.py ../docs/research/results/roundtrip-batch-v1.diff.summary.json -o ../docs/research/results/roundtrip-batch-v1.diff.metrics.strict-lineage.json --task-set-id cse307-roundtrip-batch-v1 --prompt-condition strict --model gpt-5.3-codex --task-set-json examples/task-set-v1.json --lineage-consistency fail
# 생성된 metric snapshot schema lint
python3 scripts/validate_metric_schema.py ../docs/research/results/roundtrip-batch-v1.diff.metrics.json
# 케이스 목록을 mismatch만으로 축소
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json -o ../docs/research/results/roundtrip-batch-v1.diff.summary.mismatch-only.md --csv-output ../docs/research/results/roundtrip-batch-v1.diff.mismatch-only.csv --json-output ../docs/research/results/roundtrip-batch-v1.diff.summary.mismatch-only.json --only-mismatches
# 주의: metric snapshot에 --task-set-json을 쓰는 경우 summary overview.cases_scope는 반드시 all이어야 함
# (--only-mismatches 산출물은 task-set 정합성 검증 경로에서 차단)
# mismatch 존재 시 CI를 fail(종료코드 2) 처리
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json -o ../docs/research/results/roundtrip-batch-v1.diff.summary.gate.md --fail-on-mismatch
# severity risk budget gate (종료코드 3): total/avg 기준 임계치 이상이면 fail
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json -o ../docs/research/results/roundtrip-batch-v1.diff.summary.risk-gate.md --fail-on-severity-total-ge 120 --fail-on-severity-avg-ge 60
# aggregate gate (종료코드 4): 활성화된 gate 중 하나라도 tripped면 fail
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json -o ../docs/research/results/roundtrip-batch-v1.diff.summary.aggregate-gate.md --fail-on-mismatch --fail-on-severity-total-ge 120 --fail-on-any-tripped
```

`validate_taxonomy_profiles.py` 스키마 규칙:
- 루트는 JSON object
- `default_weight`는 integer
- `weights`는 object (`"taxonomy_tag": int` 쌍)

`validate_summary_payload.py` 스키마 규칙:
- 루트는 JSON object
- 필수 top-level key: `metadata`, `title`, `overview`, `quality_signals`, `failure_taxonomy`, `top_mismatches`, `mismatch_sort`, `gates`, `cases`
- `metadata`는 `schema_version`, `generated_at_utc`, `input_report` 필수
- optional `metadata.task_set_lineage`가 존재하면 object여야 하며, 포함된 `task_set_id/alias_set_id/manifest_path`는 non-empty string이어야 함
- `overview.cases_scope`는 `all|mismatches-only` enum 중 하나여야 함
- `failure_taxonomy.severity_weighted[*]`는 `tag/count/weight/weighted_score` 필수
- `top_mismatches[*]`는 `source/failure_taxonomy/severity` 필수
- `gates`는 object여야 하며 aggregate 필드 `any_tripped`(bool), `tripped_list`(array)와 `mismatch`, `severity_total`, `severity_avg` 서브 오브젝트(각각 `enabled`, `tripped`)를 포함해야 함
- `gates.any_tripped`는 `bool(gates.tripped_list)`와 일치해야 하며 `gates.tripped_list`는 실제 `tripped=true` gate 이름 집합과 동일해야 함
- optional `gates.aggregate`가 존재하면 object여야 하며 `enabled`(bool), `exit_code`(int) 필드를 가져야 함 (`--fail-on-any-tripped` 실행 정책 노출)

`validate_task_set.py` 스키마 규칙:
- 루트는 JSON object
- 필수 root key: `schema_version`, `task_set_id`, `tasks`
- optional root key: `alias_set_id`(non-empty string), `manifest_path`(`.txt` 경로 문자열)
- `tasks`는 non-empty array
- `tasks[*]` 필수 key: `task_id`, `source` (`.py`)
- `task_id` 중복 금지
- optional `difficulty`: `easy|medium|hard`
- optional `tags`: non-empty string array

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
21. ~~mismatch highlight 정렬 옵션(`--mismatch-sort severity`) 추가~~ ✅ (taxonomy/AST/token 기반 severity 우선 정렬)
22. ~~CI summary 단계에 severity 정렬 + diff 컬럼 CSV artifact 추가~~ ✅ (`roundtrip-batch-v1.include-diff.summary.ci.csv` 업로드)
23. ~~summary Markdown taxonomy 섹션에 severity-weighted 뷰 추가~~ ✅ (`Failure Taxonomy (severity-weighted)`)
24. ~~taxonomy severity 가중치 외부 설정(JSON) 주입 지원 추가~~ ✅ (`--taxonomy-weights`, `examples/taxonomy-weights-severity-alt.json`)
25. ~~summary Markdown에 배치 위험 신호 지표(`mismatch_severity_total`, `mismatch_severity_avg`) 추가~~ ✅ (`scripts/batch_report_summary.py`)
26. ~~taxonomy weight 파일 버전 프로파일(`examples/weights/*.json`) + named profile 선택 옵션(`--taxonomy-weight-profile`) + profile 목록 조회(`--list-taxonomy-profiles`) 추가~~ ✅ (`scripts/batch_report_summary.py`)
27. ~~taxonomy profile schema lint 스크립트 + CI 검증 단계 추가~~ ✅ (`scripts/validate_taxonomy_profiles.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`)
28. ~~summary Markdown 헤더에 적용된 taxonomy weight source(기본/파일/프로파일) 기록~~ ✅ (`taxonomy_weight_source`)
29. ~~summary 스크립트에 machine-readable JSON 출력 옵션(`--json-output`) 추가~~ ✅ (overview/quality/taxonomy/top_mismatches payload + 회귀 테스트)
30. ~~summary JSON payload schema validator + 회귀 테스트/CI 단계 추가~~ ✅ (`scripts/validate_summary_payload.py`, `test_summary_payload_schema.py`)
31. ~~summary JSON payload에 재현성 메타데이터(`metadata.schema_version/generated_at_utc/input_report`) 추가~~ ✅ (`scripts/batch_report_summary.py`, `validate_summary_payload.py`, 회귀 테스트 반영)
32. ~~`dune runtest`에 taxonomy/summary schema 회귀 테스트 통합~~ ✅ (`test_taxonomy_profile_schema.py`, `test_summary_payload_schema.py` 실행 포함)
33. ~~summary 출력 스코프 필터(`--only-mismatches`) 추가로 대규모 배치에서 케이스 노이즈 축소~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`)
34. ~~summary mismatch 게이트 옵션(`--fail-on-mismatch`) 추가로 CI/자동화 파이프라인의 실패 조건 명시~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`)
35. ~~metric schema JSON 정의 + validator/회귀 테스트 추가~~ ✅ (`examples/metric-schema-v1.json`, `scripts/validate_metric_schema.py`, `test_metric_schema.py`)
36. ~~CI에 metric schema smoke validation + 회귀 테스트 연동~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `test_metric_schema.py`)
37. ~~summary JSON → metric snapshot 생성 스크립트 + schema 검증/회귀 테스트/CI artifact 연동~~ ✅ (`scripts/generate_metric_snapshot.py`, `test_generate_metric_snapshot.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`)
38. ~~실험 task set v1 fixture + schema validator/회귀 테스트/CI smoke 연동~~ ✅ (`examples/task-set-v1.json`, `scripts/validate_task_set.py`, `test_task_set_schema.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`)
39. ~~metric snapshot 생성 단계에 `--task-set-json` 일관성 검증(아이디/케이스 소스/총량) 추가~~ ✅ (`scripts/generate_metric_snapshot.py`, `examples/task-set-fixture-whitespace-linecount-v1.json`, `test_generate_metric_snapshot.py`)
40. ~~task set 스키마에 `alias_set_id`/`manifest_path` 메타데이터 확장 + validator/회귀 테스트 반영~~ ✅ (`examples/task-set-v1.json`, `scripts/validate_task_set.py`, `test_task_set_schema.py`)
41. ~~metric snapshot `source_summary`에 task-set lineage(`alias_set_id`, `manifest_path`) 전달 추가~~ ✅ (`scripts/generate_metric_snapshot.py`, `examples/task-set-fixture-whitespace-linecount-v1.json`, `test_generate_metric_snapshot.py`)
42. ~~batch summary(`batch_report_summary.py`)에 `--task-set-json` 입력 기반 lineage 메타데이터(task_set_id/alias_set_id/manifest_path) 노출 추가~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`)
43. ~~summary payload validator에 optional `metadata.task_set_lineage` 타입/비어있음 검증 추가 + 회귀 테스트 반영~~ ✅ (`scripts/validate_summary_payload.py`, `test_summary_payload_schema.py`)
44. ~~metric snapshot 생성기(`generate_metric_snapshot.py`)에 summary/task-set lineage 교차 일관성 검증(`--lineage-consistency off|warn|fail`) + lineage `task_set_id` 포함~~ ✅ (`scripts/generate_metric_snapshot.py`, `test_generate_metric_snapshot.py`)
45. ~~CI metric snapshot 단계에 `--task-set-json examples/task-set-v1.json` + `--lineage-consistency fail` 적용해 end-to-end lineage chain 강제~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
46. ~~metric snapshot 파이프라인 정책 문서화: `--task-set-json` 경로에서는 `cases_scope=all`만 허용하고 `--only-mismatches` 산출물 차단을 README/에러 메시지에 명시~~ ✅ (`README.md`, `scripts/generate_metric_snapshot.py`)
47. ~~summary payload validator에 `overview.cases_scope` enum(`all|mismatches-only`) 검증 명시 + 회귀 테스트 추가~~ ✅ (`scripts/validate_summary_payload.py`, `test_summary_payload_schema.py`)
48. ~~`generate_metric_snapshot.py` 실패 경로의 traceback 노이즈 제거 + `ERROR:` prefix 단일 메시지로 CI 로그 가독성 개선~~ ✅ (`scripts/generate_metric_snapshot.py`, `test_generate_metric_snapshot.py`)
49. ~~summary 게이트에 severity 임계치 정책(`--fail-on-severity-total-ge`, `--fail-on-severity-avg-ge`) 추가해 mismatch 유무 외 위험 예산 기반 CI 차단 지원~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`)
50. ~~`generate_metric_snapshot.py` 실패 시 GitHub Actions annotation(`::error::`) 동시 출력으로 CI 로그 내 원인 탐색 속도 개선~~ ✅ (`scripts/generate_metric_snapshot.py`, `test_generate_metric_snapshot.py`)
51. ~~`batch_report_summary.py` 실패 경로도 traceback 억제 + `ERROR:`/`::error::`(GHA) 출력으로 로그 포맷 일관화~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`)
52. ~~summary/metric 스크립트의 error helper 중복 제거를 위해 공통 모듈(`scripts/error_utils.py`)로 추출 + 회귀 테스트 추가~~ ✅ (`scripts/error_utils.py`, `scripts/batch_report_summary.py`, `scripts/generate_metric_snapshot.py`, `test_error_utils.py`)
53. ~~validator 계열 스크립트(`validate_summary_payload.py`, `validate_metric_schema.py`, `validate_task_set.py`, `validate_taxonomy_profiles.py`)에도 공통 error helper를 적용해 `ERROR:` + `::error::` 출력 UX 일관화~~ ✅ (`scripts/error_utils.py`, validator 4종, `test_validator_error_output.py`)
54. ~~validator 실패 메시지에 구조화 힌트(`HINT: input=...` 등) 추가 + CI에 `test_validator_error_output.py` 명시 실행으로 dune 비의존 smoke 회귀 보강~~ ✅ (`scripts/error_utils.py`, validator 4종, `.github/workflows/ocaml-confusion-lang-ci.yml`, `test_validator_error_output.py`)
55. ~~`batch_report_summary.py`/`generate_metric_snapshot.py` gate/예외 실패 경로에도 구조화 힌트(`HINT: input=...`, 임계치/관측값 등) 적용 + 회귀 테스트 보강~~ ✅ (`scripts/batch_report_summary.py`, `scripts/generate_metric_snapshot.py`, `test_batch_report_summary.py`, `test_generate_metric_snapshot.py`)
56. ~~`batch_report_summary.py` 입력 batch JSON에 대해 필수 필드/카운터 정합성(`total/ok/mismatch` vs `cases[]`) fail-fast 검증 추가 + 회귀 테스트 보강~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`)
57. ~~CI Python 회귀 테스트 단계 중복 제거(동일 테스트 세트 single-pass 실행)로 파이프라인 시간/비용 최적화~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
58. ~~summary payload/Markdown에 gate 상태(`gates`: mismatch/severity_total/severity_avg) 노출 추가 + payload validator/회귀 테스트 연동~~ ✅ (`scripts/batch_report_summary.py`, `scripts/validate_summary_payload.py`, `test_summary_payload_schema.py`)
59. ~~CI 워크플로우에 `concurrency`(`cancel-in-progress`) 적용해 동일 브랜치 중복 실행 자동 취소로 Actions 분당 소모/대기열 비용 절감~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
60. ~~CI를 변경 감지 기반 경량 모드/전체 모드로 분리해 Python-only 변경에서는 OCaml build/setup를 생략, OCaml 엔진 변경에서만 full smoke 실행~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
61. ~~변경 감지 경계 보정: OCaml smoke 입력 fixture(`examples/**/*.tsv|*.txt|*.py`) 변경 시에도 full CI 경로를 강제해 roundtrip drift 누락을 방지~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
62. ~~Python 회귀 테스트 목록을 스크립트(`scripts/run_python_regression_tests.sh`)로 단일화해 lightweight/full CI 간 테스트 드리프트와 중복 유지보수 비용을 줄이기~~ ✅ (`scripts/run_python_regression_tests.sh`, `.github/workflows/ocaml-confusion-lang-ci.yml`)
63. ~~`workflow_dispatch` 수동 실행에 `ci_mode`(`auto|lightweight|full`) 입력을 추가해 운영자가 비용 우선/정밀 우선 경로를 명시적으로 선택 가능하게 만들기~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
64. ~~`detect-changes` 단계에서 `manual_mode/detected_full_ci/resolved_full_ci` 결정을 GitHub Step Summary에 기록해 경량/전체 분기 원인을 실행 로그만으로 바로 추적 가능하게 만들기~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
65. ~~`pull_request` 이벤트에서는 artifact 업로드 단계를 건너뛰어 저장소 스토리지/업로드 시간을 절감하고, `push`/수동 실행에서만 결과 산출물을 보존~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
66. ~~summary payload/Markdown에 aggregate gate 상태(`gates.any_tripped`, `gates.tripped_list`)를 추가해 다운스트림 자동화가 "어떤 gate가 막았는지"를 단일 필드로 추적 가능하도록 개선~~ ✅ (`scripts/batch_report_summary.py`, `scripts/validate_summary_payload.py`, `test_batch_report_summary.py`, `test_summary_payload_schema.py`)
67. ~~summary gate 결과에 대해 단일 종료코드 정책(`--fail-on-any-tripped`)을 추가해 CI/오케스트레이터가 개별 gate 코드를 해석하지 않고도 실패 여부를 일관되게 처리하도록 개선~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`, `README.md`)
68. ~~`batch_report_summary.py` 입력 스키마 fail-fast를 강화해 케이스 필드 타입/상태 enum(`ok|mismatch`)과 루트 counter 정수 타입을 명시 검증하여 손상된 batch JSON의 조기 차단/오탐 집계를 방지~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`)
69. ~~summary payload validator에 `gates.aggregate` 타입/필수 필드 검증과 `any_tripped`/`tripped_list` 일관성 검사를 추가해 gate 메타데이터 손상을 조기 차단~~ ✅ (`scripts/validate_summary_payload.py`, `test_summary_payload_schema.py`, `README.md`)
70. ~~PR 경로에서 artifact를 생략하더라도 디버깅 가능한 최소 결과 스냅샷(케이스/리스크/gate)을 `GITHUB_STEP_SUMMARY`에 자동 기록해 관측성 유지~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
71. ~~Step Summary에 `top1_mismatch_source` 단일 디버그 힌트를 추가해 PR 실패 triage 시작점을 즉시 노출~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
72. ~~Step Summary에 `top1_mismatch_taxonomy` 단일 힌트를 추가해 triage 분기(토큰/라인카운트/치환)를 즉시 파악 가능하게 개선~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
73. ~~Step Summary에 `top1_mismatch_severity`를 추가해 triage 우선순위(리스크 크기) 판단을 artifact 없이도 즉시 가능하게 개선~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
