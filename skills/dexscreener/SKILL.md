---
name: dexscreener
description: |
  Expert assistant for DexScreener API — free, unauthenticated public API for
  current DEX pair data across 20+ chains (Solana, Ethereum, Base, BSC, TON, etc.).

  Use when the user wants: current price / volume / liquidity / market cap of any
  token on any chain, search a token by symbol/name/address, find all trading
  pairs for a token, check trending tokens, monitor token boosts / profiles /
  community takeovers, or pull quick pair data for multiple tokens at once.

  Not for: historical data (no archive — use Dune/Bitquery), real-time streaming
  (no WebSocket — use PumpPortal WS for pump.fun or direct RPC for others).
compatibility:
  tools:
    - Bash
    - Write
    - Read
---

# DexScreener Skill

Reference files:
- `references/endpoints.md` — full endpoint list with rate limits per group
- `references/examples/` — working Python scripts (batch token lookup, search, monitor)

---

## 🚨 Key facts (memorize)

1. **No auth, no key, no paid tier.** Public API, free for everyone.
2. **No history.** Only current state. For historical: use Dune or Bitquery.
3. **No WebSocket.** Polling only. For real-time pump.fun: PumpPortal; for others: direct RPC.
4. **Search max 30 results, no pagination.** Don't try to scroll past 30.
5. **Two rate tiers:** 60 rpm (profiles/boosts/metas/orders) vs 300 rpm (`latest/dex/*`).
6. **Terms prohibit competing products** and aggressive scraping. Fair analytical use is fine.

## Base URL
```
https://api.dexscreener.com
```

---

## When to use vs alternatives

| Need | Best tool |
|------|-----------|
| Quick current price, any token, any chain | **DexScreener** `/tokens/v1/{chain}/{addr}` |
| Discover trending memecoins | DexScreener `/token-boosts/top/v1` + `/token-profiles/latest/v1` |
| Batch price for 30 tokens | **DexScreener** `/tokens/v1/{chain}/{addrs}` (one call) |
| Full liquidity/volume for a pair | **DexScreener** `/latest/dex/pairs/{chain}/{pair}` |
| Historical price | `dune-skill` (`prices.usd`) or Birdeye |
| Real-time trade stream | `pumpfun-skill` (PumpPortal WS) or `solana-rpc-skill` (LaserStream) |
| Deep wallet analysis | `solscan-skill` or `nansen-skill` |
| NFT data | `solana-rpc-skill` (DAS API) |

---

## Step-by-step workflow

**1. Identify input**
- User pastes token address → `/tokens/v1/{chain}/{address}` or `/latest/dex/search?q={address}`
- User mentions name/symbol → `/latest/dex/search?q={query}` (max 30 results)
- User asks for trending → `/token-boosts/top/v1` or `/metas/trending/v1`
- User has pair/pool address → `/latest/dex/pairs/{chain}/{pair}`

**2. Detect chain**
Chain IDs: `solana`, `ethereum`, `base`, `bsc`, `polygon`, `arbitrum`, `optimism`, `avalanche`, `ton`, `sui`, `tron`, `hyperliquid`, etc. If unknown, use `/search` first (it returns `chainId` in results).

**3. Call the endpoint**
- Plain `curl` or `httpx.get()` — no headers needed
- Honor 60/300 rpm rate limit: if batch-polling, `asyncio.Semaphore(5)` keeps safe

**4. Extract what's needed**
Typical fields: `priceUsd`, `volume.h24`, `liquidity.usd`, `priceChange.h24`, `txns.h24.buys/sells`, `marketCap`, `fdv`, `pairCreatedAt`.

**5. Present**
- Format USD with commas
- Shorten addresses (4+4 chars)
- Link to DexScreener UI: `https://dexscreener.com/{chainId}/{pairAddress}`

---

## Common patterns

### Quick price lookup
```bash
curl "https://api.dexscreener.com/latest/dex/search?q=BONK"
```
Returns up to 30 matching pairs sorted by relevance. Pick the top Raydium/Jupiter pair on Solana for BONK.

### Batch 30 tokens at once
```bash
curl "https://api.dexscreener.com/tokens/v1/solana/MINT1,MINT2,MINT3,...,MINT30"
```
Single request covers 30 tokens — way cheaper than 30 individual calls.

### Monitor a token's all pairs
```bash
curl "https://api.dexscreener.com/token-pairs/v1/solana/{TOKEN}"
```
Useful when a token trades on multiple DEXes (Raydium, Meteora, Orca) — get liquidity for each.

### Trending + boosts combination
```bash
# What paid advertisers are pushing
curl https://api.dexscreener.com/token-boosts/top/v1

# Organic trends
curl https://api.dexscreener.com/metas/trending/v1
```
Compare these — divergence signals pump-or-rug patterns.

---

## Error handling

| Status | Meaning | Action |
|--------|---------|--------|
| 200 | OK | Parse JSON |
| 429 | Rate limited | Back off 30-60s, drop concurrency |
| 404 | Token/pair not found | Verify chainId and address |
| 500-502 | Upstream error | Retry with backoff |

429 doesn't include `Retry-After` — just exponentially back off.

## Reference files

- [`references/endpoints.md`](references/endpoints.md) — all endpoints, rate tiers, response shapes
- [`references/examples/search_token.py`](references/examples/search_token.py) — quick symbol/name lookup
- [`references/examples/batch_prices.py`](references/examples/batch_prices.py) — bulk price fetch for N tokens
- [`references/examples/trending_monitor.py`](references/examples/trending_monitor.py) — periodic trending dump
