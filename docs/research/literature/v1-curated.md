# v1 Curated Literature (의미있는 항목만)

> 상태 라벨
> - ✅ 검토완료: 원문/설계/한계까지 확인
> - 🟡 1차검토: 핵심 주장 확인, 원문 세부 검토 진행중

---

## 1) (🟡 1차검토) 코딩 보조 AI가 디버깅 성과에 미치는 영향 연구

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

## 2) (✅ 검토완료) Alias 충돌과 규칙 준수율 해석의 관계 (내부 실험 설계 지식)

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

## 다음 업데이트 계획
1. Anthropic 원문/공개 자료 링크 기준으로 실험 설계·통계 항목까지 검증 후 상태를 ✅로 승격 또는 제외
2. 코딩 학습 효과 관련 최신 연구를 동일 템플릿으로 최소 3건 추가
3. `docs/research/papers/v2.md`의 Related Work 섹션에 반영
