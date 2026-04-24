# pump.fun On-chain Access (Raw RPC + Dune + Bitquery)

Sources beyond PumpPortal — for historical analysis, independent data, and deeper research.

## Direct RPC parsing

Filter Solana transactions by the pump.fun program ID:
```
6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P
```

### Approach A: Helius Enhanced Transactions
Fastest way to get parsed pump.fun events. Helius auto-labels pump.fun instructions.

```python
import httpx, os
HELIUS = os.environ["SOLANA_RPC_URL"]  # must be Helius

# All pump.fun trades for an address
r = httpx.post(HELIUS, json={
    "jsonrpc": "2.0", "id": 1,
    "method": "getTransactionsForAddress",
    "params": ["WALLET", {"limit": 100, "source": "PUMP_FUN"}]
})
```
Filter by `source` or `type` in response for pump.fun specifically.

### Approach B: Raw getTransaction + manual parse
For when Helius Enhanced isn't available or you need fields it doesn't expose.

```python
# Pull tx, find instruction with programId = pump.fun
tx = rpc.getTransaction(sig, encoding="jsonParsed", maxSupportedTransactionVersion=0)
for ix in tx["transaction"]["message"]["instructions"]:
    if ix.get("programId") == "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P":
        # Decode manually using Anchor IDL or discriminator
        pass
```

Discriminators (first 8 bytes of instruction data) identify the method:
- `create` / `create_v2` — creation
- `buy` — buy instruction
- `sell` — sell instruction

Get the IDL from `pump-public-docs` repo; use `anchorpy` (Python) or `@coral-xyz/anchor` (TS) to decode.

### Reading bonding curve state directly
```python
# Pass the bonding curve PDA (derived from mint)
r = rpc.getAccountInfo(bonding_curve_pda, encoding="base64")
# Decode with borsh layout: virtualSolReserves (u64), virtualTokenReserves (u64),
# realSolReserves (u64), realTokenReserves (u64), tokenTotalSupply (u64),
# complete (bool), is_mayhem_mode (bool)
```

## Dune Analytics

Tables (names may drift — always verify with `searchTables` via `dune-skill`):

| Table | Contents |
|-------|----------|
| `pumpdotfun_solana.pump_evt_create` | Every token creation |
| `pumpdotfun_solana.pump_evt_buy` | Every buy on bonding curve |
| `pumpdotfun_solana.pump_evt_sell` | Every sell on bonding curve |
| `pumpdotfun_solana.pump_evt_complete` | Graduation events (token migrated) |

### Query examples

**Daily token creation count:**
```sql
SELECT date_trunc('day', block_time) AS day,
       COUNT(*) AS tokens_created
FROM pumpdotfun_solana.pump_evt_create
WHERE block_time >= NOW() - INTERVAL '30' DAY
GROUP BY 1
ORDER BY 1
```

**Graduation rate by day:**
```sql
WITH created AS (
  SELECT date_trunc('day', block_time) AS day, COUNT(*) AS created
  FROM pumpdotfun_solana.pump_evt_create
  WHERE block_time >= NOW() - INTERVAL '30' DAY
  GROUP BY 1
),
graduated AS (
  SELECT date_trunc('day', block_time) AS day, COUNT(*) AS graduated
  FROM pumpdotfun_solana.pump_evt_complete
  WHERE block_time >= NOW() - INTERVAL '30' DAY
  GROUP BY 1
)
SELECT c.day, c.created, COALESCE(g.graduated, 0) AS graduated,
       ROUND(100.0 * COALESCE(g.graduated, 0) / c.created, 2) AS pct
FROM created c LEFT JOIN graduated g ON c.day = g.day
ORDER BY c.day
```

**Top creators by volume (creator PF stats — useful for mass-deploy analysis):**
```sql
SELECT creator,
       COUNT(*) AS tokens_launched,
       SUM(CASE WHEN graduated_sig IS NOT NULL THEN 1 ELSE 0 END) AS graduated,
       ROUND(100.0 * SUM(CASE WHEN graduated_sig IS NOT NULL THEN 1 ELSE 0 END) / COUNT(*), 2) AS graduate_rate
FROM (
  SELECT c.creator, c.mint, comp.signature AS graduated_sig
  FROM pumpdotfun_solana.pump_evt_create c
  LEFT JOIN pumpdotfun_solana.pump_evt_complete comp ON comp.mint = c.mint
  WHERE c.block_time >= NOW() - INTERVAL '90' DAY
)
GROUP BY creator
HAVING COUNT(*) >= 10
ORDER BY graduated DESC
LIMIT 50
```

**Mass deploy detection (high-frequency creators):**
```sql
SELECT creator,
       COUNT(*) AS tokens_24h,
       MIN(block_time) AS first_launch,
       MAX(block_time) AS last_launch
FROM pumpdotfun_solana.pump_evt_create
WHERE block_time >= NOW() - INTERVAL '1' DAY
GROUP BY creator
HAVING COUNT(*) >= 20   -- 20+ tokens in one day
ORDER BY tokens_24h DESC
```

Call Dune credits: each of these ~5-50 credits depending on time range. See `dune-skill` credit rules.

## Bitquery GraphQL

Real-time + historical combined. GraphQL query language. Paid tiers, but free for light use.

Endpoint: `https://streaming.bitquery.io/graphql` (real-time) or `https://graphql.bitquery.io` (historical)

Sample query: all pump.fun trades for a specific mint in the last hour
```graphql
{
  Solana {
    DEXTrades(
      where: {
        Instruction: {Program: {Address: {is: "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"}}}
        Trade: {Buy: {Currency: {MintAddress: {is: "<mint>"}}}}
        Block: {Time: {since: "2026-04-24T00:00:00Z"}}
      }
      limit: {count: 100}
      orderBy: {descending: Block_Time}
    ) {
      Block { Time }
      Transaction { Signature }
      Trade {
        Buy { Amount Currency { Symbol MintAddress } Account { Address } }
        Sell { Amount Currency { Symbol MintAddress } Account { Address } }
      }
    }
  }
}
```

See https://docs.bitquery.io/docs/blockchain/Solana/Pumpfun/Pump-Fun-API/ for full schemas.

## Choosing among RPC / Dune / Bitquery / PumpPortal

| Use case | Best |
|----------|------|
| Real-time sniper | PumpPortal WS or LaserStream gRPC |
| Real-time copytrade | PumpPortal WS subscribeAccountTrade |
| Historical stats (daily creators, graduation rates) | **Dune** |
| Single-token lifecycle deep-dive | Dune for bulk, Helius for parsed tx |
| Cross-chain or combined queries | Bitquery |
| Build own bot with minimal deps | Direct RPC + own IDL |
