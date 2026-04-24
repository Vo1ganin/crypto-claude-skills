# PumpPortal Trading API

Third-party API for programmatic pump.fun trading. Two modes:

## Lightning API (managed)

```
POST https://pumpportal.fun/api/trade?api-key=YOUR_KEY
Content-Type: application/json
```

PumpPortal signs and submits the transaction — you just describe what you want. **0.5% fee per trade** on top of pump.fun's protocol fees.

### Request body
```json
{
  "action": "buy",               // "buy" or "sell"
  "mint": "<token_address>",     // from pump.fun URL
  "amount": 0.1,                 // SOL or token amount; "100%" for full sell
  "denominatedInSol": "true",    // "true"=amount is SOL, "false"=amount is tokens
  "slippage": 10,                // percent
  "priorityFee": 0.00001,        // SOL
  "pool": "auto",                // see pools below
  "jitoOnly": "false",           // "true"=route only via Jito bundles
  "skipPreflight": "true"        // "true"=skip sim (faster)
}
```

### Response
```json
{"signature": "5xY2..."}         // success
{"error": "..."}                 // failure
```

PumpPortal handles: dedicated Solana nodes, SWQoS routing, private+public Jito bundle relays. Good landing rate without effort.

## Local API (full control)

```
POST https://pumpportal.fun/api/trade-local
Content-Type: application/json
```

Returns a **serialized unsigned transaction**. You sign and submit yourself. **No PumpPortal fee** (you still pay network + optional Jito tips).

### Request body
Same as Lightning, plus:
```json
{
  "publicKey": "<your_wallet_pubkey>",
  // ... all other Lightning params
}
```

No `api-key` needed for Local.

### Response
Base64-encoded serialized tx. Flow:
1. Decode the tx
2. Sign with your private key (solders / @solana/web3.js)
3. Submit via your own RPC (Helius, QuickNode, direct Jito, etc.)

### Python example (Local + submit via own RPC)

```python
import base64, httpx, os
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client

RPC = Client(os.environ["SOLANA_RPC_URL"])
KP = Keypair.from_base58_string(os.environ["SOLANA_PRIVATE_KEY"])

# 1. Get unsigned tx from PumpPortal
resp = httpx.post("https://pumpportal.fun/api/trade-local", json={
    "publicKey": str(KP.pubkey()),
    "action": "buy",
    "mint": "<token_mint>",
    "amount": 0.05,
    "denominatedInSol": "true",
    "slippage": 15,
    "priorityFee": 0.0001,
    "pool": "auto",
})
tx_bytes = base64.b64decode(resp.content)

# 2. Sign locally
tx = VersionedTransaction.from_bytes(tx_bytes)
signed = VersionedTransaction(tx.message, [KP])

# 3. Submit via own RPC
sig = RPC.send_raw_transaction(bytes(signed))
print(sig)
```

## Pool parameter

| Value | Trades against |
|-------|----------------|
| `pump` (default) | pump.fun bonding curve |
| `pump-amm` | PumpSwap AMM (post-migration) |
| `raydium` | Raydium v4 AMM |
| `raydium-cpmm` | Raydium CPMM |
| `launchlab` | LaunchLab pools |
| `bonk` | Bonk.fun pools |
| `auto` | PumpPortal chooses best |

**Recommendation:** use `auto` unless you know exactly where the token lives. If you're sniping a new token, use `pump`. For bonded tokens use `pump-amm`. `auto` often picks right but can be slightly slower.

## Fee breakdown per trade

On a buy through Lightning:
- Pump.fun protocol fee: ~1% (depends on creator config)
- PumpPortal service fee: 0.5%
- Priority fee: you set (microlamports → SOL)
- Network fee: ~0.000005 SOL (negligible)
- Optional Jito tip: you set if `jitoOnly: true`

Local API saves the PumpPortal 0.5% fee.

## Priority fee tuning

Low activity: `0.00001` SOL works (10,000 lamports)
Normal: `0.0001` SOL (100,000 lamports)
Competitive sniping: `0.001` SOL+ (1,000,000 lamports) plus Jito tip

For live estimates: `getPriorityFeeEstimate` (Helius) or `qn_estimatePriorityFees` (QuickNode) — see `solana-rpc-skill`.

## Slippage tuning

Calm market: 5-10%
Moderate volatility: 15-25%
New-token sniping / hot coin: 50%+ (curve moves fast)

Too-low slippage → tx reverts wasting fees. Too-high → you can get rekt on a dump. For snipes, high slippage is the lesser evil.

## Creating tokens

PumpPortal supports token creation via a separate endpoint. Not commonly needed for trading; see PumpPortal docs for `create` endpoint details.

## Claim creator fees

If you launched a token and accumulated creator fees (from all trades on your coin), use PumpPortal's claim endpoint or call the on-chain instruction directly. See PumpPortal /fees/ docs.

## When NOT to use PumpPortal

- You need absolutely minimum latency → skip PumpPortal, build tx locally from pump.fun IDL, submit directly to Jito block engine
- You want zero third-party dependency → same — use pump.fun program directly + Anchor IDL

For most use cases (sniping, copytrade, analytics), PumpPortal Local is the best balance.
