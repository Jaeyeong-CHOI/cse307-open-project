# Roundtrip Batch Result Report (fixture-task-set-v1)

- 생성 시각(UTC): 2026-03-23T05:07:39Z
- task_set_id: `fixture-task-set-v1`
- prompt_condition: `strict`
- model: `gpt-5.3-codex`

## Metrics (v1)
- ACR: **0.333**
- PRR: **0.667**
- ESR: **0.667**
- MFB: **65.0**
- LGP: **0.667**

## Interpretation (quick)
- 현재 fixture 기준으로 alias 준수율(ACR)이 낮고, Python 회귀율(PRR)이 높은 편이다.
- 실행 성공률(ESR)은 0.667 수준으로, 완전 실패는 아니지만 안정적 성공으로 보기 어렵다.
- 이는 “모델이 혼동 유도 문법보다 기존 Python 습관으로 회귀하는 경향” 가설과 일치한다.

## Source Files
- `roundtrip-batch-v1.fixture.summary.md`
- `roundtrip-batch-v1.fixture.summary.csv`
- `roundtrip-batch-v1.fixture.summary.json`
- `roundtrip-batch-v1.fixture.metrics.json`
