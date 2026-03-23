# Research Live Status

마지막 업데이트: 2026-03-23 17:35 KST

## Snapshot
- 전체 진행도(추정): **79%**
- 현재 단계: **Phase 4~5 (안정화 완료권 + 결과 누적/분석 강화 단계)**
- 핵심 병목: **실험 runner 인프라(LLM API + dune 실행 환경) 가용성**

## KPI Board
- CI 안정성: 🟢 (최근 연속 success)
- 결과 파일 누적: 🟡 (fixture 기반 누적 1개 추가, 실제 대규모 배치 미확대)
- 지표 산출(ACR/PRR/ESR): 🟡 (fixture 결과 메트릭 재생성 완료, 추가 배치 필요)
- 문서화 품질: 🟢 (status/log/papers 업데이트)

## This Week Progress
- [x] 연구 구조/문서 허브 정리
- [x] alias/lineage/schema validator 확장
- [x] planner/preset/state-code 기능 확장
- [x] CI 안정화 이슈 원인 정리 및 개선 반영
- [x] 1차 배치 실험 결과(JSON/CSV/MD) 검증 완료
- [x] fixture 요약 기반 metric snapshot 누적 1건 추가
  - `docs/research/results/roundtrip-batch-v1.fixture.metrics.accum.2026-03-23.json`
- [ ] 배치 실험 결과(JSON) 대규모 누적 확대(LLM 모델/alias 조합)
- [ ] `papers/v2.md` 정량 분석 반영

## Immediate Next Actions
1. 실행 환경 정비: `dune` 설치 또는 대체 런처 확보 후 실제 roundtrip batch 재실행
2. 유효한 LLM API 키/엔드포인트 확보 후 `run_gpt54_eval.py` 배치 실행
3. `docs/research/results/`에 task-set별 누적 결과(JSON) 정기 저장 및 스키마 검증 자동화
4. `papers/v2.md`에 누적 지표(ACR/PRR/ESR + mismatch taxonomy) 반영

## Links
- 로드맵: `docs/research/roadmap.md`
- 로그: `docs/research/log/`
- 결과: `docs/research/results/`
- 논문형 문서: `docs/research/papers/`
- 최신연구 리뷰: `docs/research/literature/`
