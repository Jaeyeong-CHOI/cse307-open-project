# v1 Curated Literature (의미있는 항목만)

> 상태 라벨
> - ✅ 검토완료: 원문/설계/한계까지 확인
> - 🟡 1차검토: 핵심 주장 확인, 원문 세부 검토 진행중

---

## 1) (🟡 1차검토) 코딩 보조 AI가 디버깅 성과에 미치는 영향

- Source: Anthropic 연구 공유 자료(사용자 제공 스크린샷 기반 1차 확인)
- Claim (요약):
  - 주니어 개발자 집단에서 AI 사용군이 디버깅/과제 성과에서 낮은 점수를 보였다는 결과가 보고됨
  - 속도 이득은 일부 있으나 통계적으로 강하지 않거나 제한적
  - 작업 시간의 유의미한 비율이 AI 질의/프롬프트 조정에 사용됨
- Evidence strength: **Medium (원문 세부 검증 전)**
- Relevance to this project:
  - "LLM 사용이 즉시 생산성은 줄 수 있지만 스킬 형성에는 역효과 가능"이라는 가설을 강화
  - 본 프로젝트의 교육축(검수·수정 과정 유도)과 직접 연결
- How we integrate:
  1. 교육 실험에서 단순 정답률 외에 `Manual Fix Burden`, `이해도 전/후 변화` 지표 강화
  2. 프롬프트 의존 시간/수정 시간 분리 측정
  3. "빠름 vs 학습" trade-off 섹션을 논문형 문서(v2+)에 명시
- Limitations / caveats:
  - 현재는 스크린샷 기반 요약이며, 원문 실험 설계/샘플/통계 검증 필요
  - 외부 환경/참가자 숙련도에 따라 재현 결과가 달라질 수 있음

---

## 2) (✅ 검토완료) Alias 충돌과 규칙 준수율 해석의 관계 (내부 실험 설계 근거)

- Source: 본 프로젝트 내부 실패 로그 + alias preset 실험
- Claim:
  - `if/elif` 등 키워드에 동일 alias를 부여하면 역치환 모호성이 급증하고 결과 해석이 왜곡됨
- Evidence strength: **High (재현 가능)**
- Relevance to this project:
  - 모델 성능 문제와 설계 결함을 구분하기 위한 필수 통제 변수
- How we integrate:
  1. 모든 배치에서 1:1 alias 제약 강제
  2. 충돌 감지 실패 케이스는 모델 실패 통계에서 분리
- Limitations / caveats:
  - alias 설계 공간이 넓어 일반화에는 추가 실험 필요

---

## 3) (🟡 1차검토) 코드 생성 대형모델 계보

- Papers: Chen et al. 2021; Austin et al. 2021
- 핵심 claim: HumanEval/MBPP 중심의 성능 비교가 코드 생성 연구의 출발점이 되었으나, 변환 언어 제약 적응성 측정은 상대적으로 미비
- Relevance:
  - 본 연구의 지표 구조가 기존 pass@k 위주 평가에서 보완 지표(ACR/PRR/ESR)로 확장됨

---

## 4) (🟡 1차검토) 코드 이해/생성 사전학습 모델군

- Papers: CodeBERT, CodeT5, UniXcoder, InCoder
- 핵심 claim: 코드 표현 학습은 향상되었지만, alias 교체 규칙 준수 같은 명시적 문법 규약 적응은 별도 제약 레이어가 필요
- Relevance: 현재 파이프라인에서 provenance/roundtrip/스키마 검증을 결합한 이유의 이론적 근거

---

## 5) (🟡 1차검토) 실무형 과제 난이도(SWE-bench 계열)

- Paper: Jimenez et al. 2023\*\* \(SWE-bench\)
- 핵심 claim: 실제 GitHub 이슈 기반 문제는 단일 함수 합성보다 훨씬 어렵고, 실측 성능이 낮음
- Relevance: 본 연구에서 fixture 기반에서 실측 확장으로 넘어갈 때 필요한 상위 레벨 난이도 맥락

---

## 6) (🟡 1차검토) 제약 기반 생성(타입/규칙)

- Candidate: Mündler et al. 2025 Type-constrained decoding
- 핵심 claim: 타입/규칙 기반 디코딩으로 컴파일률/유효성 개선 가능성
- Relevance: 향후 confusion-language의 syntax+semantic 제약을 합치기 위한 다음 단계

---

## 다음 업데이트 계획
1. 선행연구 원문 링크 기준으로 각 항목을 DOI/저널 정보까지 정밀화
2. 코딩 학습 효과/디버깅 관련 실험 연구를 최소 3편 추가
3. `docs/research/papers/v2.md`와 Overleaf References를 정합되게 정리
