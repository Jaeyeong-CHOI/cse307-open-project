# CSE307 Open Project

Python 혼동 유도 언어(Confusion Language) 기반 LLM 코드 준수율 연구 저장소.

## What this repo does
- Python-like 변형 문법(alias)에서 LLM이 규칙을 지키는지 측정
- Python 원문법 회귀 패턴을 실험적으로 분석
- 교육 맥락에서 “생성코드 검수·수정” 학습효과를 연구

## Structure
- `web/` : 시연 UI (GitHub Pages)
- `ocaml-confusion-lang/` : OCaml 변환/검증 CLI
- `scripts/` : 평가 보조 스크립트
- `docs/` : 연구 문서 허브

## Start here
1. 문서 허브: `docs/README.md`
2. 연구 로드맵: `docs/research/roadmap.md`
3. 버전별 분석 문서: `docs/research/papers/`
4. 시연용 alias 세트: `docs/presets/final-demo-aliases.md`
5. OCaml 툴 빠른 실행:
   ```bash
   cd ocaml-confusion-lang
   dune exec confusionlang -- validate examples/case-c2.tsv
   dune exec confusionlang -- roundtrip examples/case-c2.tsv examples/sample.py
   ```

## Notes
- 과거 prompt 실험 기록은 `docs/archive/`에 보관
- 현재 활성 연구/운영 기준은 `docs/research/` 기준으로 유지
