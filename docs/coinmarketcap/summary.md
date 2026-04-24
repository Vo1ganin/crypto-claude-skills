# CoinMarketCap Pro API — Summary

Compiled 2026-04-24 via live key test + `pro.coinmarketcap.com/llms-full.txt` (171kb, saved locally).

## Basics

- **Base URL:** `https://pro-api.coinmarketcap.com`
- **Auth:** header `X-CMC_PRO_API_KEY: <key>`
- **All endpoints: GET** (most) or POST (a few DEX batch endpoints)
- **Sandbox:** `https://sandbox-api.coinmarketcap.com` (reused free quota, test key available)
- **MCP server available:** `https://coinmarketcap.com/api/mcp/` (hosted, call-credit priced)

## Plan tiers (official)

| Plan | $ / month | Credits / mo | Rate limit | Historical |
|------|-----------|--------------|------------|------------|
| Basic (free) | $0 | 10,000 | 30 / min | — |
| Hobbyist | $29 | 110,000 | 30 / min | 12 months |
| Startup | $79 | 300,000 | 30 / min | 24 months |
| Standard | $299 | 1,200,000 | 60 / min | 60 months |
| Professional | $699 | 3,000,000 | 90 / min | all-time |
| Enterprise | Custom | 30M+ | 120+ / min | all-time |

## User's current plan (live query 2026-04-24)

From `GET /v1/key/info` on user's key:

```json
{
  "plan": {
    "credit_limit_monthly": 450000,
    "rate_limit_minute": 600,
    "credit_limit_monthly_reset_timestamp": "2026-05-20T18:55:51Z"
  },
  "usage": {
    "current_month": { "credits_used": 29352, "credits_left": 420648 },
    "current_day": { "credits_used": 16062 }
  }
}
```

**Notable:** 450k/mo and 600 req/min is **not a stock tier** — likely a negotiated mid-tier between Startup and Standard, or a legacy plan. The 600 req/min ceiling is uniquely high (even Professional is 90/min), so **rate limit is NOT the bottleneck** — credits are.

## Credit cost model (empirical + docs)

Core formula: **`credits = max(1, ceil(data_points / 100))`**, where data_points ≈ rows × columns.

Per-endpoint multipliers (verified live where marked ✓):

| Endpoint | Credit formula |
|----------|----------------|
| `/v1/key/info` | 0 (free) ✓ |
| `/v1/cryptocurrency/map` | 1 per request ✓ |
| `/v2/cryptocurrency/info` | 1 per 100 cryptos (rounded up) |
| `/v1/cryptocurrency/listings/latest` | 1 per 200 cryptos + 1 per convert ✓ |
| `/v1/cryptocurrency/listings/historical` | 1 per 100 cryptos + 1 per convert |
| `/v2/cryptocurrency/quotes/latest` | 1 per 100 cryptos + 1 per convert ✓ |
| `/v3/cryptocurrency/quotes/historical` | 1 per 100 data points + 1 per convert |
| `/v2/cryptocurrency/market-pairs/latest` | 1 per 100 pairs + 1 per convert |
| `/v2/cryptocurrency/ohlcv/historical` | 1 per 100 points + 1 per convert |
| `/v2/cryptocurrency/ohlcv/latest` | 1 per 100 values + 1 per convert |
| `/v2/cryptocurrency/price-performance-stats/latest` | 1 per 100 cryptos + 1 per convert |
| `/v1/cryptocurrency/categories` | 1 per request + 1 per 200 cryptos + 1 per convert |
| `/v1/cryptocurrency/category` | 1 per request + 1 per 200 cryptos + 1 per convert |
| `/v1/cryptocurrency/airdrops` / `/airdrop` | 1 per request |
| `/v1/cryptocurrency/trending/*` | 1 per 200 cryptos + 1 per convert |
| `/v1/global-metrics/quotes/latest` | 1 per request ✓ |
| `/v2/tools/price-conversion` | 1 per call + 1 per convert beyond first |
| `/v3/fear-and-greed/*` | 1 per 100 points |

**Response field `status.credit_count`** gives the exact cost of each call — always log it.

## Empirical cost tests (user's key, 2026-04-24)

| Call | credit_count | elapsed_ms |
|------|--------------|------------|
| `/v1/cryptocurrency/map?limit=1` | 1 | 14 |
| `/v2/cryptocurrency/quotes/latest?id=1` | 1 | 6 |
| `/v1/global-metrics/quotes/latest` | 1 | 9 |
| `/v1/cryptocurrency/categories?limit=1` | 1 | 2 |
| `/v1/cryptocurrency/listings/latest?limit=200` | 1 | 18 |
| `/v1/cryptocurrency/listings/latest?limit=5000` | **25** | 685 |
| `/v2/cryptocurrency/quotes/latest?id=<20 coins>` | 1 | 21 |
| `/v2/cryptocurrency/ohlcv/historical?id=1&count=30` | 1 | 78 |

Confirms: up to 200 cryptos = 1 credit on `listings/latest`, up to 100 on other endpoints. Batch aggressively.

## Endpoint categories

### Cryptocurrency (primary)
- `/v1/cryptocurrency/map` — name/symbol → CMC ID lookup
- `/v2/cryptocurrency/info` — static metadata (logo, URLs, desc)
- `/v1/cryptocurrency/listings/latest|historical|new` — ranked lists
- `/v2/cryptocurrency/quotes/latest`, `/v3/cryptocurrency/quotes/historical` — price quotes
- `/v2/cryptocurrency/market-pairs/latest` — trading pairs
- `/v2/cryptocurrency/ohlcv/latest|historical` — candles
- `/v2/cryptocurrency/price-performance-stats/latest` — performance stats
- `/v1/cryptocurrency/categories`, `/v1/cryptocurrency/category` — groupings
- `/v1/cryptocurrency/airdrops`, `/v1/cryptocurrency/airdrop`
- `/v1/cryptocurrency/trending/latest|most-visited|gainers-losers`

### Exchange
- `/v1/exchange/map` (names → IDs)
- `/v1/exchange/info` (metadata)
- `/v1/exchange/listings/latest` (ranked exchanges)
- `/v1/exchange/quotes/latest|historical`
- `/v1/exchange/market-pairs/latest`
- `/v1/exchange/assets` (holdings per exchange)

### DEX (on-chain DEX data)
- `/v1/dex/platform/list`, `/v1/dex/platform/detail`
- `/v1/dex/token`, `/v1/dex/token/price`, `/v1/dex/token/price/batch`, `/v1/dex/token/pools`
- `/v1/dex/token-liquidity/query`, `/v1/dex/tokens/batch-query`
- `/v1/dex/tokens/transactions`, `/v1/dex/tokens/trending/list`
- `/v4/dex/pairs/quotes/latest`, `/v4/dex/spot-pairs/latest`
- `/v1/dex/search`, `/v1/dex/gainer-loser/list`, `/v1/dex/liquidity-change/list`
- `/v1/dex/meme/list`, `/v1/dex/new/list`, `/v1/dex/security/detail`

### Global Metrics
- `/v1/global-metrics/quotes/latest` — total market cap, BTC dominance
- `/v1/global-metrics/quotes/historical`

### Fear & Greed
- `/v3/fear-and-greed/latest`, `/v3/fear-and-greed/historical`

### Indices
- `/v3/index/cmc100-latest`, `/v3/index/cmc100-historical`
- `/v3/index/cmc20-latest`, `/v3/index/cmc20-historical`

### Community
- `/v1/community/trending/token`, `/v1/community/trending/topic`

### Content
- `/v1/content/latest` — news/Alexandria articles
- `/v1/content/posts/latest|top|comments`

### K-line (alternative OHLCV)
- `/v1/k-line/candles`, `/v1/k-line/points`

### Tools
- `/v1/fiat/map`
- `/v1/key/info` (free — use liberally)
- `/v2/tools/price-conversion`
- `/v1/tools/postman` (Postman collection export)

### x402 (pay-per-call with USDC)
- `/x402/v1/dex/search`
- `/x402/v3/cryptocurrency/quotes/latest`
- `/x402/v3/cryptocurrency/listings/latest`
- `/x402/v4/dex/pairs/quotes/latest`
- For use when no API key available or for one-off queries

## Response envelope

All endpoints return:
```json
{
  "status": {
    "timestamp": "2026-04-24T12:49:54Z",
    "error_code": 0,
    "error_message": null,
    "elapsed": 6,
    "credit_count": 1,
    "notice": null
  },
  "data": { ... }
}
```

**Always log `status.credit_count`** for budget tracking.

## Error codes

| HTTP | Meaning | CMC error codes |
|------|---------|-----------------|
| 400 | Bad request (wrong params) | 400 |
| 401 | Invalid / missing key | 1001, 1002, 1005 |
| 402 | Overdue balance | 1003, 1004 |
| 403 | Plan missing access | 1006 |
| 429 | Rate or credit limit | 1008 (minute), 1009 (daily), 1010 (monthly), 1011 (IP) |
| 500 | Server error | |

On 429: wait 60s (minute-limit), await reset (daily/monthly) or upgrade. On 500: exponential backoff.

## Best practices (from docs)

1. **Use CMC IDs, not symbols** — IDs stable, symbols can collide or change
2. **Bundle IDs** — 100+ IDs in one call vs many small calls
3. **Cache aggressively** — listings rarely change mid-minute; cache for 60s+ on your side
4. **Use `listings` for ranked/paginated lists**, `quotes` for specific IDs
5. **Check `credit_count` on every response** — budget awareness
6. **Call `/v1/key/info` before heavy sessions** to verify remaining budget

## Sources

- `https://pro.coinmarketcap.com/llms-full.txt` (171kb — saved locally)
- `https://coinmarketcap.com/api/documentation/`
- `https://coinmarketcap.com/api/pricing/`
- `https://coinmarketcap.com/api/documentation/pro-api-reference/cryptocurrency`
- Live key tests against user's key (2026-04-24)
