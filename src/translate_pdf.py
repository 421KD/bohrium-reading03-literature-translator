#!/usr/bin/env python3
"""Translation scaffold extractor for scientific PDFs.

Builds a structured, evidence-mapped translation scaffold:
  scaffold.json  paragraphs (reading order, page/bbox/section), candidate terms,
                 an empty glossary map, tables, figures, uncertainties
  scaffold.md    human-readable bilingual-alignment template

Reuses the layout-aware parser in parse_pdf.py (bundled), then adds terminology
candidates and the glossary template. The actual translation is done by the agent;
this script supplies the structured source and term candidates.
"""

import argparse
import json
import os
import re
from collections import Counter

import parse_pdf

ACRONYM_RE = re.compile(r"\b[A-Z]{2,6}\b")
CAPS_PHRASE_RE = re.compile(r"\b([A-Z][a-z0-9-]+(?:\s+[A-Z][a-z0-9-]+){0,4})\b")

STOP = set(
    """the a an of in on at for to by with from as is are was were be been and or
not this that these those it its we our you your he she they their which who whom
whose than then when where why how also can may will would should could such
between among within without during through under over above below via per vs
using based due into onto upon some any each all every""".split()
)


def _candidate_terms(paragraphs):
    acro = Counter()
    phrase = Counter()
    for p in paragraphs:
        text = p.get("text", "")
        for m in ACRONYM_RE.finditer(text):
            acro[m.group(0)] += 1
        for m in CAPS_PHRASE_RE.finditer(text):
            words = m.group(1).split()
            if 2 <= len(words) <= 5 and all(w.lower() not in STOP for w in words):
                phrase[" ".join(words)] += 1
    terms = []
    for t, c in acro.items():
        if c >= 2:
            terms.append({"term": t, "kind": "acronym", "count": c})
    for t, c in phrase.items():
        if c >= 3:
            terms.append({"term": t, "kind": "phrase", "count": c})
    terms.sort(key=lambda x: (-x["count"], x["term"]))
    return terms


def _render_scaffold_md(s):
    lines = [f"# Translation scaffold: {s['meta']['source']}", "", "## Glossary (to fill)", "",
             "| term | 译名 | source |", "|---|---|---|"]
    for t in s["candidate_terms"][:40]:
        lines.append(f"| {t['term']} |  |  |")
    lines += ["", "## Paragraphs (source)", ""]
    for p in s["paragraphs"]:
        bid = p.get("block_id", p.get("id", "?"))
        lines.append(f"### {bid}  [p{p['page']}]")
        lines.append(f"**Source:** {p['text']}")
        lines.append("**Translation:** ")
        lines.append("")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Build a translation scaffold from a PDF")
    ap.add_argument("pdf")
    ap.add_argument("outdir")
    args = ap.parse_args(argv)

    if parse_pdf.HAS_FITZ:
        parsed = parse_pdf.parse_with_fitz(args.pdf, args.outdir)
    else:
        parsed = parse_pdf.parse_text_fallback(args.pdf, args.outdir)

    paragraphs = [b for b in parsed["blocks"] if b.get("type") in ("paragraph", "heading", "equation")]
    terms = _candidate_terms(paragraphs)

    scaffold = {
        "schema": "literature-translator/1",
        "meta": parsed["meta"],
        "paragraphs": paragraphs,
        "sections": parsed["sections"],
        "tables": parsed["tables"],
        "figures": parsed["figures"],
        "candidate_terms": terms,
        "glossary": {},
        "uncertainties": parsed["uncertainties"],
    }

    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, "scaffold.json"), "w", encoding="utf-8") as f:
        json.dump(scaffold, f, ensure_ascii=False, indent=2)
    with open(os.path.join(args.outdir, "scaffold.md"), "w", encoding="utf-8") as f:
        f.write(_render_scaffold_md(scaffold))

    print(json.dumps({
        "paragraphs": len(paragraphs),
        "sections": len(parsed["sections"]),
        "tables": len(parsed["tables"]),
        "figures": len(parsed["figures"]),
        "candidate_terms": len(terms),
        "uncertainties": len(parsed["uncertainties"]),
        "outdir": args.outdir,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
