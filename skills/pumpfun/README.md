# pump.fun Skill

Claude Code skill for [pump.fun](https://pump.fun) — Solana memecoin launchpad. Covers bonding-curve mechanics, PumpPortal API (real-time WebSocket + Lightning / Local trading), direct on-chain access via RPC / Dune / Bitquery.

## What it does

- Real-time streaming: new token creations, specific-token trades, KOL trades, migrations
- Programmatic trading: Lightning (managed, 0.5% fee) or Local (your own RPC, no extra fee)
- Bonding curve math: progress %, virtual reserves, price discovery, supply allocation (793.1M curve + 206.9M reserved)
- Historical analysis via Dune tables (`pumpdotfun_solana.*`)
- Raw RPC parsing with program ID `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

## When it triggers

Any mention of pump.fun, memecoin launchpad, bonding curves, token graduation, PumpSwap migration, mass deploy, creator analysis, "sniper bot", copytrade of pf traders, or when the user pastes a pump.fun URL.

## Files

| File | Purpose |
|------|---------|
| [`SKILL.md`](SKILL.md) | Workflow, three hard rules, common patterns |
| [`references/mechanics.md`](references/mechanics.md) | Bonding curve math, program IDs, supply allocation |
| [`references/trading-api.md`](references/trading-api.md) | PumpPortal Lightning + Local APIs, all params |
| [`references/streaming.md`](references/streaming.md) | WebSocket data API, single-connection rule |
| [`references/onchain.md`](references/onchain.md) | Helius Enhanced Tx + Dune tables + Bitquery GraphQL |
| [`references/examples/ws_monitor.py`](references/examples/ws_monitor.py) | WS listener for all event types |
| [`references/examples/sniper_bot.py`](references/examples/sniper_bot.py) | Auto-buy new tokens (Local API + own RPC) |
| [`references/examples/copytrade_watcher.py`](references/examples/copytrade_watcher.py) | Mirror KOL trades |
| [`references/examples/migration_watcher.py`](references/examples/migration_watcher.py) | Detect graduations to PumpSwap |

## Key rules

1. **ONE WebSocket connection for ALL subscriptions** — PumpPortal bans clients with multiple connections
2. **Lightning vs Local trading** — Lightning (PumpPortal signs) is fast; Local (own RPC, own sign) saves the 0.5% fee and gives full control
3. **`jitoOnly: true`** for competitive landing on hot snipes
4. **Supply math** — 1B total / 793.1M on curve / 206.9M reserved (seed PumpSwap LP)

## Quick examples

```bash
# Stream new tokens
python references/examples/ws_monitor.py --new

# Sniper: auto-buy new tokens with 0.02 SOL
SOLANA_RPC_URL=... SOLANA_PRIVATE_KEY=... \
  python references/examples/sniper_bot.py \
    --amount-sol 0.02 --slippage 30 --priority-fee 0.001

# Copytrade 5 KOL wallets
SOLANA_RPC_URL=... SOLANA_PRIVATE_KEY=... \
  python references/examples/copytrade_watcher.py \
    --kols kols.txt --amount-sol 0.05 --delay-ms 300

# Detect migrations
python references/examples/migration_watcher.py --out migrations.jsonl
```

## Setup

Trading examples need:
- `SOLANA_RPC_URL` — your Solana RPC (Helius/QuickNode, see [`solana-rpc-skill`](../solana-rpc))
- `SOLANA_PRIVATE_KEY` — base58 private key of your hot wallet
- Optional: PumpPortal API key (only for Lightning trading endpoint, not Data/Local)

Install Python deps:
```bash
pip install websockets httpx solana solders
```

## Related skills

- [`solana-rpc-skill`](../solana-rpc) — base Solana RPC, DAS, Helius Enhanced Tx
- [`jito-skill`](../jito) — Jito bundles for competitive tx landing (recommended for sniping)
- [`dune-skill`](../dune) — historical pump.fun analytics queries
- [`solscan-skill`](../solscan) — wallet profile + tx history
