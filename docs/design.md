# 설계 노트

## 언어 코어
- Expr:
  - 리터럴: int, bool
  - 연산자: +, -, *, <, ==
  - 제어: if-then-else
  - 바인딩: let x = e1 in e2
  - 함수: fun x -> e / e1 e2
  - 추적: emit(tag, value)

## Trace 모델
이벤트 스키마(JSON 유사):
- `{ step, event, node, value, envHash }`

핵심 이벤트 타입:
- `EvalStart(node)`
- `EvalEnd(node, value)`
- `BranchTaken(node, then|else)`
- `UserEmit(tag, value)`

## 과제 변형
`(student_id, assignment_id, salt)`가 주어지면:
- seed = hash(...) 계산
- 파라미터화된 상수/케이스 생성
- hidden test 부분집합 선택

## 검증 절차
1. 학생 제출물을 인터프리터로 실행
2. 관측 출력과 기대 출력 비교
3. trace 정책 검증:
   - 필수 이벤트 존재 여부
   - 이벤트 순서 제약 충족 여부
   - trace 해시의 정규화 규칙 일치 여부

## 리스크 / 한계
- trace 제약을 과도하게 걸면 창의적 구현이 불리해질 수 있음
- trace를 축약해도 패턴 정보가 남을 수 있음
- 엄격함과 교육적 유연성 사이의 균형이 필요함
