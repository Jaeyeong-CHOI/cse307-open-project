# Research Roadmap: Confusion-Inducing Python-like Language

## 0) Research Motivation
최근 LLM은 코드/수학 데이터 학습량 증가로 코딩 성능이 빠르게 향상되었고,
특히 Python 우선 생성 경향이 강함.
본 연구는 Python 유사 변형 문법(혼동 유도 언어)을 제시했을 때,
모델이 **지시된 변형 문법**을 따르는지, 혹은 **원본 Python 습관**으로 회귀하는지 비교·분석한다.

---

## 1) Core Questions
1. 모델은 변형 문법을 얼마나 정확히 준수하는가?
2. 어떤 키워드/구문에서 Python 회귀가 많이 발생하는가?
3. 프롬프트 설계(엄격 지시/예시 제공/단계적 변환)가 준수율에 미치는 영향은?
4. 학생 학습 관점에서 “검수·수정 과정”이 코드 이해도 향상에 기여하는가?

---

## 2) Experimental Axes
- **문법 변형 유형**: 키워드 alias, 구문 일부 치환, 복합 문장형 alias
- **모델군**: frontier/open 모델 혼합
- **프롬프트 조건**:
  - Base instruction
  - Strict instruction
  - Few-shot examples
  - Two-step conversion (alias→intermediate→python)
- **평가 단위**:
  - 키워드 단위 준수율
  - 프로그램 단위 컴파일/실행 성공률
  - Python 회귀 빈도
  - 오류 유형 분류(충돌/누락/부분 치환/연쇄 치환)

---

## 3) Metrics
- Alias Compliance Rate (ACR)
- Python Reversion Rate (PRR)
- Execution Success Rate (ESR)
- Manual Fix Burden (MFB): 사람이 고치기 위해 필요한 수정 횟수/토큰
- Learning Gain Proxy (LGP): 전/후 테스트 기반 이해도 변화(교육 실험 단계)

---

## 4) Work Packages
### WP1. Benchmark Set Construction
- 대표 Python 과제 셋 구성(기초/중급/자료구조/알고리즘)
- 정답 코드 + 테스트 케이스 + 변형 문법 정답셋 준비

### WP2. Prompting & Transformation Engine Validation
- alias 충돌 방지 규칙 강화
- single-pass 치환/문자열·주석 보호 검증
- 로그(중간 코드/최종 코드) 표준화

### WP3. Model Evaluation
- 동일 과제/동일 seed 조건 반복 평가
- 모델별·조건별 성능 표와 오류 매트릭스 작성

### WP4. Education Layer Study
- 학생 대상: 생성 코드 검수·수정 워크플로우 설계
- 사전/사후 코드 이해도 비교

---

## 5) 2-Week Initial Execution Plan
### Day 1-2
- 실험 스펙 고정, 평가 지표 정의, task set v1 확정
### Day 3-4
- 변형 문법 세트(A~E + variants) 안정성 검증
### Day 5-7
- 모델 1차 배치 평가 + 오류 로그 정리
### Day 8-10
- 프롬프트 조건 비교 실험(base/strict/few-shot/2-step)
### Day 11-12
- 결과 시각화, failure taxonomy 작성
### Day 13-14
- 중간 보고서 초안 + 다음 실험 backlog 정리

---

## 6) Update Policy (GitHub)
- 작업 단위별 커밋(문서/코드/실험결과 분리)
- 연속 작업 중에도 **의미 있는 변경 단위마다 즉시 커밋/푸시**
- 주기적 스냅샷:
  - `docs/research-log/YYYY-MM-DD.md`
  - `docs/results/*.json`
  - `docs/figures/*`

---

## 7) Cost Control Policy (GPT API 포함)
- 기본 원칙: **cheap-first, selective-escalation**
- 모델 사용 단계화:
  1. 문서 정리/포맷/기초 변환: 저비용 모델
  2. 실패 케이스 분석/정교한 비교: 중간 비용 모델
  3. 핵심 실험(샘플링된 일부 배치): 고성능 모델 제한 사용
- 호출량 제한:
  - 동일 프롬프트 반복 호출 금지
  - 배치당 샘플 수 상한 설정(예: task subset)
  - 실패 재시도 횟수 제한
- 비용 추적:
  - 실험 로그에 `model / calls / est. cost` 기록
  - 일/주간 soft cap를 넘기면 고성능 모델 호출 중단 후 저비용 모드 전환

---

## 8) Continuous Execution Mode (며칠 연속 작업)
- “매일 1회”가 아니라, **연속 세션 기반으로 backlog를 순차 처리**
- 실행 방식:
  1. TODO queue를 우선순위로 정렬
  2. 완료할 때마다 즉시 결과 반영 + 커밋
  3. 블로커 발생 시 우회 경로 먼저 수행
  4. 장시간 구간은 checkpoint 커밋으로 안정화
- 중단/재개 용이성 확보:
  - 각 단계 산출물 경로 고정
  - 로그에 다음 시작 포인트 명시

---

## 9) Immediate Next Actions
1. 실험 task set v1 파일 생성
2. metric schema JSON 정의
3. batch eval 스크립트 뼈대 작성
4. research log 템플릿 추가
