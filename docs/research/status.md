# Research Live Status

마지막 업데이트: 2026-03-25 09:20 KST

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

- [x] 2026-03-25 06:29 §9 experiment log (E12-E15) + §10 config snapshot stale text 수정
  - E12: gpt-4.1 family + o4-mini L1 ctx-pack (2026-03-25 실험 추가)
  - E13/E14: L4 ablation n=50, all 7 models
  - E15: L4 multi-task (225 runs)
  - §10 모델 목록 7개로 업데이트, o4-mini temp=1 명시
  - PDF 재컴파일 (10p), commit 115272d push 완료

- [x] 2026-03-25 06:20 §3 Threats to Validity stale text 수정
  - "single benchmark task → multi-task extension needed" → 이미 완료(T1/T2/T3)로 수정
  - "GPT-family" → "OpenAI-family" 정확도 개선
  - PDF 재컴파일(10p), commit 321759e push 완료

- [x] 2026-03-25 07:10 Scale-up 실험: gpt-4o T3(count_vowels) n=50 + gpt-4.1 T2(is_sorted) n=50
  - **gpt-4o T3 n=50**: 0/50 pass, OpSub=47/50 (94%, Wilson 95% CI: [83%,99%]) — operational substitution이 압도적 dominant failure mode 확인
    - 기존 n=10 결과(1 pass)는 statistical artifact — n=50에서 0/50 (Wilson CI: [0%, 7.1%])
  - **gpt-4.1 T2 n=50**: 1/50 pass, PPR=0.42 (Wilson CI: [29%,56%])
    - gpt-4.1-mini 20/20 대비 within-family inconsistency 통계적으로 확인 (Fisher's exact p < 0.0001)
  - 논문 §5 Table 4 업데이트 (n 정정, Wilson CIs 각주, Fisher's exact 추가)
  - 논문 §5 findings (3)(6) 업데이트, Three Failure Modes 섹션 강화
  - 논문 §6.3 Limits / §6.4 Next steps operational substitution 서술 업데이트
  - 논문 §4 multi-task runs 325 total 업데이트
  - PDF 재컴파일(10p), commit 35aab33 push 완료
  - 산출물: `L4-scaleup-count_vowels.gpt4o.n50.2026-03-25.json`, `L4-scaleup-is_sorted.gpt41.n50.2026-03-25.json`
  - 신규 스크립트: `scripts/run_targeted_scaleup.py`

- [x] 2026-03-25 07:59 gpt-5.4-mini L4 multi-task 완료 (n=30, 0/30)
  - T1 fib: 0/10, PPR=1.0 (prior dominance); T2 sorted: 0/10, PPR=1.0 (prior dominance)
  - T3 vowels: 0/10, PPR=0.0 (operational substitution — 동일 패턴 across capable models)
  - 논문 Table 4: 6 models → 7 models (7번째 finding 추가), runs 325 → 355
  - scripts/run_l4_multitask.py: COMPLETION_TOKEN_MODELS 추가 (gpt-5.4-mini fix)
  - PDF 재컴파일(10p), commit f20befa push 완료

- [x] 2026-03-25 09:00 o4-mini T1 multi-task 결과 수정 (token budget 버그 수정)
  - `scripts/run_l4_multitask.py`: reasoning model max_completion_tokens 400→5000
  - `L4-multitask.o4mini.2026-03-25.json`: T1_fib **0/15→8/15** (53% pass, noticed_inversion=True)
  - 논문 Table 4: o4-mini T1 row 수정 (8/15, PPR=0.33)
  - Finding (2): "모든 모델 T1 실패" → "reasoning model은 partially-annotated에서 성공"
  - Finding (5): "reasoning이 pattern blindness 극복 못함" → "partial annotation에서는 부분적 완화"
  - §6.2 education: o4-mini T1 예외 반영
  - `sec:l4_ablation` label 추가 (undefined ref 경고 수정)
  - PDF 재컴파일(11p), commit 0d15882 push 완료
  - **핵심 인사이트**: o4-mini는 token 공간이 충분하면 partial annotation에서 추론 능력으로 inversion 파악 가능 (dense 모델은 불가)

- [ ] `docs/research/context-compression.md` 운영 적용

- [x] 2026-03-25 03:45 o4-mini L4 multitask 완료 (n=45, 0/45)
  - T1 fib: 0/15, T2 sorted: 0/15, T3 vowels: 0/15 (all PPR=0.00)
  - reasoning model도 L4 pattern blindness 극복 못함 확인
  - 논문 Table 4 (l4_multitask) o4-mini 행 추가, §5.4 5번째 finding 추가
  - PDF 재컴파일 완료 (9 pages), commit 643ebf9 push 완료

- [x] 2026-03-25 05:15 L4 ablation gpt-4.1/gpt-4.1-nano n=20→n=50 확장 완료
  - gpt-4.1: 0/50, PPR=1.0 (모든 variant A-E, 완전 prior dominance)
  - gpt-4.1-nano: 0/50, PPR=1.0 (모든 variant A-E, 완전 prior dominance)
  - Table 3 업데이트 (n 정정, 캡션), PDF 재컴파일(10p), commit b0b3bd3 push 완료
  - Total L4 ablation: 6×50 + o4-mini×20 = 320 runs
- [x] 2026-03-25 05:57 o4-mini L4 ablation n=20→n=50 스케일업 완료
  - o4-mini: 0/50 pass, PPR=0.92 (이전 1/20 preliminary → 통계 아티팩트 확인)
  - 전 7모델 n=50 균일 달성 (350 total L4 ablation runs)
  - Table 3 업데이트, §4/§5.2/§6.2 수정, PDF 재컴파일(10p), commit 132dc13 push

- [x] 2026-03-25 05:49 논문 stale model count 수정 (five→seven) + L3 success 모델 명시 (gpt-4.1-mini 추가)
  - main.tex abstract, §3 Threats, §1 Introduction 업데이트
  - PDF 재컴파일 (10p), commit 22fcf3c push 완료

- [x] 2026-03-25 gpt-4.1 family + o4-mini 실험 추가 (L1 + L4)
  - **L1 ctx-pack (n=20, v1-v20)**: gpt-4.1 (KLR=0.295), gpt-4.1-mini (KLR=0.210), gpt-4.1-nano (KLR=0.378), o4-mini (KLR=0.265)
  - **L4 ablation (n=20, 5×4)**: gpt-4.1 (PPR=1.0, 0/20), gpt-4.1-nano (PPR=1.0, 0/20), o4-mini (PPR=0.95, **1/20 pass** — first L4 pass from reasoning model)
  - o4-mini requires temperature=1 (API constraint); patched scripts used
  - gpt-4.1-mini ctx-pack achieved lowest KLR (0.21) across all models
  - 논문 Table 1 (L1), Table 3 (L4 ablation) 업데이트, 재컴파일 완료 (9p)
  - 산출물: `l1-gpt41-contextpack-2026-03-25.json`, `l1-gpt41mini-contextpack-2026-03-25.json`, `l1-gpt41nano-contextpack-2026-03-25.json`, `l1-o4mini-contextpack-2026-03-25.json`, `L4-ablation-n50.gpt41.2026-03-25.json`, `L4-ablation-n50.gpt41nano.2026-03-25.json`, `L4-ablation-n50.o4mini.2026-03-25.json`

## Immediate Next Actions
1. ~~**Multi-task 실험 설계 및 실행**~~ ✅ (6 모델 완료: gpt-4o, gpt-4o-mini, gpt-4.1, gpt-4.1-mini, gpt-4.1-nano, o4-mini)
   - 논문 Table 4 + §5.4 업데이트 완료 (6th finding: within-family non-monotonic capacity)
   - 2026-03-25 05:10: gpt-4.1/gpt-4.1-nano 추가, 225 total multi-task runs (up from 165)
2. ~~Human pilot 프로토콜 설계~~ ✅ (`docs/research/human-pilot/pilot-protocol.md`)
   - **다음 과제**: 실제 파일럿 실행 (IRB/instructor 승인 후, n=10~15 학부생)
3. ~~gpt-5.4-mini L4 ablation 완성~~ ✅ (n=50 완료, 논문 반영)
4. 논문 Section 3 (Method) 업데이트: taxonomy 형식화 재검토
5. o4-mini L4 pass 분석: variant E에서 reasoning model이 pattern blindness를 극복한 메커니즘 조사

## Links
- 로드맵: `docs/research/roadmap.md`
- 로그: `docs/research/log/` (`*_digest.md` 우선 참조)
- 상태: `docs/research/context-state.json`
- 압축 규칙: `docs/research/context-compression.md`
- 결과: `docs/research/results/`
- 논문형 문서: `docs/research/papers/`
- 최신연구 리뷰: `docs/research/literature/`

- [x] 2026-03-25 07:17 §9 실험 로그 E16 추가 + 레포지토리 구조 표 보완
  - E16: gpt-4o T3 n=50 (OpSub 94%), gpt-4.1 T2 n=50 (1/50) scale-up 정식 기록
  - `run_targeted_scaleup.py` 포함하여 스크립트 목록 완성
  - multi-task 총 run 수 225→325 정정
  - PDF 재컴파일(10p), commit 43d1a98 push 완료

- [x] 2026-03-25 07:27 논문 전체 데이터 정합성 검증 완료 (자동 cron tick)
  - 실험 결과 JSON vs 논문 수치 교차 검증: 전체 일치 확인
    - gpt-4o T2: 10/10 ✓, gpt-4.1-mini T2: 20/20 ✓, gpt-4.1 T2 n=50: 1/50 PPR=0.42 ✓
    - gpt-4o T3 n=50: 0/50, OpSub 47/50(94%) ✓
    - o4-mini multitask: 0/45 ✓
    - gpt-4.1-nano T1 PPR=0.20 ✓, gpt-4.1 T1 PPR=1.0 ✓
    - L4 ablation 350 total runs ✓, multi-task 325 total runs ✓
  - Paper placeholder 없음 확인 (TODO/FIXME 없음)
  - Current state: 논문 10p, 모든 수치 실측값 기반, 과도한 주장 없음
  - 다음 우선 과제: Human pilot 실행 (IRB/instructor 승인 후)

- [x] 2026-03-25 09:20 critic report (09:08) 기반 논문 수정 (M2/M8/C2/W2)
  - **M2**: gpt-5.4-mini var-E PPR=1.0† → N/A (n_eff=2; excluded) 수정; Overall PPR footnote 추가
  - **C2**: Table 4 caption에 bold 경고 추가 ("not directly comparable to Table 3 (strict example-only)")
  - **M8**: abstract에 multi-task 355 runs + 700+ total L4 runs 수치 추가
  - **W2**: L1 "scale does not predict" → "model-family-specific compliance patterns"으로 완화; training corpus hypothesis 명시적 가설로 표시
  - PDF 재컴파일 (11p), commit 17cac4e push 완료

- [x] 2026-03-25 09:32 Table 2 + L2/L3 subsections 업데이트 (새 n=20 실측 데이터 반영)
  - **Table 2 확장**: L2 gpt-4o/gpt-4.1-mini/gpt-4.1-nano 20/20 행 추가, L3 동일 3모델 20/20 행 추가
  - **핵심 contrast 단락 추가**: gpt-4.1-nano L3 20/20 → L4 0/50 (PPR=1.0) within-model 대비
    - 동일 모델이 명시적 rule에서는 완벽 성공, example-only에서는 완전 실패
    - Pattern blindness가 rule-following 능력과 독립적인 실패 모드임을 직접 증명
  - **§5.2 L2**: "all models" → "4 evaluated models (n=20 each)" 정확도 개선
  - **§5.3 L3**: gpt-4.1-nano 추가, key contrast 단락 신설
  - **.env → .gitignore** 추가 (GitHub secret scanning push protection 대응)
  - PDF 재컴파일(11p), commit ea3568e push 완료

- [x] 2026-03-25 09:45 Batch experiments + paper fixes
  - **L2 expansion (n=20 each)**: gpt-4o 20/20, gpt-4.1-mini 20/20, gpt-4.1-nano 20/20 (all SIR=0.0)
  - **L3 expansion (n=20 each)**: gpt-4o 20/20, gpt-4.1-mini 20/20, gpt-4.1-nano 20/20 (all PPR=0.0)
    - gpt-4.1-nano L3 success (20/20) is surprising; confirms explicit rule sufficient even for smallest model
  - **o4-mini L4 T2/T3 (n=20 each)**: T2 0/20 (PPR=0.30), T3 0/20 (PPR=0.00) — consistent with prior
  - **CoT ablation (n=20 per condition, 2 models)**:
    - gpt-4o: no_cot 0/20 (PPR=1.0), cot 0/20 (PPR=0.15, mentions_inv=100%)
    - gpt-4.1-mini: no_cot 0/20 (PPR=0.4), cot 0/20 (PPR=0.0, mentions_inv=100%)
    - **Key finding**: reasoning--generation dissociation; models articulate inversion in CoT but still generate Python prior
  - **Failure taxonomy (419 failed L4 runs)**: Type-I 83.1%, Type-II 12.6%, Type-III 4.3%
  - **Paper updates**: Table 4 pivoted to model×task matrix, CoT ablation section added, abstract updated (780+ L4 runs), ACL format draft created
  - **ACL format**: `main_acl.tex` + `acl.sty` (minimal wrapper)
  - New scripts: `run_l3_eval.py`, `run_l4_cot_ablation.py`, `categorize_failures.py`
  - PDF 재컴파일(11p)

- [x] 2026-03-25 09:36 Open-weight 결과 + o4-mini T2/T3 scale-up 논문 반영 (commit dbe002d)
  - **Table 1 확장**: Llama-3.3-70B (KLR=0.23, PSS=0.34), Qwen3-32B (KLR=1.00, PSS=0.00) 추가
    - KLR 오름차순 정렬; open-weight 모델 ★ 각주 표기
    - Qwen3-32B가 전체 모델 중 최악 KLR (1.00); Llama는 OpenAI 최선과 유사 (0.21 vs 0.23)
  - **새 §5.6 (Open-Weight Preliminary)**: L1 + L4 Variant A 결과 서술
    - Llama PPR=0.05 (0/20), Qwen PPR=1.00 (0/20) → pattern blindness cross-family 확인
    - L1 family variance (0.23 vs 1.00) > gpt-4.x 내부 분산 (0.21–0.69)
    - "architecture/fine-tuning > parameter count" 결론 추가
    - Limitations 절 명시 (n=20, Variant A only, Groq API)
  - **o4-mini T2/T3 scale-up**: n=15→20 반영, T2 PPR=0.30, T3 PPR=0.00
    - Table 4 행 + 각주 $^\P$ 추가; finding (5) 텍스트 수정
    - Multi-task 총 runs: 355→395
  - **Abstract**: "9 models (7 OpenAI, 2 open-weight)", L1 variance 언급으로 업데이트
  - 산출물: `l1-llama33-70b-*`, `l4-ablation-groq-llama33-70b-*`, `l1-qwen3-32b-*`, `l4-ablation-groq-qwen3-32b-*`, `l4-multitask-o4mini-T2T3-n20-*` JSON 커밋
  - PDF 재컴파일: 12p, 0 errors, commit dbe002d push 완료
  - 다음 우선 과제: Qwen3-32B L2/L3 실험 (capacity threshold 비교), Llama L4 full ablation (n=50, Variant A–E)
