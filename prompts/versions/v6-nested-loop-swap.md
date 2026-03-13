# V6 - Nested Loop Pattern Swap

## [언어 설명]
Python 문법은 그대로 유지합니다.
키워드 별칭은 사용자가 원하는 문자열(공백 포함)로 설정할 수 있습니다.
실행 시에는 입력 코드에서 별칭을 감지하고, 변경된 키워드는 원본 Python 키워드와 같은 글자수의 난수 토큰을 거친 뒤 Python 원본 키워드로 변환해 실행합니다.

## 현재 설정 요약
- def --> case
- case --> def
- for --> match
- match --> for
- while --> return
- return --> while
- in --> no, use exact python original grammer

## [문제 설명]
아래 동작을 만족하는 코드를 작성하시오.
1) table(n) 함수를 정의하라.
2) 이중 for 반복문으로 1..n 곱셈표를 출력하라.
3) 각 행은 공백으로 구분된 문자열 형태로 출력하라.
4) table(5)를 호출하라.

## 관찰 포인트
- 중첩 반복문에서 블록 구조 안정성
- 함수 정의 + 반복 + 반환 규칙 충돌 시 복구 능력
