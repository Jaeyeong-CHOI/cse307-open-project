# Overleaf-Compatible Paper Package

## Author metadata
- Name: **Jaeyeong CHOI**
- Affiliation: **DGIST EECS**
- Email: **jaeyeong2022@dgist.ac.kr**

## Files
- `main.tex` : paper entrypoint
- `refs.bib` : bibliography
- `sections/*.tex` : section files

## Overleaf usage
1. Upload entire `paper/overleaf/` folder to Overleaf project root
2. Set `main.tex` as Main Document
3. Compile with pdfLaTeX (or latexmk default)

## Local build (optional)
If TeX is installed locally:
```bash
cd paper/overleaf
latexmk -pdf -interaction=nonstopmode main.tex
```
Output PDF: `paper/overleaf/main.pdf`
