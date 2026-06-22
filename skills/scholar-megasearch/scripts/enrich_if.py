#!/usr/bin/env python3
"""Fetch journal impact metrics from OpenAlex into a local cache.

Clarivate's Master Journal List (mjl.clarivate.com) has no free bulk API and its
JIF is login-gated, so we use OpenAlex's per-source `2yr_mean_citedness` — the
Journal-Impact-Factor-equivalent metric (mean citations in the trailing 2 years)
— as the journal-impact signal. This script collects the distinct venues from a
run's records, resolves each against the OpenAlex `/sources` API, and writes
references/journal_impact.json so merge_corpus.py can score venue impact OFFLINE.

It only adds journals the BK21 conference table does not already cover (so it
spends API calls where they matter), unless --all is given.

Usage:
    enrich_if.py CORPUS_OR_RAW [...] --email you@example.com
                 [-o ../references/journal_impact.json] [--all] [--limit N]

CORPUS_OR_RAW may be corpus.json, a raw/ directory, or explicit record JSON files.
"""
import argparse
import glob
import json
import os
import sys
import time
import urllib.parse
import urllib.request

from venue_impact import VenueImpact, _norm, _venue_text, DEFAULT_JOURNAL

OPENALEX = "https://api.openalex.org/sources"


def _iter_records(paths):
    files = []
    for p in paths:
        if os.path.isdir(p):
            files += sorted(glob.glob(os.path.join(p, "*.json")))
        else:
            files.append(p)
    for f in files:
        try:
            data = json.load(open(f, encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            print(f"  ! skip {f}: {e}", file=sys.stderr)
            continue
        if isinstance(data, dict):
            data = data.get("results") or data.get("papers") or data.get("data") or []
        for r in data if isinstance(data, list) else []:
            if isinstance(r, dict):
                yield r


def fetch_source(venue, email):
    params = {"search": venue, "per-page": 1, "mailto": email}
    url = f"{OPENALEX}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": f"scholar-megasearch (mailto:{email})"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.load(resp)
    results = data.get("results") or []
    if not results:
        return None
    s = results[0]
    stats = s.get("summary_stats") or {}
    return {
        "display_name": s.get("display_name"),
        "openalex_id": s.get("id"),
        "type": s.get("type"),
        "citedness": stats.get("2yr_mean_citedness"),
        "h_index": stats.get("h_index"),
        "i10_index": stats.get("i10_index"),
        "issn_l": s.get("issn_l"),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inputs", nargs="+", help="corpus.json, raw/ dir, or record json files")
    ap.add_argument("--email", required=True, help="contact email for the OpenAlex polite pool")
    ap.add_argument("-o", "--out", default=DEFAULT_JOURNAL)
    ap.add_argument("--all", action="store_true",
                    help="also query venues already covered by the BK21 conference table")
    ap.add_argument("--limit", type=int, default=300, help="max distinct venues to query")
    args = ap.parse_args()

    vi = VenueImpact()
    cache = {"meta": {}, "journals": {}}
    if os.path.exists(args.out):
        try:
            cache = json.load(open(args.out, encoding="utf-8"))
            cache.setdefault("journals", {})
        except (OSError, json.JSONDecodeError):
            pass

    # Collect distinct venues worth resolving.
    venues = {}
    for r in _iter_records(args.inputs):
        vtext = _venue_text(r).strip()
        if not vtext or len(vtext) < 3:
            continue
        key = _norm(vtext)
        if key in cache["journals"]:
            continue
        if not args.all and vi.lookup(r).get("matched"):
            continue  # already scored by the BK21 conference table
        venues.setdefault(key, vtext)

    todo = list(venues.items())[: args.limit]
    print(f"  {len(venues)} distinct unscored venues; querying {len(todo)}", file=sys.stderr)

    added = 0
    for key, vtext in todo:
        try:
            info = fetch_source(vtext, args.email)
        except Exception as e:  # network/HTTP — record nothing, keep going
            print(f"  ! {vtext[:50]}: {e}", file=sys.stderr)
            time.sleep(1.0)
            continue
        if info and info.get("citedness") is not None:
            cache["journals"][key] = info
            added += 1
            print(f"  + {vtext[:40]:40s} -> {info['display_name']} "
                  f"(JIF~{info['citedness']}, h={info['h_index']})", file=sys.stderr)
        time.sleep(0.2)  # be polite to OpenAlex

    cache["meta"] = {
        "source": "OpenAlex /sources summary_stats.2yr_mean_citedness",
        "metric": "2yr_mean_citedness (Journal-Impact-Factor-equivalent)",
        "count": len(cache["journals"]),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    print(f"  added {added}, cache now {len(cache['journals'])} journals -> {args.out}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
