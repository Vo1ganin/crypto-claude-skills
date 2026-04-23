# Crypto Claude Skills

> Production-ready [Claude Code](https://claude.com/claude-code) skills for on-chain data APIs — Dune Analytics, Solscan Pro, Nansen, and universal Solana RPC (Helius / QuickNode / any provider).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Skills: 4](https://img.shields.io/badge/skills-4-blue.svg)](#skills)
[![Powered by Claude](https://img.shields.io/badge/powered%20by-Claude%20Code-ff6b6b.svg)](https://claude.com/claude-code)

Each skill enforces **credit budget rules**, prefers **batch/parsed APIs over raw loops**, and ships with **ready-to-run async Python examples** — built from real-world on-chain research (copytrade analysis, bot reverse-engineering, wallet profiling).

---

## Table of Contents

- [Skills](#skills)
- [Install](#install)
- [Configure API keys](#configure-api-keys)
- [Design principles](#design-principles)
- [Repository layout](#repository-layout)
- [Contributing](#contributing)
- [License](#license)

---

## Skills

| Skill | Use for | Signature feature |
|-------|---------|-------------------|
| [**dune**](skills/dune) | SQL on 100+ chains (Dune Analytics) | 500 / 700 credit budget gates, FREE ↔ PAID key rotation, partition-pruning SQL templates |
| [**solscan**](skills/solscan) | Solana wallet/token/NFT data (Solscan Pro v2) | Export endpoints = 15× cheaper than pagination, multi-endpoints = 50× cheaper than loops |
| [**nansen**](skills/nansen) | Smart Money + wallet profiling on 37 chains | `premium_labels: true` 30× cost trap, live credit balance headers |
| [**solana-rpc**](skills/solana-rpc) | Raw Solana RPC (Helius / QuickNode / Ankr / …) | JSON-RPC array batching, DAS over `getProgramAccounts`, Helius Enhanced Tx |

Each skill folder contains `SKILL.md`, topic `references/*.md`, and runnable `references/examples/*.py`.

---

## Install

```bash
# Clone
git clone https://github.com/YOUR-USERNAME/crypto-claude-skills.git
cd crypto-claude-skills

# Install all four skills to Claude Code
mkdir -p ~/.claude/skills
for s in dune solscan nansen solana-rpc; do
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
