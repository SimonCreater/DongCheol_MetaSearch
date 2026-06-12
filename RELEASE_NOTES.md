# Release Notes

## 0.4.0 - Claude Code + Codex

- Added first-class Codex support while preserving the existing Claude Code install path.
- Extended `setup/install.sh` with `--target claude|codex|both`, `--register-codex-mcp`, `--email`, and `PYTHON_BIN` support.
- Added Codex MCP template generation for `~/.codex/config.toml` and automatic `codex mcp add` registration for `arxiv-mcp-server`, `asta`, and `paper-search-mcp`.
- Added Codex `agents/openai.yaml` metadata for both skills, with Asta declared as the safe auto-installable HTTP MCP dependency.
- Kept all source buckets A-G and depth levels L1-L5 available in Codex; `SKILL.md` now states the core MCP engines and bucket map directly.
- Pinned `chardet==5.2.0` to avoid `requests` compatibility warnings in fresh skill venvs.
- Updated English and Korean README instructions for Claude Code, Codex, and dual-host installs.

Validation performed:

- `quick_validate.py` passes for `scholar-megasearch` and `arxiv-search`.
- Codex install completed into `$HOME/.agents/skills` and registered all three MCP servers.
- Fresh `codex exec` invocation loaded `$scholar-megasearch` and recognized L1-L5, A-G, and the expected MCP servers.
- MCP initialize/tools-list probes succeeded for `arxiv-mcp-server`, `paper-search-mcp`, and Ai2 Asta.
