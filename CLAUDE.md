# UniFi Management Tools for AI Agents

One Python package (`unifi-tools`) exposing the official UniFi Network Integration API and an
optional gateway-SSH escape hatch as both a CLI (`unifi ...`) and an MCP server (`unifi mcp`).
Not an agent — tool extensions for agents.

## Layout

- `src/unifi_tools/core.py` — config (env > `unifi init` file), FastMCP instance, tool registry, API client
- `src/unifi_tools/api.py` — 73 tools, complete documented surface of the Network API v10.3.58
- `src/unifi_tools/ssh.py` — `ssh exec` / `mongo read|write` / `provision`, enabled only when `UNIFI_SSH_KEY`/`UNIFI_SSH_PASSWORD` is set
- `src/unifi_tools/cli.py` — generic dispatcher: `unifi_list_devices` ⇄ `unifi list devices`; destructive commands need `--yes`
- `skills/unifi/` — the agent skill (read `skills/unifi/SKILL.md` before using the tools)
- `.claude-plugin/` — this repo is its own Claude Code plugin marketplace (plugin ships the skill)

## Rules

- Every tool registers as both CLI command and MCP tool via `@tool()` in core.py; `uv run pytest` asserts parity — run it after any tool change.
- API ground truth is developer.ui.com (currently v10.3.58), not this codebase. Verify against docs before changing payloads.
- SSH/MongoDB is only for what the API doesn't expose (radio config, port profiles, settings). After DB writes, force-provision (`unifi provision <macs>`).
- Local dev MCP config lives in untracked `.mcp.json`; credentials in untracked `.env` / the `unifi init` config file.
