# CoinMarketCap Endpoint Catalog

Base: `https://pro-api.coinmarketcap.com`
Auth: header `X-CMC_PRO_API_KEY: <key>`

Credit formulas use `⌈x/N⌉` notation for "1 credit per N items, rounded up". Most endpoints also charge **1 extra credit per additional `convert` currency** beyond the first.

## Cryptocurrency (primary)

| Endpoint | Method | Credits | Required tier |
|----------|--------|---------|---------------|
| `/v1/cryptocurrency/map` | GET | 1 per request | Basic+ |
| `/v2/cryptocurrency/info` | GET | ⌈ids/100⌉ | Basic+ |
| `/v1/cryptocurrency/listings/latest` | GET | ⌈cryptos/200⌉ + convert | Basic+ |
| `/v1/cryptocurrency/listings/historical` | GET | ⌈cryptos/100⌉ + convert | Hobbyist (1mo), Startup (1mo), Standard (3mo), Pro (12mo), Ent (6y) |
| `/v1/cryptocurrency/listings/new` | GET | ⌈cryptos/200⌉ + convert | Startup+ |
| `/v2/cryptocurrency/quotes/latest` | GET | ⌈ids/100⌉ + convert | Basic+ |
| `/v3/cryptocurrency/quotes/historical` | GET | ⌈data_points/100⌉ + convert | Hobbyist (1mo) – Ent (6y) |
| `/v2/cryptocurrency/market-pairs/latest` | GET | ⌈pairs/100⌉ + convert | Basic+ |
| `/v2/cryptocurrency/ohlcv/latest` | GET | ⌈values/100⌉ + convert | Basic+ |
| `/v2/cryptocurrency/ohlcv/historical` | GET | ⌈points/100⌉ + convert | Startup (1mo) – Ent (6y) |
| `/v2/cryptocurrency/price-performance-stats/latest` | GET | ⌈cryptos/100⌉ + convert | Basic+ |
| `/v1/cryptocurrency/categories` | GET | 1 + ⌈cryptos/200⌉ + convert | Free+ |
| `/v1/cryptocurrency/category` | GET | 1 + ⌈cryptos/200⌉ + convert | Free+ |
| `/v1/cryptocurrency/airdrops` | GET | 1 per request | Hobbyist+ |
| `/v1/cryptocurrency/airdrop` | GET | 1 per request | Hobbyist+ |
| `/v1/cryptocurrency/trending/latest` | GET | ⌈cryptos/200⌉ + convert | Startup+ |
| `/v1/cryptocurrency/trending/most-visited` | GET | ⌈cryptos/200⌉ + convert | Startup+ |
| `/v1/cryptocurrency/trending/gainers-losers` | GET | ⌈cryptos/200⌉ + convert | Startup+ |

Common params:
- `id` — comma-separated CMC IDs (up to 100, sometimes 200)
- `symbol` — symbol-based (less stable; prefer IDs)
- `slug` — URL slug
- `convert` / `convert_id` — target currency/ies (each extra = +1 credit)
- `aux` — request optional fields (e.g. `aux=cmc_rank,num_market_pairs`)

## Exchange

| Endpoint | Method | Credits |
|----------|--------|---------|
| `/v1/exchange/map` | GET | 1 per request |
| `/v1/exchange/info` | GET | ⌈ids/100⌉ |
| `/v1/exchange/listings/latest` | GET | ⌈exchanges/100⌉ + convert |
| `/v1/exchange/quotes/latest` | GET | ⌈ids/100⌉ + convert |
| `/v1/exchange/quotes/historical` | GET | ⌈data_points/100⌉ + convert |
| `/v1/exchange/market-pairs/latest` | GET | ⌈pairs/100⌉ + convert |
| `/v1/exchange/assets` | GET | ⌈holdings/100⌉ |

## DEX (on-chain DEX data across 100+ chains)

Uses `network_slug` (e.g. `solana`, `ethereum`, `base`) and `contract_address`/`pair_address`.

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/dex/platform/list` | GET | Valid `network_slug` values + platform IDs |
| `/v1/dex/platform/detail` | GET | Single platform details |
| `/v1/dex/token` | GET | Token details by network + address |
| `/v1/dex/token/price` | GET | Latest DEX price for a single token |
| `/v1/dex/token/price/batch` | POST | Batch token prices |
| `/v1/dex/token/pools` | GET | Liquidity pools holding a token |
| `/v1/dex/token-liquidity/query` | GET | Token liquidity time series |
| `/v1/dex/tokens/batch-query` | POST | Batch token metadata |
| `/v1/dex/tokens/transactions` | GET | Recent DEX trades |
| `/v1/dex/tokens/trending/list` | POST | Trending DEX tokens (filters: chain, timeframe) |
| `/v4/dex/pairs/quotes/latest` | GET | Latest DEX pair quotes |
| `/v4/dex/spot-pairs/latest` | GET | DEX spot pairs listing |
| `/v1/dex/search` | GET | Search tokens/pairs by keyword |
| `/v1/dex/gainer-loser/list` | POST | Top DEX gainers/losers (per chain, timeframe) |
| `/v1/dex/liquidity-change/list` | GET | Tokens with significant liquidity changes |
| `/v1/dex/meme/list` | POST | Meme tokens on DEX |
| `/v1/dex/new/list` | POST | Newly discovered DEX tokens |
| `/v1/dex/security/detail` | GET | Token security/risk flags (honeypot, mint authority, etc.) |

Credit costs similar to cryptocurrency endpoints (1 per batch of 100 items).

## Global Metrics

| Endpoint | Credits |
|----------|---------|
| `/v1/global-metrics/quotes/latest` | 1 per request |
| `/v1/global-metrics/quotes/historical` | ⌈data_points/100⌉ |

Returns: `total_market_cap_usd`, `btc_dominance`, `eth_dominance`, `active_cryptocurrencies`, `active_exchanges`, `active_market_pairs`, `total_volume_24h`.

## Fear & Greed Index

| Endpoint | Credits |
|----------|---------|
| `/v3/fear-and-greed/latest` | 1 |
| `/v3/fear-and-greed/historical` | ⌈points/100⌉ |

Values 0 (extreme fear) – 100 (extreme greed).

## CMC Indices

| Endpoint | Credits |
|----------|---------|
| `/v3/index/cmc100-latest` | 1 |
| `/v3/index/cmc100-historical` | ⌈points/100⌉ |
| `/v3/index/cmc20-latest` | 1 |
| `/v3/index/cmc20-historical` | ⌈points/100⌉ |

CMC100 = top 100 by mcap; CMC20 = top 20.

## Community

| Endpoint | Credits |
|----------|---------|
| `/v1/community/trending/token` | 1 per request |
| `/v1/community/trending/topic` | 1 per request |

Community-signal based trending (not search/price-based).

## Content

| Endpoint | Credits |
|----------|---------|
| `/v1/content/latest` | ⌈items/100⌉ — news + Alexandria articles |
| `/v1/content/posts/latest` | ⌈items/100⌉ |
| `/v1/content/posts/top` | ⌈items/100⌉ |
| `/v1/content/posts/comments` | ⌈items/100⌉ |

Can filter by `id` / `slug` / `symbol` for content about a specific coin.

## K-line (alternative OHLCV format)

| Endpoint | Credits |
|----------|---------|
| `/v1/k-line/candles` | ⌈points/100⌉ |
| `/v1/k-line/points` | ⌈points/100⌉ |

Different shape than `/cryptocurrency/ohlcv/*` — TradingView-style candles.

## Tools

| Endpoint | Credits |
|----------|---------|
| `/v1/fiat/map` | 1 per request — fiat currencies ↔ IDs |
| `/v1/key/info` | **0** (free!) — plan + usage |
| `/v2/tools/price-conversion` | 1 per call + 1 per convert beyond first |
| `/v1/tools/postman` | Export full Postman collection |

## x402 (pay-per-call via USDC, no API key)

Useful when you don't have a CMC key but have a USDC-capable wallet. Send request to `x402/*` endpoint → receive `402 Payment Required` → pay USDC → retry with payment signature → receive data.

| Endpoint | Mirror of |
|----------|-----------|
| `/x402/v1/dex/search` | `/v1/dex/search` |
| `/x402/v3/cryptocurrency/quotes/latest` | Cryptocurrency quotes |
| `/x402/v3/cryptocurrency/listings/latest` | Cryptocurrency listings |
| `/x402/v4/dex/pairs/quotes/latest` | DEX pair quotes |

x402 is a separate billing path — doesn't consume your plan credits. Priced per call in USDC (typical: cents per call).

## Response envelope (universal)

```json
{
  "status": {
    "timestamp": "2026-04-24T12:49:54.203Z",
    "error_code": 0,
    "error_message": null,
    "elapsed": 6,
    "credit_count": 1,
    "notice": null
  },
  "data": { ... }
}
```

**Always log `status.credit_count`** — it's the authoritative cost.

## Tier gating summary

Minimum plan required for specific endpoint groups:

| Feature | Min plan |
|---------|----------|
| Latest quotes/map/info/listings/metadata | Basic (free) |
| Categories, airdrops | Basic/Hobbyist |
| Historical OHLCV (1 month) | Hobbyist / Startup |
| Trending (latest, most-visited, gainers-losers) | Startup |
| Historical deeper than 1 month | Standard (3mo), Professional (12mo), Enterprise (6y+) |
| New listings endpoint | Startup |

If you get HTTP 403 → `API_KEY_PLAN_NOT_AUTHORIZED` (code 1006) → upgrade plan or find different endpoint.
