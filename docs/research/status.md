# Research Live Status

마지막 업데이트: 2026-03-25 04:30 KST

## Snapshot
- 전체 진행도(추정): **92%**
- 현재 단계: **Phase 5 완료 + Human Pilot 프로토콜 설계 완료**
- 핵심 병목: **Human pilot 실행 미착수 (n=10~15, IRB/instructor 승인 필요)**

## KPI Board
- CI 안정성: 🟢 (최근 연속 success)
- 결과 파일 누적: 🟢 (full-range 실측 14개 JSON + 변형조건(contextpack/legacy/probe) + 부분 재실행(v1-20) 포함)
- 지표 산출(ACR/PRR/ESR): 🟡 (모델별 편차 존재: gpt-4o는 contextpack 우세 추세, 2026-03-24 재실행에서 pass 3건으로 일시 향상 확인(+1), gpt-5.4-mini는 contextpack 갱신으로 조건 비교 우세(delta_avg_score=+12.583, nonzero=+13, passed=+3))
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
- [x] 4th 모델 교차 실측 누적: `gpt-5.4-mini` full-range v1~v120
  - 단일 배치 확정: `prompt-batch-v1-120.gpt54-mini.2026-03-23.json` (`total=120`, `passed=0`, `failed=120`)
  - HTTP 실패: `0` (인증/런타임 실패 없음)
  - 누적 합계(당일 확정 배치): `total=480`, `passed=0`, `failed=480`
  - 요약/집계 갱신: `.summary.csv`, `.summary.md`, `prompt-batch-aggregated-2026-03-23.json`
- [x] 5th 모델 교차 실측 누적: `gpt-4o` full-range v1~v120
  - 단일 배치 확정: `prompt-batch-v1-120.gpt4o.2026-03-23.json` (`total=120`, `passed=2`, `failed=118`)
  - HTTP 실패: `0` (인증/런타임 실패 없음)
  - 누적 합계(당일 확정 배치): `total=600`, `passed=2`, `failed=598`
  - 관측 포인트: full-range batch 최초 pass 발생(2건)
  - 요약/집계 갱신: `.summary.csv`, `.summary.md`, `prompt-batch-aggregated-2026-03-23.json`
- [x] 조건 비교 실측 추가: `gpt-4o` legacy(no contextpack) full-range v1~v120
  - 신규 배치: `prompt-batch-v1-120-legacy.gpt4o.2026-03-23.json` (`total=120`, `passed=1`, `failed=119`)
  - 비교 리포트: `prompt-batch-compare-contextpack-vs-legacy.gpt4o.2026-03-23.{json,md}`
  - 비교 결과: contextpack ON이 legacy 대비 `delta_passed=+1`, `delta_avg_score=+0.583`
- [x] 조건 비교 실측 추가: `gpt-4o-mini` legacy(no contextpack) full-range v1~v120
  - 신규 배치: `prompt-batch-v1-120-legacy.gpt4o-mini.2026-03-24.json` (`total=120`, `passed=0`, `failed=120`, `http_failures=0`)
  - 비교 리포트: `prompt-batch-compare-contextpack-vs-legacy.gpt4o-mini.2026-03-24.{json,md}`
  - 비교 결과: contextpack ON이 legacy 대비 `delta_avg_score=+1.083`, `delta_nonzero_score=+3` 개선(`delta_passed=0`)
- [x] 모델 가용성 probe: `gpt-5.3-codex` 1건 실행(HTTP 404)으로 unsupported 확인
  - 산출: `prompt-batch-v1-120.gpt53-codex.2026-03-23.json` (`total=1`, `http_failures=1`)
- [x] 조건 비교 실측 추가: `gpt-5.4-mini` legacy(no contextpack) full-range v1~v120
  - 신규 배치: `prompt-batch-v1-120-legacy.gpt54-mini.2026-03-24.json` (`total=120`, `passed=0`, `failed=120`, `http_failures=0`)
  - 비교 리포트: `prompt-batch-compare-contextpack-vs-legacy.gpt54-mini.2026-03-24.{json,md}`
  - 비교 결과: **legacy가 contextpack 대비** `avg_score +2.500`, `nonzero_score +3` 우세(`passed=0` 동률)
  - 통합 집계 갱신: `prompt-batch-aggregated-2026-03-24.json` (유효 full-range run 13개)
- [x] 재실행 정밀 체크: `gpt-4o` full-range 재평가(v1~v120, contextpack)
  - 신규 배치: `prompt-batch-v1-120-contextpack.gpt4o.2026-03-24.json` (`total=120`, `passed=3`, `failed=117`, `http_failures=0`)
  - 요약: `prompt-batch-v1-120-contextpack.gpt4o.2026-03-24.json.summary.{csv,md}`
  - 비교 리포트: `prompt-batch-v1-120-contextpack.gpt4o.compare-2026-03-23-vs-2026-03-24.{json,md}`
  - 비교 결과: `delta_avg_score=+5.750`, `delta_nonzero_score=+5`, `delta_passed=+1`
- [x] 조건 비교 실측 추가: `gpt-5.4-mini` contextpack full-range v1~v120
  - 신규 배치: `prompt-batch-v1-120-contextpack.gpt54-mini.2026-03-24.json` (`total=120`, `passed=3`, `failed=117`, `http_failures=0`)
  - 비교 리포트: `prompt-batch-compare-contextpack-vs-legacy.gpt54-mini.2026-03-24.{json,md}`
  - 비교 결과: contextpack이 legacy 대비 `delta_avg_score=+12.583`, `delta_nonzero_score=+13`, `delta_passed=+3`
- [x] 조건 비교 실측 추가: `gpt-4.1-mini` contextpack full-range v1~v120
  - 신규 배치: `prompt-batch-v1-120-contextpack.gpt41-mini.2026-03-24.json` (`total=120`, `passed=1`, `failed=119`, `http_failures=0`)
  - 비교 리포트: `prompt-batch-compare-contextpack-vs-legacy.gpt41-mini.2026-03-24.{json,md}`
  - 비교 결과: contextpack이 legacy 대비 `delta_avg_score=-2.250`, `delta_nonzero_score=-12`, `delta_passed=+1`

- [x] 조건 비교 실측 추가: `gpt-4.1-mini` legacy(no contextpack) full-range v1~v120
  - 신규 배치: `prompt-batch-v1-120-legacy.gpt41-mini.2026-03-24.json` (`total=120`, `passed=0`, `failed=120`, `http_failures=0`)
  - 비교 리포트: `prompt-batch-compare-contextpack-vs-legacy.gpt41-mini.2026-03-24.v2.{json,md}`
  - 비교 결과: contextpack ON 대비 `delta_avg_score=-2.416`, `delta_nonzero_score=-11`, `delta_passed=+0`

- [x] 배치 재실행: `gpt-4o-mini` contextpack 부분 재현성 확인(v1-20)
  - 산출물: `docs/research/results/prompt-batch-v1-20-contextpack.gpt4o-mini.2026-03-24.json`
  - 실측 결과: `total=20`, `passed=0`, `failed=20`, `http_failures=0`
  - 비교 리포트: `docs/research/results/prompt-batch-compare-contextpack-gpt4o-mini-2026-03-23-vs-2026-03-24.v1-20.{json,md}`
  - 비교 결과: `delta_avg_score=0.000`, `delta_passed=0`, `delta_nonzero=0`
- [x] 2026-03-25 04:00 논문 과도한 주장(overclaiming) 수정 + 실험 카운트 정정
  - §6.3 Limits: "two models" → 4모델(165 total multi-task runs)로 정정
  - §4: multi-task n 수 정확히 기재
  - §6.2 Education: T2 gpt-4o/4.1-mini 100% pass 사실 반영, 단언 완화
  - §6.2: human study(Exp-5) 없이 교육적 효과 단언하는 문구 조건부 표현으로 완화
  - PDF 재컴파일(9p), commit e6162e0 push 완료
- [x] 2026-03-25 04:30 Human pilot 프로토콜 설계 완료
  - 산출물: `docs/research/human-pilot/pilot-protocol.md`
  - within-subjects, T1/T2/T3 × n=10~15, open-book L4 rule sheet
  - 평가지표: HPR, gap(HPR - LLM_pass), Wilcoxon 검정 계획
  - 예상 소요: ~1주 (IRB 제외 시 3~4일)
  - 논문 §6.2 업데이트 계획 명시 (H1/H2 확인 시 수치 대입)

- [ ] `docs/research/context-compression.md` 운영 적용

- [x] 2026-03-25 03:45 o4-mini L4 multitask 완료 (n=45, 0/45)
  - T1 fib: 0/15, T2 sorted: 0/15, T3 vowels: 0/15 (all PPR=0.00)
  - reasoning model도 L4 pattern blindness 극복 못함 확인
  - 논문 Table 4 (l4_multitask) o4-mini 행 추가, §5.4 5번째 finding 추가
  - PDF 재컴파일 완료 (9 pages), commit 643ebf9 push 완료

- [x] 2026-03-25 gpt-4.1 family + o4-mini 실험 추가 (L1 + L4)
  - **L1 ctx-pack (n=20, v1-v20)**: gpt-4.1 (KLR=0.295), gpt-4.1-mini (KLR=0.210), gpt-4.1-nano (KLR=0.378), o4-mini (KLR=0.265)
  - **L4 ablation (n=20, 5×4)**: gpt-4.1 (PPR=1.0, 0/20), gpt-4.1-nano (PPR=1.0, 0/20), o4-mini (PPR=0.95, **1/20 pass** — first L4 pass from reasoning model)
  - o4-mini requires temperature=1 (API constraint); patched scripts used
  - gpt-4.1-mini ctx-pack achieved lowest KLR (0.21) across all models
  - 논문 Table 1 (L1), Table 3 (L4 ablation) 업데이트, 재컴파일 완료 (9p)
  - 산출물: `l1-gpt41-contextpack-2026-03-25.json`, `l1-gpt41mini-contextpack-2026-03-25.json`, `l1-gpt41nano-contextpack-2026-03-25.json`, `l1-o4mini-contextpack-2026-03-25.json`, `L4-ablation-n50.gpt41.2026-03-25.json`, `L4-ablation-n50.gpt41nano.2026-03-25.json`, `L4-ablation-n50.o4mini.2026-03-25.json`

## Immediate Next Actions
1. ~~**Multi-task 실험 설계 및 실행**~~ ✅ (모든 모델 완료: gpt-4o, gpt-4o-mini, gpt-4.1-mini, o4-mini)
   - 논문 Table 4 + §5.4 업데이트 완료 (5th finding: reasoning ≠ pattern blindness resolution)
2. ~~Human pilot 프로토콜 설계~~ ✅ (`docs/research/human-pilot/pilot-protocol.md`)
   - **다음 과제**: 실제 파일럿 실행 (IRB/instructor 승인 후, n=10~15 학부생)
3. ~~gpt-5.4-mini L4 ablation 완성~~ ✅ (n=50 완료, 논문 반영)
4. 논문 Section 3 (Method) 업데이트: taxonomy 형식화 재검토
5. o4-mini multitask T3 완료 (현재 n=5/20) + 논문 반영
6. o4-mini L4 pass 분석: variant E에서 reasoning model이 pattern blindness를 극복한 메커니즘 조사

## Links
- 로드맵: `docs/research/roadmap.md`
- 로그: `docs/research/log/` (`*_digest.md` 우선 참조)
- 상태: `docs/research/context-state.json`
- 압축 규칙: `docs/research/context-compression.md`
- 결과: `docs/research/results/`
- 논문형 문서: `docs/research/papers/`
- 최신연구 리뷰: `docs/research/literature/`
