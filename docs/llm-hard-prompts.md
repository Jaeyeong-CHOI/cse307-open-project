# LLM Hard Prompts (Curated)

기준: `docs/prompt-eval-results.json` + `docs/prompt-failures-table.md`를 리뷰해,
**파싱 실패(syntax error) 또는 키워드 prior 회귀가 반복적으로 발생한 케이스**만 선별.

## Selection Criteria
- **Hard-1 (Critical):** 정규화 후 Python parse 실패
- **Hard-2 (High):** 원본 키워드 회귀가 2개 이상 동시 발생
- **Hard-3 (Notable):** 긴 자연어 alias가 문법 슬롯을 오염시켜 구조 붕괴

---

## A. Critical (Parse Failure 중심)

1. `docs/prompt-versions/v8.md`
- 사유: `in` alias 미적용 + 정규화 후 parse 실패
- 관찰: 자연어 alias + 루프 문맥에서 문법 슬롯 붕괴

2. `docs/prompt-versions/v10.md`
- 사유: `if` 회귀 + 정규화 후 parse 실패
- 관찰: 조건문 위치에서 alias 복원 실패

3. `docs/prompt-versions/v18.md`
- 사유: `def` 원본 사용 + 1행 parse 실패
- 관찰: 함수 헤더 단계에서 즉시 붕괴

4. `docs/prompt-versions/v20.md`
- 사유: `if` 회귀 + `in` alias 누락 + parse 실패
- 관찰: 조건/반복 축 동시 오류

5. `docs/prompt-versions/v23.md`
- 사유: `for` 회귀 + parse 실패
- 관찰: 반복문 재구성 단계 불안정

6. `docs/prompt-versions/v24.md`
- 사유: `return` 회귀 + parse 실패(괄호/구문 문제)
- 관찰: 반환문 매핑에서 구조 손상

7. `docs/prompt-versions/v36.md`
- 사유: `return`, `for` 회귀 + parse 실패(콜론 누락 유형)
- 관찰: 블록 경계 기호 처리 취약

8. `docs/prompt-versions/v40.md`
- 사유: `for` 회귀 + parse 실패
- 관찰: 루프 헤더 문법 슬롯 교란

9. `docs/prompt-versions/v41.md`
- 사유: `for` 회귀 + parse 실패
- 관찰: 긴 alias 문구를 토큰처럼 처리하지 못함

10. `docs/prompt-versions/v47.md`
- 사유: `def`, `if` 회귀 + 1행 parse 실패
- 관찰: 초반 prior 회귀 후 복구 불가

11. `docs/prompt-versions/v49.md`
- 사유: `for` 회귀 + 1행 parse 실패
- 관찰: 시작 토큰이 오염되면 전체 생성 실패

---

## B. High (Prior 회귀 강함)

12. `docs/prompt-versions/v1.md`
- 사유: `if`, `return`, `for` 원본 키워드 동시 회귀
- 관찰: 기본 Python prior로 강한 복귀

13. `docs/prompt-versions/v2.md`
- 사유: `def`, `if` alias 누락 + 원본 사용
- 관찰: alias 지시보다 표준 문법을 우선

14. `docs/prompt-versions/v16.md`
- 사유: `if`, `return`, `for` 원본 사용
- 관찰: 다중 키워드 동시 회귀

15. `docs/prompt-versions/v25.md`
- 사유: `def`, `if` alias 누락 + 원본 사용
- 관찰: 템플릿형 정답 회귀

---

## 추천 사용 방식
- 데모/실험 시에는 위 15개만 우선 사용 (noise 대비 실패 재현률 높음)
- 보고서에는 A그룹(파싱 실패) 3개 + B그룹(회귀 실패) 2개를 대표 사례로 제시
- 향후 확장 시, 동일 기준(Hard-1~3)으로만 추가

