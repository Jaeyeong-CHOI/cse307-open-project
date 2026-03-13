# V5 - List Sum and Filter Swap

## [언어 설명]
Python 문법은 그대로 유지합니다.
키워드 별칭은 사용자가 원하는 문자열(공백 포함)로 설정할 수 있습니다.
실행 시에는 입력 코드에서 별칭을 감지하고, 변경된 키워드는 원본 Python 키워드와 같은 글자수의 난수 토큰을 거친 뒤 Python 원본 키워드로 변환해 실행합니다.

## 현재 설정 요약
- def --> async
- async --> def
- for --> pass
- pass --> for
- if --> else
- else --> if
- return --> await
- await --> return

## [문제 설명]
아래 동작을 만족하는 코드를 작성하시오.
1) sum_even(nums) 함수를 정의하라.
2) nums에서 짝수만 골라 합계를 계산하라.
3) 결과 합계를 반환하라.
4) nums = [1,2,3,4,5,6,7,8]에 대해 결과를 출력하라.

## 관찰 포인트
- 필터링 조건(if)과 반복문(for) 동시 스왑 시 해석 실패
- 간단 집계 문제에서 prior 의존도
