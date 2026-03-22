# Research Live Status

마지막 업데이트: 2026-03-22 15:20 KST

## Snapshot
- 전체 진행도(추정): **68%**
- 현재 단계: **Phase 3~5 경계 (파이프라인 안정화 + 결과 패키징 준비)**
- 핵심 병목: **OCaml confusion-lang CI 연쇄 실패(설정 드리프트)**

## KPI Board
- CI 안정성: 🔴 (최근 연속 fail)
- 결과 파일 누적: 🟡 (`docs/research/results/` 실질 결과 부족)
- 지표 산출(ACR/PRR/ESR): 🟡 (파이프라인 준비됨, 누적 부족)
- 문서화 품질: 🟢 (roadmap/log/papers/literature 체계화)

## This Week Progress
- [x] 연구 구조/문서 허브 정리
- [x] alias/lineage/schema validator 확장
- [x] planner/preset 탐색 기능 대폭 확장
- [ ] CI 안정화 완전 해결
- [ ] 배치 실험 결과(JSON) 본격 누적

## Immediate Next Actions
1. CI fail 원인 즉시 트래킹 후 패치/재검증 반복
2. 결과 JSON 자동 누적 경로 정상화
3. `papers/v2.md`에 정량 지표 기반 중간 분석 반영

## Links
- 로드맵: `docs/research/roadmap.md`
- 로그: `docs/research/log/`
- 결과: `docs/research/results/`
- 논문형 문서: `docs/research/papers/`
- 최신연구 리뷰: `docs/research/literature/`
