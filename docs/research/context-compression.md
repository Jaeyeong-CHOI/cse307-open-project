# 연구 컨텍스트 압축 전략 (cse307-open-project)

이 문서는 대화/메모/로그가 길어질 때 컨텍스트 사용량을 줄이기 위한 기준이다.

## 1) 메시지 보고 규칙
연구 진행 보고는 아래 항목만 고정 포맷으로 축약해서 전달한다.

- 진행도: `현재 진행도(%)`
- 핵심 이벤트(최대 3개)
- 지표 변화: `ACR/PRR/ESR` (변화 없으면 `변화 없음`)
- 차단요인(있으면 1개)
- Next action(1~2개)
- 최근 커밋 1개

예:
- 진행도: 79%
- 핵심: 1) … 2) … 3) …
- 지표: ACR=0.333, PRR=0.667, ESR=0.667
- 차단: LLM 실행 환경 미확보
- 다음: 1) … 2) …
- 최근 커밋: `xxxxxxx`

## 2) 저장 구조 분리
- `docs/research/context-state.json`: 현재 상태의 구조화 스냅샷(자동 갱신 대상)
- `docs/research/status.md`: 사람이 보는 대시보드
- `docs/research/log/YYYY-MM-DD_digest.md`: 일일 요약 로그
- `docs/research/log/YYYY-MM-DD.md`: 원본 상세 로그(필요 시만)

## 3) 컨텍스트 재생성 규칙
- 대화에서 상세 실행 로그는 참조 파일로 위임
- 메시지에서는 raw 로그를 반복 기재하지 않음
- 새 정보는 요약만 추가 (최대 5문장)
- 오래된 일일 로그는 월간/주간 덤프에 압축

## 4) 상태 갱신 주기
- 배치 성공/실패, 파일 누적 증가, 지표 갱신 시 state + status 동시 갱신
- `context-state.json`은 다음 키를 유지:
  - `updated_at`
  - `overall_progress_percent`
  - `phase`
  - `kpi`(ACR/PRR/ESR/MFB/LGP)
  - `artifact_count`
  - `active_blockers`
  - `next_actions`
  - `recent_commits`

## 5) 중복 방지
- 동일 메시지 반복 금지: 같은 run-id/status는 다시 알리지 않음
- 보고값이 바뀐 경우에만 요약 송출

## 6) 주간 청소
- 일주일 누적 로그는 `docs/research/log/YYYY-MM-DD_weekly.md` 또는 `docs/research/log/archive.md`로 옮김
- 월말에는 `memory/YYYY-MM-DD.md`로 핵심 의사결정만 반영
