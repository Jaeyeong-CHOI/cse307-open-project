# scripts

연구 보조 스크립트 모음.

- `generate_prompt_cases.py` : 프롬프트 케이스 생성
- `run_gpt54_eval.py` : 모델 평가 실행(비용 주의)

## 원칙
- 대량 API 호출 전 샘플 배치로 dry-run
- 결과는 `docs/research/results/`에 저장
- 같은 조건 반복 호출 금지 (비용 통제)
