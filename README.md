# TraceLang + GuardLab (CSE307 오픈 프로젝트)

부정행위(치팅)에 강한 과제용 프로그래밍 언어 및 프로그래밍 환경 프로젝트입니다.

## 배경
기존 프로그래밍 과제는 다음 문제에 취약합니다.
- AI가 생성한 정답 코드의 직접 제출
- 코드 공유 및 피상적 변형
- 풀이 과정을 보지 않는 결과 중심 채점

이 프로젝트는 **과정 인지형(process-aware) 채점 모델**을 제안합니다. 즉, 학생은 실행 결과뿐 아니라 실행 추적(trace)도 함께 제출해야 합니다.

## 핵심 아이디어
- **TraceLang**: 필수 추적 이벤트를 포함한 소형 언어
- **GuardLab**: 학생별 seed 기반 변형 과제 환경
- **Verifier**: 출력값 + trace 정합성 검증기

## 상위 아키텍처
1. **Generator**: 공통 템플릿에서 학생별 과제 인스턴스 생성
2. **Interpreter**: TraceLang 실행 및 구조화된 trace 생성
3. **Verifier**: 의미적 정답성과 trace 제약 동시 검사
4. **Feedback**: trace 기준 최초 실패 지점을 안내

## MVP 범위
- 최소 TraceLang 문법(산술, let, if, 함수)
- `emit(tag, value)` 추적 원시 연산
- seed 기반 테스트/제약 변형
- output+trace 검증용 CLI verifier

## 저장소 구조
- `docs/proposal.md` – 1페이지 프로젝트 제안서
- `docs/design.md` – 상세 설계 및 평가 계획
- `src/` – OCaml 프로토타입 스켈레톤
- `demo/` – 시연 시나리오

## 다음 단계
1. TraceLang 구문/의미 확정
2. OCaml 파서/인터프리터 스켈레톤 구현
3. hidden test + trace 검사 포함 verifier 구현
4. 데모 및 평가 결과 정리

## 웹 데모
간단한 데모 UI는 `web/index.html`에 포함되어 있습니다.

로컬 실행:
```bash
cd web
python3 -m http.server 8080
# 브라우저에서 http://localhost:8080 접속
```

데모에서 확인 가능한 기능:
- seed 기반 과제 변형 생성
- output + trace 인지형 검증 로직

## OCaml ↔ 웹 브리지 (데모)
OCaml 스텁으로 샘플 제출 JSON을 생성한 뒤 웹 UI에서 업로드할 수 있습니다.
```bash
./scripts/generate_sample_submission.sh
# 이후 브라우저에서 demo/submission.json 업로드
```

## GitHub Pages
`.github/workflows/pages.yml` 워크플로가 포함되어 있습니다.
저장소 설정에서 Pages를 활성화하면 `web/` 폴더가 자동 배포됩니다.
