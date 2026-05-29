# Academic Paper Search Skill

학술 논문 검색 전용 스킬. API 키 없이 arXiv, Semantic Scholar를 검색하며, MCP 서버(arxiv-mcp-server, semantic-scholar-mcp)도 활용 가능하다.

## 언제 사용하는가

- 논문/학술 자료 검색 요청 시
- arXiv 논문 검색 또는 다운로드 시
- Semantic Scholar로 인용/피인용 분석 시
- PDF 부록 코드 추출 시

## 설치된 도구

| 도구 | 경로 / 방법 | 용도 |
|------|------------|------|
| `arxiv` Python 패키지 | `~/.claude/skill_venv/bin/python3` | arXiv 검색 |
| `semanticscholar` Python 패키지 | `~/.claude/skill_venv/bin/python3` | Semantic Scholar 검색 |
| `arxiv-mcp-server` | MCP 등록 완료 (uvx) | Claude Code MCP 도구 |
| `semantic-scholar-mcp` | MCP 등록 완료 (python3) | Claude Code MCP 도구 |
| `paper-search-mcp` | `~/.claude/skill_venv` | arXiv+SS+PubMed 통합 |
| `ddgs` | `~/.claude/skill_venv/bin/python3` | DuckDuckGo 보조 검색 |
| `pdfplumber` | `~/.claude/skill_venv/bin/python3` | PDF 텍스트 추출 |
| `crwl` (crawl4ai) | `~/.claude/skill_venv/bin/crwl` | 웹 크롤링 |

## 핵심 명령 패턴

### 1. arXiv 검색 (권장)

```python
~/.claude/skill_venv/bin/python3 << 'EOF'
import arxiv, json

client = arxiv.Client()
search = arxiv.Search(
    query="MuMax3 ferrimagnet domain wall mass",
    max_results=20,
    sort_by=arxiv.SortCriterion.Relevance
)
results = []
for r in client.results(search):
    results.append({
        "title": r.title,
        "authors": [str(a) for a in r.authors[:3]],
        "year": r.published.year,
        "arxiv_id": r.entry_id.split("/")[-1],
        "pdf_url": r.pdf_url,
        "categories": r.categories,
        "summary": r.summary[:300]
    })
print(json.dumps(results, indent=2, ensure_ascii=False))
EOF
```

### 2. Semantic Scholar 검색 (200M+ 논문)

```python
~/.claude/skill_venv/bin/python3 << 'EOF'
from semanticscholar import SemanticScholar
import json

sch = SemanticScholar()
results = sch.search_paper(
    "MuMax3 domain wall inertia ferrimagnet",
    limit=20,
    fields=["title", "authors", "year", "externalIds", "openAccessPdf", "citationCount", "abstract"]
)
output = []
for p in results:
    output.append({
        "title": p.title,
        "year": p.year,
        "citations": p.citationCount,
        "doi": p.externalIds.get("DOI") if p.externalIds else None,
        "arxiv_id": p.externalIds.get("ArXiv") if p.externalIds else None,
        "pdf": p.openAccessPdf.get("url") if p.openAccessPdf else None,
        "abstract": (p.abstract or "")[:300]
    })
print(json.dumps(output, indent=2, ensure_ascii=False))
EOF
```

### 3. DuckDuckGo 보조 검색 (GitHub, 블로그 등)

```python
~/.claude/skill_venv/bin/python3 << 'EOF'
from ddgs import DDGS
import json

results = DDGS().text(
    "site:github.com MuMax3 ferrimagnet domain wall simulation",
    max_results=15
)
print(json.dumps(results, indent=2, ensure_ascii=False))
EOF
```

### 4. PDF 논문 텍스트 추출

```python
~/.claude/skill_venv/bin/python3 << 'EOF'
import pdfplumber

with pdfplumber.open("paper.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        if text:
            print(f"=== Page {i+1} ===")
            print(text[:500])
EOF
```

### 5. URL → 마크다운 스크래핑

```bash
~/.claude/skill_venv/bin/crwl "https://arxiv.org/abs/2401.12345" -o markdown
```

### 6. arXiv PDF 다운로드

```python
~/.claude/skill_venv/bin/python3 << 'EOF'
import arxiv, os

client = arxiv.Client()
paper = next(client.results(arxiv.Search(id_list=["2401.12345"])))
paper.download_pdf(dirpath="./papers/", filename="paper.pdf")
print(f"Downloaded: {paper.title}")
EOF
```

## MCP 사용 (Claude Code 세션 내)

`arxiv-mcp-server`와 `semantic-scholar-mcp`가 Claude Code에 등록되어 있다.
Claude Code 세션에서 자동으로 MCP 도구를 호출 가능하다.

## 프로젝트 헬퍼 스크립트

프로젝트 폴더의 `tools/` 디렉토리에 통합 검색 스크립트가 있다:

```bash
# 통합 학술 검색
~/.claude/skill_venv/bin/python3 \
  /path/to/URP_Simulation_MuMax3_References/tools/search_papers.py \
  "MuMax3 ferrimagnet domain wall" --limit 20 --output results.json
```

## 검색 전략 가이드 (MuMax3/자기학)

| 검색 대상 | 권장 도구 | 키워드 예시 |
|----------|----------|------------|
| 최신 arXiv 프리프린트 | `arxiv` 패키지 | `MuMax3 ferrimagnet 2024 2025` |
| 인용수 높은 논문 | Semantic Scholar | `domain wall mass inertia simulation` |
| GitHub 코드 | ddgs `site:github.com` | `site:github.com MuMax3 ferrimagnet` |
| 물리 리뷰 저널 | Semantic Scholar + CrossRef | `Physical Review B domain wall mass` |
| 한국어 자료 | ddgs | `도메인 월 MuMax3 시뮬레이션` |

## 주요 arXiv 카테고리 (자기학)

- `cond-mat.mes-hall` — 메조스코픽/나노구조 물리
- `cond-mat.mtrl-sci` — 재료과학
- `cond-mat.str-el` — 강상관계 전자계
- `physics.comp-ph` — 계산물리

```python
# 특정 카테고리 필터링
search = arxiv.Search(
    query="domain wall mass ferrimagnet",
    max_results=20,
    sort_by=arxiv.SortCriterion.SubmittedDate
)
```
