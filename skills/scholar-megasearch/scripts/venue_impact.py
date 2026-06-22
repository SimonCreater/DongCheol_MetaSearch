#!/usr/bin/env python3
"""Venue-impact lookup: map a paper's venue to an impact score in [0, 1].

Two impact sources, combined into one normalized venue-impact layer:

  1. BK21 conference table (references/venue_impact.json) — the authoritative
     AI/CS conference list with recognized IF 1-4. Built by build_venue_impact.py.
  2. OpenAlex journal cache (references/journal_impact.json) — per-source
     `2yr_mean_citedness` (the Journal-Impact-Factor-equivalent metric) plus
     h-index, fetched by enrich_if.py. Covers journals the BK21 list does not.

`merge_corpus.py` imports VenueImpact to compute its venue-impact ranking layer;
nothing here touches the network (enrich_if.py does the OpenAlex calls, offline-
cacheable). Matching is conservative: long conference names match by substring,
acronyms match only as whole tokens, and 2-letter acronyms additionally require
the venue text to be (essentially) just that acronym — so "RE" or "CC" do not
sweep up unrelated venues.
"""
import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
_REF = os.path.normpath(os.path.join(_HERE, "..", "references"))
DEFAULT_BK21 = os.path.join(_REF, "venue_impact.json")
DEFAULT_JOURNAL = os.path.join(_REF, "journal_impact.json")

# OpenAlex 2yr_mean_citedness reference ceiling for log-normalization. Most CS/AI
# journals sit well under this; top venues (e.g. Nature-tier) approach it.
JIF_CEILING = 40.0
# h-index reference ceiling for the fallback floor (top journals ~ 800+).
H_CEILING = 800.0

_PTYPE_DEDUCT = {"regular": 0, "short": 1, "spotlight": 2, "poster": 0}

# Modern venue names / spellings the BK21 list (frozen ~2018) does not carry.
# Keyed by BK21 acronym; values add matchable acronym tokens and name substrings.
# Most important for AI: NeurIPS (BK21 says "NIPS") and CVF-era proceedings.
_ALIASES = {
    "NIPS": {"acronyms": ["neurips"], "names": ["neural information processing systems"]},
    "ACL": {"names": ["annual meeting of the association for computational linguistics"]},
    "EMNLP": {"names": ["empirical methods in natural language processing"]},
    "KDD": {"names": ["knowledge discovery and data mining"]},
}

# Top AI/ML venues that postdate the 2018 BK21 list and so are absent from it.
# Scored on the same 1-4 BK21 scale (4 = top tier) so they rank alongside BK21
# conferences. Kept separate from the official PDF data on purpose — edit freely.
_EXTRA_VENUES = [
    {"acronym": "ICLR", "name": "International Conference on Learning Representations",
     "if": 4, "match_acronyms": ["iclr"],
     "match_name": "international conference on learning representations"},
    {"acronym": "COLM", "name": "Conference on Language Modeling",
     "if": 3, "match_acronyms": ["colm"],
     "match_name": "conference on language modeling"},
]


def _norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def _tokens(s):
    return set(_norm(s).split())


def _venue_text(record):
    parts = [record.get(k) for k in
             ("venue", "journal", "journal_name", "container", "container_title", "publicationVenue")]
    return " ".join(str(p) for p in parts if p)


def _detect_ptype(vtext):
    low = vtext.lower()
    for ptype in ("spotlight", "short", "poster"):
        if ptype in low:
            return ptype
    return "regular"


class VenueImpact:
    def __init__(self, bk21_path=DEFAULT_BK21, journal_path=DEFAULT_JOURNAL):
        self.scale_max = 4
        self.acronym_index = {}   # variant -> list of venue dicts
        self.venues = []
        self.journals = {}        # normalized name -> {citedness, h_index, display_name}
        self._load_bk21(bk21_path)
        self._load_journals(journal_path)

    def _load_bk21(self, path):
        if not path or not os.path.exists(path):
            return
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.scale_max = (data.get("meta") or {}).get("scale_max", 4) or 4
        for v in list(data.get("venues", [])) + _EXTRA_VENUES:
            v = {"type": "regular", **v}
            alias = _ALIASES.get(v.get("acronym"))
            if alias:
                v = dict(v)
                v["match_acronyms"] = sorted(set(v.get("match_acronyms", [])) | set(alias.get("acronyms", [])))
                if alias.get("names"):
                    # extra distinctive name substrings, matched alongside match_name
                    v["alias_names"] = [_norm(n) for n in alias["names"]]
            self.venues.append(v)
            for a in v.get("match_acronyms", []):
                self.acronym_index.setdefault(a, []).append(v)
                self.acronym_index.setdefault(a.replace(" ", ""), []).append(v)

    def _load_journals(self, path):
        if not path or not os.path.exists(path):
            return
        try:
            data = json.load(open(path, encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        for name, info in (data.get("journals") or {}).items():
            self.journals[_norm(name)] = info

    # ---- conference (BK21) matching -------------------------------------
    def _match_conference(self, vtext):
        nt = _norm(vtext)
        if not nt:
            return None
        toks = set(nt.split())
        best = None  # (if_raw, venue)
        # 1) acronym as a whole token
        for variant, vlist in self.acronym_index.items():
            short = len(variant.replace(" ", "")) <= 2
            hit = (variant in toks) or (variant.replace(" ", "") in toks)
            if short:
                # 2-char acronyms only count if the venue text is essentially
                # just that acronym (avoids "RE"/"CC"/"VR" false positives).
                hit = nt == variant or nt == variant.replace(" ", "")
            if hit:
                for v in vlist:
                    if best is None or v["if"] > best[0]:
                        best = (v["if"], v)
        # 2) full conference name as a substring (distinctive, low false-positive)
        for v in self.venues:
            names = [v.get("match_name") or ""] + (v.get("alias_names") or [])
            if any(len(mn) >= 12 and mn in nt for mn in names):
                if best is None or v["if"] > best[0]:
                    best = (v["if"], v)
        if not best:
            return None
        if_raw, venue = best
        ptype = _detect_ptype(vtext)
        if_raw = max(0, if_raw - _PTYPE_DEDUCT.get(ptype, 0))
        return {
            "matched": True,
            "kind": "conference",
            "label": venue["acronym"],
            "name": venue["name"],
            "if_raw": if_raw,
            "if_scale_max": self.scale_max,
            "impact": round(if_raw / self.scale_max, 6),
            "presentation": ptype,
            "source": "bk21",
        }

    # ---- journal (OpenAlex cache) matching ------------------------------
    def _match_journal(self, vtext):
        if not self.journals:
            return None
        nt = _norm(vtext)
        if not nt:
            return None
        info = self.journals.get(nt)
        if not info:
            # try token-superset: cached name fully contained in the venue text
            toks = set(nt.split())
            for name, cand in self.journals.items():
                ctoks = set(name.split())
                if ctoks and ctoks <= toks:
                    info = cand
                    break
        if not info:
            return None
        import math
        cited = float(info.get("citedness") or info.get("2yr_mean_citedness") or 0.0)
        h_index = float(info.get("h_index") or 0.0)
        # Primary: log-normalized JIF-equivalent. Fallback: a weaker h-index floor
        # so top journals OpenAlex reports with citedness 0 (e.g. JMLR) still score.
        impact_cited = math.log1p(max(0.0, cited)) / math.log1p(JIF_CEILING)
        impact_h = 0.6 * (math.log1p(h_index) / math.log1p(H_CEILING)) if h_index else 0.0
        impact = min(1.0, max(impact_cited, impact_h))
        return {
            "matched": True,
            "kind": "journal",
            "label": info.get("display_name") or vtext,
            "if_raw": round(cited, 3),
            "impact": round(impact, 6),
            "h_index": info.get("h_index"),
            "source": "openalex",
        }

    def lookup(self, record):
        """Return an impact dict (impact in [0,1]) or a not-matched stub."""
        vtext = _venue_text(record)
        return (self._match_conference(vtext)
                or self._match_journal(vtext)
                or {"matched": False, "kind": None, "impact": 0.0})


if __name__ == "__main__":
    import sys
    vi = VenueImpact()
    print(f"loaded {len(vi.venues)} BK21 venues, {len(vi.journals)} journals", file=sys.stderr)
    for q in sys.argv[1:]:
        print(q, "->", json.dumps(vi.lookup({"venue": q}), ensure_ascii=False))
