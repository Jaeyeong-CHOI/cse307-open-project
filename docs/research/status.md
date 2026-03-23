# Research Live Status

마지막 업데이트: 2026-03-23 14:08 KST

## Snapshot
- 전체 진행도(추정): **79%**
- 현재 단계: **Phase 4~5 (안정화 완료권 + 결과 누적/분석 강화 단계)**
- 핵심 병목: **정량 실험 결과(JSON) 누적량 부족**

## KPI Board
- CI 안정성: 🟢 (최근 연속 success)
- 결과 파일 누적: 🟡 (1차 batch 결과 생성 완료, 누적 확대 필요)
- 지표 산출(ACR/PRR/ESR): 🟡 (파이프라인 준비됨, 누적 강화 필요)
- 문서화 품질: 🟢 (roadmap/log/papers/literature 체계화)

## This Week Progress
- [x] 연구 구조/문서 허브 정리
- [x] alias/lineage/schema validator 확장
- [x] planner/preset/state-code 탐색 기능 확장
- [x] CI 안정화 이슈 핵심 원인 정리 및 해결
- [x] 1차 배치 실험 결과(JSON/CSV/MD) 생성 및 검증 완료
- [ ] 배치 실험 결과(JSON) 누적 확대
- [ ] `papers/v2.md` 정량 분석 반영

## Immediate Next Actions
1. full/targeted 실험 배치 추가 실행 후 `docs/research/results/` 결과 JSON 누적
2. 결과 요약(ACR/PRR/ESR + mismatch taxonomy) 자동 리포트 누적 생성
3. `docs/research/papers/v2.md`에 1차 수치(ACR=0.333, PRR=0.667, ESR=0.667) 반영

## Links
- 로드맵: `docs/research/roadmap.md`
- 로그: `docs/research/log/`
- 결과: `docs/research/results/`
- 논문형 문서: `docs/research/papers/`
- 최신연구 리뷰: `docs/research/literature/`
