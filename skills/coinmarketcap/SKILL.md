---
name: coinmarketcap
description: |
  Expert assistant for CoinMarketCap Pro API — price quotes, listings, historical OHLCV,
  market metrics, Fear & Greed Index, CMC100/CMC20 indices, exchange data, DEX data,
  airdrops, trending, community sentiment. Covers 10+ endpoint categories across
  REST + MCP + x402 pay-per-call modes.

  Use when the user wants: current or historical crypto prices, market cap rankings,
  top gainers/losers, trending coins, OHLCV candles, exchange volume data, DEX token
  details, Fear & Greed Index readings, global market metrics (total mcap, BTC
  dominance), airdrop discovery, or fiat conversion rates.

  Enforces: budget awareness (credits, not requests), CMC IDs over symbols, aggressive
  batching (100-200 items per call), client-side caching, live credit_count logging.
compatibility:
  tools:
    - Bash
    - Write
    - Read
---

# CoinMarketCap Skill

Reference files:
- [`references/endpoints.md`](references/endpoints.md) — full catalog by category with credit formulas
- [`references/credits.md`](references/credits.md) — budget rules, cost estimation, plan tiers
- [`references/patterns.md`](references/patterns.md) — batching, caching, CMC vs alternatives
- [`references/examples/*.py`](references/examples/) — working Python scripts

---

## 🚨 Rule #1: credits, not requests

CoinMarketCap meters by **credits**, not by request count. The formula is:

```
credits_per_call = max(1, ceil(data_points_returned / 100))
```

Where `data_points ≈ rows × columns × (1 + extra_convert_currencies)`.

**Cheap calls (1 credit):**
- Up to 100 cryptos on `quotes/latest`
- Up to 200 cryptos on `listings/latest`
- Any single-token lookup (map, info, pools)
- `global-metrics`, `key/info`, `fiat/map`

**Expensive calls:**
- `listings/latest?limit=5000` = **25 credits** (verified)
- `ohlcv/historical` with many points × many cryptos = points / 100
- `market-pairs/latest` with 500+ pairs
- Adding `convert=USD,EUR,GBP` → +1 credit per extra currency

**Always check `status.credit_count`** in response and log it.

## 🚨 Rule #2: budget thresholds (applied per call)

| Estimated credits | Action |
|-------------------|--------|
| `< 50` | Proceed silently |
| `50–200` | Announce cost + reason before calling |
| `> 200` | STOP. Propose alternative (narrower `limit`, targeted `id` list, cached data, different endpoint). Execute only with approval. |

For **batch jobs** (N calls): threshold applied to total. 100 × 2 credits = 200 → announce. 100 × 5 = 500 → stop.

Check budget via `GET /v1/key/info` (free, 0 credits) before big sessions.

## 🚨 Rule #3: use CMC IDs, not symbols

Symbols collide (BTC might point to any of several tokens), can change, and break over time. CMC IDs are stable numeric identifiers.

**Always:**
1. Resolve symbols/names once via `/v1/cryptocurrency/map`
2. Cache the ID → (symbol, name) mapping on your side
3. Use IDs for all subsequent `/quotes/*`, `/ohlcv/*`, `/info` calls

Example:
```
BTC → 1
ETH → 1027
SOL → 5426
```

## 🚨 Rule #4: batch aggressively

Single call endpoints accept many IDs:
- `/v2/cryptocurrency/quotes/latest?id=1,1027,5426,...` — up to 100 IDs, still 1 credit
- `/v1/cryptocurrency/listings/latest?limit=200` — 1 credit for top 200
- `/v2/cryptocurrency/info?id=1,2,3,...,100` — 1 credit for 100 tokens' metadata

**Never loop `for sym in symbols: quote(sym)`.** One call with all IDs saves N-1 credits and N-1 round trips.

---

## Authentication

```bash
export CMC_API_KEY="..."
curl -H "X-CMC_PRO_API_KEY: $CMC_API_KEY" \
  "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?symbol=BTC"
```

Base URL:
- Production: `https://pro-api.coinmarketcap.com`
- Sandbox (testing): `https://sandbox-api.coinmarketcap.com`

## Step-by-step workflow

**1. Classify the task**
- "What's the price of X?" → `/v2/cryptocurrency/quotes/latest` with `id=<CMC_ID>`
- "Top N by market cap" → `/v1/cryptocurrency/listings/latest?limit=N`
- "Historical price chart" → `/v3/cryptocurrency/quotes/historical` or `/v2/cryptocurrency/ohlcv/historical`
- "What's trending right now" → `/v1/cryptocurrency/trending/latest`
- "Global market stats" → `/v1/global-metrics/quotes/latest`
- "Fear & Greed" → `/v3/fear-and-greed/latest`
- "Exchange volume" → `/v1/exchange/listings/latest` or `/v1/exchange/quotes/latest`
- "DEX token details" → `/v1/dex/token` (needs network_slug + contract_address)

**2. Resolve any symbols to CMC IDs first** (if you don't have them cached)
```
curl "$BASE/v1/cryptocurrency/map?symbol=BTC,ETH,SOL" -H "X-CMC_PRO_API_KEY: $KEY"
```

**3. Estimate credits** — see `references/credits.md`. Apply thresholds.

**4. Execute** — batch as much as the endpoint allows.

**5. Log `status.credit_count`** from response. If the user has ongoing budget concerns, run `/v1/key/info` periodically.

**6. Present results** — format USD with commas, timestamps to local, mcap in B/T (billions/trillions).

## Common recipes

### Price for 50 tokens right now
```python
ids = ",".join([str(cmc_id) for cmc_id in coins])  # up to 100
r = httpx.get(f"{BASE}/v2/cryptocurrency/quotes/latest?id={ids}",
              headers={"X-CMC_PRO_API_KEY": KEY})
# 1 credit, one round trip
```

### Daily OHLCV for BTC, last 90 days
```python
r = httpx.get(f"{BASE}/v2/cryptocurrency/ohlcv/historical",
              params={"id": 1, "count": 90, "interval": "daily"},
              headers={"X-CMC_PRO_API_KEY": KEY})
# 1 credit (90 points < 100)
```

### Top 200 coins by mcap
```python
r = httpx.get(f"{BASE}/v1/cryptocurrency/listings/latest?limit=200",
              headers={"X-CMC_PRO_API_KEY": KEY})
# 1 credit
```

### Fear & Greed today + 30 days back
```python
r = httpx.get(f"{BASE}/v3/fear-and-greed/historical?count=30",
              headers={"X-CMC_PRO_API_KEY": KEY})
```

### Live budget check
```bash
curl -H "X-CMC_PRO_API_KEY: $KEY" "$BASE/v1/key/info"
# 0 credits; returns plan, usage, remaining
```

See `references/examples/` for complete runnable scripts.

## Error handling

| HTTP | CMC code | Meaning | Action |
|------|----------|---------|--------|
| 401 | 1001 | Invalid key | Check env var |
| 401 | 1002 | Missing key header | Add `X-CMC_PRO_API_KEY` |
| 403 | 1006 | Endpoint not in plan | Report to user; find alternative |
| 429 | 1008 | Minute limit hit | Sleep 60s |
| 429 | 1009 | Daily limit | Await daily reset or upgrade |
| 429 | 1010 | Monthly limit | Await monthly reset or upgrade |
| 429 | 1011 | IP rate limit | Lower concurrency |
| 500 | — | Server error | Exponential backoff, then report |

## CoinMarketCap vs alternatives

| Need | Best |
|------|------|
| Authoritative price + market cap rankings | **CMC** (what the industry references) |
| Live DEX pair data on specific chain | DexScreener (free) or GeckoTerminal |
| On-chain Solana-specific | Solscan, Helius |
| Historical 5y+ OHLCV | **CMC** (Professional plan, all-time) |
| Rich metadata (logos, descriptions, URLs) | **CMC** `/v2/cryptocurrency/info` |
| Exchange volume over time | **CMC** `/v1/exchange/quotes/historical` |
| Fear & Greed Index | **CMC** `/v3/fear-and-greed/*` (authoritative source) |
| Broad trending + community pulse | **CMC** `/community/trending/*` + `/content/*` |

Use CMC for authoritative/historical/ranked data, DexScreener or chain-specific APIs for real-time DEX/token granularity.

## Reference files

- [`references/endpoints.md`](references/endpoints.md) — catalog + credit formulas, tier requirements
- [`references/credits.md`](references/credits.md) — budget rules, plan comparison, cost estimation heuristics
- [`references/patterns.md`](references/patterns.md) — batching, caching, when to use CMC
- [`references/examples/fetch_prices_batch.py`](references/examples/fetch_prices_batch.py) — bulk quote fetch with ID resolution
- [`references/examples/historical_ohlcv.py`](references/examples/historical_ohlcv.py) — daily candles for analysis
- [`references/examples/global_dashboard.py`](references/examples/global_dashboard.py) — global metrics + F&G + trending in one shot

## Related skills

- [`dexscreener-skill`](../dexscreener) — free/no-auth DEX pair data
- [`dune-skill`](../dune) — historical SQL with deeper granularity than CMC OHLCV
- [`solana-rpc-skill`](../solana-rpc) — on-chain Solana specifics
- [`nansen-skill`](../nansen) — smart-money + wallet profiling (orthogonal to CMC)
