# CoinMarketCap — Credits, Budget Rules, Cost Estimation

## Plan tiers (official)

| Plan | Cost | Credits/mo | Rate (req/min) | Historical window |
|------|------|------------|----------------|-------------------|
| Basic | Free | 10,000 | 30 | — |
| Hobbyist | $29/mo | 110,000 | 30 | 12 months |
| Startup | $79/mo | 300,000 | 30 | 24 months |
| Standard | $299/mo | 1,200,000 | 60 | 60 months |
| Professional | $699/mo | 3,000,000 | 90 | All-time |
| Enterprise | Custom | 30M+ | 120+ | All-time |

All plans offer 20% annual discount.

## Check current plan and usage (free)

```bash
curl -H "X-CMC_PRO_API_KEY: $CMC_API_KEY" \
  "https://pro-api.coinmarketcap.com/v1/key/info"
```

Returns:
```json
{
  "data": {
    "plan": {
      "credit_limit_monthly": <int>,
      "rate_limit_minute": <int>,
      "credit_limit_monthly_reset_timestamp": "..."
    },
    "usage": {
      "current_minute": { "requests_made": <int>, "requests_left": <int> },
      "current_day": { "credits_used": <int> },
      "current_month": { "credits_used": <int>, "credits_left": <int> }
    }
  }
}
```

**Costs 0 credits** — call it liberally at the start of sessions.

## Credit cost formula

Universal: `credits_per_call = max(1, ceil(data_points_returned / 100))`.

Where `data_points ≈ rows × columns × (1 + extra_convert_currencies)`.

### By endpoint (from official docs + live verification)

| Endpoint | Formula |
|----------|---------|
| `/v1/key/info`, `/v1/fiat/map`, `/v1/tools/postman` | **0** |
| `/v1/cryptocurrency/map` | 1 per request |
| `/v2/cryptocurrency/info` | 1 per 100 cryptos |
| `/v1/cryptocurrency/listings/latest` | 1 per 200 cryptos + 1 per convert |
| `/v1/cryptocurrency/listings/historical` | 1 per 100 cryptos + 1 per convert |
| `/v1/cryptocurrency/listings/new` | 1 per 200 + 1 per convert |
| `/v2/cryptocurrency/quotes/latest` | 1 per 100 cryptos + 1 per convert |
| `/v3/cryptocurrency/quotes/historical` | 1 per 100 data points + 1 per convert |
| `/v2/cryptocurrency/market-pairs/latest` | 1 per 100 pairs + 1 per convert |
| `/v2/cryptocurrency/ohlcv/latest` | 1 per 100 values + 1 per convert |
| `/v2/cryptocurrency/ohlcv/historical` | 1 per 100 points + 1 per convert |
| `/v2/cryptocurrency/price-performance-stats/latest` | 1 per 100 cryptos + 1 per convert |
| `/v1/cryptocurrency/categories` | 1 + 1 per 200 cryptos + 1 per convert |
| `/v1/cryptocurrency/category` | 1 + 1 per 200 cryptos + 1 per convert |
| `/v1/cryptocurrency/airdrops` (and single) | 1 per request |
| `/v1/cryptocurrency/trending/*` | 1 per 200 cryptos + 1 per convert |
| `/v1/global-metrics/quotes/latest` | 1 per request |
| `/v1/global-metrics/quotes/historical` | 1 per 100 points |
| `/v3/fear-and-greed/latest` | 1 |
| `/v3/fear-and-greed/historical` | 1 per 100 points |
| `/v3/index/cmc100-latest`, `/v3/index/cmc20-latest` | 1 |
| `/v3/index/cmc*-historical` | 1 per 100 points |
| `/v1/community/trending/*` | 1 per request |
| `/v1/content/*` | 1 per 100 items |
| `/v1/k-line/candles`, `/v1/k-line/points` | 1 per 100 points |
| `/v2/tools/price-conversion` | 1 per call + 1 per convert beyond first |
| Exchange endpoints | 1 per 100 items + 1 per convert |
| DEX endpoints | 1 per 100 items (verify per call) |

## 🚨 Budget thresholds (applied per operation)

| Estimated credits | Action |
|-------------------|--------|
| `< 50` | Proceed silently |
| `50 – 200` | Announce estimate + reason before calling |
| `> 200` | STOP. Propose alternative (narrower filter, smaller limit, different endpoint, or use cached data). Execute only with user approval. |

For batch jobs, threshold applies to total estimated spend.

## Cost estimation heuristics

### Before heavy calls
```
listings_latest(limit=L)    → ⌈L/200⌉ + (converts - 1)
listings_historical(L, N)   → (⌈L/100⌉ × N) + (converts - 1)
quotes_latest(N ids)        → ⌈N/100⌉ + (converts - 1)
quotes_historical(1 id, T points) → ⌈T/100⌉ + (converts - 1)
ohlcv_historical(N ids, T points) → ⌈N×T/100⌉ + (converts - 1)
```

### Traps that burn credits

1. **`convert=USD,EUR,GBP,JPY`** — each extra currency adds +1 credit per call. On a 5000-listing call that's 5 extra credits per convert.
2. **`limit=5000` on listings** — 25 credits. Rarely needed; paginate or narrow.
3. **Historical with many points × many cryptos** — scales multiplicatively.
4. **Forgetting to batch** — 100 × single-id `quotes/latest` = 100 credits. One call with `id=1,2,...,100` = 1 credit. **100× cheaper.**
5. **Polling without caching** — refreshing the same listings every 10s wastes credits. Most data doesn't change within 60s.
6. **Querying exchange listings with `convert_id=USD,EUR,GBP`** — exchange endpoints also charge per convert.

## Multi-key rotation (if applicable)

If user has multiple CMC keys (one per project), rotate on 429 (monthly limit):
```python
KEYS = [os.environ[k] for k in ("CMC_API_KEY", "CMC_API_KEY_2") if k in os.environ]
# Use first; fall back to second on 1010
```

Credits don't pool across keys — each has own quota.

## When to upgrade

Signs you should bump your plan:
- Frequently hitting `1010 API_KEY_PLAN_MONTHLY_RATE_LIMIT_REACHED`
- Need historical beyond what your tier allows (often 3mo Standard or 12mo Professional)
- Running `trending/*` or `listings/new` but on Basic/Hobbyist (requires Startup+)
- Doing real-time monitoring and hitting `1008 minute rate limit` often

Signs you can downgrade:
- Using `<10%` of monthly credits consistently
- Rate limit never becomes bottleneck
- Historical data you need falls within smaller window

## Alternatives when CMC credits run out

| Need | Alternative |
|------|-------------|
| Current token prices | DexScreener (free, 300 rpm on `/latest/dex/*`) |
| On-chain Solana data | Solscan, Helius DAS |
| Historical price OHLCV | CoinGecko (free tier), Dune `prices.usd` (Dune credits) |
| Market cap rankings | CoinGecko, DefiLlama (free) |
| Fear & Greed | Direct `alternative.me` free API |

Use CMC as the authoritative source for reporting, alternatives for high-frequency internal polling.
