<h1 align="center">scholar-megasearch</h1>

<p align="center">
  <strong>Massive multi-source academic literature search for Claude Code.</strong><br>
  <em>One skill that fans out subagents across 20+ scholarly databases, merges everything into a single deduplicated corpus, and acquires the original PDFs.</em>
</p>

<p align="center">
  <a href="./README.ko.md">한국어 README</a>
  &nbsp;·&nbsp;
  <a href="./skills/scholar-megasearch/SKILL.md">SKILL.md</a>
  &nbsp;·&nbsp;
  <a href="./skills/scholar-megasearch/references/sources.md">Source catalog</a>
  &nbsp;·&nbsp;
  <a href="./skills/scholar-megasearch/references/orchestration.md">Orchestration</a>
</p>

<p align="center">
  <img src="https://img.shields.io/github/license/TaewoooPark/scholar-megasearch?style=flat-square&labelColor=000000&color=333333&cacheSeconds=3600" alt="License">
  <img src="https://img.shields.io/github/stars/TaewoooPark/scholar-megasearch?style=flat-square&logo=github&logoColor=white&labelColor=000000&color=333333&cacheSeconds=3600" alt="GitHub stars">
  <img src="https://img.shields.io/github/last-commit/TaewoooPark/scholar-megasearch?style=flat-square&labelColor=000000&color=333333&cacheSeconds=3600" alt="Last commit">
  <img src="https://img.shields.io/github/languages/top/TaewoooPark/scholar-megasearch?style=flat-square&labelColor=000000&color=333333&cacheSeconds=3600" alt="Top language">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Claude%20Code-000000?style=flat-square&logo=anthropic&logoColor=white&labelColor=000000&cacheSeconds=3600" alt="Claude Code">
  <img src="https://img.shields.io/badge/Skill%20%2B%20MCP-000000?style=flat-square&labelColor=000000&color=000000&cacheSeconds=3600" alt="Skill plus MCP">
  <img src="https://img.shields.io/badge/Python-000000?style=flat-square&logo=python&logoColor=white&labelColor=000000&cacheSeconds=3600" alt="Python">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/arXiv-000000?style=flat-square&logo=arxiv&logoColor=white&labelColor=000000&cacheSeconds=3600" alt="arXiv">
  <img src="https://img.shields.io/badge/Semantic%20Scholar-000000?style=flat-square&labelColor=000000&color=000000&cacheSeconds=3600" alt="Semantic Scholar">
  <img src="https://img.shields.io/badge/Crossref-000000?style=flat-square&labelColor=000000&color=000000&cacheSeconds=3600" alt="Crossref">
  <img src="https://img.shields.io/badge/OpenAlex-000000?style=flat-square&labelColor=000000&color=000000&cacheSeconds=3600" alt="OpenAlex">
  <img src="https://img.shields.io/badge/PubMed%20%2F%20PMC-000000?style=flat-square&labelColor=000000&color=000000&cacheSeconds=3600" alt="PubMed and PMC">
  <img src="https://img.shields.io/badge/Unpaywall-000000?style=flat-square&labelColor=000000&color=000000&cacheSeconds=3600" alt="Unpaywall">
  <img src="https://img.shields.io/badge/DOAJ%20%C2%B7%20CORE%20%C2%B7%20BASE-000000?style=flat-square&labelColor=000000&color=000000&cacheSeconds=3600" alt="DOAJ, CORE, BASE">
  <img src="https://img.shields.io/badge/DBLP%20%C2%B7%20IACR%20%C2%B7%20SSRN-000000?style=flat-square&labelColor=000000&color=000000&cacheSeconds=3600" alt="DBLP, IACR, SSRN">
</p>

---

> **One sentence:** ask Claude Code for a topic, and get back a single ranked,
> deduplicated, provenance-tracked corpus of papers — with the PDFs already on disk.

- 🔭 **20+ databases in one pass** — arXiv, Semantic Scholar, Crossref, OpenAlex, PubMed/PMC, bioRxiv/medRxiv, DOAJ, CORE, BASE, OpenAIRE, Zenodo, Unpaywall, HAL, DBLP, IACR, SSRN, CiteSeerX, Europe PMC, plus web/GitHub.
- 🧵 **Subagent fan-out** — one searcher per source bucket, running in parallel, so breadth doesn't cost you serial wall-clock.
- 🧹 **Dedup with provenance** — merged by DOI → arXiv-id → normalized title; every paper records *which* databases surfaced it.
- 📊 **Corroboration ranking** — papers found by more independent databases rank higher, not just the ones with good SEO.
- 📄 **Original PDFs** — top-K acquired automatically via open-access routes, with a manifest of what landed and what needs a paywall fallback.
- 🧭 **Domain-aware routing** — physics, life sciences, CS, crypto, economics, or math each pull the right subset of databases.

## Why It Exists

Searching one database at a time is how good papers get missed. arXiv won't show
you the published version's citation count; Semantic Scholar won't surface the
bioRxiv preprint; Google Scholar won't tell you which of its hits also appear in
three other indexes. So you end up running the same query in five tabs, copy-pasting
into a doc, hand-deduplicating, and then hunting each PDF down separately.

`scholar-megasearch` collapses that into one request. It treats "search the
literature" as a fan-out problem: decompose the topic, send each **source bucket** to
its own subagent, and reconcile everything afterward. The output isn't a chat reply —
it's a corpus on disk where every entry is deduplicated, ranked by how many
independent databases corroborate it, and backed by a downloaded PDF wherever a free
route exists.

## How It Works

<p align="center">
  <img src="./docs/pipeline.png" width="900" alt="scholar-megasearch pipeline: topic → decompose into facets → fan out one subagent per source bucket → merge_corpus.py (dedup + rank) → fetch_pdfs.py → synthesize">
</p>

Orchestration runs as a deterministic **Workflow** when available, and falls back to
direct **Agent** fan-out otherwise. A domain → bucket routing table picks the right
4–7 buckets per topic.

### Dedup & ranking

Records from different databases are merged when they share **any** of: a normalized
DOI, an arXiv id (version-stripped), or a normalized title. The merged record keeps
the richest value per field — the longest abstract, the most complete author list,
the maximum citation count — and accumulates the **set of sources** that found it.
Ranking is then `(number of sources, citation count, year)`, descending. Pass
`--min-sources 2` to keep only papers corroborated by two or more databases — a
high-precision shortlist that filters out single-index noise.

### A typical run

A mid-depth sweep (≈ **L3 Deep**) on a focused topic looks roughly like this *(illustrative)*:

```
topic: "spin–orbit torque switching in ferrimagnets"
  facets:  6 subqueries        buckets: A B C E G (5 searchers)
  raw hits: ~310 across buckets
  unique:   ~150 after dedup   (≈60 corroborated by ≥2 databases)
  PDFs:     22 / 25 acquired   (3 flagged needs_mcp — paywalled)
  output:   ./literature_search/spin-orbit-torque-ferri_2026-05-29/
```

## Install

```bash
git clone https://github.com/TaewoooPark/scholar-megasearch.git
cd scholar-megasearch
bash setup/install.sh you@example.com      # email used for Unpaywall OA + arXiv politeness
```

The script installs the skills into `~/.claude/skills/`, builds
`~/.claude/skill_venv` and `~/.claude/paper_search_mcp_venv`, clones/installs the
three MCP servers (`paper-search-mcp` from git main — the PyPI build lacks
Crossref/OpenAlex), and writes `setup/mcp.servers.resolved.json`. Merge that file's
`mcpServers` entries into `~/.claude.json` and restart Claude Code.

**Requirements**

| | |
|---|---|
| Python | 3.11+ |
| [`uv`](https://astral.sh/uv) | for `uvx arxiv-mcp-server` |
| `git` | to clone `semantic-scholar-mcp` at install time |
| Claude Code | the skill is triggered from within a session |

## Usage

Inside Claude Code, trigger the skill in natural language:

```
search every database for spin–orbit torque switching and grab the PDFs
MoE 관련 최근 1년 논문 방대하게 검색해줘, PDF까지
```

Or run the scripts directly:

```bash
# merge per-source result files into one ranked corpus
python3 ~/.claude/skills/scholar-megasearch/scripts/merge_corpus.py \
  ./literature_search/<topic>_<date>/raw \
  -o corpus.json --md corpus.md --min-sources 2

# acquire original PDFs for the top 25 ranked papers
python3 ~/.claude/skills/scholar-megasearch/scripts/fetch_pdfs.py \
  corpus.json -o ./pdfs --email you@example.com --top 25
```

### Depth levels

One knob scales **breadth** (facets × buckets × hits per query) and **recursion**
(extra waves) together. Pick a level per run — an explicit `depth=N` / `LN` / bare
`1–5` wins; otherwise it's inferred from phrasing (`quick`/`빠르게` → L1 …
`every source`/`전수조사` → L5); otherwise it defaults to **L2**.

| Level | Facets | Buckets | Hits/query | Waves | Output |
|-------|:------:|:-------:|:----------:|-------|--------|
| **L1 · Quick** | 3 | 4 | 15 | wave 1 only | corpus |
| **L2 · Standard** *(default)* | 5 | 5 | 25 | wave 1 only | corpus |
| **L3 · Deep** | 6 | 6 | 30 | + citation snowball | corpus |
| **L4 · Exhaustive** | 8 | 7 (all) | 40 | + snowball + completeness-critic pass | corpus + ≥2 shortlist |
| **L5 · Total** (전수조사) | 8 | 7 (all) | 40 | + snowball + critic loop-until-dry | corpus + ≥2 shortlist |

Each wave is a fan-out followed by a merge into the *same* corpus: the **citation
snowball** (L3+) seeds the top DOIs/arXiv ids back through citation graphs; the
**completeness-critic** (L4+) names missing subtopics/authors that become the next
wave's facets, looped until dry at L5. L4/L5 also emit a `--min-sources 2` shortlist.
Higher levels spawn more subagents and cost more tokens — L5 is bounded only by the
token budget.

## Outputs

Everything lands under `./literature_search/<topic>_<date>/` in the working directory:

```
literature_search/<topic>_<date>/
├── raw/<bucket>.json     # per-source hits (one file per subagent)
├── corpus.json           # deduplicated, ranked, provenance-tracked corpus
├── corpus.md             # human-readable digest
├── pdfs/                  # acquired original PDFs + manifest.json
└── summary.md            # synthesized review
```

## Source Buckets

| Bucket | Databases |
|--------|-----------|
| A · Preprints | arXiv (search · semantic · citation graph) |
| B · Citations | Semantic Scholar (200M+, citation counts) |
| C · DOI / published | Crossref, OpenAlex |
| D · Life sciences | PubMed, PMC, bioRxiv, medRxiv, Europe PMC |
| E · Open access | DOAJ, CORE, BASE, OpenAIRE, Zenodo, Unpaywall, HAL |
| F · Domain | DBLP (CS), IACR (crypto), SSRN (econ/law), CiteSeerX |
| G · Web | DuckDuckGo, GitHub, crawl4ai / firecrawl |

### Domain → bucket routing

| Topic domain | Always | Plus |
|---|---|---|
| Physics / materials / cond-mat | A · B · C | E · G |
| CS / ML / systems | A · B · F (DBLP) | C · G (GitHub) |
| Biology / medicine / neuro | D · B · C | E |
| Cryptography / security | A · F (IACR) · B | G (GitHub) |
| Economics / social science / law | F (SSRN) · B · C | G |
| Math | A · B · C | F |
| Interdisciplinary / unknown | A · B · C · D | E · G |

Full per-bucket tool lists are in
[`skills/scholar-megasearch/references/sources.md`](./skills/scholar-megasearch/references/sources.md);
the orchestration templates (Workflow + Agent fan-out) and the record schema are in
[`references/orchestration.md`](./skills/scholar-megasearch/references/orchestration.md).

## Repository Layout

```
scholar-megasearch/
├── README.md · README.ko.md · LICENSE
├── setup/
│   ├── install.sh            # skills + venvs + MCP servers + resolved config
│   ├── requirements.txt      # pinned search/acquisition deps
│   └── mcp.servers.json      # MCP registration template for ~/.claude.json
└── skills/
    ├── scholar-megasearch/   # the skill
    │   ├── SKILL.md
    │   ├── references/{sources.md, orchestration.md}
    │   └── scripts/{merge_corpus.py, fetch_pdfs.py, search_local.py}
    └── arxiv-search/          # supporting venv-search skill
```

This repository contains only original MIT-licensed work (the two skills and the
setup scripts). The three MCP servers are **not** vendored — `setup/install.sh`
fetches each from its upstream source at install time. See [Attribution](#attribution).

## Notes & Limitations

- **PDF acquisition is open-access-first.** `fetch_pdfs.py` only uses free/legal
  routes (a known OA `pdf_url`, arXiv, Unpaywall) and verifies every file is a real
  `%PDF-`. Closed-access papers are flagged `needs_mcp` in the manifest; fetching
  those is left to the session's MCP download tools.
- **arXiv rate-limits heavy fan-out** (HTTP 429). Searchers stagger and lean on
  Semantic Scholar / OpenAlex when arXiv pushes back.
- **`paper-search-mcp` must be the git-main build** — the PyPI release omits
  Crossref and OpenAlex. The installer handles this.
- **The claude.ai Scholar Gateway is best-effort** — it may be absent in
  headless/cron runs, so it is never a bucket's only source.
- **Honest synthesis.** `summary.md` reports what was actually searched and which
  sources failed; nothing is invented to fill a gap.

## Attribution

The MCP servers are third-party projects, installed from their upstream sources by
`setup/install.sh` — none of their code is redistributed here:

- **semantic-scholar-mcp** — [JackKuo666/semanticscholar-MCP-Server](https://github.com/JackKuo666/semanticscholar-MCP-Server) (cloned at install time)
- **paper-search-mcp** — [openags/paper-search-mcp](https://github.com/openags/paper-search-mcp) (pip install from git main)
- **arxiv-mcp-server** — launched on demand via `uvx`

Original work in this repository (the `scholar-megasearch` and `arxiv-search` skills
and the setup scripts) is released under the [MIT License](./LICENSE).
