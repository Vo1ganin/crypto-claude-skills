# MEV Bundles & Bribes on Solana — Summary

Compiled 2026-04-24. Covers Jito as the canonical reference + stubs for other MEV-protected delivery providers (to be filled as the user supplies details).

## What is a "bribe" on Solana (precisely)

The word **"bribe"** in Solana trading is an informal term for a fee paid to get a transaction prioritized for inclusion. Depending on context, it refers to one or more of:

1. **Priority fee** — standard Solana fee (microlamports per compute unit) paid to validators for priority in their block queue. Every Solana tx can include this. Doesn't reach MEV searchers or block builders specifically.

2. **Jito tip** — SOL transfer to one of Jito's 8 tip accounts. Used in bundles or `sendTransaction` with 70/30 split. Compensates Jito-enabled validators + block engine for prioritized inclusion. Not paid to regular validators.

3. **Alternative relay tip** — similar mechanic for Bloxroute, Helius Sender, Paladin/Nozomi, NextBlock, etc. Each has its own tip account or implicit charging.

**When people say "bribe" in trading contexts**, they usually mean **Jito tip** specifically (because that's where competitive sniping/sandwich markets exist). When discussing copytrade bot pricing: "brayby" = tip + priority fee combined cost per tx.

## Priority fee vs Jito tip (key distinction)

| | Priority fee | Jito tip |
|--|--------------|----------|
| Who gets it | Block-producing validator | Jito block engine (shared w/ validators + Jito fund) |
| Goes through | Any RPC | Only Jito-enabled RPC / block engine |
| Typical magnitude | micro-to-milli lamports | thousands to millions of lamports (>= 1000 lam minimum) |
| Effect | Better placement in mempool / local queue | Guaranteed bundle-priority auction entry |
| Required for sniping hot pump.fun token | Yes (competitive) | Yes (during Jito leader slots) |

**Common strategy:** pay both. Jito's `sendTransaction` with 70/30 split (70% priority fee, 30% tip) is a reasonable default.

## Jito Block Engine

### Regional endpoints
```
https://mainnet.block-engine.jito.wtf            (global)
https://amsterdam.mainnet.block-engine.jito.wtf
https://dublin.mainnet.block-engine.jito.wtf
https://frankfurt.mainnet.block-engine.jito.wtf
https://london.mainnet.block-engine.jito.wtf
https://ny.mainnet.block-engine.jito.wtf
https://slc.mainnet.block-engine.jito.wtf
https://singapore.mainnet.block-engine.jito.wtf
https://tokyo.mainnet.block-engine.jito.wtf
```
Testnet: `https://testnet.block-engine.jito.wtf`, `https://dallas.testnet.block-engine.jito.wtf`, `https://ny.testnet.block-engine.jito.wtf`.

**Pick the region closest to your server** — shaves tens of ms off round trip.

### API endpoints (at each regional URL)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/v1/transactions` | `sendTransaction` | Single tx with MEV protection. Returns bundle_id in `x-bundle-id` header |
| `/api/v1/bundles` | `sendBundle` | Atomic bundle of up to 5 tx |
| `/api/v1/getBundleStatuses` | POST | Check confirmed status (historical) |
| `/api/v1/getInflightBundleStatuses` | POST | Check bundle still in flight (last 5 min) |
| `/api/v1/getTipAccounts` | POST | List the 8 tip accounts |

### Tip accounts (all 8)
```
96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5
HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe
Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY
ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49
DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh
ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt
DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL
3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT
```
**Rotate randomly across these** to reduce contention (all validators respect all 8).

### Tip pricing data

- REST: `https://bundles.jito.wtf/api/v1/bundles/tip_floor` → current 25/50/75/95/99th percentile tips
- WebSocket stream: `wss://bundles.jito.wtf/api/v1/bundles/tip_stream` → live tip-floor updates

Use the REST endpoint before submission to pick competitive tip. See `references/bribes.md`.

### Rate limits

**Free tier:** 1 request per second per IP per region. 429 on exceed.

For higher: apply for auth UUID (open Discord ticket). Pass as `x-jito-auth: <uuid>` header or `?uuid=<uuid>` query param.

### Bundle mechanics

- Up to **5 transactions** per bundle, executed **sequentially and atomically**
- **Tip** = SOL transfer instruction (inside one of your txs) to a Jito tip account
- **Minimum tip 1000 lamports**, but competitive sniping often needs much more (hundreds of thousands of lamports)
- Tip instruction should go in the **last transaction** of the bundle (convention)
- Bundle only lands if Jito-enabled validator is the block leader at that slot

### Bundle lifecycle statuses

From `getInflightBundleStatuses`:
| Status | Meaning |
|--------|---------|
| `Invalid` | Bundle rejected (bad format, signature, etc.) |
| `Pending` | Accepted, waiting for Jito-slot |
| `Failed` | Non-landing failure |
| `Landed` | Included on-chain, see `landed_slot` |

From `getBundleStatuses` (after confirmed/finalized):
`processed` → `confirmed` → `finalized` (standard Solana commitment).

## Other MEV-Protected Relays (PLACEHOLDER — fill when user supplies)

### Bloxroute
(TBD — user to supply endpoint, auth, tip account, pricing, code example)

### Helius Sender
Covered in `solana-rpc-skill/references/helius-extensions.md`. Key points:
- Dual-routes through staked validator connections + Jito bundles simultaneously
- Higher landing rate than plain sendTransaction
- Configured on Helius endpoint, not a separate URL

### Paladin (formerly Nozomi)
(TBD — user to supply details)

### NextBlock
(TBD — user to supply)

### Temporal
(TBD — if still active)

## Bundle Analysis (reverse-engineering others' bundles)

Understanding others' bundles is valuable for:
- Detecting sandwich attacks on your trades
- Reverse-engineering competitor sniper bots
- Analyzing KOL wallet tip strategies
- Studying mass deploy patterns

### Tools
- **explorer.jito.wtf** — lookup bundle by ID, see all txs and tip amount
- **Bitquery Jito Bundle API** — GraphQL queries over bundles
- **Dune `jito_solana.*` tables** — historical analysis (tips, validators, bundle types)
- **Direct parsing** — any tx with transfer to one of 8 tip accounts is Jito-bundled

### Common bundle types
1. **Single-tx bundle** (sendTransaction with tip) — just priority + MEV protection
2. **Sandwich attack** — attacker_tx1 → victim_tx → attacker_tx2 (all atomic, attacker profits from price move)
3. **Back-running** — victim_tx → attacker_tx (arbitrage after large swap)
4. **Pump.fun snipe bundle** — snipe_buy + optional dust txs to outbid competitors
5. **Mass deploy bundle** — one creator spawns multiple tokens atomically

### Detection patterns
- Your tx sandwiched → your block has (same-pool swap before) → (your swap) → (same-pool swap after) from same wallet
- KOL using bundles → check their recent txs; any transfer to Jito tip accounts indicates Jito usage
- Sniper tip levels → query `bundles.jito.wtf/api/v1/bundles/tip_floor` historically via Jito API or Dune

## Sources

- https://docs.jito.wtf/lowlatencytxnsend/
- https://jito-foundation.gitbook.io/mev/mev-payment-and-distribution/on-chain-addresses
- https://www.quicknode.com/guides/solana-development/transactions/jito-bundles
- https://docs.bitquery.io/docs/blockchain/Solana/Solana-Jito-Bundle-api/
- Jito tip-floor REST: https://bundles.jito.wtf/api/v1/bundles/tip_floor
