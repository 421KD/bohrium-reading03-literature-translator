# literature-translator

A Skill + companion scripts that translate a scientific paper into a bilingual, evidence-mapped result with a locked terminology glossary and automatic preservation verification.

## What it does

1. Extracts paragraphs in reading order with page/bbox/section provenance (reusing the layout-aware parser).
2. Proposes candidate domain terms (acronyms + repeated capitalized noun phrases).
3. Provides a glossary map that locks one Chinese 译名 per term.
4. Guides segment-by-segment translation that carries context and preserves numbers/units/formulas/references.
5. Verifies the translation: number/unit preservation, figure/table/equation/citation markers, negation/limitation logic, and glossary term consistency.

## Files

| Path | Purpose |
|---|---|
| `SKILL.md` | Skill definition + workflow |
| `src/translate_pdf.py` | Builds `scaffold.json` / `scaffold.md` (paragraphs + candidate terms + glossary template) |
| `src/verify_translation.py` | Checks `translation.json` and writes `verification.json` / `verification.md` |
| `src/parse_pdf.py` | Layout-aware PDF parser (bundled dependency) |
| `src/requirements.txt` | PyMuPDF |

## Usage

```bash
pip install -r src/requirements.txt
python3 src/translate_pdf.py paper.pdf out
# agent fills scaffold.glossary, translates each paragraph -> translation.json
python3 src/verify_translation.py translation.json out
```

## Output

- `scaffold.json` — paragraphs, sections, tables, figures, candidate terms, empty glossary, uncertainties.
- `scaffold.md` — bilingual alignment template.
- `translation.json` — the filled translation (produced by the agent).
- `verification.json` / `verification.md` — preservation + term-consistency issues.

## Limitations

- Translation is performed by the calling agent; the scripts handle structure and verification.
- Term candidates are heuristic; the agent curates the final glossary.
- Formulas/tables embedded as images are flagged, not reconstructed.
- Scanned PDFs (no text layer) are flagged for OCR.

## Self-check

Confirm: one term = one 译名 everywhere; segment ids map 1:1 to source paragraphs; numbers/units/references/logic markers survive; every segment carries page + source.
