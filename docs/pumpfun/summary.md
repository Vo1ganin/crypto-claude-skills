# pump.fun — Documentation Summary

Compiled 2026-04-24 from pump.fun on-chain research, PumpPortal, Bitquery, and pump-public-docs.

## Core mechanics

### What is pump.fun
Solana memecoin launchpad. Anyone can launch a token with **fixed 1B supply**. Tokens trade on a bonding curve (constant product AMM with virtual reserves) until fully bonded, then migrate to **PumpSwap** (pump's native AMM, formerly Raydium in the early era).

### Supply allocation (per token)
- **Total:** 1,000,000,000 (1B)
- **On bonding curve:** 793,100,000 (79.31%)
- **Reserved for migration:** 206,900,000 (20.69%) — seeded into PumpSwap LP on graduation

### Bonding curve formula
Constant product AMM with virtual reserves. Classic initial reserves (still commonly documented):
- Virtual SOL reserves: 30
- Virtual token reserves: 1,073,000,000

Price discovery: `price_per_token = (virtualSol + realSol) / (virtualTokens + realTokens)`

Non-linear — early buyers get lowest prices.

### Bonding curve progress
```
progress = 100 - (((tokensLeft - 206_900_000) * 100) / 793_100_000)
```
100% progress → migration to PumpSwap triggers.

### Migration
At 100% bonding (≈ 85 SOL raised historically, subject to change), the token migrates to PumpSwap via its `create_pool` instruction. The 206.9M reserved tokens + accumulated SOL seed the AMM pool.

## Program IDs

| Program | ID |
|---------|-----|
| **pump.fun (main)** | `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` |
| **Mayhem (paid mode)** | `MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e` |
| **Global params PDA** | `13ec7XdrjF3h3YcqBTFDSReRcUFwbCnJaAQspM4j6DDJ` |
| **SOL Vault** | `BwWK17cbHxwWBKZkUYvzxLcNQ1YVyaFezduWbtm2de6s` |

## Instructions (main program)

| Instruction | Purpose |
|-------------|---------|
| `create` | Legacy token creation |
| `create_v2` | New token creation using Token2022 for the mint |
| `buy` | Swap SOL → tokens via bonding curve |
| `sell` | Swap tokens → SOL via bonding curve |
| (migration) | Triggered automatically when curve completes |

## Events (for on-chain indexers)

Programs emit inner-instruction logs for:
- Token creation
- Each buy / sell trade (includes amounts, reserves after, user)
- Bonding complete / migration

Bitquery indexes as `DEXTrades` on Solana with `Instruction.Program.Address = 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`.

## Data access options

### 1. PumpPortal (easiest)
Third-party API, **Data API is free** (rate-limited), Trading API is paid (0.5% fee).

**WebSocket:** `wss://pumpportal.fun/api/data`
Subscriptions:
- `subscribeNewToken` — new coin creations
- `subscribeTokenTrade` — trades on specific mints (pass `keys: ["mint1", ...]`)
- `subscribeAccountTrade` — trades by specific wallets
- `subscribeMigration` — graduation events to PumpSwap

**Critical:** one WebSocket connection for ALL subscriptions. Multiple connections → hourly ban.

### 2. PumpPortal Trading API

**Lightning endpoint** (PumpPortal signs & submits):
```
POST https://pumpportal.fun/api/trade?api-key=YOUR_KEY
```
- 0.5% fee per trade
- Handles landing via dedicated nodes + SWQoS + Jito bundles

**Local endpoint** (you sign with own wallet):
```
POST https://pumpportal.fun/api/trade-local
```
- Returns serialized unsigned tx
- You sign + submit via your own RPC
- No PumpPortal fee beyond free data, but requires owning a signing wallet client-side

**Trading params:**
- `action`: `"buy"` | `"sell"`
- `mint`: token contract
- `amount`: number or `"100%"` for full sell
- `denominatedInSol`: bool (true = amount is SOL, false = tokens)
- `slippage`: percent
- `priorityFee`: SOL
- `pool`: `"pump"` (default) | `"raydium"` | `"pump-amm"` | `"launchlab"` | `"raydium-cpmm"` | `"bonk"` | `"auto"`
- `jitoOnly`: bool (default false)
- `skipPreflight`: bool (default true)

### 3. Dune Analytics
Tables: `pumpdotfun_solana.pump_evt_create`, `pumpdotfun_solana.pump_evt_buy`, `pumpdotfun_solana.pump_evt_sell`, `pumpdotfun_solana.pump_evt_complete` (names may vary per schema update — use `searchTables`).

Good for historical analysis (full year PF stats, token lifespan analysis, creator behavior).

### 4. Bitquery GraphQL
Real-time + historical, complex queries. Paid tiers. Docs: https://docs.bitquery.io/docs/blockchain/Solana/Pumpfun/

### 5. Direct RPC (raw)
Parse inner instructions of `6EF8rrecthR5...` program. Use Helius Enhanced Transactions for parsed variant, or write own decoder. Most complex, max flexibility.

## PumpSwap (post-migration)

Pump's native AMM where bonded tokens live after graduation. Program details in separate docs (https://docs.bitquery.io/docs/blockchain/Solana/Pumpfun/pump-swap-api/). Historically many tokens migrated to Raydium — now default is PumpSwap.

## Typical use cases

| Use case | Best approach |
|----------|--------------|
| Sniper bot (buy on creation) | PumpPortal WS `subscribeNewToken` + Local Trading API + own Helius/QuickNode RPC |
| Copytrade KOL wallets | PumpPortal WS `subscribeAccountTrade` |
| Monitor specific token trades | PumpPortal WS `subscribeTokenTrade` |
| Historical PF analysis | Dune `pumpdotfun_solana.*` tables |
| Migration detection | PumpPortal WS `subscribeMigration` |
| Mass deploy analysis (creator patterns) | Dune + Helius Enhanced Tx on creator wallet |

## Sources

- https://github.com/pump-fun/pump-public-docs (official)
- https://pumpportal.fun/ (third-party API)
- https://pumpportal.fun/trading-api/ (Lightning)
- https://pumpportal.fun/local-trading-api/trading-api/ (Local)
- https://docs.bitquery.io/docs/blockchain/Solana/Pumpfun/Pump-Fun-API/
- https://docs.bitquery.io/docs/blockchain/Solana/Pumpfun/Pump-Fun-Marketcap-Bonding-Curve-API/
