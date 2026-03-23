# Research Live Status

마지막 업데이트: 2026-03-23 19:52 KST

## Snapshot
- 전체 진행도(추정): **79%**
- 현재 단계: **Phase 4~5 (안정화 완료권 + 결과 누적/분석 강화 단계)**
- 핵심 병목: **실험 runner 인프라(LLM API + dune 실행 환경) 가용성**

## KPI Board
- CI 안정성: 🟢 (최근 연속 success)
- 결과 파일 누적: 🟢 (prompt-batch v1~v120 실측 JSON 3개 모델×120건 = 360건 누적 확정)
- 지표 산출(ACR/PRR/ESR): 🟡 (실측 호출은 복구, task pass는 여전히 0으로 난도 높음)
- 문서화 품질: 🟢 (status/log/results 업데이트)

## This Week Progress
- [x] 연구 구조/문서 허브 정리
- [x] alias/lineage/schema validator 확장
- [x] planner/preset/state-code 기능 확장
- [x] CI 안정화 이슈 원인 정리 및 개선 반영
- [x] 1차 배치 실험 결과(JSON/CSV/MD) 검증 완료
- [x] fixture 요약 기반 metric snapshot 누적 1건 추가
  - `docs/research/results/roundtrip-batch-v1.fixture.metrics.accum.2026-03-23.json`
- [x] 배치 샘플 12건 LLM 평가 실행 파이프라인(프롬프트→JSON/CSV/MD) 누적 시도
  - 산출물: `docs/research/results/prompt-batch-top12.gpt4o-mini.2026-03-23.*`
  - 실측 결과: `passed=0`, `failed=12` (401 인증 실패 동일)
- [x] 추가 배치(v110~v120) 11건 연속 누적 시도
  - 산출물: `docs/research/results/prompt-batch-v110-120.gpt4o-mini.2026-03-23.*`
  - 실측 결과: `passed=0`, `failed=11` (401 인증 실패 동일)
- [x] 배치 재시도: `docs/archive/prompt-versions/v1~v3` quick3 배치 실행
  - 산출물: `docs/research/results/prompt-batch-quick3.gpt4o-mini.2026-03-23.*`
  - 실측 결과: `passed=0`, `failed=3` (401 인증 실패 동일)
- [x] Prompt 배치 결과 누적 통합 생성(요약)
  - 산출물: `docs/research/results/prompt-batch-aggregated-2026-03-23.json`
  - 누적 요약: `total=46, passed=0, failed=46` (HTTP 401 동시 실패)
  - JSON 카운트/필수키 정합성 검증(OK)
- [x] 추가 배치(v70~v89) 20건 연속 누적 시도
  - 산출물: `docs/research/results/prompt-batch-v70-89.gpt4o-mini.2026-03-23.*`
  - 실측 결과: `passed=0`, `failed=20` (401 인증 실패 동일)
- [x] 추가 배치(v90~v109) 20건 실측 누적 (실호출)
  - 산출물: `docs/research/results/prompt-batch-v90-109.gpt4o-mini.2026-03-23.*`
  - 실측 결과: `passed=0`, `failed=20` (HTTP 401 없음, judge violation 중심 실패)
- [x] 일일 누적 통합 재생성
  - `docs/research/results/prompt-batch-aggregated-2026-03-23.json`
  - 누적 합계 갱신: `total=135, passed=0, failed=135`
- [x] 배치 실험 결과(JSON) 대규모 누적 확대 2차 달성
  - 단일 배치 확정: `prompt-batch-v1-120.gpt4o-mini.2026-03-23.json` (`total=120, passed=0, failed=120`)
  - HTTP 실패: `0` (401 재발 없음, judge violation 중심 실패)
  - 요약/검증 산출: `.summary.csv`, `.summary.md`, `prompt-batch-aggregated-2026-03-23.json`
- [x] 동일 조건 교차모델 추가 실측(실데이터 누적 확대)
  - 단일 배치 확정: `prompt-batch-v1-120.gpt41-mini.2026-03-23.json` (`total=120, passed=0, failed=120`)
  - HTTP 실패: `0` (인증/런타임 실패 없음)
  - 누적 합계(당일 확정 배치): `total=240, passed=0, failed=240`
  - 통합 집계 갱신: `docs/research/results/prompt-batch-aggregated-2026-03-23.json`
- [x] 3rd 모델 교차 실측 누적: `gpt-4.1-nano` full-range v1~v120
  - 단일 배치 확정: `prompt-batch-v1-120.gpt41-nano.2026-03-23.json` (`total=120`, `passed=0`, `failed=120`)
  - HTTP 실패: `0` (인증 실패 없음, 타임아웃 2건)
  - 누적 합계(당일 확정 배치): `total=360, passed=0, failed=360`
  - 상위 위반: `original keyword used=407`, `python parse failed after normalization=111`
  - 요약/집계 갱신: `.summary.csv`, `.summary.md`, `prompt-batch-aggregated-2026-03-23.json`
- [ ] `docs/research/context-compression.md` 운영 적용

## Immediate Next Actions
1. 실행 환경 정비: `dune` 설치 또는 대체 런처 확보 후 실제 roundtrip batch 재실행
2. `run_gpt54_eval.py` 배치의 judge taxonomy(상위 violation) 요약 자동화 및 프롬프트 수정 루프 연결
3. 확보된 v1~v120 실측 JSON을 기준으로 task-set별 누적 지표(JSON) 정기 저장/자동화
4. `papers/v2.md`에 누적 지표(ACR/PRR/ESR + mismatch taxonomy) 반영

## Links
- 로드맵: `docs/research/roadmap.md`
- 로그: `docs/research/log/` (`*_digest.md` 우선 참조)
- 상태: `docs/research/context-state.json`
- 압축 규칙: `docs/research/context-compression.md`
- 결과: `docs/research/results/`
- 논문형 문서: `docs/research/papers/`
- 최신연구 리뷰: `docs/research/literature/`
