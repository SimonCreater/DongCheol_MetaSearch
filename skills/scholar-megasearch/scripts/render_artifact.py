#!/usr/bin/env python3
"""Render a scholar-megasearch run directory as a self-contained HTML artifact.

Reads an existing literature_search/<topic>_<date>/ directory containing corpus.json,
optional summary.md, and optional pdfs/manifest.json. Writes artifact/index.html.

The artifact is static by default. Pass --serve to preview it on localhost; the preview
server binds to 127.0.0.1 by default and serves only the run directory that contains the
generated artifact and its sibling outputs.
"""
import argparse
import html
import json
import os
import re
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


DEFAULT_PORT = 8765


def _read_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as e:
        raise SystemExit(f"invalid JSON in {path}: {e}") from e


def _e(value):
    return html.escape("" if value is None else str(value), quote=True)


def _num(value, default=0):
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


def _float(value, default=0.0):
    try:
        return float(value or default)
    except (TypeError, ValueError):
        return default


def _slug(value):
    value = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    return value or "paper"


def _doi_url(doi):
    if not doi:
        return None
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", str(doi).strip(), flags=re.I)
    return f"https://doi.org/{doi}"


def _arxiv_url(arxiv_id):
    if not arxiv_id:
        return None
    aid = re.sub(r"^arxiv:", "", str(arxiv_id).strip(), flags=re.I)
    return f"https://arxiv.org/abs/{aid}"


def _safe_remote_href(url):
    if not url:
        return None
    url = str(url).strip()
    parsed = urlparse(url)
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        return None
    return url


def _pdf_href(file_value, run_dir, artifact_dir):
    if not file_value:
        return None
    path = Path(str(file_value))
    if not path.is_absolute():
        path = run_dir / path
    try:
        href = os.path.relpath(path, artifact_dir)
    except ValueError:
        href = path.as_uri()
    return href.replace(os.sep, "/")


def _manifest_by_rank(run_dir):
    manifest = _read_json(run_dir / "pdfs" / "manifest.json", [])
    if not isinstance(manifest, list):
        return {}
    by_rank = {}
    for entry in manifest:
        if not isinstance(entry, dict):
            continue
        rank = entry.get("rank", entry.get("i"))
        if rank is not None:
            by_rank[_num(rank)] = entry
    return by_rank


def _summary_stats(corpus, manifest_by_rank):
    years = [_num(p.get("year")) for p in corpus if _num(p.get("year"))]
    sources = sorted({str(s) for p in corpus for s in (p.get("sources") or [])})
    pdf_ok = sum(1 for m in manifest_by_rank.values() if m.get("status") == "ok")
    pdf_needs = sum(1 for m in manifest_by_rank.values() if m.get("status") == "needs_mcp")
    return {
        "papers": len(corpus),
        "sources": len(sources),
        "source_names": sources,
        "year_min": min(years) if years else "—",
        "year_max": max(years) if years else "—",
        "pdf_ok": pdf_ok,
        "pdf_needs": pdf_needs,
    }


def _status_label(status):
    labels = {
        "ok": "PDF downloaded",
        "needs_mcp": "needs_mcp",
        "missing": "PDF missing",
    }
    return labels.get(status or "missing", str(status or "missing"))


def _paper_card(paper, manifest, run_dir, artifact_dir):
    rank = _num(paper.get("rank"), 0)
    title = paper.get("title") or "(untitled)"
    authors = paper.get("authors") or []
    if not isinstance(authors, list):
        authors = [authors]
    authors_text = ", ".join(str(a) for a in authors[:6])
    if len(authors) > 6:
        authors_text += " et al."
    sources = [str(s) for s in (paper.get("sources") or [])]
    queries = [str(q) for q in (paper.get("queries") or [])]
    status = (manifest or {}).get("status") or "missing"
    pdf_href = _pdf_href((manifest or {}).get("file"), run_dir, artifact_dir)
    score = _float(paper.get("score"), 0.0)
    year = _num(paper.get("year"), 0)
    citations = _num(paper.get("citations"), 0)
    layers = paper.get("rank_layers") if isinstance(paper.get("rank_layers"), dict) else {}

    link_bits = []
    for label, url in (
        ("DOI", _doi_url(paper.get("doi"))),
        ("arXiv", _arxiv_url(paper.get("arxiv_id") or paper.get("arxiv"))),
        ("PDF URL", _safe_remote_href(paper.get("pdf_url"))),
        ("Source", _safe_remote_href(paper.get("url"))),
    ):
        if url:
            link_bits.append(f'<a href="{_e(url)}" target="_blank" rel="noreferrer">{_e(label)}</a>')
    if pdf_href:
        link_bits.append(f'<a href="{_e(pdf_href)}">Local PDF</a>')

    source_chips = "".join(f'<span class="chip source">{_e(s)}</span>' for s in sources)
    query_chips = "".join(f'<span class="chip query">{_e(q)}</span>' for q in queries[:8])
    if len(queries) > 8:
        query_chips += f'<span class="chip query">+{len(queries) - 8} more</span>'
    layer_bits = "".join(
        f'<span><strong>{_e(k)}</strong> {float(v):.3f}</span>'
        for k, v in sorted(layers.items())
        if isinstance(v, (int, float))
    )

    search_text = " ".join([title, authors_text, paper.get("abstract") or "", " ".join(sources), " ".join(queries)]).lower()
    return f"""
    <article class="paper-card" id="paper-{rank or _slug(title)}"
      data-rank="{rank}" data-year="{year}" data-citations="{citations}"
      data-score="{score:.6f}" data-sources-count="{len(sources)}"
      data-sources="{_e(' '.join(sources))}" data-pdf-status="{_e(status)}"
      data-search="{_e(search_text)}">
      <div class="paper-head">
        <div class="rank">#{rank:02d}</div>
        <div class="paper-main">
          <h2>{_e(title)}</h2>
          <p class="meta">{_e(authors_text)}{(' · ' + _e(year)) if year else ''}{(' · ' + _e(paper.get('venue'))) if paper.get('venue') else ''}</p>
        </div>
        <div class="score">score <strong>{score:.3f}</strong></div>
      </div>
      <div class="metrics">
        <span>{citations} citations</span>
        <span>{len(sources)} sources</span>
        <span class="pdf-status { _e(status) }">{_e(_status_label(status))}</span>
      </div>
      <div class="chips">{source_chips}</div>
      <p class="abstract">{_e(paper.get('abstract') or '')}</p>
      <details>
        <summary>Provenance, queries, and rank layers</summary>
        <div class="queries">{query_chips or '<span class="muted">No query metadata</span>'}</div>
        <div class="layers">{layer_bits or '<span class="muted">No rank layer metadata</span>'}</div>
      </details>
      <div class="links">{' '.join(link_bits) or '<span class="muted">No links recorded</span>'}</div>
    </article>
    """


def _summary_section(summary_text, summary_ko):
    """Build the Summary section, showing Korean and English together when both exist."""
    en = (summary_text or "").strip()
    ko = (summary_ko or "").strip()
    if not en and not ko:
        return '    <section aria-label="Summary">\n      <h2>Summary</h2>\n      <div class="summary">No summary.md / summary.ko.md found.</div>\n    </section>'

    panels = []
    if ko:
        panels.append(
            f'        <div class="summary summary-pane" data-lang="ko">'
            f'<div class="lang-label">한국어 · summary.ko.md</div>{_e(ko)}</div>'
        )
    if en:
        panels.append(
            f'        <div class="summary summary-pane" data-lang="en">'
            f'<div class="lang-label">English · summary.md</div>{_e(en)}</div>'
        )

    # Toggle is only useful when both languages are present.
    toggle = ""
    if en and ko:
        toggle = (
            '      <div class="lang-toggle" role="group" aria-label="Summary language">\n'
            '        <button type="button" data-show="both" class="active">둘 다 / Both</button>\n'
            '        <button type="button" data-show="ko">한국어</button>\n'
            '        <button type="button" data-show="en">English</button>\n'
            '      </div>'
        )

    panels_html = "\n".join(panels)
    return (
        '    <section aria-label="Summary">\n'
        '      <div class="summary-head"><h2>Summary</h2>\n'
        f'{toggle}\n'
        '      </div>\n'
        f'      <div class="summary-wrap" id="summaryWrap" data-show="both">\n{panels_html}\n      </div>\n'
        '    </section>'
    )


def _build_html(run_dir, corpus, manifest_by_rank, summary_text, summary_ko=""):
    artifact_dir = run_dir / "artifact"
    stats = _summary_stats(corpus, manifest_by_rank)
    source_options = "\n".join(f'<option value="{_e(s)}">{_e(s)}</option>' for s in stats["source_names"])
    cards = "\n".join(
        _paper_card(p, manifest_by_rank.get(_num(p.get("rank"))), run_dir, artifact_dir)
        for p in corpus
    )
    run_name = run_dir.name
    summary_section = _summary_section(summary_text, summary_ko)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(run_name)} · scholar-megasearch artifact</title>
  <style>
    :root {{ color-scheme: dark; --bg:#0b0d12; --panel:#121723; --panel2:#171e2b; --text:#ecf2ff; --muted:#9aa8bd; --line:#263246; --accent:#89b4ff; --ok:#72d391; --warn:#ffd166; --bad:#ff7b7b; }}
    * {{ box-sizing: border-box; }}
    body {{ margin:0; font: 15px/1.55 ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: radial-gradient(circle at top left, #172033, var(--bg) 34rem); color:var(--text); }}
    a {{ color:var(--accent); text-decoration:none; }}
    a:hover {{ text-decoration:underline; }}
    header {{ padding: 42px clamp(20px, 5vw, 72px) 24px; border-bottom:1px solid var(--line); }}
    .eyebrow {{ color:var(--accent); text-transform:uppercase; letter-spacing:.14em; font-size:12px; font-weight:700; }}
    h1 {{ margin:.25rem 0 .5rem; font-size: clamp(30px, 5vw, 56px); line-height:1.02; }}
    .sub {{ max-width: 920px; color:var(--muted); font-size:17px; }}
    main {{ padding: 24px clamp(20px, 5vw, 72px) 64px; }}
    .stats {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(150px,1fr)); gap:12px; margin: 20px 0 22px; }}
    .stat {{ background:rgba(18,23,35,.86); border:1px solid var(--line); border-radius:16px; padding:16px; }}
    .stat strong {{ display:block; font-size:26px; }}
    .stat span {{ color:var(--muted); }}
    .summary {{ white-space:pre-wrap; background:rgba(18,23,35,.75); border:1px solid var(--line); border-radius:18px; padding:18px; color:#d8e3f7; max-height:320px; overflow:auto; }}
    .summary-head {{ display:flex; align-items:center; gap:14px; flex-wrap:wrap; }}
    .lang-toggle {{ display:inline-flex; gap:6px; }}
    .lang-toggle button {{ cursor:pointer; border:1px solid var(--line); background:var(--panel); color:var(--muted); border-radius:999px; padding:5px 12px; font-size:13px; }}
    .lang-toggle button.active {{ background:var(--accent); color:#07111d; border-color:var(--accent); font-weight:700; }}
    .lang-label {{ display:block; margin:-4px 0 8px; color:var(--accent); text-transform:uppercase; letter-spacing:.08em; font-size:11px; font-weight:700; }}
    .summary-wrap {{ display:grid; gap:12px; grid-template-columns: 1fr 1fr; }}
    .summary-wrap[data-show="ko"] {{ grid-template-columns: 1fr; }}
    .summary-wrap[data-show="en"] {{ grid-template-columns: 1fr; }}
    .summary-wrap[data-show="ko"] .summary-pane[data-lang="en"] {{ display:none; }}
    .summary-wrap[data-show="en"] .summary-pane[data-lang="ko"] {{ display:none; }}
    @media (max-width: 780px) {{ .summary-wrap {{ grid-template-columns: 1fr; }} }}
    .controls {{ position:sticky; top:0; z-index:2; display:grid; grid-template-columns: 2fr repeat(3, minmax(150px, .7fr)); gap:10px; padding:14px 0; backdrop-filter: blur(12px); background:linear-gradient(rgba(11,13,18,.92), rgba(11,13,18,.72)); }}
    input, select {{ width:100%; border:1px solid var(--line); border-radius:12px; background:var(--panel); color:var(--text); padding:12px 13px; }}
    .result-count {{ color:var(--muted); margin: 6px 0 16px; }}
    .paper-list {{ display:grid; gap:14px; }}
    .paper-card {{ background:linear-gradient(180deg, rgba(23,30,43,.95), rgba(18,23,35,.94)); border:1px solid var(--line); border-radius:20px; padding:18px; box-shadow: 0 18px 60px rgba(0,0,0,.20); }}
    .paper-head {{ display:flex; gap:14px; align-items:flex-start; }}
    .rank {{ flex:0 0 auto; color:#07111d; background:var(--accent); font-weight:800; border-radius:12px; padding:8px 10px; }}
    .paper-main {{ flex:1; min-width:0; }}
    .paper-main h2 {{ margin:0; font-size:20px; line-height:1.25; }}
    .meta, .muted {{ color:var(--muted); }}
    .score {{ flex:0 0 auto; color:var(--muted); text-align:right; }}
    .metrics, .chips, .links, .queries, .layers {{ display:flex; flex-wrap:wrap; gap:8px; margin-top:10px; }}
    .metrics span, .chip, .layers span {{ border:1px solid var(--line); background:rgba(255,255,255,.035); border-radius:999px; padding:4px 9px; color:#dce7fa; }}
    .chip.source {{ border-color:#38598a; }}
    .chip.query {{ color:var(--muted); }}
    .pdf-status.ok {{ color:var(--ok); border-color:rgba(114,211,145,.55); }}
    .pdf-status.needs_mcp {{ color:var(--warn); border-color:rgba(255,209,102,.55); }}
    .pdf-status.missing {{ color:var(--bad); border-color:rgba(255,123,123,.45); }}
    .abstract {{ color:#ccd8ec; }}
    details {{ margin-top:10px; color:#dce7fa; }}
    summary {{ cursor:pointer; color:var(--accent); }}
    .links a {{ display:inline-flex; border:1px solid #3b5278; border-radius:10px; padding:6px 9px; background:rgba(137,180,255,.08); }}
    @media (max-width: 780px) {{ .controls {{ grid-template-columns:1fr; position:static; }} .paper-head {{ flex-direction:column; }} .score {{ text-align:left; }} }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">scholar-megasearch artifact</div>
    <h1>{_e(run_name)}</h1>
    <p class="sub">Interactive offline report generated from <code>corpus.json</code>, <code>summary.md</code>, and <code>pdfs/manifest.json</code>. Existing Markdown/JSON outputs remain unchanged.</p>
    <section class="stats" aria-label="Run summary">
      <div class="stat"><strong>{stats['papers']}</strong><span>unique papers</span></div>
      <div class="stat"><strong>{stats['sources']}</strong><span>sources</span></div>
      <div class="stat"><strong>{_e(stats['year_min'])}–{_e(stats['year_max'])}</strong><span>year range</span></div>
      <div class="stat"><strong>{stats['pdf_ok']}</strong><span>PDFs acquired</span></div>
      <div class="stat"><strong>{stats['pdf_needs']}</strong><span>need MCP fallback</span></div>
    </section>
  </header>
  <main>
{summary_section}
    <section class="controls" aria-label="Filters">
      <input id="searchInput" type="search" placeholder="Search papers, authors, abstracts, sources, queries" aria-label="Search papers">
      <select id="sourceFilter" aria-label="Filter by source"><option value="">All sources</option>{source_options}</select>
      <select id="pdfFilter" aria-label="Filter by PDF status"><option value="">All PDF states</option><option value="ok">PDF downloaded</option><option value="needs_mcp">needs_mcp</option><option value="missing">Missing PDF</option></select>
      <select id="sortSelect" aria-label="Sort papers"><option value="rank">Rank</option><option value="score">Score</option><option value="citations">Citations</option><option value="year">Year</option><option value="sources">Source count</option></select>
    </section>
    <div class="result-count" id="resultCount"></div>
    <section class="paper-list" id="paperList" aria-label="Ranked papers">
      {cards}
    </section>
  </main>
  <script>
    const list = document.getElementById('paperList');
    const cards = Array.from(document.querySelectorAll('.paper-card'));
    const searchInput = document.getElementById('searchInput');
    const sourceFilter = document.getElementById('sourceFilter');
    const pdfFilter = document.getElementById('pdfFilter');
    const sortSelect = document.getElementById('sortSelect');
    const resultCount = document.getElementById('resultCount');

    function numeric(card, key) {{ return Number(card.dataset[key] || 0); }}
    function applyFilters() {{
      const q = searchInput.value.trim().toLowerCase();
      const source = sourceFilter.value;
      const pdf = pdfFilter.value;
      let visible = 0;
      cards.forEach(card => {{
        const okSearch = !q || card.dataset.search.includes(q);
        const okSource = !source || (` ${{card.dataset.sources}} `).includes(` ${{source}} `);
        const okPdf = !pdf || card.dataset.pdfStatus === pdf;
        const show = okSearch && okSource && okPdf;
        card.hidden = !show;
        if (show) visible += 1;
      }});
      resultCount.textContent = `${{visible}} / ${{cards.length}} papers shown`;
    }}
    function applySort() {{
      const mode = sortSelect.value;
      const sorted = [...cards].sort((a, b) => {{
        if (mode === 'rank') return numeric(a, 'rank') - numeric(b, 'rank');
        if (mode === 'score') return numeric(b, 'score') - numeric(a, 'score');
        if (mode === 'citations') return numeric(b, 'citations') - numeric(a, 'citations');
        if (mode === 'year') return numeric(b, 'year') - numeric(a, 'year');
        if (mode === 'sources') return numeric(b, 'sourcesCount') - numeric(a, 'sourcesCount');
        return 0;
      }});
      sorted.forEach(card => list.appendChild(card));
      applyFilters();
    }}
    [searchInput, sourceFilter, pdfFilter].forEach(el => el.addEventListener('input', applyFilters));
    sortSelect.addEventListener('input', applySort);
    applySort();

    const summaryWrap = document.getElementById('summaryWrap');
    document.querySelectorAll('.lang-toggle button').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.lang-toggle button').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (summaryWrap) summaryWrap.setAttribute('data-show', btn.dataset.show);
      }});
    }});
  </script>
</body>
</html>
"""


def render_artifact(run_dir, output=None):
    """Render run_dir/corpus.json into a self-contained artifact/index.html."""
    run_dir = Path(run_dir).expanduser()
    corpus_path = run_dir / "corpus.json"
    corpus = _read_json(corpus_path, None)
    if corpus is None:
        raise SystemExit(f"missing required corpus file: {corpus_path}")
    if not isinstance(corpus, list):
        raise SystemExit(f"expected {corpus_path} to contain a JSON list")

    artifact_dir = Path(output).expanduser().resolve().parent if output else run_dir / "artifact"
    artifact_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(output).expanduser().resolve() if output else artifact_dir / "index.html"

    summary_path = run_dir / "summary.md"
    summary_text = summary_path.read_text(encoding="utf-8") if summary_path.exists() else ""
    summary_ko_path = run_dir / "summary.ko.md"
    summary_ko = summary_ko_path.read_text(encoding="utf-8") if summary_ko_path.exists() else ""
    manifest_by_rank = _manifest_by_rank(run_dir)
    html_text = _build_html(run_dir, corpus, manifest_by_rank, summary_text, summary_ko)
    output_path.write_text(html_text, encoding="utf-8")
    return output_path


def serve_artifact(run_dir, bind="127.0.0.1", port=DEFAULT_PORT, open_browser=False):
    """Serve only the run directory so artifact links to sibling PDFs can resolve."""
    run_dir = Path(run_dir).expanduser().resolve()

    class ArtifactHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(run_dir), **kwargs)

        def do_GET(self):
            if self.path in ("/", ""):
                self.send_response(302)
                self.send_header("Location", "/artifact/index.html")
                self.end_headers()
                return
            return super().do_GET()

    httpd = ThreadingHTTPServer((bind, int(port)), ArtifactHandler)
    url = f"http://{bind}:{int(port)}/artifact/index.html"
    print(f"serving {run_dir} at {url}")
    if open_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped preview server")
    finally:
        httpd.server_close()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_dir", help="literature_search/<topic>_<date>/ directory containing corpus.json")
    ap.add_argument("-o", "--out", help="output HTML path (default: RUN_DIR/artifact/index.html)")
    ap.add_argument("--serve", action="store_true", help="preview the generated artifact on localhost")
    ap.add_argument("--bind", default="127.0.0.1", help="address for --serve (default: 127.0.0.1)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port for --serve (default: {DEFAULT_PORT})")
    ap.add_argument("--open", action="store_true", dest="open_browser", help="open the localhost preview in a browser")
    args = ap.parse_args(argv)

    output = render_artifact(args.run_dir, args.out)
    print(f"wrote {output}")
    if args.serve:
        serve_artifact(args.run_dir, bind=args.bind, port=args.port, open_browser=args.open_browser)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
