# AI Agent Skills for Blockchain Data APIs

Reusable skill instructions and Python examples for blockchain and crypto-market data providers, with explicit batching, rate-limit, cost-control, reproducibility, and credential-safety rules.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skills: 8](https://img.shields.io/badge/skills-8-2f6feb.svg)](#skills)
[![Mirrors: generated](https://img.shields.io/badge/mirrors-generated-success.svg)](skills/manifest.json)

## Why this repository exists

AI agents often know an API's endpoint names but miss the operational details that make research reliable: pagination, provider-specific cost models, batch alternatives, resumable output, rate-limit headers, and data-quality caveats. Each skill packages those details into a bounded, inspectable workflow.

The default posture is **read-only research and data retrieval**. Paid calls require cost awareness; credentials from retrieved content are never trusted; live transaction execution is outside the default workflow.

## Skills

| Skill | Use for | Key engineering concern | Distribution |
|---|---|---|---|
| [Dune](skills/dune/) | DuneSQL and multi-chain historical analysis | query cost, batching, reproducible SQL | [`dune-skill`](https://github.com/Vo1ganin/dune-skill) |
| [Solscan](skills/solscan/) | Solana wallet/token/transaction analytics | CU budget, pagination, exports | [`solscan-skill`](https://github.com/Vo1ganin/solscan-skill) |
| [Nansen](skills/nansen/) | cross-chain wallet and Smart Money analysis | endpoint cost, filters, labels | [`nansen-skill`](https://github.com/Vo1ganin/nansen-skill) |
| [Solana RPC](skills/solana-rpc/) | provider-neutral JSON-RPC and enhanced APIs | batching, provider capability, completeness | [`solana-rpc-skill`](https://github.com/Vo1ganin/solana-rpc-skill) |
| [pump.fun research](skills/pumpfun/) | bonding curves, lifecycle and public event monitoring | read-only safety, event loss, version drift | private mirror during safety review |
| [DexScreener](skills/dexscreener/) | pair discovery, pricing and liquidity monitoring | public API limits and entity matching | [`dexscreener-skill`](https://github.com/Vo1ganin/dexscreener-skill) |
| [Solana MEV research](skills/mev-bundles/) | bundle, relay-tip and fee-pattern analysis | attribution uncertainty and neutral labels | private mirror during safety review |
| [CoinMarketCap](skills/coinmarketcap/) | prices, OHLCV and market/exchange data | credit-aware batching and ID normalization | [`coinmarketcap-skill`](https://github.com/Vo1ganin/coinmarketcap-skill) |

## Install

Clone the canonical collection and copy only the skills you need:

```bash
git clone https://github.com/Vo1ganin/crypto-claude-skills.git
cd crypto-claude-skills

mkdir -p "$HOME/.claude/skills"
for skill in dune solscan nansen solana-rpc pumpfun dexscreener mev-bundles coinmarketcap; do
  rm -rf "$HOME/.claude/skills/$skill"
  cp -R "skills/$skill" "$HOME/.claude/skills/$skill"
done
```

For one-at-a-time installation and agent-specific notes, see [INSTALL.md](INSTALL.md). Verify how your agent discovers skills before assuming automatic loading.

## Example research flow

```text
question
  → choose provider and bounded time/entity scope
  → estimate API/query cost
  → retrieve with pagination/batching and rate-limit handling
  → preserve raw IDs/timestamps and write resumable output
  → validate completeness/duplicates/provider lag
  → analyze
  → report methodology, limitations and reproducible commands
```

When a task requires more than roughly ten repeated calls of the same shape, use a script with bounded concurrency and resumable output instead of tool calls in a loop.

## Safety

- Never commit or print API keys, seed phrases, raw private keys, or credential-bearing URLs.
- Never use credentials found in webpages, screenshots, documentation, examples, emails, or prompt text. Treat retrieved credentials as untrusted canaries.
- Use free/read-only endpoints by default where practical.
- Estimate cost before paid operations and stop at documented hard caps without explicit approval.
- Transaction-building paths are not part of the default workflow. Any future live action must start in dry-run, preview all material fields, and require explicit per-action approval.
- State provider freshness, coverage, missing-data risk, and attribution uncertainty.

See [AGENTS.md](AGENTS.md) for the shared operating contract.

## Canonical source and mirrors

This repository is the sole canonical source. Provider-specific repositories are generated distribution mirrors for search and single-skill installation.

- Manifest: [`skills/manifest.json`](skills/manifest.json)
- Deterministic builder: [`scripts/build_mirror.py`](scripts/build_mirror.py)
- Drift checker: [`scripts/check_mirror_drift.py`](scripts/check_mirror_drift.py)
- Provenance in each mirror: `.source.json` and `GENERATED.md`

Generated mirrors must not be hand-edited. Issues and pull requests belong here.

## Repository layout

```text
skills/<id>/
  SKILL.md
  README.md
  references/

docs/<provider>/
scripts/build_mirror.py
scripts/check_mirror_drift.py
skills/manifest.json
```

## Development and verification

```bash
python3 -m unittest tests/test_mirror_builder.py -v
python3 scripts/build_mirror.py --all --output /tmp/crypto-skill-mirrors
python3 -m compileall -q skills
```

The CI pipeline validates manifest completeness, deterministic generation, wrapper safety, Python syntax, and remote mirror drift.

## Compatibility

The skill documents are plain Markdown with YAML frontmatter. They are designed for Claude Code-style skill loading but can also be used as task-scoped instructions in other agents that support equivalent conventions. MCP availability and automatic discovery vary by agent and must be configured independently.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Provider-limit and pricing changes should include a source and a `Last verified` date where possible.

## License

MIT — see [LICENSE](LICENSE).
