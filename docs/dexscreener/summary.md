# DexScreener API — Summary

Compiled 2026-04-24.

## Basics

- **Base URL:** `https://api.dexscreener.com`
- **Auth:** none — fully public, free
- **No paid tier** — rate limits are uniform
- **No history** — only current state
- **No WebSocket** — polling only
- **Search capped at 30 results** — no pagination available

## Rate limits (uniform across all clients)

| Tier | Rpm | Endpoints |
|------|-----|-----------|
| **Slow (60/min)** | 60 | `token-profiles/*`, `token-boosts/*`, `community-takeovers/*`, `ads/*`, `metas/*`, `orders/*` |
| **Fast (300/min)** | 300 | `latest/dex/*` (search, pairs, token-pairs, tokens) |

429 on exceed. No `Retry-After` header in responses; back off manually.

## Endpoints

### Pair / token data (300 rpm)

**`GET /latest/dex/search?q={query}`**
Search pairs/tokens. Max 30 results, no pagination.
- `q` — symbol, name, or address
- Returns array of pairs with price, volume, liquidity, buy/sell counts, chain info

**`GET /latest/dex/pairs/{chainId}/{pairAddress}`**
Details for a specific DEX pair (pool).
- `chainId` — e.g. `solana`, `ethereum`, `bsc`
- `pairAddress` — pool/pair contract address

**`GET /token-pairs/v1/{chainId}/{tokenAddress}`**
All trading pairs for a specific token.

**`GET /tokens/v1/{chainId}/{tokenAddresses}`**
**Batch** endpoint — up to ~30 token addresses comma-separated.
- `tokenAddresses` — CSV of mint/contract addresses
- Returns pair info for each token (picks top pair per token typically)

### Promotions & discovery (60 rpm)

**`GET /token-profiles/latest/v1`**
Newest token profiles (projects that enhanced their listing with banner, description, links).

**`GET /token-profiles/recent-updates/v1`**
Recently updated profiles.

**`GET /token-boosts/latest/v1`** / **`GET /token-boosts/top/v1`**
Tokens with active paid boost ads — latest and top-ranked.

**`GET /community-takeovers/latest/v1`**
Community-led takeovers of abandoned tokens.

**`GET /ads/latest/v1`**
Currently running DexScreener ads.

**`GET /orders/v1/{chainId}/{tokenAddress}`**
On-chain orders (if the chain supports orderbook-style DEX).

### Metas (categories)

**`GET /metas/trending/v1`**
Trending categories with aggregate market stats.

**`GET /metas/meta/v1/{slug}`**
Specific category details + list of pairs in it.

## Response shape (typical pair object)

```json
{
  "chainId": "solana",
  "dexId": "raydium",
  "url": "https://dexscreener.com/solana/...",
  "pairAddress": "...",
  "baseToken": {"address": "...", "name": "...", "symbol": "..."},
  "quoteToken": {"address": "...", "symbol": "SOL"},
  "priceNative": "0.00001",
  "priceUsd": "0.0015",
  "txns": {"m5": {"buys": 3, "sells": 1}, "h1": {...}, "h6": {...}, "h24": {...}},
  "volume": {"h24": 12345.67, "h6": ..., "h1": ..., "m5": ...},
  "priceChange": {"h24": 12.5, "h6": ..., "h1": ..., "m5": ...},
  "liquidity": {"usd": 50000, "base": ..., "quote": ...},
  "fdv": 123456,
  "marketCap": 98765,
  "pairCreatedAt": 1712345678000,
  "info": {"imageUrl": "...", "websites": [...], "socials": [...]}
}
```

## Supported chain IDs

Common values: `solana`, `ethereum`, `bsc`, `polygon`, `arbitrum`, `optimism`, `base`, `avalanche`, `fantom`, `cronos`, `sui`, `ton`, `tron`, `ronin`, `zksync`, `linea`, `mantle`, `scroll`, `blast`, `sei`, `hyperliquid`.

Full list via trial or `GET /latest/dex/pairs/<chain>/...` — chains not listed here may still work.

## Terms restrictions

Free + unauthenticated, but API Terms prohibit:
- Building products that compete with DexScreener
- Aggressive scraping beyond rate limits
- Reselling or repackaging data as your own API

Fair internal/analytical use is allowed.

## Good use cases

- Quick price lookup for any token on any chain (no key, no setup)
- Discover trending tokens without watching UI
- Check liquidity / FDV / market cap for due diligence
- Monitor boosts/profiles for memecoin activity signals

## Bad fit (use something else)

- Historical data (no API — use Dune, Bitquery, Birdeye)
- Real-time streaming (no WebSocket — use PumpPortal WS for pump.fun, direct RPC for others)
- High-frequency batch queries (rate limit is too low — use Birdeye Pro, Helius DAS)
- Deep token analysis (use Moralis, Nansen, or direct on-chain)

## Sources

- https://docs.dexscreener.com/api/reference
- https://docs.dexscreener.com/api/api-terms-and-conditions
