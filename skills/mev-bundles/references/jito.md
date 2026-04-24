# Jito Block Engine — Full API

## Regional endpoints (pick closest to your server)

| Region | URL |
|--------|-----|
| Global (auto-route) | `https://mainnet.block-engine.jito.wtf` |
| Amsterdam | `https://amsterdam.mainnet.block-engine.jito.wtf` |
| Dublin | `https://dublin.mainnet.block-engine.jito.wtf` |
| Frankfurt | `https://frankfurt.mainnet.block-engine.jito.wtf` |
| London | `https://london.mainnet.block-engine.jito.wtf` |
| New York | `https://ny.mainnet.block-engine.jito.wtf` |
| Salt Lake City | `https://slc.mainnet.block-engine.jito.wtf` |
| Singapore | `https://singapore.mainnet.block-engine.jito.wtf` |
| Tokyo | `https://tokyo.mainnet.block-engine.jito.wtf` |
| Testnet (global) | `https://testnet.block-engine.jito.wtf` |
| Testnet Dallas | `https://dallas.testnet.block-engine.jito.wtf` |
| Testnet NY | `https://ny.testnet.block-engine.jito.wtf` |

Each region includes Shred Receiver + NTP Server sub-infrastructure. Region-pick saves 10-100ms RTT.

## Auth

**Free tier:** 1 request per second per IP per region. No authentication required.

**Higher limits:** Request a UUID via Jito Discord. Pass as:
- Header: `x-jito-auth: <uuid>`
- Or query string: `?uuid=<uuid>`

## Endpoints

### 1. `sendTransaction` — single tx with MEV protection

```
POST https://{region}.mainnet.block-engine.jito.wtf/api/v1/transactions
Content-Type: application/json
```

**Request:**
```json
{
  "id": 1,
  "jsonrpc": "2.0",
  "method": "sendTransaction",
  "params": [
    "<base64 signed tx>",
    {"encoding": "base64"}
  ]
}
```

**Response:**
```json
{"jsonrpc": "2.0", "result": "<signature>", "id": 1}
```

Also the response has HTTP header:
```
x-bundle-id: <bundle_id_for_tracking>
```

Recommended split: 70% priority fee, 30% Jito tip. Tip goes as a SOL transfer instruction inside the same tx.

### 2. `sendBundle` — atomic bundle up to 5 txs

```
POST https://{region}.mainnet.block-engine.jito.wtf/api/v1/bundles
Content-Type: application/json
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "sendBundle",
  "params": [
    ["<base64 tx1>", "<base64 tx2>", "...", "<base64 tx5>"],
    {"encoding": "base64"}
  ]
}
```

**Response:**
```json
{"jsonrpc": "2.0", "result": "<bundle_id>", "id": 1}
```

**Key properties:**
- All txs execute sequentially in same block (or none do — atomic)
- Tip transfer should be in the last tx, to one of the 8 tip accounts
- No priority fee split required — only tip matters for bundles
- Auction frequency: every 50ms inside the block engine

### 3. `getBundleStatuses` — historical status

```
POST https://{region}.mainnet.block-engine.jito.wtf/api/v1/getBundleStatuses
```

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "getBundleStatuses",
  "params": [["<bundle_id_1>", "<bundle_id_2>"]]
}
```
Max 5 bundle IDs per request.

**Response:**
```json
{
  "result": {
    "context": {"slot": 242806119},
    "value": [
      {
        "bundle_id": "...",
        "transactions": ["<sig1>", "<sig2>"],
        "slot": 242804011,
        "confirmation_status": "finalized",
        "err": {"Ok": null}
      }
    ]
  }
}
```

`confirmation_status`: `processed` | `confirmed` | `finalized`.

### 4. `getInflightBundleStatuses` — real-time (last 5 min)

```
POST https://{region}.mainnet.block-engine.jito.wtf/api/v1/getInflightBundleStatuses
```

**Request:** same shape as `getBundleStatuses`.

**Response:**
```json
{
  "result": {
    "value": [
      {
        "bundle_id": "...",
        "status": "Landed",
        "landed_slot": 280998500
      }
    ]
  }
}
```

**Status values:**
| Status | Meaning |
|--------|---------|
| `Invalid` | Rejected (bad signature, format, etc.) |
| `Pending` | Accepted, awaiting Jito leader slot |
| `Failed` | Landed but reverted, or expired |
| `Landed` | Included on-chain at `landed_slot` |

Bundles older than 5 min → 500 error; use `getBundleStatuses` instead.

### 5. `getTipAccounts` — list the 8 tip destinations

```
POST https://{region}.mainnet.block-engine.jito.wtf/api/v1/getTipAccounts
```

Returns:
```json
{
  "result": [
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
    "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT"
  ]
}
```

Hardcoding these is fine (they're stable) but calling the endpoint is future-proof.

## Tip pricing data APIs

### Tip-floor REST (current percentiles)
```
GET https://bundles.jito.wtf/api/v1/bundles/tip_floor
```

Returns live percentiles (25th, 50th, 75th, 95th, 99th) of **landed** bundle tips.

### Tip-floor WebSocket stream
```
wss://bundles.jito.wtf/api/v1/bundles/tip_stream
```

Subscribes to live updates. Useful for bots that adjust tips dynamically.

## Rate limits

| Tier | Limit |
|------|-------|
| Free | 1 req/sec per IP per region |
| Authed | Higher — request UUID via Discord |

**Trick:** each region has its own rate limit. If you run a multi-region bot, you can parallel-submit across 2-3 regions legitimately.

429 on exceed → back off. No `Retry-After` header typically.

## Common errors

| Error | Cause |
|-------|-------|
| `-32600` invalid request | Malformed JSON-RPC |
| `-32603` internal | Jito-side issue; retry different region |
| HTTP 429 | Rate limit exceeded |
| Bundle `Invalid` status | Bad signature, stale blockhash, or format error — rebuild and resend |
| Bundle `Failed` after landing | Tx reverted on-chain — check via `getTransaction` for the err |

## Reference searcher implementations

Official Jito searcher examples: https://github.com/jito-labs/searcher-examples

Language-specific:
- Rust (recommended for searchers): jito-labs/searcher-examples/tree/main/rust
- TypeScript: jito-labs/searcher-examples/tree/main/typescript
- Python: community-maintained; see jito-py on PyPI

For most trading bots, our Python examples in `examples/` are sufficient.
