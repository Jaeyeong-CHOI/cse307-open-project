# v3 - Prime Check

[언어 설명]
Python 문법은 그대로 유지합니다.
키워드 별칭은 사용자가 원하는 문자열(공백 포함)로 설정할 수 있습니다.
실행 시에는 입력 코드에서 별칭을 감지하고, 변경된 키워드는 원본 Python 키워드와 같은 글자수의 난수 토큰을 거친 뒤 Python 원본 키워드로 변환해 실행합니다.

현재 설정 요약:
if --> branch
elif --> branch2
else --> otherwise
def --> make
for --> scan
in --> member token
return --> out

[문제 설명]
[문제] 정수 x가 소수인지 판별하는 코드를 작성하시오.
1) is_prime(x) 함수를 정의하라.
2) x <= 1이면 False를 반환하라.
3) 2부터 sqrt(x)까지 나누어 떨어지는 수가 있으면 False를 반환하라.
4) 없으면 True를 반환하고, x=2, 9, 17 결과를 출력하라.
