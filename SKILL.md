---
name: literature-translator
description: Translate a scientific paper PDF into a bilingual, evidence-mapped result with a locked terminology glossary, paragraph-level source/translation alignment, and automatic preservation verification. Use when the task requires translating, bilingual-alignment, or terminology-consistent rendering of a research paper.
---

# Literature Translator

Translate a research paper into a bilingual, verifiable result. The goal is not a fluent paraphrase, but a segment-aligned translation where terminology is locked, structure is complete, numbers/formulas/references survive, and every translation points back to the source.

## When to use

Use this Skill when the input is a scientific PDF and the task asks for translation, bilingual alignment, terminology-consistent rendering, or a translation with source evidence. Do **not** use it to summarise or to change the paper's claims.

## Inputs

Read `/input/case.json` and `task.md` first, then the actual PDF. Record the output_contract fields and `case_id`. Never assume the paper's content from its filename or topic labels.

## Workflow

### 1. Inventory
List `/input`, read `case.json` + `task.md`, and locate the PDF and any required output contract.

### 2. Build the translation scaffold
```bash
python3 src/translate_pdf.py /input/<paper>.pdf /app/work/scaffold
```
This emits `scaffold.json` (paragraphs in reading order with page/bbox/section provenance, candidate terms, an empty glossary map, tables, figures, uncertainties) and `scaffold.md`.

### 3. Build and lock the glossary (术语稳)
From `candidate_terms`, select the domain terms and assign each **one** Chinese 译名. Store it as `glossary.json`:
```json
{"term": "译名", "attention mechanism": "注意力机制"}
```
Rule: one term = one 译名, enforced identically in title, abstract, body, figure/table captions, and conclusion. The glossary must be an actual enforced map, not a note in the prompt.

### 4. Translate segment by segment (段落全 / 关系准)
For each paragraph in reading order, translate to Chinese while carrying:
- the locked glossary for every term that appears;
- the previous paragraph's context for pronouns and cross-page continuation;
- numbers, units, formulas, equation numbers, `[1]`/`[2,3]`, `Fig. 2`, `Table 3` verbatim.

Keep equations and formulas **unchanged**. Do not invent or smooth over content; mark unclear or untranslatable parts explicitly.

### 5. Align and verify (可核验)
Write `translation.json`:
```json
{"source": "paper.pdf", "glossary": {}, "segments": [{"id": "p1.0", "page": 1, "source": "...", "translation": "...", "notes": ""}]}
```
Then run the verifier:
```bash
python3 src/verify_translation.py translation.json /app/work/verify
```
Fix every flagged issue: missing numbers/units, missing figure/table/reference markers, lost negation/limitation logic, and glossary term inconsistencies.

### 6. Write the final result
Write `/app/output/result.json` with all `output_contract` fields + `case_id`, plus `status` (`ok`/`partial`/`unreadable`), `sources`, `uncertainty`, `change_records`. Also copy `scaffold.json`, `glossary.json`, `translation.json`, `verification.json`, and a bilingual aligned Markdown into `/app/output`.

## Quality checks before finishing

- [ ] 术语稳: every glossary term uses the same 译名 in every segment.
- [ ] 段落全: segment ids map 1:1 to source paragraphs; none missing, duplicated, or misordered across pages/columns/sections.
- [ ] 关系准: numbers, units, formulas, figure/table/equation numbers, and citation markers are preserved; negation, limitation, causal/concessive relations unchanged.
- [ ] 可核验: every segment carries page (and where available bbox) + source text; unclear parts are marked, never silently filled in.

## Failure handling

- No text layer → run OCR with `ocr-tool`, or mark the page `unreadable`.
- Formulas/tables embedded as images → keep the reference to the image and mark "image formula/table, manual confirmation needed".
- Broken or unresolvable citation/reference → keep it verbatim and flag it.

## Notes

- This Skill reproduces the paper's claims with evidence; it does not judge or correct the science.
- Bundled: `src/translate_pdf.py` (scaffold), `src/verify_translation.py` (verification), `src/parse_pdf.py` (layout parser), `src/requirements.txt` (PyMuPDF).
