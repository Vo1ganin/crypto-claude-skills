# CoinMarketCap Skill

Claude Code skill for the [CoinMarketCap Pro API](https://coinmarketcap.com/api/) — price quotes, OHLCV history, market caps, Fear & Greed Index, CMC100/CMC20 indices, exchange data, DEX data across 100+ chains, airdrops, trending, community sentiment.

## What it does

- Current prices + market caps (batched up to 100 IDs per call)
- Historical OHLCV candles + quote series
- Global market metrics (total mcap, BTC/ETH dominance, 24h volume)
- Fear & Greed Index (current + historical)
- CMC100 / CMC20 indices
- Exchange metadata, volumes, assets, market pairs
- DEX data across chains (tokens, pools, liquidity, trending, gainers/losers, security flags)
- Airdrops, content (news), community trending
- Fiat conversion rates

## When it triggers

User asks about a token's price, market cap ranking, historical chart, F&G index, global market stats, exchange volume, airdrop info, trending coins — even without "CMC" keyword.

## Files

| File | Purpose |
|------|---------|
| [`SKILL.md`](SKILL.md) | Workflow + four hard rules (credits / budget / IDs / batching) |
| [`references/endpoints.md`](references/endpoints.md) | Full endpoint catalog by category with credit formulas |
| [`references/credits.md`](references/credits.md) | Plan tiers, budget rules, cost estimation heuristics |
| [`references/patterns.md`](references/patterns.md) | Caching, batching, pagination, avoiding credit traps |
| [`references/examples/fetch_prices_batch.py`](references/examples/fetch_prices_batch.py) | Bulk quote fetch with symbol → ID resolution |
| [`references/examples/historical_ohlcv.py`](references/examples/historical_ohlcv.py) | Daily candles for a coin, CSV output |
| [`references/examples/global_dashboard.py`](references/examples/global_dashboard.py) | Global metrics + F&G + trending in one go |

## Key rules

1. **Credits, not requests** — all endpoints metered by `ceil(data_points / 100)`. Log `status.credit_count`.
2. **Budget thresholds per call:** < 50 silent, 50–200 announce, > 200 stop + propose alternative.
3. **Use CMC IDs, not symbols** — stable, don't collide, don't break.
4. **Batch aggressively** — up to 100 IDs per `quotes/latest`, up to 200 per `listings/latest`.
5. **Cache client-side** — listings refresh once per minute, OHLCV is immutable. Save credits by caching.

## Plan tiers (reference)

| Plan | $ / mo | Credits / mo | Rate (req/min) | Historical |
|------|--------|--------------|----------------|------------|
| Basic | $0 | 10k | 30 | — |
| Hobbyist | $29 | 110k | 30 | 12 mo |
| Startup | $79 | 300k | 30 | 24 mo |
| Standard | $299 | 1.2M | 60 | 60 mo |
| Professional | $699 | 3M | 90 | all-time |

Run `GET /v1/key/info` (0 credits) at the start of any session to check your current plan + usage.

## Quick examples

```bash
# Prices for N symbols
CMC_API_KEY=... python references/examples/fetch_prices_batch.py BTC ETH SOL BONK WIF

# 90-day daily OHLCV for BTC
CMC_API_KEY=... python references/examples/historical_ohlcv.py BTC 90 btc_90d.csv

# Global market + Fear & Greed + trending
CMC_API_KEY=... python references/examples/global_dashboard.py
```

## Setup

```bash
pip install httpx
cp .env.example .env  # fill CMC_API_KEY
set -a; source .env; set +a
```

## Related skills

- [`dexscreener-skill`](../dexscreener) — free/no-auth DEX pair data (complements CMC's DEX endpoints)
- [`dune-skill`](../dune) — historical blockchain SQL, deeper than CMC OHLCV
- [`nansen-skill`](../nansen) — smart-money + wallet profiling (orthogonal use case)
- [`solana-rpc-skill`](../solana-rpc) — direct Solana data

## Sources

- Live tests against the user's CMC key (2026-04-24)
- `https://pro.coinmarketcap.com/llms-full.txt` (171kb, saved in `docs/coinmarketcap/`)
- Official docs, pricing, cryptocurrency reference pages
