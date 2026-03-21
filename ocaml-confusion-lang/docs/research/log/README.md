# Research Logs

이 디렉터리는 실험 반복 과정의 checkpoint를 남기는 공간입니다.

- 권장 파일명: `YYYY-MM-DD.md`
- 템플릿: `TEMPLATE.md`
- 원칙: 결과/명령/산출물 경로를 남겨 재현 가능성 확보

빠른 시작:

```bash
cp docs/research/log/TEMPLATE.md docs/research/log/$(date +%F).md
```

운영 권장:
- 의미 있는 변경 단위마다 한 줄이라도 누적 기록
- push 전에 `Commit / Push` 섹션 업데이트
- 실패/반례도 숨기지 말고 기록 (다음 iteration의 입력값)
