---
name: scholar-megasearch
description: >-
  Massive multi-source academic literature search via subagent orchestration.
  Fans out parallel searchers across every available scholarly source — arXiv,
  Semantic Scholar, Crossref, OpenAlex, PubMed/PMC, bioRxiv/medRxiv, DOAJ, CORE,
  BASE, DBLP, IACR, SSRN, Zenodo, Unpaywall, plus web/GitHub — then deduplicates
  by DOI/arXiv-id/title into one ranked corpus and synthesizes it. Use when the
  user wants a broad/exhaustive literature sweep, a large-scale paper search, a
  systematic review corpus, citation snowballing, or to find as many papers as
  possible on a topic across many databases at once. Triggers: "massive literature
  search", "literature review", "search across every database", "systematic search",
  "mega search", "search every source", "exhaustive search". Localized trigger phrases
  in other languages map to the same intent.
---

# scholar-megasearch

Integrates every academic search MCP/skill in this environment into one fan-out →
merge → synthesize pipeline. Each subagent owns one **source bucket** and searches in
parallel; results are merged into a single deduplicated, provenance-tracked, ranked
corpus. Prefer this over single-source searches whenever breadth matters.

Works in both Claude Code and Codex. Use the host's native tool discovery when MCP
schemas are deferred: Claude Code may expose `ToolSearch`; Codex may expose
`tool_search`. Use the skill directory from the loaded skill path for bundled scripts.
Default install locations:

- Claude Code: `~/.claude/skills/scholar-megasearch`, venv `~/.claude/skill_venv`.
- Codex: `~/.agents/skills/scholar-megasearch`, venv `${CODEX_HOME:-~/.codex}/skill_venv`.

Core engines expected when fully installed:

- MCP servers: `arxiv-mcp-server`, `asta`, and `paper-search-mcp`.
- Local fallbacks: `scripts/search_local.py {arxiv|semanticscholar|ddg}` and
  `scripts/resilient_search.py`, plus `scripts/fetch_pdfs.py`.
- Artifact viewer: `scripts/render_artifact.py <run-dir>` writes a self-contained
  `artifact/index.html`; `--serve` previews it on `127.0.0.1` without replacing the
  Markdown/JSON outputs.

Source buckets A-G:

- A arXiv; B Semantic Scholar via Ai2 Asta; C Crossref + OpenAlex.
- D PubMed/PMC/bioRxiv/medRxiv/Europe PMC; E DOAJ/CORE/BASE/OpenAIRE/Zenodo/Unpaywall/HAL.
- F DBLP/IACR/CiteSeerX/SSRN; G web, GitHub, grey literature, and page scraping.

For the full source list and which tools live in each bucket, read
`references/sources.md`. For the orchestration templates and the record schema, read
`references/orchestration.md`.

## Workflow

### 1. Frame the query + pick a depth level
Restate the topic in one line. If it is underspecified (e.g. "find papers on neural
networks"), do a **mini survey** before fanning out. Ask for exactly:

- **Field**: e.g. `ai-research`, `cs-ml`, `biomed`, `physics`, `chem-materials`,
  `crypto-security`, `econ-social-law`, `math`, or `interdisciplinary`.
  **Default when unspecified: `cs-ml`.**
- **Goal**: `survey`, `systematic`, `newest`, `seminal`, `implementation`, `pdf-corpus`,
  or **`impact`** (venue-IF-first — ranks high-impact venues to the top).
- **Depth**: numeric `1`–`5` only.

For an AI researcher who wants the **highest-impact-venue papers first**, default to
`--field ai-research --goal impact`. That turns on the **venue-impact ranking layer**
(see below), which scores each paper by the IF of the venue it appeared in.

If the user already gave these, do not ask. Otherwise ask once, then continue. For terminal
planning or repeatable runs, generate the same plan with:
```bash
python3 <skill-dir>/scripts/plan_run.py "<topic>" --field cs-ml --goal survey --depth 3
```
Depth sets the facet count, bucket count, per-source hit cap, and how many waves run.
An explicit `depth=N` / `LN` / bare `1–5` in the request wins; otherwise use the user's
numeric mini-survey answer; otherwise default **L2** only when the user asks not to be asked.

### 2. Decompose into facets + route to buckets
- **Facets** (count set by the depth level, 3–8): synonyms, sub-aspects, method vs.
  phenomenon, key authors, and at least one each of a broad and a narrow phrasing. For
  topics with strong non-English literature, add a localized query in the relevant
  language for Bucket G.
- **Buckets** (count set by the depth level, 4–7): pick from the domain→bucket routing
  table in `references/sources.md` based on the topic's field. Default for
  unknown topics (CS/ML-first): A, B, F (DBLP), C, G (GitHub). Use A, B, C, D, E, G only
  for clearly non-CS / interdisciplinary topics.

### 3. Set up the run directory
Create `./literature_search/<slug>_<YYYY-MM-DD>/raw/` under the **current working
directory** (slug = short kebab of the topic; use today's date). All artifacts go here.

### 4. Fan out the searchers (wave 1)
- **If the user opted into workflows** ("workflow" keyword / ultracode): run the Workflow
  script in `references/orchestration.md`, passing `{topic, facets, buckets, cap}` as `args`
  (`cap` = the level's hits/subquery). Then write each returned `raw[i]` to `raw/<bucket>.json`.
- **Otherwise**: spawn one Agent per bucket in a single message (concurrent), each writing
  its own `raw/<bucket>.json`. Use the Agent prompt skeleton in `references/orchestration.md`.

Every searcher returns records in the schema (title, authors, year, doi, arxiv_id,
pdf_url, url, citations, abstract, **source**, **query**) and does NOT dedupe. This is
**wave 1**; L3+ add further waves after the first merge — see `## Depth levels`.

### 5. Merge into one corpus
Dedupes by DOI → arXiv-id → normalized title, merges duplicates (keeping the richest
fields + max citations), then ranks with the **six-layer** scorer described below
(the sixth layer is venue impact / IF). For `--goal impact` or any journal-heavy run,
first enrich the journal-IF cache so journal venues score offline:
```bash
python3 <skill-dir>/scripts/enrich_if.py ./literature_search/<slug>_<date>/raw \
  --email you@example.com
```
Then merge. Pass the goal and topic so the relevance/weight profile is aligned with the
mini survey (venue impact is on by default):
```bash
python3 <skill-dir>/scripts/merge_corpus.py \
  ./literature_search/<slug>_<date>/raw \
  -o ./literature_search/<slug>_<date>/corpus.json \
  --md ./literature_search/<slug>_<date>/corpus.md \
  --goal <goal> --topic "<topic>"
```
`corpus.md` is the human-readable digest. Use `--min-sources 2` to keep only papers
corroborated by ≥2 databases (high-precision shortlist). Use `--ranking classic` only
when reproducing old runs.

### 6. Synthesize
Read `corpus.json` and write `summary.md` in the run dir. **Write `summary.md` prose in
Korean (한국어)** — section headings, the per-paper "왜 중요한가" one-liners, and the
gap/frontier discussion are all in Korean. Keep paper titles, author names, venue names,
and DOI/arXiv ids in their original form (do not translate them). The structure below is
unchanged:
- Headline count (unique papers, sources hit, year span).
- Top ~15–25 papers grouped by sub-theme, each with a one-line "why it matters".
- **Number every paper by its `corpus.json` `rank`** (1-based) shown as `[#NN]`. That
  same number is the `NN_` prefix of the acquired `pdfs/NN_*.pdf` and the `rank`/`i` in
  `pdfs/manifest.json`, so a reader jumps from a summary `[#NN]` straight to its file.
- Seminal/most-cited works, recent frontier (last 2 yrs), and notable gaps.
- Cite by DOI/arXiv id. Report honestly what was searched and any source that failed —
  no fabricated entries (see memory `feedback_honest_writing`).

### 7. Acquire original PDFs
Pull the original PDFs for the depth level's count — L1 → top 10, L2 → 30, L3 → 50,
L4 → 100, **L5 → `all`** (every paper in the corpus). `--top all` (or `0`) takes the
whole corpus; files are saved as `NN_<slug>.pdf` by `corpus.json` rank, matching the
`[#NN]` in `summary.md`:
```bash
python3 <skill-dir>/scripts/fetch_pdfs.py \
  ./literature_search/<slug>_<date>/corpus.json \
  -o ./literature_search/<slug>_<date>/pdfs \
  --email you@example.com --top 30
```
This auto-acquires via the free/legal routes — known open-access `pdf_url`, arXiv
direct, then Unpaywall OA API — verifying each file is a real PDF, and writes
`pdfs/manifest.json`. Papers with no free route are flagged `"status": "needs_mcp"`.
For those, fetch via the session MCP download tools (`paper-search-mcp.
download_with_fallback`, source-specific `download_*`, or `download_scihub`) — a
standalone script cannot reach MCP. To read extracted full text afterward, use the
`read_*_paper` MCP tools or `pdfplumber`/`pymupdf` from the installed host venv.
See `references/sources.md` for the full acquisition tool list.

### 8. Render the HTML artifact viewer
Create a portable, self-contained report after `corpus.json`, `summary.md`, and optional
`pdfs/manifest.json` exist:
```bash
python3 <skill-dir>/scripts/render_artifact.py \
  ./literature_search/<slug>_<date>
```
This writes `./literature_search/<slug>_<date>/artifact/index.html` with run stats,
summary text, source/provenance chips, rank layers, PDF status, links, and client-side
search/filter/sort controls. It does not replace `corpus.md` or `summary.md`.

For a quick local preview, opt in explicitly:
```bash
python3 <skill-dir>/scripts/render_artifact.py \
  ./literature_search/<slug>_<date> --serve --open
```
The preview server binds to `127.0.0.1` by default and serves only the run directory
so sibling PDF links can resolve. Use `--port` or `--bind` only when you intentionally
need a different preview target.

## Depth levels (L1–L5)
One knob: breadth (facets × buckets × hits) and recursion (extra waves) scale together.
Pick one per run — explicit `depth=N` / `LN` / bare `1–5` wins; else infer from phrasing;
else default **L2**. Clamp out-of-range to 1–5, and state the level you ran at.

| Lvl | facets | buckets | hits/subq | waves | PDFs | output |
|-----|--------|---------|-----------|-------|------|--------|
| **L1 Quick** | 3 | 4 | 15 | wave 1 only | top 10 | corpus |
| **L2 Standard** *(default)* | 5 | 5 | 25 | wave 1 only | top 30 | corpus |
| **L3 Deep** | 6 | 6 | 30 | + citation-snowball | top 50 | corpus |
| **L4 Exhaustive** | 8 | 7 (all) | 40 | + snowball + 1 completeness-critic pass | top 100 | corpus + ≥2 shortlist |
| **L5 Total / Exhaustive** | 8 | 7 (all) | 40 | + snowball + critic **loop-until-dry** | all | corpus + ≥2 shortlist |

Phrasing → level when not explicit: quick·first look·taste → L1 · *(no signal)* → L2 ·
deep·snowball·trace citations → L3 · systematic review·comprehensive·thorough → L4 ·
exhaustive·every source·all of them·to the end → L5. Equivalent phrases in other
languages map the same way. Higher levels spawn more subagents and cost more tokens
(L5 is bounded only by the token budget, not a fixed wave count).

## Six-layer ranking (incl. venue impact / IF)
`merge_corpus.py` ranks each merged paper with six orthogonal layers. Each layer is
normalized to 0–1 and written to `rank_layers`; the weighted total is `score`.

1. **Provenance**: independent source agreement (`sources_count`), not citation-based.
2. **Impact**: citation count plus age-normalized citation velocity.
3. **Recency**: publication-year frontier signal, independent of citations.
4. **Access/completeness**: DOI/arXiv id, PDF URL, abstract, authors, venue/year/url.
5. **Relevance**: overlap between topic/query terms and title/abstract/venue/query text.
6. **Venue impact (IF)**: the published-in venue's impact, from two tables —
   - **BK21 conferences** (`references/venue_impact.json`): 188 top CS/AI conferences
     with recognized IF 1–4 (AAAI, CVPR, NeurIPS, ICML, ACL, KDD, …; +ICLR/COLM that
     postdate the list). A matched venue scores `IF / 4`. The BK21 deduction rule
     (Regular=IF, Short=IF−1, Spotlight=IF−2, Poster=0) is applied when the venue text
     names the presentation type.
   - **OpenAlex journals** (`references/journal_impact.json`): per-source
     `2yr_mean_citedness` (the Journal-Impact-Factor-equivalent metric), log-normalized,
     with an h-index fallback. Covers journals the BK21 list does not (TPAMI, JMLR,
     IJCV, Nature MI, …). Clarivate's Master Journal List JIF is login-gated with no
     free bulk API, so OpenAlex's metric is used as the automatable IF proxy.

   Venue impact is **on by default**. A paper from a venue in neither table keeps its
   other five layers (additive boost, not a hard filter) — pass `--no-venue-impact` to
   drop the layer entirely (weights rescale over the other five).

Goal-specific weights stay intentionally separate: `systematic` emphasizes provenance,
`seminal` emphasizes impact, `newest` emphasizes recency, `implementation` emphasizes
relevance/access, `pdf-corpus` emphasizes access, and **`impact` emphasizes venue IF**
(weight 0.30 — use it to surface high-IF-venue papers first). `survey` is balanced.

### Keeping the journal-IF table fresh
The BK21 conference table ships ready (built from the PDF by `scripts/build_venue_impact.py`).
The journal cache ships seeded with ~20 top AI journals; extend it for a run's venues
**before** merging so journal scores are available offline:
```bash
python3 <skill-dir>/scripts/enrich_if.py \
  ./literature_search/<slug>_<date>/raw \
  --email you@example.com   # queries OpenAlex for venues not in the BK21 table, caches them
```
Then run `merge_corpus.py` as usual (it reads the cache automatically). To rebuild the
conference table from a newer BK21 PDF:
```bash
python3 <skill-dir>/scripts/build_venue_impact.py "<BK21 list>.pdf" \
  -o <skill-dir>/references/venue_impact.json
```

**Waves** — each is a fan-out followed by a `merge_corpus.py` pass into the *same* corpus;
applies to both the Workflow and Agent paths:
1. **Wave 1** (all levels): `buckets` searchers, each running the `facets` subqueries,
   ~`hits` per subquery.
2. **Citation-snowball** (L3+): take the top ~10 DOIs/arXiv ids from the corpus so far and
   fan out one wave that expands their forward (cited-by) + backward (references) neighbours.
   Workflow: re-run the script with `seeds:[...]`. Agent: tell each searcher to run
   `asta get_citations` / arXiv `citation_graph` / OpenAlex cited-by on the seeds.
3. **Completeness-critic** (L4+): a critic agent reads `corpus.md` and names the missing
   subtopics / seminal authors; those become new facets for one more wave-1-style fan-out.
4. **Loop-until-dry** (L5): repeat the critic → facets → fan-out → merge cycle until two
   consecutive critic passes surface nothing new (or, under Workflow, `budget.remaining()`
   runs low).

L4/L5 also re-run the merge with `--min-sources 2` → `corpus_shortlist.json` (papers
corroborated by ≥2 databases) alongside the full `corpus.json`.

## Fallback when MCP is unavailable
If MCP servers are down/headless, searchers use `scripts/search_local.py {arxiv|
semanticscholar|ddg} "query"` with the installed host venv Python. arXiv may
rate-limit (HTTP 429) under heavy fan-out — stagger or lean on Asta/OpenAlex. The Asta
(Semantic Scholar) MCP is remote and needs **no key** (a key only raises rate limits) —
in headless/cron runs just ensure network access, or fall back to
`search_local.py semanticscholar`. Never let a host-specific scholar gateway be a
bucket's only tool (absent in headless runs).

For failure-recovery runs, use the resilient local ladder instead of aborting:
```bash
python3 <skill-dir>/scripts/resilient_search.py "<query>" \
  --sources arxiv,semanticscholar,ddg -n 20 \
  -o ./literature_search/<slug>_<date>/raw/local_recovery.json \
  --status ./literature_search/<slug>_<date>/raw/local_recovery.status.json
```
Each searcher should follow the same policy: preferred MCP → alternate MCP in the bucket
→ local resilient fallback where applicable → record the failed source in a status file
and continue with partial results. Do not fail the whole run because one source fails.
