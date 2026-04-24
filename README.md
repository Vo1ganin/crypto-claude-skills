# Crypto Claude Skills

> Production-ready [Claude Code](https://claude.com/claude-code) skills for on-chain data APIs — Dune Analytics, Solscan Pro, Nansen, and universal Solana RPC (Helius / QuickNode / any provider).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skills: 7](https://img.shields.io/badge/skills-7-blue.svg)](#skills)
[![Powered by Claude](https://img.shields.io/badge/powered%20by-Claude%20Code-ff6b6b.svg)](https://claude.com/claude-code)
[![Cross-agent](https://img.shields.io/badge/agents-Claude%20%7C%20Codex%20%7C%20Cursor-brightgreen.svg)](AGENTS.md)

Each skill enforces **credit budget rules**, prefers **batch/parsed APIs over raw loops**, and ships with **ready-to-run async Python examples** — built from real-world on-chain research (copytrade analysis, bot reverse-engineering, wallet profiling).

---

## Table of Contents

- [Skills](#skills)
- [Install](#install)
- [Configure API keys](#configure-api-keys)
- [Cross-agent support](#cross-agent-support)
- [Design principles](#design-principles)
- [Repository layout](#repository-layout)
- [Contributing](#contributing)
- [License](#license)

---

## Skills

| Skill | Standalone repo | Use for | Signature feature |
|-------|-----------------|---------|-------------------|
| [**dune**](skills/dune) | [`dune-skill`](https://github.com/Vo1ganin/dune-skill) | SQL on 100+ chains (Dune Analytics) | 500 / 700 credit budget gates, FREE ↔ PAID key rotation |
| [**solscan**](skills/solscan) | [`solscan-skill`](https://github.com/Vo1ganin/solscan-skill) | Solana wallet/token/NFT data (Solscan Pro v2) | Export endpoints 15× cheaper than pagination, multi-endpoints 50× cheaper |
| [**nansen**](skills/nansen) | [`nansen-skill`](https://github.com/Vo1ganin/nansen-skill) | Smart Money + wallet profiling on 37 chains | `premium_labels: true` 30× cost trap, live credit balance headers |
| [**solana-rpc**](skills/solana-rpc) | [`solana-rpc-skill`](https://github.com/Vo1ganin/solana-rpc-skill) | Raw Solana RPC (Helius / QuickNode / Ankr / …) | JSON-RPC array batching, DAS over `getProgramAccounts`, Helius Enhanced Tx |
| [**pumpfun**](skills/pumpfun) | [`pumpfun-skill`](https://github.com/Vo1ganin/pumpfun-skill) | pump.fun bonding curves + PumpPortal API | WebSocket streaming (single-conn rule), Lightning vs Local trading, sniper/copytrade examples |
| [**dexscreener**](skills/dexscreener) | [`dexscreener-skill`](https://github.com/Vo1ganin/dexscreener-skill) | Current DEX pair data across 20+ chains | Free/no-auth API, batch 30 tokens per call, 300 rpm fast tier |
| [**mev-bundles**](skills/mev-bundles) | [`mev-bundles-skill`](https://github.com/Vo1ganin/mev-bundles-skill) | MEV bundles + bribes: what/how to find/how to identify | Jito + 8 other relays (Bloxroute, Nozomi, Astralane, BlockRazor, Stellium, Falcon, Flashblocks, 1node), sandwich detection |

Each skill folder contains `SKILL.md`, topic `references/*.md`, and runnable `references/examples/*.py`. Each skill is also available as a **standalone public GitHub repo** — install just the one you need from its own repo.

---

## Install

```bash
# Clone
git clone https://github.com/Vo1ganin/crypto-claude-skills.git
cd crypto-claude-skills

# Install all seven skills to Claude Code
mkdir -p ~/.claude/skills
for s in dune solscan nansen solana-rpc pumpfun dexscreener mev-bundles; do
  cp -R skills/$s ~/.claude/skills/
done
```

Restart Claude Code. Skills trigger automatically based on your prompt (e.g. "analyze this Solana wallet" → Solscan or solana-rpc fires).

For one-at-a-time install or to run Python examples standalone, see [`INSTALL.md`](INSTALL.md).

---

## Configure API keys

```bash
cp .env.example .env
# edit .env with your keys
set -a; source .env; set +a
```

| Variable | For |
|----------|-----|
| `DUNE_API_KEY_FREE` | Dune (default) |
| `DUNE_API_KEY_PAID` | Dune (bulk exports, optional) |
| `SOLSCAN_API_KEY` | Solscan Pro v2 |
| `NANSEN_API_KEY` | Nansen |
| `SOLANA_RPC_URL` | Any Solana RPC provider (Helius, QuickNode, …) |

Full key reference with examples in [`.env.example`](.env.example).

---

## Cross-agent support

Primary target is Claude Code — but the content works across other AI coding agents too.

| Agent | What to do | How it's used |
|-------|-----------|---------------|
| **Claude Code** | `cp -R skills/<name> ~/.claude/skills/` | Auto-triggers on prompt keywords |
| **Claude Agent SDK** | Load `SKILL.md` programmatically | Your own Claude-based bot |
| **OpenAI Codex / Codex CLI** | Reads [`AGENTS.md`](AGENTS.md) automatically on project load | Cross-skill instructions |
| **Cursor / Windsurf** | Copy `SKILL.md` into `.cursor/rules/` | Per-project rules |
| **MCP-aware clients** (Claude, Cursor, ChatGPT, Codex, OpenCode) | Configure Dune + Solscan MCP servers per `.env.example` | Tool calls work natively |
| **Any LLM via API** | Include `SKILL.md` as system prompt | Self-contained instructions |

Note: `skills/*/references/examples/*.py` are provider-agnostic — they work with plain Python, no assistant needed.

See [`AGENTS.md`](AGENTS.md) for the full agents.md-spec instruction set.

---

## Design principles

### 💰 Credits are real money
Every skill enforces budget thresholds **before** expensive calls. Dune: 500 warn / 700 block per operation. Nansen: 50 warn / 200 block. Skills announce estimated cost and reason when approaching a threshold and refuse to proceed above the hard limit without explicit user approval.

### 🤖 Scripts for batches, MCP for exploration
- ≤ 10 API calls → MCP tools or inline `curl`
- \> 10 calls of the same shape → async Python script with `asyncio.Semaphore`, resume-safe JSONL output, live rate-limit monitoring via response headers

MCP-in-a-loop is a documented antipattern — see each skill's `references/*-patterns.md`.

### 🚀 Parsed > raw, batch > loop
- Helius **Enhanced Transactions** > `getSignaturesForAddress` + N × `getTransaction`
- DAS **`getAssetsByOwner`** > `getTokenAccountsByOwner` + metadata
- Solscan **`transaction/detail/multi`** (50 sigs / 100 CU) > 50 × `transaction/detail` (5000 CU)
- Dune **`VALUES` batch clauses** > many small queries
- **JSON-RPC array requests** > N sequential HTTP POSTs

### 🔁 Multi-key rotation (safely)
Dune and Nansen skills support multiple keys per tier. On `402`/`429` they rotate FREE keys automatically. Escalation to PAID key requires **explicit user consent** every time — never silent.

---

## Repository layout

```
crypto-claude-skills/
├── README.md                 ← you are here
├── INSTALL.md                ← step-by-step install & troubleshooting
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── .env.example              ← key template (never commit .env)
├── .gitignore
├── docs/                     ← per-provider documentation corpus
│   ├── dune/
│   ├── solscan/
│   ├── nansen/               ← includes llms-full.txt (official LLM-ready docs)
│   └── quicknode/            ← Solana RPC + Helius llms.txt
└── skills/                   ← four Claude Code skills (copy to ~/.claude/skills/)
    ├── dune/
    ├── solscan/
    ├── nansen/
    └── solana-rpc/
```

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Particularly welcome:
- New provider extensions (Triton, Ankr, Chainstack specifics)
- Additional `references/examples/*.py` scripts for common use cases
- Cost/limit table updates when providers change pricing

---

## License

[MIT](LICENSE)
