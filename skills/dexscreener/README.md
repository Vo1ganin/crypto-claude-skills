# DexScreener Skill

Claude Code skill for [DexScreener](https://dexscreener.com) — free, unauthenticated public API for current DEX pair data across 20+ chains (Solana, Ethereum, Base, BSC, TON, Hyperliquid, etc.).

## What it does

- Token search by symbol / name / address
- Current price, liquidity, volume, market cap, FDV, price change (5m/1h/6h/24h)
- Batch price lookups — up to 30 tokens in one call
- All trading pairs for a specific token across DEXes
- Trending categories + paid boosts + community takeovers + ads

## When it triggers

User asks for current price of any token, volume/liquidity check, "is this token still alive", which DEXes trade X, what's trending, memecoin discovery, token due diligence.

## Files

| File | Purpose |
|------|---------|
| [`SKILL.md`](SKILL.md) | Workflow + key facts (no auth, no history, no WS) |
| [`references/endpoints.md`](references/endpoints.md) | All endpoints, rate tiers, response shapes, chain IDs |
| [`references/examples/search_token.py`](references/examples/search_token.py) | Quick lookup by symbol/name/address |
| [`references/examples/batch_prices.py`](references/examples/batch_prices.py) | Bulk price fetch — 30 tokens per call |
| [`references/examples/trending_monitor.py`](references/examples/trending_monitor.py) | Periodic trending + boosts snapshot |

## Key facts

- **Free. No auth. No paid tier.** Rate limits uniform across all clients.
- **60 rpm** for profiles/boosts/metas/orders; **300 rpm** for `/latest/dex/*` pairs/search/tokens.
- **No history, no WebSocket.** Snapshot only — for history use Dune, for streaming use PumpPortal WS or direct RPC.
- **Search max 30 results, no pagination.**
- **Terms prohibit competing products and aggressive scraping.** Personal analytics OK.

## Quick examples

```bash
# Search
python references/examples/search_token.py BONK

# Batch 30 prices
python references/examples/batch_prices.py solana tokens.txt out.csv

# Monitor trending every 5 min
python references/examples/trending_monitor.py --interval 300 --out trends.jsonl
```

## Setup

```bash
pip install httpx
```

No API key. Just call it.

## Related skills

- [`pumpfun-skill`](../pumpfun) — pump.fun bonding curves + real-time streaming (DexScreener is too slow)
- [`solana-rpc-skill`](../solana-rpc) — raw Solana data
- [`solscan-skill`](../solscan) — parsed wallet/token history
- [`dune-skill`](../dune) — historical DEX analytics
