<h1 align="center">scholar-megasearch</h1>

<p align="center">
  <strong>Claude Code를 위한 대규모 멀티소스 학술 논문 검색.</strong><br>
  <em>20개 이상의 학술 DB에 서브에이전트를 팬아웃해, 모든 결과를 하나의 중복제거된 코퍼스로 병합하고 원본 PDF까지 확보하는 단일 스킬.</em>
</p>

<p align="center">
  <a href="./README.md">English README</a>
  &nbsp;·&nbsp;
  <a href="./skills/scholar-megasearch/SKILL.md">SKILL.md</a>
  &nbsp;·&nbsp;
  <a href="./skills/scholar-megasearch/references/sources.md">소스 카탈로그</a>
  &nbsp;·&nbsp;
  <a href="./skills/scholar-megasearch/references/orchestration.md">오케스트레이션</a>
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

> **한 줄 요약:** Claude Code에 주제를 던지면, 중복제거·출처추적·랭킹된 단일 논문 코퍼스를
> PDF까지 디스크에 담아 돌려준다.

- 🔭 **한 번에 20개 이상 DB** — arXiv, Semantic Scholar, Crossref, OpenAlex, PubMed/PMC, bioRxiv/medRxiv, DOAJ, CORE, BASE, OpenAIRE, Zenodo, Unpaywall, HAL, DBLP, IACR, SSRN, CiteSeerX, Europe PMC, 그리고 웹/GitHub.
- 🧵 **서브에이전트 팬아웃** — 소스 버킷당 검색 에이전트 1개를 병렬 실행 → 넓은 커버리지를 직렬 대기 없이.
- 🧹 **출처를 동반한 중복제거** — DOI → arXiv-id → 정규화 제목으로 병합하고, 각 논문이 *어떤* DB에서 나왔는지 기록.
- 📊 **교차 검증 랭킹** — 독립된 DB가 더 많이 잡아낸 논문이 상위로 — SEO 잘 된 논문이 아니라.
- 📄 **원본 PDF** — 상위 K편을 오픈액세스 경로로 자동 확보, 받은 것·페이월 폴백 필요한 것을 manifest로 기록.
- 🧭 **도메인 인식 라우팅** — 물리·생명과학·CS·암호·경제·수학마다 알맞은 DB 부분집합을 자동 선택.

## 왜 필요한가

DB를 하나씩 검색하는 방식이 좋은 논문을 놓치는 이유다. arXiv는 출판본의 인용수를 보여주지
않고, Semantic Scholar는 bioRxiv 프리프린트를 안 띄우며, Google Scholar는 그 결과가 다른
세 개 인덱스에도 있는지 알려주지 않는다. 결국 같은 쿼리를 탭 다섯 개에 돌리고, 문서에
복붙하고, 손으로 중복을 거르고, PDF를 따로따로 사냥하게 된다.

`scholar-megasearch`는 이걸 한 번의 요청으로 압축한다. "문헌 검색"을 팬아웃 문제로 다룬다 —
주제를 분해하고, 각 **소스 버킷**을 독립 서브에이전트에 보내고, 사후에 전부 화해시킨다.
산출물은 채팅 답변이 아니라 디스크 위의 코퍼스다. 모든 항목이 중복제거되고, 몇 개의 독립
DB가 교차 검증하는지로 랭킹되며, 무료 경로가 있으면 PDF가 함께 받쳐진다.

## 동작 방식

<p align="center">
  <img src="./docs/pipeline.png" width="900" alt="scholar-megasearch 파이프라인: 주제 → facet 분해 → 소스 버킷당 서브에이전트 팬아웃 → merge_corpus.py(중복제거+랭킹) → fetch_pdfs.py → 합성">
</p>

오케스트레이션은 가능할 때 결정론적 **Workflow**로, 아니면 직접 **Agent** 팬아웃으로
폴백한다. 도메인 → 버킷 라우팅 표가 주제별로 알맞은 4~7개 버킷을 고른다.

### 중복제거 & 랭킹

서로 다른 DB의 레코드는 정규화 DOI · (버전 제거한) arXiv id · 정규화 제목 중 **하나라도**
일치하면 병합된다. 병합된 레코드는 필드별로 가장 풍부한 값(가장 긴 초록, 가장 완전한 저자
목록, 최대 인용수)을 유지하고, 그것을 잡아낸 **소스 집합**을 누적한다. 랭킹은
`(소스 개수, 인용수, 연도)` 내림차순. `--min-sources 2`를 주면 두 개 이상 DB가 교차 검증한
논문만 남겨 단일 인덱스 노이즈를 걸러낸 고정밀 shortlist를 얻는다.

### 전형적인 실행 예시

집중된 주제에 대한 중간 깊이 스윕(≈ **L3 Deep**)은 대략 이렇다 *(예시 수치)*:

```
주제: "ferrimagnet의 spin–orbit torque switching"
  facets:  서브쿼리 6개        buckets: A B C E G (검색 에이전트 5개)
  raw hits: 버킷 합산 ~310건
  unique:   중복제거 후 ~150건  (≈60건은 2개 이상 DB 교차검증)
  PDFs:     25편 중 22편 확보   (3편 needs_mcp — 페이월)
  output:   ./literature_search/spin-orbit-torque-ferri_2026-05-29/
```

## 설치

```bash
git clone https://github.com/TaewoooPark/scholar-megasearch.git
cd scholar-megasearch
bash setup/install.sh you@example.com      # Unpaywall OA + arXiv 예의용 이메일
```

스크립트는 스킬을 `~/.claude/skills/`에 설치하고, `~/.claude/skill_venv`와
`~/.claude/paper_search_mcp_venv`를 빌드하며, MCP 서버 3종을 clone/설치하고
(`paper-search-mcp`는 git main — PyPI 빌드는 Crossref/OpenAlex 미포함),
`setup/mcp.servers.resolved.json`을 생성한다. 그 파일의 `mcpServers` 항목을
`~/.claude.json`에 병합한 뒤 Claude Code를 재시작하면 된다.

**요구사항**

| | |
|---|---|
| Python | 3.11+ |
| [`uv`](https://astral.sh/uv) | `uvx arxiv-mcp-server`용 |
| `git` | 설치 시 `semantic-scholar-mcp` clone |
| Claude Code | 스킬은 세션 안에서 트리거됨 |

## 사용법

Claude Code 안에서 자연어로 스킬을 트리거한다:

```
도메인월 측정 논문 방대하게 검색해줘, PDF까지
spin–orbit torque switching 모든 DB에서 다 찾고 PDF까지 받아줘
```

또는 스크립트를 직접 실행:

```bash
# 소스별 결과 파일을 하나의 랭킹 코퍼스로 병합
python3 ~/.claude/skills/scholar-megasearch/scripts/merge_corpus.py \
  ./literature_search/<주제>_<날짜>/raw \
  -o corpus.json --md corpus.md --min-sources 2

# 상위 25편 원본 PDF 확보
python3 ~/.claude/skills/scholar-megasearch/scripts/fetch_pdfs.py \
  corpus.json -o ./pdfs --email you@example.com --top 25
```

### 깊이 단계 (L1–L5)

하나의 노브가 **너비**(facets × buckets × 쿼리당 hits)와 **재귀**(추가 웨이브)를 함께
스케일한다. 실행마다 레벨을 고른다 — 명시적 `depth=N` / `LN` / 맨숫자 `1–5`가 최우선,
없으면 표현으로 추론(`빠르게`/`quick` → L1 … `전수조사`/`every source` → L5),
그래도 없으면 **L2** 기본.

| 레벨 | facets | buckets | 쿼리당 hits | 웨이브 | 산출물 |
|------|:------:|:-------:|:----------:|--------|--------|
| **L1 · Quick** | 3 | 4 | 15 | 웨이브 1 | corpus |
| **L2 · Standard** *(기본)* | 5 | 5 | 25 | 웨이브 1 | corpus |
| **L3 · Deep** | 6 | 6 | 30 | + 인용 스노우볼 | corpus |
| **L4 · Exhaustive** | 8 | 7 (전체) | 40 | + 스노우볼 + completeness-critic 패스 | corpus + ≥2 shortlist |
| **L5 · Total** (전수조사) | 8 | 7 (전체) | 40 | + 스노우볼 + critic 루프(고갈까지) | corpus + ≥2 shortlist |

각 웨이브는 팬아웃 후 *같은* 코퍼스로 병합된다. **인용 스노우볼**(L3+)은 상위 DOI/arXiv
id를 인용 그래프에 재투입하고, **completeness-critic**(L4+)은 누락된 하위주제·저자를 짚어
다음 웨이브의 facet으로 삼으며 L5에서는 고갈될 때까지 반복한다. L4/L5는 `--min-sources 2`
shortlist도 함께 낸다. 상위 레벨일수록 서브에이전트와 토큰을 더 쓴다 — L5는 토큰 budget만이
상한이다.

## 산출물

모든 결과는 작업 디렉토리의 `./literature_search/<주제>_<날짜>/` 아래에 저장된다:

```
literature_search/<주제>_<날짜>/
├── raw/<bucket>.json     # 소스별 검색 결과 (서브에이전트당 1파일)
├── corpus.json           # 중복제거·랭킹·출처추적 코퍼스
├── corpus.md             # 사람이 읽는 다이제스트
├── pdfs/                  # 확보한 원본 PDF + manifest.json
└── summary.md            # 합성 리뷰
```

## 소스 버킷

| 버킷 | DB |
|--------|-----------|
| A · 프리프린트 | arXiv (검색 · 시맨틱 · 인용 그래프) |
| B · 인용 | Semantic Scholar (2억+, 인용수) |
| C · DOI / 출판본 | Crossref, OpenAlex |
| D · 생명과학 | PubMed, PMC, bioRxiv, medRxiv, Europe PMC |
| E · 오픈액세스 | DOAJ, CORE, BASE, OpenAIRE, Zenodo, Unpaywall, HAL |
| F · 도메인 특화 | DBLP (CS), IACR (암호), SSRN (경제/법), CiteSeerX |
| G · 웹 | DuckDuckGo, GitHub, crawl4ai / firecrawl |

### 도메인 → 버킷 라우팅

| 주제 도메인 | 항상 | 추가 |
|---|---|---|
| 물리 / 재료 / cond-mat | A · B · C | E · G |
| CS / ML / 시스템 | A · B · F (DBLP) | C · G (GitHub) |
| 생물 / 의학 / 신경 | D · B · C | E |
| 암호 / 보안 | A · F (IACR) · B | G (GitHub) |
| 경제 / 사회과학 / 법 | F (SSRN) · B · C | G |
| 수학 | A · B · C | F |
| 학제간 / 미상 | A · B · C · D | E · G |

버킷별 전체 도구 목록은
[`skills/scholar-megasearch/references/sources.md`](./skills/scholar-megasearch/references/sources.md)에,
오케스트레이션 템플릿(Workflow + Agent 팬아웃)과 레코드 스키마는
[`references/orchestration.md`](./skills/scholar-megasearch/references/orchestration.md)에 있다.

## 저장소 구조

```
scholar-megasearch/
├── README.md · README.ko.md · LICENSE
├── setup/
│   ├── install.sh            # 스킬 + venv + MCP 서버 + 해석된 설정
│   ├── requirements.txt      # 고정 버전 검색/획득 의존성
│   └── mcp.servers.json      # ~/.claude.json용 MCP 등록 템플릿
└── skills/
    ├── scholar-megasearch/   # 스킬 본체
    │   ├── SKILL.md
    │   ├── references/{sources.md, orchestration.md}
    │   └── scripts/{merge_corpus.py, fetch_pdfs.py, search_local.py}
    └── arxiv-search/          # 보조 venv 검색 스킬
```

이 저장소에는 원본 MIT 라이선스 작업(스킬 2종 + 설치 스크립트)만 포함된다. MCP 서버 3종은
**벤더링하지 않으며**, `setup/install.sh`가 설치 시점에 각 상위 소스에서 가져온다.
[출처](#출처-attribution) 참조.

## 참고 & 한계

- **PDF 확보는 오픈액세스 우선.** `fetch_pdfs.py`는 무료·합법 경로(알려진 OA `pdf_url`,
  arXiv, Unpaywall)만 쓰고 모든 파일이 진짜 `%PDF-`인지 검증한다. 폐쇄형 논문은 manifest에
  `needs_mcp`로 표기되며, 그 확보는 세션의 MCP 다운로드 도구에 맡긴다.
- **arXiv는 헤비 팬아웃에 레이트리밋(HTTP 429)을 건다.** 검색 에이전트는 요청을 분산하고
  arXiv가 막으면 Semantic Scholar / OpenAlex에 의존한다.
- **`paper-search-mcp`는 반드시 git-main 빌드.** PyPI 릴리스는 Crossref·OpenAlex가 빠져
  있다 — 설치 스크립트가 처리한다.
- **claude.ai Scholar Gateway는 best-effort** — 헤드리스/크론 실행에서 없을 수 있어, 어떤
  버킷의 유일한 소스로도 쓰지 않는다.
- **정직한 합성.** `summary.md`는 실제로 검색한 것과 실패한 소스를 보고하며, 공백을 메우려고
  무엇도 날조하지 않는다.

## 출처 (Attribution)

MCP 서버는 모두 서드파티 프로젝트이며, `setup/install.sh`가 상위 소스에서 설치한다 —
이 저장소에는 그들의 코드를 재배포하지 않는다:

- **semantic-scholar-mcp** — [JackKuo666/semanticscholar-MCP-Server](https://github.com/JackKuo666/semanticscholar-MCP-Server) (설치 시 clone)
- **paper-search-mcp** — [openags/paper-search-mcp](https://github.com/openags/paper-search-mcp) (git main에서 pip 설치)
- **arxiv-mcp-server** — `uvx`로 온디맨드 실행

이 저장소의 원본 작업(`scholar-megasearch`·`arxiv-search` 스킬과 설치 스크립트)은
[MIT License](./LICENSE)로 배포된다.
