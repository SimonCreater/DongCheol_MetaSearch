#!/usr/bin/env bash
# scholar-megasearch installer
# Reconstitutes the scholar-megasearch literature-search stack on a fresh machine:
#   1. installs the skills into ~/.claude/skills/
#   2. builds the search/acquisition venv (~/.claude/skill_venv) from requirements.txt
#   3. installs the local MCP servers (arxiv-mcp-server via uvx, paper-search-mcp from
#      git main); Semantic Scholar (Bucket B) uses the REMOTE Ai2 Asta MCP — no install,
#      and it works WITHOUT a key (rate-limited)
#   4. emits a resolved MCP config you can merge into ~/.claude.json
#
# Usage:  bash setup/install.sh [you@example.com]
#   The optional email is used for the Unpaywall OA lookup + arXiv politeness.
#   Semantic Scholar (Asta) needs no key for basic use. For higher rate limits,
#   request a free key at https://allenai.org/asta/resources/mcp and add a header to
#   the asta entry in ~/.claude.json:  "headers": { "x-api-key": "YOUR_ASTA_KEY" }
#   (paste the literal key — do NOT use a ${ENV} placeholder; it is sent verbatim and
#   rejected with HTTP 403). Asta use is subject to Ai2's License Agreement + Terms of
#   Use; Semantic Scholar data is ODC-BY.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SKILLS_DST="${HOME}/.claude/skills"
SKILL_VENV="${HOME}/.claude/skill_venv"
PSM_VENV="${HOME}/.claude/paper_search_mcp_venv"
EMAIL="${1:-you@example.com}"

echo "==> scholar-megasearch install"
echo "    repo:   ${REPO_DIR}"
echo "    skills: ${SKILLS_DST}"

# --- 1. skills ---------------------------------------------------------------
mkdir -p "${SKILLS_DST}"
for s in scholar-megasearch arxiv-search; do
  echo "==> installing skill: ${s}"
  rm -rf "${SKILLS_DST:?}/${s}"
  cp -R "${REPO_DIR}/skills/${s}" "${SKILLS_DST}/${s}"
done

# --- 2. search/acquisition venv ---------------------------------------------
if [ ! -d "${SKILL_VENV}" ]; then
  echo "==> creating skill_venv at ${SKILL_VENV}"
  python3 -m venv "${SKILL_VENV}"
fi
echo "==> installing Python deps into skill_venv"
"${SKILL_VENV}/bin/python" -m pip install -q --upgrade pip
"${SKILL_VENV}/bin/python" -m pip install -q -r "${REPO_DIR}/setup/requirements.txt"

# --- 3. MCP servers ----------------------------------------------------------
# Semantic Scholar (Bucket B) is the official Ai2 Asta Scientific Corpus Tool — a
# REMOTE MCP (https://asta-tools.allen.ai/mcp/v1), so there is nothing to clone or
# run locally, and it works WITHOUT a key (rate-limited). For higher limits, request a
# free key at https://allenai.org/asta/resources/mcp and add an x-api-key header to the
# asta entry in ~/.claude.json (paste the literal key — Asta use is subject to Ai2's
# License Agreement + Terms of Use).
# Remove any superseded local semantic-scholar-mcp clone from older installs.
rm -rf "${SKILLS_DST:?}/semantic-scholar-mcp"
echo "==> Semantic Scholar uses the remote Ai2 Asta MCP (no local install, no key needed)"

# paper-search-mcp MUST be the git-main build (the PyPI build lacks Crossref/OpenAlex).
if [ ! -d "${PSM_VENV}" ]; then
  echo "==> creating paper_search_mcp_venv at ${PSM_VENV}"
  python3 -m venv "${PSM_VENV}"
fi
echo "==> installing paper-search-mcp (git main)"
"${PSM_VENV}/bin/python" -m pip install -q --upgrade pip
"${PSM_VENV}/bin/python" -m pip install -q "git+https://github.com/openags/paper-search-mcp.git"

# arxiv-mcp-server is launched on demand via uvx (no persistent install needed).
if ! command -v uvx >/dev/null 2>&1; then
  echo "!!  uvx not found. Install uv:  curl -LsSf https://astral.sh/uv/install.sh | sh"
fi

# --- 4. resolved MCP config --------------------------------------------------
RESOLVED="${REPO_DIR}/setup/mcp.servers.resolved.json"
sed -e "s|HOME|${HOME}|g" -e "s|you@example.com|${EMAIL}|g" \
    "${REPO_DIR}/setup/mcp.servers.json" > "${RESOLVED}"
echo "==> wrote resolved MCP config: ${RESOLVED}"
echo
echo "Done. Final steps — register the MCP servers:"
echo "  1. merge the \"mcpServers\" entries from ${RESOLVED}"
echo "     into the \"mcpServers\" block of ~/.claude.json"
echo "  2. (optional) higher Semantic Scholar limits: request a free key at"
echo "     https://allenai.org/asta/resources/mcp and add to the asta entry:"
echo "       \"headers\": { \"x-api-key\": \"YOUR_ASTA_KEY\" }"
echo "  3. restart Claude Code."
echo
echo "Verify the skill loads:  ask Claude '논문 방대하게 검색' or run"
echo "  python3 ${SKILLS_DST}/scholar-megasearch/scripts/merge_corpus.py --help"
