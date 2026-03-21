# v1 Summary Result Sheet

- 버전: v1
- 성격: 초기 파이프라인 구축 결과 (정량 대규모 평가 전)

## 구현 완료 항목
- [x] alias 1:1 검증(필수 키 + 중복 감지)
- [x] transform (Python -> alias)
- [x] roundtrip (Python -> alias -> Python)
- [x] mismatch 첫 diff 라인 출력

## 미완료 항목
- [ ] 모델별 배치 평가 자동화
- [ ] ACR/PRR/ESR 집계 JSON 자동 생성
- [ ] 실패 taxonomy 자동 라벨링

## 재현 메모
현재 환경에서 `dune` 미설치 시 OCaml 실행 검증이 제한될 수 있음.
(도구체인 자체는 repo 내 구현 완료)
