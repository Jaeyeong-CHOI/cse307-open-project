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
- `python3 scripts/batch_report_summary.py <batch_json> [-o output_md] [--csv-output output.csv] [--json-output output.json] [--top-k-mismatches 5] [--include-diff-columns] [--mismatch-sort input|severity] [--taxonomy-weights weights.json] [--taxonomy-weight-profile profile_name] [--only-mismatches] [--fail-on-mismatch] [--fail-on-severity-total-ge N] [--fail-on-severity-avg-ge X] [--require-explicit-event-name]`: batch JSON을 사람 친화적인 Markdown 요약으로 변환하고(선택) case-level CSV/JSON으로 내보냄 (`mismatch_severity_total`, `mismatch_severity_avg` 위험 신호 지표 + `taxonomy_weight_source` 재현성 메타데이터 + `gates`(mismatch/severity gate 상태) 포함, `--only-mismatches`로 mismatch row만 필터링 가능, severity threshold 기반 CI gate 지원, `--require-explicit-event-name`로 run_context event fallback(`unknown`)을 금지 가능)
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
# run_context 메타데이터를 summary JSON에 주입 (run_id/run_url/event/repo/sha/ref/workflow/job/actor)
python3 scripts/batch_report_summary.py ../docs/research/results/roundtrip-batch-v1.diff.json --json-output ../docs/research/results/roundtrip-batch-v1.diff.summary.with-run-context.json --run-id 123456789 --run-url https://github.com/Jaeyeong-CHOI/cse307-open-project/actions/runs/123456789 --event-name workflow_dispatch --repository Jaeyeong-CHOI/cse307-open-project --sha abcdef1 --ref refs/heads/main --workflow ocaml-confusion-lang-ci --job summary-regression --actor github-actions
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
# summary schema version range 허용 (예: v1~v2)
python3 scripts/validate_summary_payload.py ../docs/research/results/roundtrip-batch-v1.diff.summary.json --schema-version-min 1 --schema-version-max 2
# metric schema JSON lint
python3 scripts/validate_metric_schema.py examples/metric-schema-v1.json
# metric schema version range 허용 (예: v1~v2)
python3 scripts/validate_metric_schema.py examples/metric-schema-v1.json --schema-version-min 1 --schema-version-max 2
# task set schema JSON lint
python3 scripts/validate_task_set.py examples/task-set-v1.json
# task set schema version range 허용 (예: v1~v2)
python3 scripts/validate_task_set.py examples/task-set-v1.json --schema-version-min 1 --schema-version-max 2
# CI step snapshot JSON schema lint
python3 scripts/validate_ci_result_snapshot.py ../docs/research/results/roundtrip-batch-v1.include-diff.snapshot.ci.json
# snapshot schema version range 허용 (예: v1~v2)
python3 scripts/validate_ci_result_snapshot.py ../docs/research/results/roundtrip-batch-v1.include-diff.snapshot.ci.json --schema-version-min 1 --schema-version-max 2
# snapshot emit 시 schema version override (v2 실험 분기)
python3 scripts/emit_ci_result_snapshot.py ../docs/research/results/roundtrip-batch-v1.include-diff.summary.ci.json --metric-json ../docs/research/results/roundtrip-batch-v1.include-diff.metrics.ci.json --json-output ../docs/research/results/roundtrip-batch-v1.include-diff.snapshot.v2.ci.json --schema-version ci_result_snapshot.v2
# summary JSON -> metric snapshot 생성 (task-set lineage 자동 포함)
python3 scripts/generate_metric_snapshot.py ../docs/research/results/roundtrip-batch-v1.diff.summary.json -o ../docs/research/results/roundtrip-batch-v1.diff.metrics.json --task-set-id cse307-roundtrip-batch-v1 --prompt-condition strict --model gpt-5.3-codex --task-set-json examples/task-set-v1.json
# batch eval run plan 생성(offline, dedupe + cheap-first ordering + run cap)
python3 scripts/build_batch_eval_plan.py examples/task-set-v1.json --models gpt-5-mini,gpt-5-pro,gpt-5-mini --prompt-conditions base,strict,base --repeats 2 --cheap-first --max-total-runs 64 --max-runs-per-model 24 -o ../docs/research/results/roundtrip-batch-v1.plan.json
# summary/task-set lineage 불일치 시 fail-fast
python3 scripts/generate_metric_snapshot.py ../docs/research/results/roundtrip-batch-v1.diff.summary.json -o ../docs/research/results/roundtrip-batch-v1.diff.metrics.strict-lineage.json --task-set-id cse307-roundtrip-batch-v1 --prompt-condition strict --model gpt-5.3-codex --task-set-json examples/task-set-v1.json --lineage-consistency fail
# run_context fallback event_name(unknown/derived) 차단(엄격 모드)
python3 scripts/generate_metric_snapshot.py ../docs/research/results/roundtrip-batch-v1.diff.summary.json -o ../docs/research/results/roundtrip-batch-v1.diff.metrics.strict-event-name.json --task-set-id cse307-roundtrip-batch-v1 --prompt-condition strict --model gpt-5.3-codex --task-set-json examples/task-set-v1.json --require-explicit-event-name
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
- `metadata.schema_version`은 `vN` 형식이어야 하며 validator의 `--schema-version-min/max` 범위 내여야 함 (기본: v1 고정)
- optional `metadata.task_set_lineage`가 존재하면 object여야 하며, 포함된 `task_set_id/alias_set_id/manifest_path`는 non-empty string이어야 함
- `overview.cases_scope`는 `all|mismatches-only` enum 중 하나여야 함
- `failure_taxonomy.severity_weighted[*]`는 `tag/count/weight/weighted_score` 필수
- `top_mismatches[*]`는 `source/failure_taxonomy/severity` 필수
- `gates`는 object여야 하며 aggregate 필드 `any_tripped`(bool), `tripped_list`(array)와 `mismatch`, `severity_total`, `severity_avg` 서브 오브젝트(각각 `enabled`, `tripped`)를 포함해야 함
- `gates.any_tripped`는 `bool(gates.tripped_list)`와 일치해야 하며 `gates.tripped_list`는 실제 `tripped=true` gate 이름 집합과 동일해야 함
- optional `gates.aggregate`가 존재하면 object여야 하며 `enabled`(bool), `tripped`(bool), `exit_code`(int) 필드를 가져야 함 (`--fail-on-any-tripped` 실행 정책 노출)
- optional `run_context`가 존재하면 허용 키(`run_id`, `run_url`, `run_attempt`, `event_name`, `repository`, `sha`, `ref`, `workflow`, `job`, `actor`)만 포함해야 함 (typo/드리프트 fail-fast)
- optional `run_context`가 존재하면 `run_id`/`run_url`은 함께 제공되어야 하며(`pair`), `run_url`은 `http(s)` 형식이고 `run_id`를 포함해야 함(실행 역추적성 보장)
- optional `run_context.run_id`/`run_attempt`는 숫자 문자열이어야 함
- optional `run_context.run_url`은 `https://github.com/<owner>/<repo>/actions/runs/<run_id>[/attempts/<n>]` 형식이어야 함
- `run_context.run_attempt`가 제공되면 `run_url`에도 `/attempts/<n>` segment가 있어야 하며 값이 일치해야 함 (반대로 `run_url`에 attempt segment가 있으면 `run_attempt`도 필수)
- optional `run_context.repository`는 `<owner>/<repo>` 형식이어야 하며, `run_url`이 있을 때 URL의 repository segment와 일치해야 함
- optional `run_context.sha`는 7~40 길이 hex 문자열이어야 함 (short/full SHA 허용)
- optional `run_context.ref`는 `refs/heads/*`, `refs/tags/*`, `refs/pull/*` 중 하나의 네임스페이스를 따라야 함 (예: `refs/heads/main`, `refs/tags/v1.0.0`, `refs/pull/123/merge`)
- optional `run_context.event_name`는 `push|pull_request|pull_request_target|merge_group|workflow_dispatch|schedule|workflow_run|repository_dispatch|unknown` 중 하나여야 함 (`unknown`은 event 메타데이터를 확보하지 못한 fallback)
- `batch_report_summary.py --require-explicit-event-name`를 사용하면 run_context 주입 시 `--event-name` 생략을 허용하지 않고 fail-fast 처리해 fallback(`unknown`) 유입을 차단할 수 있음
- optional `run_context.workflow`/`run_context.job`은 non-empty string이어야 하며 길이는 1~128자로 제한됨 (비정상적으로 긴 메타데이터 fail-fast 차단)
- optional `run_context.actor`는 `^[A-Za-z0-9-]+$` 패턴이어야 함 (다운스트림 파서 입력 오염 차단)

`validate_task_set.py` 스키마 규칙:
- 루트는 JSON object
- 필수 root key: `schema_version`, `task_set_id`, `tasks`
- `schema_version`은 `vN` 형식이어야 하며 validator의 `--schema-version-min/max` 범위 내여야 함 (기본: v1 고정)
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
74. ~~Step Summary에 `top1_mismatch_first_diff_line`/`top1_mismatch_first_token_diff_index`를 추가해 실패 지점(라인/토큰 인덱스)을 artifact 다운로드 없이 즉시 확인 가능하게 개선~~ ✅ (`scripts/batch_report_summary.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `test_batch_report_summary.py`)
75. ~~Step Summary의 top-1 mismatch 힌트를 단일 compact key-value 라인으로 통합해 모바일/PR 뷰에서 세로 길이를 줄이고 triage 가독성을 개선~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
76. ~~Step Summary compact `top1_mismatch` key 순서를 `severity -> taxonomy -> source -> diff`로 재정렬해 triage 우선순위(리스크 먼저) 파악 속도 개선~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
77. ~~Step Summary 스냅샷 생성 로직을 공용 스크립트(`scripts/emit_ci_result_snapshot.py`)로 추출해 lightweight/full CI 간 중복을 제거하고, no-mismatch 케이스 출력(`n/a`)을 일관화~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `test_emit_ci_result_snapshot.py`)
78. ~~`emit_ci_result_snapshot.py`에 `--top-k-mismatches` 옵션을 추가해 Step Summary에서 top-1 외 다중 mismatch 힌트를 compact 1-line으로 노출~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`)
79. ~~`workflow_dispatch` 입력에 `snapshot_top_k_mismatches`(1~3)를 추가하고 lightweight/full Step Summary 생성 단계에 전달해 운영자가 mismatch 힌트 밀도를 실행 단위로 조절 가능하게 개선~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`)
80. ~~`emit_ci_result_snapshot.py` top-k compact 출력에 truncation 힌트(`... (+N more)`)를 추가해 `snapshot_top_k_mismatches`로 일부만 노출할 때도 남은 mismatch 개수를 즉시 파악 가능하게 개선~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`)
81. ~~`snapshot_top_k_mismatches=auto` 모드를 추가해 mismatch 수에 따라 Step Summary 힌트 밀도를 자동 조정(0~1→top1, 2~3→top2, 4+→top3)~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`)
82. ~~`emit_ci_result_snapshot.py`의 `--top-k-mismatches` 입력 범위를 workflow 정책(1~3/auto)과 동일하게 강제하고, out-of-range 입력을 명시 에러로 fail-fast 처리~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`)
83. ~~Step Summary에 `top_k_mismatches` 요청값/해결값(`requested`, `resolved`)을 함께 기록해 `auto` 해석 결과를 실행 로그만으로 즉시 관측 가능하게 개선~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`)
84. ~~Step Summary에 `gate_details` compact 라인(mismatch/severity_total/severity_avg/aggregate)을 추가해 gate 설정/관측값/trip 상태를 artifact 없이 즉시 파악 가능하게 개선~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`)
85. ~~`emit_ci_result_snapshot.py`에 `--json-output` 옵션을 추가해 동일 스냅샷을 machine-readable JSON으로도 저장하고, 오케스트레이터/후속 자동화에서 markdown 재파싱 없이 직접 소비 가능하게 개선~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`)
86. ~~CI snapshot JSON 전용 schema validator(`validate_ci_result_snapshot.py`)와 회귀 테스트를 추가하고, lightweight/full 워크플로우에서 `--json-output` 산출물을 즉시 검증해 Step Summary↔JSON 드리프트를 fail-fast로 차단~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`)
87. ~~`emit_ci_result_snapshot.py` 입력 summary payload에 대한 fail-fast shape 검증(`overview/gates` 필수 타입)과 `ERROR:`/`HINT:` 출력 추가로 손상된 summary를 조기 차단~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`)
88. ~~CI snapshot JSON payload에 `schema_version`(`ci_result_snapshot.v1`)를 도입하고 validator에서 버전 고정을 검증해 향후 필드 확장 시 호환성 관리 기준을 명확화~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `scripts/validate_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`)
89. ~~summary payload의 `gates.aggregate`에 `tripped`(bool)를 추가하고 validator/step snapshot 표시를 동기화해 aggregate gate trip 상태를 artifact 없이도 명시적으로 관측 가능하게 개선~~ ✅ (`scripts/batch_report_summary.py`, `scripts/validate_summary_payload.py`, `test_batch_report_summary.py`, `test_summary_payload_schema.py`, `test_emit_ci_result_snapshot.py`, `README.md`)
90. ~~CI snapshot validator에 schema version 범위 옵션(`--schema-version-min/--schema-version-max`)을 추가해 v1 고정 검증과 향후 v2 점진 도입 검증을 모두 지원~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
91. ~~CI snapshot JSON/Step Summary에 실행 컨텍스트(`run_id`, `run_url`, `sha`, `ref`)를 optional 메타데이터로 포함해 실패 스냅샷을 워크플로우 실행과 즉시 역추적 가능하게 개선~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `scripts/validate_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
92. ~~CI snapshot run_context에 `run_attempt`/`event_name` 메타데이터를 추가해 재실행(workflow rerun)과 트리거 유형(push/PR/manual)을 Step Summary/JSON만으로 즉시 식별 가능하게 개선~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `scripts/validate_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
93. ~~CI snapshot run_context에 `repository`/`actor` 메타데이터를 추가해 multi-repo 운영 및 수동 실행 주체 추적을 Step Summary/JSON 단일 뷰에서 즉시 가능하게 개선~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `scripts/validate_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
94. ~~`emit_ci_result_snapshot.py`에 `--schema-version` override 옵션을 추가해 v2 실험 분기에서도 동일 emitter를 재사용하고, validator의 버전 범위 검증(`--schema-version-min/max`)과 조합해 점진 롤아웃 경로를 단일 CLI로 유지~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`, `README.md`)
95. ~~snapshot validator의 `run_context` 검증을 강화해 `run_id`/`run_url` pair 강제 + URL traceability(`run_url`에 `run_id` 포함) + `run_attempt` 숫자 문자열 규칙을 추가하여 실행 역추적 metadata의 무결성을 fail-fast 보장~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
96. ~~CI snapshot run_context에 `workflow`/`job` 메타데이터를 추가해 동일 run 내 어떤 워크플로우/잡에서 생성된 스냅샷인지 Step Summary/JSON만으로 즉시 식별 가능하게 개선~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `scripts/validate_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
97. ~~snapshot validator에 `run_context.sha` 형식 검증(7~40 hex)을 추가해 잘못된 commit 메타데이터를 조기 차단~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
98. ~~snapshot validator에 `run_context.ref` 형식 검증(`refs/` prefix)을 추가해 브랜치/PR ref 메타데이터 손상을 조기 차단~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
99. ~~snapshot validator에 `run_context.run_id` 숫자 형식 및 `run_context.repository` `<owner>/<repo>` 패턴 검증을 추가해 실행/저장소 메타데이터 오염을 조기 차단~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
100. ~~snapshot validator에 `run_context.run_url` GitHub Actions canonical 형식 검증과 `run_url`↔`run_id`/`repository` segment 일치 검증을 추가해 실행 링크 메타데이터 무결성을 강화~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
101. ~~snapshot validator에 `run_context.run_attempt`↔`run_url /attempts/<n>` pair/값 일치 검증을 추가해 rerun attempt 메타데이터 추적 무결성을 fail-fast 보장~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
102. ~~snapshot validator에 `run_context.actor` 허용 문자 패턴(`^[A-Za-z0-9-]+$`) 검증을 추가해 다운스트림 파서 입력 오염을 fail-fast 차단~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
103. ~~snapshot validator에 `cases.total == cases.ok + cases.mismatch` 및 non-negative 카운터 검증을 추가해 손상/집계 불일치 스냅샷을 fail-fast 차단~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
104. ~~snapshot validator의 `run_context.ref` 검증을 whitelist(`refs/heads/*|refs/tags/*|refs/pull/*`)로 강화해 비표준 ref 네임스페이스 오염을 조기 차단~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
105. ~~snapshot validator에 `run_context.workflow`/`run_context.job` 길이 상한(<=128) 검증을 추가해 비정상적으로 긴 실행 메타데이터를 fail-fast 차단~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
106. ~~snapshot validator의 `run_context.event_name` 허용 enum에 `pull_request_target`/`merge_group`를 추가해 merge queue 및 보안 컨텍스트 PR 실행 메타데이터를 false-positive 없이 수용~~ ✅ (`scripts/validate_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
107. ~~`run_context.event_name` 허용 enum 정의를 공통 모듈(`scripts/run_context_schema.py`)로 단일 소스화하고 emitter/validator가 동일 집합을 공유하도록 정리해 drift를 차단~~ ✅ (`scripts/run_context_schema.py`, `scripts/emit_ci_result_snapshot.py`, `scripts/validate_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`)
108. ~~workflow 시작 단계에서 `github.event_name`을 공용 schema(`run_context_schema`)로 즉시 검증해 워크플로우 trigger/validator enum drift를 fail-fast 차단~~ ✅ (`scripts/validate_run_context_event_name.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `test_run_context_event_name_schema.py`)
109. ~~`run_context_schema` event enum을 JSON/Markdown으로 export하는 스크립트(`scripts/export_run_context_event_names.py`)와 회귀 테스트를 추가해 문서/자동화 소비 경로에서 enum drift를 단일 소스로 고정~~ ✅ (`scripts/export_run_context_event_names.py`, `test_run_context_schema_export.py`, `examples/run-context-event-names.v1.json`, `docs/run-context-event-names.v1.md`)
110. ~~summary payload validator(`validate_summary_payload.py`)에도 optional `run_context`(run_url/repository/ref/event_name/workflow/job) 형식 검증을 추가해 summary↔snapshot 메타데이터 무결성 규칙을 정렬~~ ✅ (`scripts/validate_summary_payload.py`, `test_summary_payload_schema.py`, `README.md`)
111. ~~`batch_report_summary.py`가 optional `run_context`(run_id/run_url/run_attempt/event/repository/sha/ref/workflow/job/actor)를 직접 주입할 수 있도록 CLI 플래그를 추가하고, summary validator에 `actor` 패턴 검증을 확장해 summary 생성기↔validator 간 규칙 parity를 강화~~ ✅ (`scripts/batch_report_summary.py`, `scripts/validate_summary_payload.py`, `test_summary_payload_schema.py`, `README.md`)
112. ~~`run_context` 검증 로직을 공통 모듈(`scripts/run_context_validation.py`)로 추출해 `validate_summary_payload.py`/`validate_ci_result_snapshot.py` 간 규칙 drift와 중복 유지보수 비용을 줄이기~~ ✅ (`scripts/run_context_validation.py`, `scripts/validate_summary_payload.py`, `scripts/validate_ci_result_snapshot.py`)
113. ~~`run_context` payload에 허용 키 화이트리스트 검증(unknown key fail-fast)을 공통 validator에 추가해 오타/스키마 드리프트를 조기 차단~~ ✅ (`scripts/run_context_validation.py`, `test_summary_payload_schema.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
114. ~~snapshot emitter에서 `event_name` 미지정 시 `unknown` fallback을 자동 주입하고 공용 enum에 포함해 summary/snapshot 경로의 run_context 정책(`n/a` vs `unknown`)을 명시적으로 통일~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `scripts/run_context_schema.py`, `test_emit_ci_result_snapshot.py`, `test_run_context_event_name_schema.py`, `test_run_context_schema_export.py`, `README.md`)
115. ~~metric snapshot `source_summary`에 `run_context`를 전달하고 metric validator가 해당 run_context 규칙을 동일하게 검증하도록 확장해 summary→metric→snapshot 추적 체인의 metadata parity를 강화~~ ✅ (`scripts/generate_metric_snapshot.py`, `scripts/validate_metric_schema.py`, `examples/metric-schema-v1.json`, `test_generate_metric_snapshot.py`, `test_metric_schema.py`)
116. ~~summary payload validator에 schema version range 옵션(`--schema-version-min/--schema-version-max`)을 추가해 v1 고정 검증과 향후 v2 점진 도입 검증을 모두 지원~~ ✅ (`scripts/validate_summary_payload.py`, `test_summary_payload_schema.py`, `README.md`)
117. ~~metric schema validator(`validate_metric_schema.py`)에도 schema version range 옵션(`--schema-version-min/--schema-version-max`)을 추가해 summary/snapshot과 동일한 점진 버전 검증 흐름을 지원~~ ✅ (`scripts/validate_metric_schema.py`, `test_metric_schema.py`, `README.md`)
118. ~~task-set schema validator(`validate_task_set.py`)에도 schema version range 옵션(`--schema-version-min/--schema-version-max`)을 추가해 validator 계열의 버전 정책 인터페이스를 통일~~ ✅ (`scripts/validate_task_set.py`, `test_task_set_schema.py`, `README.md`)
119. ~~`batch_report_summary.py`의 `--run-*` 입력에 대해 공통 `run_context` 규칙을 즉시 검증해(요약 생성 전 fail-fast) 잘못된 run URL/attempt 조합이 summary→metric 파이프라인으로 흘러들어가는 것을 차단~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`, `README.md`)
120. ~~snapshot emitter가 `event_name` 자동 fallback(`unknown`) 시 `run_context.event_name_source=derived`를 함께 기록하고, validator가 `event_name_source` enum(`provided|derived`)을 검증하도록 확장해 run_context provenance를 명시~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `scripts/run_context_validation.py`, `scripts/validate_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`, `test_ci_result_snapshot_schema.py`, `README.md`)
121. ~~`batch_report_summary.py`에서도 run_context `event_name` 미지정 시 `unknown` + `event_name_source=derived`를 자동 주입하고, `--event-name` 제공 시 `event_name_source=provided`를 기록해 summary/snapshot provenance 정책을 완전히 정렬~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`, `README.md`)
122. ~~`batch_report_summary.py`에 `--require-explicit-event-name` 옵션을 추가해 run_context 사용 시 fallback(`event_name=unknown`) 유입을 선택적으로 차단하고, 엄격 모드(명시 이벤트 강제)를 운영자가 선택할 수 있게 개선~~ ✅ (`scripts/batch_report_summary.py`, `test_batch_report_summary.py`, `README.md`)
123. ~~`workflow_dispatch` 입력에 summary event-name 정책 토글(`summary_event_name_mode=permissive|strict`)을 추가하고, lightweight/full summary 생성 단계에서 `--require-explicit-event-name` 전달 여부를 런타임으로 제어해 수동 실행에서도 fallback 허용/차단 정책을 즉시 선택 가능하게 개선~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
124. ~~공통 `run_context` validator가 `event_name` 존재 시 `event_name_source`도 필수로 강제해 summary/metric/snapshot provenance 필드 누락을 fail-fast 차단~~ ✅ (`scripts/run_context_validation.py`, `test_summary_payload_schema.py`, `test_ci_result_snapshot_schema.py`, `test_metric_schema.py`, `test_generate_metric_snapshot.py`, `examples/metric-schema-v1.json`, `README.md`)
125. ~~snapshot emitter(`emit_ci_result_snapshot.py`)에 strict event-name 정책(`--require-explicit-event-name`)을 추가하고, workflow_dispatch 입력(`snapshot_event_name_mode=permissive|strict`)으로 lightweight/full CI snapshot 단계에서 fallback(`unknown`) 허용 여부를 런타임 제어~~ ✅ (`scripts/emit_ci_result_snapshot.py`, `test_emit_ci_result_snapshot.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
126. ~~CI mode resolution Step Summary에 strict event-name 정책 배너를 추가해(`summary/snapshot` 각각) 수동 실행 시 fallback 차단 상태를 로그 첫 화면에서 즉시 식별 가능하게 개선~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
127. ~~`generate_metric_snapshot.py`에 `--require-explicit-event-name` 옵션을 추가해 summary run_context fallback(`unknown/derived`) 유입을 선택적으로 차단하고, metric 단계에서도 strict event-name 정책을 fail-fast로 강제~~ ✅ (`scripts/generate_metric_snapshot.py`, `test_generate_metric_snapshot.py`, `README.md`)
128. ~~`workflow_dispatch` 입력에 metric event-name 정책 토글(`metric_event_name_mode=permissive|strict`)을 추가하고 lightweight/full metric snapshot 단계에 `--require-explicit-event-name` 전달 여부를 런타임 제어해 수동 실행에서도 summary/snapshot과 동일한 strict fallback 차단 정책을 적용~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
129. ~~CI mode resolution Step Summary의 strict event-name 정책 표기를 compact 단일 라인(`event_name_policy_modes`)으로 통합하고, strict가 하나라도 활성화된 경우에만 공통 안내(`event_name_policy_note`)를 출력해 모바일/PR 뷰 가독성을 개선~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
130. ~~`event_name_policy_modes` 출력을 ultra-compact 토큰(`S/P/M`) 형식으로 축약해 모바일/PR 뷰에서 가로 폭 사용량을 줄이고 가독성을 개선~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
131. ~~CI mode summary의 event-name policy 출력 포맷을 공용 스크립트(`scripts/format_event_name_policy_modes.py`)로 추출하고 회귀 테스트를 추가해 워크플로우 인라인 bash 분기 드리프트를 줄이기~~ ✅ (`scripts/format_event_name_policy_modes.py`, `test_format_event_name_policy_modes.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `scripts/run_python_regression_tests.sh`, `README.md`)
132. ~~`detect-changes` 단계의 `*_event_name_mode`(summary/snapshot/metric) 해석 로직을 공용 스크립트(`scripts/resolve_event_name_mode.py`)로 추출하고 회귀 테스트를 추가해 인라인 bash 분기 중복/드리프트를 줄이기~~ ✅ (`scripts/resolve_event_name_mode.py`, `test_resolve_event_name_mode.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `scripts/run_python_regression_tests.sh`, `README.md`)
133. ~~CI mode resolution Step Summary에서 `*_require_explicit_event_name` raw flag 3줄을 제거하고 compact policy line(`event_name_policy_modes`)만 남겨 요약 노이즈를 줄이기~~ ✅ (`.github/workflows/ocaml-confusion-lang-ci.yml`, `README.md`)
134. ~~`detect-changes` 단계의 summary/snapshot/metric event-name mode 해석을 배치 스크립트(`scripts/resolve_event_name_modes.py`) 1회 호출로 통합해 중복 subprocess/grep 체인을 줄이고 유지보수 비용을 낮추기~~ ✅ (`scripts/resolve_event_name_modes.py`, `test_resolve_event_name_modes.py`, `.github/workflows/ocaml-confusion-lang-ci.yml`, `scripts/run_python_regression_tests.sh`, `README.md`)
135. ~~batch 평가 준비 단계에서 API 호출 전 실행계획을 deterministic하게 고정하는 planner(`scripts/build_batch_eval_plan.py`)를 추가하고, dedupe/cheap-first ordering/총 실행 cap(`--max-total-runs`)을 통해 중복 호출과 비용 폭주를 사전 차단~~ ✅ (`scripts/build_batch_eval_plan.py`, `test_build_batch_eval_plan.py`, `scripts/run_python_regression_tests.sh`, `README.md`)
136. ~~planner(`build_batch_eval_plan.py`)에 모델별 run cap(`--max-runs-per-model`)과 모델별 planned run 집계(`summary.planned_runs_by_model`)를 추가해 고비용 모델 쏠림을 사전 차단하고 비용 통제를 강화~~ ✅ (`scripts/build_batch_eval_plan.py`, `test_build_batch_eval_plan.py`, `README.md`)
137. ~~planner summary에 potential/skipped run 집계(`potential_runs_total`, `skipped_runs_total`, `potential_runs_by_model`, `skipped_runs_by_model`)를 추가해 per-model cap으로 인해 실제로 절감된 호출량을 사전 정량화~~ ✅ (`scripts/build_batch_eval_plan.py`, `test_build_batch_eval_plan.py`, `README.md`)
