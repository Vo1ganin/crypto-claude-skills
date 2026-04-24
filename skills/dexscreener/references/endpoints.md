# DexScreener — Endpoint Reference

Base: `https://api.dexscreener.com`
Auth: none
Format: all GET, JSON responses

## Rate tiers

| Tier | Limit | Endpoints |
|------|-------|-----------|
| **Fast** | **300 rpm** | `latest/dex/*` (search, pairs, token-pairs, tokens) |
| **Slow** | **60 rpm** | `token-profiles/*`, `token-boosts/*`, `community-takeovers/*`, `ads/*`, `metas/*`, `orders/*` |

---

## DEX data (300 rpm)

### Search
```
GET /latest/dex/search?q={query}
```
- `q` — token symbol, name, or address (case-insensitive)
- Returns: array of up to **30 matching pairs** (no pagination possible)
- Sorted by relevance + liquidity

### Pair details
```
GET /latest/dex/pairs/{chainId}/{pairAddress}
```
- Single pair (pool) full data
- Response has `pairs` array with one item (historically can be multiple — handle array)

### All pairs for a token
```
GET /token-pairs/v1/{chainId}/{tokenAddress}
```
- All DEX pairs that contain this token
- Example: BONK → Raydium pair, Meteora pair, Orca pair, Jupiter aggregated

### Batch tokens (up to ~30)
```
GET /tokens/v1/{chainId}/{tokenAddresses}
```
- `tokenAddresses` — comma-separated, max ~30
- Returns top-liquidity pair per token
- **Most efficient** for pricing many tokens at once

---

## Promotions / discovery (60 rpm)

### Token profiles
```
GET /token-profiles/latest/v1
GET /token-profiles/recent-updates/v1
```
Projects that "enhanced" their DexScreener listing with banner image, description, social links. A sign of active/promoted project.

Response objects: `url`, `chainId`, `tokenAddress`, `icon`, `header`, `description`, `links[]`.

### Token boosts
```
GET /token-boosts/latest/v1
GET /token-boosts/top/v1
```
Paid ad placements. `latest` = newest boosts, `top` = ranked by spending.

Often a signal of shill campaigns — useful to watch but not a quality indicator.

### Community takeovers
```
GET /community-takeovers/latest/v1
```
Abandoned tokens picked up by communities. Includes `claimDate`.

### Ads
```
GET /ads/latest/v1
```
Active banner ads — `url`, `chainId`, `tokenAddress`, `durationHours`, `impressions`.

### Orders
```
GET /orders/v1/{chainId}/{tokenAddress}
```
On-chain orders for orderbook-style DEX (rare on Solana; more common on Hyperliquid, dYdX).

---

## Metadata / categories (60 rpm)

### Trending
```
GET /metas/trending/v1
```
Trending categories (e.g. "AI agents", "memes on Solana") with aggregate stats.

### Category details
```
GET /metas/meta/v1/{slug}
```
Specific category → list of pairs in it, with liquidity/volume breakdowns.

---

## Response object (Pair)

Common fields:
```
chainId, dexId, url, pairAddress
baseToken: {address, name, symbol}
quoteToken: {address, symbol}      // usually SOL or WETH or USDC
priceNative, priceUsd
txns: {m5, h1, h6, h24} each with {buys, sells}
volume: {m5, h1, h6, h24}          // USD
priceChange: {m5, h1, h6, h24}     // percent
liquidity: {usd, base, quote}
fdv, marketCap
pairCreatedAt                       // unix millis
info:
  imageUrl
  websites: [{label, url}]
  socials: [{type, url}]
boosts: {active}                    // if boosted
```

---

## Chain IDs (common values)

| chainId | Network |
|---------|---------|
| `solana` | Solana |
| `ethereum` | Ethereum |
| `base` | Base |
| `bsc` | BNB Chain |
| `polygon` | Polygon |
| `arbitrum` | Arbitrum |
| `optimism` | Optimism |
| `avalanche` | Avalanche |
| `fantom` | Fantom |
| `cronos` | Cronos |
| `ton` | TON |
| `sui` | SUI |
| `tron` | Tron |
| `ronin` | Ronin |
| `zksync` | zkSync Era |
| `linea` | Linea |
| `mantle` | Mantle |
| `scroll` | Scroll |
| `blast` | Blast |
| `sei` | Sei |
| `hyperliquid` | Hyperliquid |

If unsure: call `/latest/dex/search?q={address}` first — response includes `chainId` for each result.

## Terms reminder

Free API, but terms forbid:
- Building a competing product (i.e. your own DexScreener clone)
- Aggressive scraping beyond rate limits
- Reselling or repackaging as your own API

Personal analytics + trading bots are fine.

## Sources

- https://docs.dexscreener.com/api/reference
- https://docs.dexscreener.com/api/api-terms-and-conditions
