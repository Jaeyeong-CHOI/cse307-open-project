# Hard Cases by Prompt-Spec Review

아래 목록은 실패표가 아니라 `prompt-versions` 원본 md를 직접 보고,
**상대적으로 쉬운 케이스를 제외한 최상위 난이도 케이스만** 남긴 결과입니다.

| Rank | Prompt | HardScore | Why Hard | Settings |
|---:|---|---:|---|---|
| 1 | `v29.md` | 16 | long alias 4, keyword collision 2, duplicate targets 2 | def --> return<br>in --> apply this mapped token before generating code<br>for --> apply this mapped token before generating code<br>return --> apply this mapped token before generating code<br>if --> if<br>print --> use this custom marker in place of original token |
| 2 | `v65.md` | 14 | long alias 5, duplicate targets 2 | in --> strictly follow this alias phrase for compilation<br>def --> go<br>for --> convert this phrase back to python reserved token<br>return --> strictly follow this alias phrase for compilation<br>if --> no, use exact python original grammer<br>elif --> no, use exact python original grammer |
| 3 | `v55.md` | 14 | long alias 4, keyword collision 1, duplicate targets 2 | if --> return<br>in --> apply this mapped token before generating code<br>def --> qn<br>for --> apply this mapped token before generating code<br>return --> keep this long alias while preserving python grammar<br>print --> apply this mapped token before generating code |
| 4 | `v25.md` | 14 | long alias 4, keyword collision 1, duplicate targets 2 | for --> def<br>in --> apply this mapped token before generating code<br>def --> apply this mapped token before generating code<br>return --> do not trust default python keyword prior<br>if --> apply this mapped token before generating code |
| 5 | `v120.md` | 14 | long alias 3, keyword collision 2, duplicate targets 2 | def --> for<br>in --> this keyword is replaced by long natural phrase<br>for --> convert this phrase back to python reserved token<br>return --> for<br>if --> convert this phrase back to python reserved token |
| 6 | `v112.md` | 14 | long alias 4, keyword collision 2, duplicate targets 1 | for --> if<br>in --> no, use exact python original grammer<br>def --> apply this mapped token before generating code<br>return --> use this token exactly for keyword mapping<br>if --> def<br>else --> no, use exact python original grammer |
