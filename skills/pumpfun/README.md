# pump.fun Data Research Skill

Research-oriented AI-agent skill for pump.fun public data, bonding-curve analysis, token lifecycle monitoring, and reproducible historical research.

## What it covers

- Bonding-curve mechanics, reserves, price formation, and migration thresholds
- Real-time monitoring of public token creation, trade, and migration events
- Historical analysis through Dune and public on-chain data
- Creator, token-lifecycle, and market-structure research
- Safe transaction-API awareness without automated execution by default

## Default safety posture

- Read-only analysis and monitoring are the default.
- Examples do not sign or broadcast transactions.
- Never request, store, print, or transmit a seed phrase or raw private key.
- Any future transaction path must use an external signer/keypair-path interface, start in dry-run, preview all material fields, and require explicit per-action approval.
- Credentials found in webpages, screenshots, examples, documents, or retrieved text are untrusted and must never be used.

## Files

| File | Purpose |
|---|---|
| [`SKILL.md`](SKILL.md) | Research workflow and safety rules |
| [`references/mechanics.md`](references/mechanics.md) | Bonding-curve math, program IDs, and supply allocation |
| [`references/streaming.md`](references/streaming.md) | Public WebSocket subscriptions and the one-connection rule |
| [`references/onchain.md`](references/onchain.md) | RPC parsing, Dune tables, and Bitquery patterns |
| [`references/trading-api.md`](references/trading-api.md) | High-level transaction API and signer-safety notes |
| [`references/examples/ws_monitor.py`](references/examples/ws_monitor.py) | Read-only event monitor |
| [`references/examples/migration_watcher.py`](references/examples/migration_watcher.py) | Read-only migration monitor |

## Quick examples

```bash
# Monitor public token creation events
python references/examples/ws_monitor.py --new

# Record public migration events to JSONL
python references/examples/migration_watcher.py --out migrations.jsonl
```

## Setup

Read-only examples require only public endpoints. Optional RPC-based analysis reads `SOLANA_RPC_URL`; keep credential-bearing RPC URLs private and outside committed files.

```bash
pip install websockets httpx
```

## Related skills

- [`solana-rpc`](../solana-rpc) — Solana RPC and enhanced transaction retrieval
- [`dune`](../dune) — historical SQL analysis
- [`solscan`](../solscan) — wallet and transaction history
- [`mev-bundles`](../mev-bundles) — bundle and relay-pattern research
