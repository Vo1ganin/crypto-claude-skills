---
name: pumpfun
description: |
  Expert assistant for pump.fun — Solana memecoin launchpad with bonding curves.

  Use whenever the user wants to: trade on pump.fun programmatically, build a sniper
  bot for new token creations, monitor KOL trades or specific tokens in real-time via
  WebSocket, detect bonding curve completions / migrations to PumpSwap, analyze
  historical pump.fun data, parse on-chain pump.fun events, or understand bonding
  curve mechanics (reserves, market cap, graduation threshold).

  Also triggers on mentions of "mass deploy", "PumpSwap migration", "bonded tokens",
  creator analysis, pf stats, or when the user pastes a pump.fun token URL.

  Enforces: use PumpPortal WebSocket (single connection!) for streaming; route trades
  via Lightning (managed) or Local (your own RPC); route through Jito for priority
  landing when `jitoOnly: true`.
compatibility:
  tools:
    - Bash
    - Write
    - Read
---

# pump.fun Skill

Reference files:
- `references/mechanics.md` — bonding curve math, reserves, migration, program IDs
- `references/trading-api.md` — PumpPortal Lightning + Local APIs, all params
- `references/streaming.md` — WebSocket data API, subscriptions, one-connection rule
- `references/onchain.md` — direct RPC parsing + Dune tables + Bitquery GraphQL
- `references/examples/` — working Python scripts (sniper, copytrade, migration watcher)

---

## 🚨 Rule #1: ONE WebSocket connection for ALL subscriptions

PumpPortal WS (`wss://pumpportal.fun/api/data`) **bans clients who open multiple connections**. Always:
- Open ONE connection
- Send all subscribe messages on that single connection
- Reconnect on disconnect — never open parallel connections

See `references/streaming.md` for pattern.

## 🚨 Rule #2: pick the right trading mode

**PumpPortal Lightning** (`POST /api/trade?api-key=KEY`):
- PumpPortal signs & submits your transaction
- 0.5% fee per trade on top of pump.fun's fees
- Routes through dedicated Solana nodes + SWQoS + Jito bundles automatically
- Use for: quick prototypes, trading bots where latency doesn't need absolute minimum

**PumpPortal Local** (`POST /api/trade-local`):
- Returns a serialized unsigned transaction
- You sign with your own wallet + submit via your own RPC
- No additional fee beyond network / Jito
- Use for: production bots, when you want full control over RPC, signing, keys

**Rule of thumb:** Local if you're serious, Lightning if you're testing. For sniping: Local + Helius Sender + Jito bundle.

## 🚨 Rule #3: `jitoOnly: true` for competitive landing

On creations (first N blocks after mint) competition is fierce. Set `jitoOnly: true` on the trading call → PumpPortal routes exclusively through Jito bundles. Higher landing rate during mempool congestion.

For very competitive snipes: skip PumpPortal entirely, build tx locally, submit via Jito block engine directly (see `jito-skill` for bundle mechanics).

---

## Core concepts (memorize these)

### Token supply (per pump.fun token)
- Total: **1,000,000,000** (1B, fixed)
- On bonding curve: **793,100,000** (79.31%)
- Reserved for migration: **206,900,000** (20.69%, seeds the AMM pool on graduation)

### Bonding curve progress formula
```
progress_pct = 100 - (((tokens_in_curve - 206_900_000) * 100) / 793_100_000)
```
At 100% → token migrates to PumpSwap (or sometimes Raydium depending on era).

### Price discovery
Constant-product AMM with virtual reserves. Initial launch reserves (classic values):
- Virtual SOL: 30
- Virtual tokens: 1,073,000,000
```
price = (virtualSol + realSol) / (virtualTokens + realTokens)
```
Non-linear — early buyers win most.

### Main program ID
`6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`

Filter DEX trades / instructions by this address.

---

## Step-by-step workflow

**1. Identify the task**
- Real-time stream → PumpPortal WS
- One-off trade → Lightning (fast) or Local (full control)
- Bot with repeated trades → Local + own RPC + Jito tips
- Historical analysis → Dune tables
- Single-wallet creator analysis → Helius `getTransactionsForAddress` filtered by program

**2. Pick the right API**
See "Data access options" in `references/mechanics.md` for the decision matrix.

**3. Setup**
- Get PumpPortal API key at https://pumpportal.fun/ (required for Lightning, not for Data/Local)
- Ensure `SOLANA_RPC_URL` is set (see `solana-rpc-skill`) — Local API + own signing requires your own RPC

**4. Execute**
- Streaming: async WebSocket client (see `examples/ws_monitor.py`)
- Trading (Lightning): simple httpx POST
- Trading (Local): request unsigned tx, sign with solders/web3.js, submit via RPC

**5. Handle failures**
- PumpPortal WS disconnects: reconnect, resend all subscribes
- Trade rejected: check slippage + priorityFee, raise both if sniping hot coin
- Jito bundle failed: retry with higher tip (see `jito-skill`)

---

## Common patterns

### Sniper bot (new token creation → auto-buy)
```
WS subscribeNewToken
  ↓ event received
Local API: request unsigned buy tx
  ↓
Sign with hot wallet
  ↓
Submit via Helius Sender OR Jito bundle
  ↓ (if Jito) include tip to JitoFeeAccount
```
Full example: `references/examples/sniper_bot.py`.

### Copytrade (mirror KOL trades)
```
WS subscribeAccountTrade keys=[KOL1, KOL2, ...]
  ↓ KOL bought token X
Local API: request buy for same mint
  ↓ (optional) wait N ms to let KOL's tx land
Submit your buy
```
Example: `references/examples/copytrade_watcher.py`.

### Migration watcher
```
WS subscribeMigration
  ↓ event received: token X migrated to PumpSwap
→ Optionally trade on PumpSwap (use solana-rpc-skill or Jupiter)
```
Example: `references/examples/migration_watcher.py`.

### Historical analysis via Dune
```sql
-- Tokens created per day last month with final market cap
SELECT date_trunc('day', block_time) AS day,
       COUNT(*) AS tokens_created
FROM pumpdotfun_solana.pump_evt_create
WHERE block_time >= NOW() - INTERVAL '30' DAY
GROUP BY 1
ORDER BY 1
```
More templates when `dune-skill` is available.

---

## Error & edge cases

- **"Bonding curve not initialized"** — token doesn't exist yet or instruction called before `create`
- **"Insufficient liquidity"** — tried to buy/sell more than curve can support; reduce amount
- **"Slippage exceeded"** — curve moved during tx build → submit; retry with higher slippage
- **Token already migrated** — stops being tradeable on bonding curve after 100% progress; use `pool: "pump-amm"` or `pool: "auto"`
- **WS 403/disconnect** — likely hit rate limit or opened multiple connections; wait, reconnect on single conn only

## Reference files

- `references/mechanics.md` — bonding curve math, program IDs, supply math
- `references/trading-api.md` — PumpPortal Lightning + Local with all params
- `references/streaming.md` — WS subscriptions + single-connection pattern
- `references/onchain.md` — raw RPC parsing, Dune queries, Bitquery GraphQL
- `references/examples/ws_monitor.py` — WebSocket listener template
- `references/examples/sniper_bot.py` — new-token sniper (Local + Helius Sender)
- `references/examples/copytrade_watcher.py` — mirror KOL wallets
- `references/examples/migration_watcher.py` — detect graduations to PumpSwap
