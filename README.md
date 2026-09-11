# UniFi Management Tools for AI Agents

**This is not an AI agent.** It's the UniFi toolset you plug into the agent you already use —
Claude Code, Codex, Cursor, Gemini CLI, or any MCP client. One Python package exposes the
official [UniFi Network API](https://developer.ui.com/) (plus an optional SSH escape hatch for
what the API doesn't cover) as:

- a **CLI** (`unifi list devices`, `unifi create wifi ...`) your agent drives through its shell — near-zero context cost, argument-level permissioning
- an **MCP server** (`unifi mcp`) for clients without a shell — same tools, same names
- a **skill** with battle-tested payloads and gotchas, so agents get it right on the first try

Built on the official Integration API with API-key auth only — no controller passwords, no
private-API scraping.

## What can it do?

Ask your agent things like:

- "List all devices and show me which ones have high CPU usage"
- "Create a guest network on VLAN 50 with a captive portal"
- "Block IoT devices from reaching the management VLAN"
- "Generate 20 hotspot vouchers for tomorrow's event, 24hr limit, 10Mbps cap"
- "Change all AP channel widths to 160MHz" *(via the SSH escape hatch)*

73 commands cover devices, clients, networks/VLANs, WiFi, zone-based firewall policies, ACLs,
DNS policies, traffic lists, vouchers, VPN/WAN/RADIUS/DPI — the complete documented surface of
the UniFi Network API (v10.3.58).

## Setup

### 1. What you need

| | Where to get it |
|---|---|
| **Controller URL** (required) | Your gateway's address, e.g. `https://192.168.1.1`. It's the address you open the UniFi web UI at. Self-hosted UniFi OS Server uses port `11443`. |
| **API key** (required) | UniFi web UI → **Settings → Control Plane → Integrations → Create API Key**. It is shown **once** — copy it immediately. Needs a UniFi OS console (Dream Machine, Cloud Gateway, CloudKey) or UniFi OS Server; legacy self-hosted controllers don't support API keys. |
| Site ID (optional) | Skip it — single-site controllers auto-resolve. Multi-site: pick from `unifi list sites`. |
| Gateway SSH password (optional) | Only for the [SSH escape hatch](#ssh-escape-hatch-optional). UniFi web UI → **Settings → System → Advanced → Device SSH Authentication** (enable + set a password). |

### 2. Where it goes — one place

All configuration lives in **one file**, written for you by `unifi init`:

- Windows: `%APPDATA%\unifi-tools\config.json`
- macOS/Linux: `~/.config/unifi-tools/config.json`

```bash
# install the CLI (only prerequisite is uv, which auto-provisions Python —
# get it with `winget install astral-sh.uv` or `curl -LsSf https://astral.sh/uv/install.sh | sh`)
uv tool install unifi-tools

unifi init            # prompts for the values above and writes the config file
unifi get app info    # verify — should print your controller version
```

Non-interactive: `unifi init --host https://192.168.1.1 --api-key XXXX [--site-id ID] [--ssh-password PW | --ssh-key ~/.ssh/id_ed25519]`.

Environment variables with the same names (`UNIFI_HOST`, `UNIFI_API_KEY`, `UNIFI_SITE_ID`, `UNIFI_SSH_KEY`, `UNIFI_SSH_PASSWORD`, `UNIFI_READ_ONLY`, `UNIFI_VERIFY_SSL`) override the file — useful for MCP client env blocks and read-only sessions. There is no other config location.

### 3. Connect your agent

| Agent | Setup |
|-------|-------|
| **Claude Code** | `/plugin marketplace add brianbell-x/Unifi-Agent` then `/plugin install unifi@unifi-tools` — installs the skill; the agent uses the CLI |
| **Other shell agents** (Codex, Cursor, Gemini CLI...) | Copy `skills/unifi/` into your agent's skills directory (or `npx skills add brianbell-x/Unifi-Agent`) |
| **MCP clients without a shell** (Claude Desktop...) | `{"command": "uvx", "args": ["unifi-tools", "mcp"]}` — config comes from the same file, or pass an `env` block to override |

That's it. Run `unifi` for the full command list.

## Safety

- **Destructive commands require `--yes`** (delete/remove/restart/power-cycle/mongo writes).
- **`UNIFI_READ_ONLY=true`** blocks every write at the API layer — hand a read-only toolset to any agent.
- Reads and writes are prefix-separable for agent permission rules: allow `unifi list *` and `unifi get *`, prompt on the rest.
- **`UNIFI_VERIFY_SSL=true`** enforces TLS verification (off by default — UniFi consoles ship self-signed certificates).

## SSH escape hatch (optional)

The official API doesn't expose radio config (channel width, TX power, min-RSSI), per-port
profiles, or controller settings. Setting `UNIFI_SSH_KEY` (or `UNIFI_SSH_PASSWORD`) enables
three extra primitives against the gateway — `unifi ssh exec`, `unifi mongo read|write`,
`unifi provision` — used as: resolve via API → write MongoDB → force-provision → verify via API.

```bash
unifi mongo write "db.device.updateMany({model:'U7P'}, {\$set:{'radio_table.\$[r].ht':'160'}}, {arrayFilters:[{'r.radio':'na'}]})" --yes
unifi provision aa:bb:cc:dd:ee:01 --yes
```

MongoDB writes are unsupported by Ubiquiti and schema-drift across firmware — the skill teaches
agents to never use SSH for anything the API covers.

## Custom integrations

Paid integration work can be scoped for a specific UniFi workflow or another documented API.
Python CLI and MCP interfaces, source code, tests, and setup instructions can be included.

Project inquiries can be sent to [me@brianbell.xyz](mailto:me@brianbell.xyz) with the API
documentation and a short example of the workflow. Scope, price, test access, and acceptance
checks are agreed before work begins. AI-assisted development is used.

## Development

```bash
git clone https://github.com/brianbell-x/Unifi-Agent && cd Unifi-Agent
uv run pytest          # offline test suite (parity, gates, mocked API)
uv run unifi --help
```

`src/unifi_tools/`: `core.py` (config, registry, API client), `api.py` (73 API tools),
`ssh.py` (gateway escape hatch), `cli.py` (CLI face + `mcp` subcommand). Every tool function
registers as both a CLI command and an MCP tool — the test suite asserts the two faces never drift.

## License

[MIT](LICENSE). Not affiliated with or endorsed by Ubiquiti Inc.
