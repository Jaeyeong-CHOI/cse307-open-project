#!/usr/bin/env python3
import random
from pathlib import Path

OUT_DIR = Path('docs/archive/prompt-versions')
OUT_DIR.mkdir(parents=True, exist_ok=True)

LANG = """[언어 설명]
Python 문법은 그대로 유지합니다.
키워드 별칭은 사용자가 원하는 문자열(공백 포함)로 설정할 수 있습니다.
실행 시에는 입력 코드에서 별칭을 감지하고, 변경된 키워드는 원본 Python 키워드와 같은 글자수의 난수 토큰을 거친 뒤 Python 원본 키워드로 변환해 실행합니다.
"""

PROBLEM = """[문제 설명]
[문제] 아래 동작을 만족하는 코드를 작성하시오.
1) fib(n) 함수를 정의하라.
2) n <= 1 이면 n을 반환하라.
3) 그 외에는 fib(n-1) + fib(n-2)를 반환하라.
4) for 반복문으로 i = 0..6까지 순회하며 print(i, fib(i))를 출력하라.
"""

PY_KWS = ["def","if","elif","else","for","while","in","return","print","range"]
SHORT = ["if","for","def","ret","loop","cond","fn","out","go","do","xk","qn"]
LONG = [
"no, use exact python original grammer",
"use this token exactly for keyword mapping",
"do not trust default python keyword prior",
"follow renamed symbol exactly and continue",
"this keyword is replaced by long natural phrase",
"apply this mapped token before generating code",
"use this custom marker in place of original token",
"strictly follow this alias phrase for compilation",
"convert this phrase back to python reserved token",
"keep this long alias while preserving python grammar",
]


def make_alias_map(rng: random.Random):
    keys = ["def","for","in","return","if"]
    m = {}
    # short swaps
    if rng.random() < 0.7:
      a,b = rng.sample(["def","for","if","return"],2)
      m[a]=b
    # always include in long style often
    if rng.random() < 0.85:
      m["in"] = rng.choice(LONG)
    # fill others mixed
    for k in keys:
      if k in m: continue
      if rng.random() < 0.5:
        m[k] = rng.choice(SHORT)
      else:
        m[k] = rng.choice(LONG)
    # add one extra occasionally
    if rng.random() < 0.4:
      extra = rng.choice([x for x in PY_KWS if x not in m])
      m[extra] = rng.choice(SHORT+LONG)
    return m


def write_case(idx:int, amap:dict):
    lines = [f"- {k} --> {v}" for k,v in amap.items()]
    txt = f"# v{idx} - Fibonacci / Mixed Alias Setting\n\n{LANG}\n현재 설정 요약:\n" + "\n".join(lines) + "\n\n" + PROBLEM
    (OUT_DIR / f"v{idx}.md").write_text(txt)


def main(total=120, seed=307):
    rng = random.Random(seed)
    for i in range(1,total+1):
      write_case(i, make_alias_map(rng))

    # rewrite index readme
    readme = ["# Prompt Versions","",f"자동 생성된 프롬프트 버전 v1~v{total}",""]
    for i in range(1,total+1):
      readme.append(f"- `docs/prompt-versions/v{i}.md`")
    (OUT_DIR / 'README.md').write_text("\n".join(readme)+"\n")

    # NOTE: do not overwrite repository root README from this script.
    # Prompt versions are archived under docs/archive/prompt-versions.

if __name__ == '__main__':
    main()
