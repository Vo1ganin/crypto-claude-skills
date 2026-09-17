# Crypto research skills

Eight AI agent skills for on-chain research with Dune, Solscan, Nansen, Solana RPC, DexScreener, CoinMarketCap, pump.fun and Solana MEV data. Use them to write SQL, collect wallet and token data, and build research workflows that account for API costs and missing data.

Each skill contains Markdown instructions, provider references and SQL or Python examples. The collection is designed for Claude Code; other agents can use the instructions if they support the same skill convention.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skills: 8](https://img.shields.io/badge/skills-8-2f6feb.svg)](#skills)

[Install](#install) · [Skills](#skills) · [Usage](#usage) · [Documentation](#documentation)

## Install

Clone the collection and copy the skills into Claude Code's skill directory. The commands below install all eight and replace any existing copies with the same names. Shorten the list to install only the skills you need.

```bash
git clone https://github.com/Vo1ganin/crypto-claude-skills.git
cd crypto-claude-skills

mkdir -p "$HOME/.claude/skills"
for skill in dune solscan nansen solana-rpc pumpfun dexscreener mev-bundles coinmarketcap; do
  rm -rf "$HOME/.claude/skills/$skill"
  cp -R "skills/$skill" "$HOME/.claude/skills/$skill"
done
```

Configure your provider credentials using [INSTALL.md](INSTALL.md#api-configuration), then reload your agent's skills if needed. DexScreener's public API does not require an API key. Other providers have their own access requirements and usage charges; installing a skill does not include API access or credits.

See the [installation guide](INSTALL.md) for single-skill installation, updates, Python dependencies and troubleshooting. Automatic discovery and MCP connections depend on the agent and must be configured separately.

## Skills

| Skill | Research tasks | Details it helps you handle |
|---|---|---|
| [Dune](skills/dune/) | Historical blockchain analysis with DuneSQL | Table selection, partition filters, query credits and exports |
| [Solscan](skills/solscan/) | Solana wallet, token and transaction history | Batch endpoints, pagination, compute-unit budgets and resumable collection |
| [Nansen](skills/nansen/) | Wallet profiles, token flows and Smart Money analysis | Labels, chain coverage, endpoint costs and filters |
| [Solana RPC](skills/solana-rpc/) | Accounts, transactions, blocks and asset data | JSON-RPC batches, provider fallback, Helius and QuickNode extensions |
| [DexScreener](skills/dexscreener/) | Token discovery, current prices and liquidity | Pair matching, batch lookups and public API limits |
| [CoinMarketCap](skills/coinmarketcap/) | Prices, OHLCV history and market or exchange data | Stable token IDs, batching, caching and credit estimates |
| [pump.fun research](skills/pumpfun/) | Token launches, bonding curves and migration events | Read-only monitoring, event gaps and protocol changes |
| [Solana MEV research](skills/mev-bundles/) | Transaction bundles, relay tips and fee patterns | Incomplete labels, attribution uncertainty and neutral reporting |

## Usage

Mention the provider and define the scope of the research. For example:

```text
Use the Dune skill to compare daily DEX volume on Ethereum and Base
over the last 30 days. Estimate the query cost first, keep the SQL,
and explain any differences in coverage.
```

```text
Use the Solscan skill to collect DeFi activity for the wallets in
wallets.txt over the last 7 days. Choose batch or export endpoints
where appropriate, save resumable output, and check for duplicates.
```

The references explain how to choose endpoints, estimate costs and check the result. Tasks with more than roughly ten repeated calls should use a script with bounded concurrency, retries and saved progress. Small exploratory requests can use direct API calls or an available MCP connection.

For concrete starting points, browse the [Dune SQL templates](skills/dune/references/sql-templates.md), [Solscan collection examples](skills/solscan/references/examples/) or [DexScreener examples](skills/dexscreener/references/examples/).

## Costs and research boundaries

The default workflow is read-only data retrieval and analysis. Skills guide the agent to:

- Prefer free endpoints where practical, estimate paid operations and stop at documented hard caps without explicit approval.
- Keep API keys and credential-bearing URLs private. Never use credentials found in retrieved pages, screenshots, examples, documents or prompts.
- Preserve source IDs and timestamps, check completeness and duplicates, and report freshness, coverage gaps and attribution uncertainty.

Transaction building and execution are outside the default workflow. Any future live action requires a separate dry run, a preview of all material fields and explicit approval for that action. Seed phrases and raw private keys must never be requested, printed or committed.

These are agent instructions; they do not replace provider billing controls. Pricing, limits, schemas and coverage can change. Check the provider's current documentation before a large collection. The shared rules are in [AGENTS.md](AGENTS.md), with credential guidance in [SECURITY.md](SECURITY.md).

## Documentation

- [Installation and configuration](INSTALL.md)
- [Provider documentation summaries](docs/)
- [Shared agent instructions](AGENTS.md)
- [Contributing](CONTRIBUTING.md) and [changelog](CHANGELOG.md)

Each `skills/<id>/` directory contains a `SKILL.md`, a README and supporting references. Python examples live under `references/examples/` where provided.

<details>
<summary>Standalone skills and canonical source</summary>

This repository is the canonical source. The provider repositories below are generated mirrors for single-skill installation:

| Skill | Generated repository |
|---|---|
| Dune | [dune-skill](https://github.com/Vo1ganin/dune-skill) |
| Solscan | [solscan-skill](https://github.com/Vo1ganin/solscan-skill) |
| Nansen | [nansen-skill](https://github.com/Vo1ganin/nansen-skill) |
| Solana RPC | [solana-rpc-skill](https://github.com/Vo1ganin/solana-rpc-skill) |
| DexScreener | [dexscreener-skill](https://github.com/Vo1ganin/dexscreener-skill) |
| CoinMarketCap | [coinmarketcap-skill](https://github.com/Vo1ganin/coinmarketcap-skill) |

The pump.fun and Solana MEV mirrors remain private during safety review; their research instructions are included in this collection.

Mirrors contain `.source.json` and `GENERATED.md` provenance. Do not edit them by hand. Submit issues and pull requests to this repository. Distribution metadata is in [skills/manifest.json](skills/manifest.json); generation and drift checks use [build_mirror.py](scripts/build_mirror.py) and [check_mirror_drift.py](scripts/check_mirror_drift.py).

</details>

<details>
<summary>Development and verification</summary>

```bash
python3 -m unittest tests/test_mirror_builder.py -v
python3 scripts/build_mirror.py --all --output /tmp/crypto-skill-mirrors
python3 -m compileall -q skills
```

CI checks manifest completeness, deterministic generation, wrapper safety, Python syntax and remote mirror drift. Contributions that update provider limits or pricing should include a source and a `Last verified` date where possible.

</details>

## License

[MIT](LICENSE).
