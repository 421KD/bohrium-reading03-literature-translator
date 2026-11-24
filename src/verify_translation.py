#!/usr/bin/env python3
"""Verify a bilingual translation for preservation and consistency issues.

Reads translation.json (written by the translating agent):
{
  "source": "paper.pdf",
  "glossary": {"term": "译名", ...},
  "segments": [{"id": "p1.0", "page": 1, "source": "...", "translation": "...", "notes": ""}]
}

Checks, per segment:
  1. numbers + units preserved
  2. formula / figure / table / equation / citation markers preserved
  3. negation / quantification / logic markers preserved
  4. glossary term consistency (locked 译名 must appear when the term appears)

Writes verification.json and verification.md.
"""

import argparse
import json
import os
import re

NUMBER_RE = re.compile(
    r"\d+(?:[.,]\d+)?\s*(?:%|‰|kg|g|mg|μg|m|cm|mm|μm|nm|s|ms|K|Pa|MPa|GPa|"
    r"Hz|kHz|MHz|GHz|W|kW|V|A|mol|M|L|mL|eV|meV|keV|J|kJ|cal|N|Å|°C|°F)?",
    re.IGNORECASE,
)
REF_RE = re.compile(
    r"\[\d+(?:[,\-\s]+\d+)*\]|\(\d+\)|Fig(?:ure)?\.?\s*\d+|Table\s*\d+|"
    r"eq(?:uation)?\.?\s*\d+|Eq\.?\s*\d+|§\s*\d+",
    re.IGNORECASE,
)
LOGIC_RE = re.compile(
    r"\b(no|not|none|never|only|all|every|each|except|without|unless|"
    r"less\s+than|greater\s+than|at\s+most|at\s+least|cannot|neither|nor|"
    r"however|although|because|therefore|thus|but|yet|despite|whereas)\b"
    r"|[≤≥<>≠±×]",
    re.IGNORECASE,
)


def _norm(s):
    return re.sub(r"\s+", " ", s or "").strip()


def _fig_key(r):
    return re.sub(r"fig(ure)?", "fig", r, flags=re.IGNORECASE).lower()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Verify a bilingual translation")
    ap.add_argument("translation_json")
    ap.add_argument("outdir")
    args = ap.parse_args(argv)

    data = json.load(open(args.translation_json, encoding="utf-8"))
    glossary = data.get("glossary", {}) or {}
    segments = data.get("segments", []) or []

    issues = []
    for seg in segments:
        src = _norm(seg.get("source", ""))
        dst = _norm(seg.get("translation", ""))
        seg_issues = []

        src_nums = set(NUMBER_RE.findall(src))
        dst_nums = set(NUMBER_RE.findall(dst))
        missing_nums = sorted(src_nums - dst_nums)
        if missing_nums:
            seg_issues.append({"kind": "numbers", "detail": f"missing in translation: {missing_nums}"})

        src_refs = [m.group(0) for m in REF_RE.finditer(src)]
        dst_keys = {_fig_key(m.group(0)) for m in REF_RE.finditer(dst)}
        missing_refs = [r for r in src_refs if _fig_key(r) not in dst_keys]
        if missing_refs:
            seg_issues.append({"kind": "references", "detail": f"possibly missing: {missing_refs}"})

        src_logic = set(LOGIC_RE.findall(src))
        dst_logic = set(LOGIC_RE.findall(dst))
        missing_logic = sorted(src_logic - dst_logic)
        if missing_logic:
            seg_issues.append({"kind": "logic_markers", "detail": f"check preservation: {missing_logic}"})

        if seg_issues:
            issues.append({"id": seg.get("id"), "page": seg.get("page"), "issues": seg_issues})

    term_issues = []
    for term, zh in glossary.items():
        zh = (zh or "").strip()
        for seg in segments:
            src = _norm(seg.get("source", ""))
            dst = _norm(seg.get("translation", ""))
            if term in src and zh and zh not in dst:
                term_issues.append({"term": term, "expected": zh, "segment": seg.get("id")})

    report = {
        "summary": {
            "segments": len(segments),
            "segments_with_issues": len(issues),
            "term_inconsistencies": len(term_issues),
        },
        "issues": issues,
        "term_inconsistencies": term_issues,
    }

    os.makedirs(args.outdir, exist_ok=True)
    with open(os.path.join(args.outdir, "verification.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    lines = [
        "# Translation verification", "",
        f"- segments: {len(segments)}",
        f"- segments with issues: {len(issues)}",
        f"- term inconsistencies: {len(term_issues)}", "",
    ]
    for it in issues:
        lines.append(f"## {it['id']} (p{it.get('page')})")
        for j in it["issues"]:
            lines.append(f"- **{j['kind']}**: {j['detail']}")
    if term_issues:
        lines.append("## Glossary inconsistencies")
        for t in term_issues:
            lines.append(f"- {t['term']} → 应为「{t['expected']}」，段落 {t['segment']} 未出现")
    with open(os.path.join(args.outdir, "verification.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(json.dumps(report["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
