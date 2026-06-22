#!/usr/bin/env python3
"""Parse the BK21 stage-4 "우수 국제학술대회 목록" PDF into a venue-impact table.

The PDF lists 188 top Computer-Science conferences, each with a BK21 "인정 IF"
(recognized impact factor, 1-4). That table is the most reliable venue-impact
signal for AI/CS work, so we convert it once into JSON that merge_corpus.py reads
to compute its venue-impact ranking layer.

Output schema (references/venue_impact.json):

    {
      "meta": {"source": "...", "scale_max": 4, "count": 188, ...},
      "venues": [
        {"code": "BKCSA001", "acronym": "AAAI", "name": "AAAI Conference ...",
         "if": 4, "type": "regular",
         "match_acronyms": ["aaai"], "match_name": "aaai conference on ..."}
      ]
    }

BK21 scoring rule (from the PDF, applied at ranking time, not here):
    Regular = table IF · Short = IF-1 · Spotlight = IF-2 · Poster = 0.

Usage:
    build_venue_impact.py "[붙임] ... BK21.pdf" -o ../references/venue_impact.json
"""
import argparse
import json
import os
import re
import sys

try:
    import pdfplumber
except ImportError:
    sys.exit("pdfplumber is required: pip install pdfplumber")


# Acronym strings in the PDF sometimes carry a presentation-type tag, e.g.
# "I C C V\n(Spotlight)" or "CVPR (Short)". We strip it to a clean acronym and
# record the type so the ranking can apply the BK21 IF deduction.
TYPE_PATTERNS = [
    ("spotlight", re.compile(r"spotlight", re.I)),
    ("short", re.compile(r"\bshort\b", re.I)),
    ("poster", re.compile(r"\bposter\b", re.I)),
]


def clean_acronym(raw):
    """Return (clean_acronym, presentation_type)."""
    ptype = "regular"
    for name, pat in TYPE_PATTERNS:
        if pat.search(raw):
            ptype = name
            break
    # Drop parenthetical tags and collapse the spaced-out letters the PDF uses
    # for some acronyms ("I C C V" -> "ICCV", "S & P" -> "S&P").
    a = re.sub(r"\([^)]*\)", " ", raw)
    a = a.replace("\n", " ").strip()
    # Collapse single-letter runs separated by spaces into a solid acronym.
    a = re.sub(r"(?<=\b\w) (?=\w\b)", "", a)
    a = re.sub(r"\s+", " ", a).strip()
    return a, ptype


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def acronym_variants(acronym):
    """Matchable forms of an acronym: spaced-collapsed and ampersand variants."""
    base = norm(acronym)
    out = {base}
    out.add(base.replace(" ", ""))
    if "&" in acronym.lower() or " and " in base:
        out.add(base.replace(" and ", " ").replace(" ", ""))
    return sorted(v for v in out if len(v) >= 2)


def parse(pdf_path):
    venues = []
    seen_codes = set()
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 4:
                        continue
                    code, acronym, name, ifv = (c or "" for c in row[:4])
                    code = code.strip()
                    if not re.fullmatch(r"BKCSA\d+", code):
                        continue  # header / stray row
                    if code in seen_codes:
                        continue
                    seen_codes.add(code)
                    try:
                        if_score = int(re.search(r"\d+", ifv).group())
                    except (AttributeError, ValueError):
                        continue
                    clean, ptype = clean_acronym(acronym)
                    name_clean = re.sub(r"\s+", " ", name.replace("\n", " ")).strip()
                    venues.append({
                        "code": code,
                        "acronym": clean,
                        "name": name_clean,
                        "if": if_score,
                        "type": ptype,
                        "match_acronyms": acronym_variants(clean),
                        "match_name": norm(name_clean),
                    })
    return venues


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", help="path to the BK21 우수 국제학술대회 목록 PDF")
    ap.add_argument("-o", "--out", required=True, help="output venue_impact.json path")
    args = ap.parse_args()

    venues = parse(args.pdf)
    if not venues:
        sys.exit("no venue rows parsed — is this the BK21 conference-list PDF?")

    scale_max = max(v["if"] for v in venues)
    payload = {
        "meta": {
            "source": os.path.basename(args.pdf),
            "description": "BK21 4단계 CS 분야 우수 국제학술대회 인정 IF 목록",
            "scale_max": scale_max,
            "count": len(venues),
            "scoring_rule": "regular=if, short=if-1, spotlight=if-2, poster=0",
        },
        "venues": sorted(venues, key=lambda v: (-v["if"], v["code"])),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    print(f"  parsed {len(venues)} venues (IF 1-{scale_max}) -> {args.out}", file=sys.stderr)
    dist = {}
    for v in venues:
        dist[v["if"]] = dist.get(v["if"], 0) + 1
    print("  IF distribution: " + ", ".join(f"IF{k}={dist[k]}" for k in sorted(dist, reverse=True)),
          file=sys.stderr)


if __name__ == "__main__":
    main()
