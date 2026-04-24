# PumpPortal Data API — Real-time Streaming

## Endpoint
```
wss://pumpportal.fun/api/data
```

No authentication. Free.

## 🚨 CRITICAL: one connection for everything

**You MUST use a single WebSocket connection for all subscriptions.** Opening multiple connections triggers an **hourly ban**. Send new `subscribe*` messages on the same open socket.

Correct:
```
ws = connect(wss://pumpportal.fun/api/data)
ws.send(subscribeNewToken)
ws.send(subscribeTokenTrade {keys: [...]})
ws.send(subscribeAccountTrade {keys: [...]})
# All on same ws — good
```

Wrong:
```
ws1 = connect(...); ws1.send(subscribeNewToken)
ws2 = connect(...); ws2.send(subscribeTokenTrade ...)
# Multiple connections — BAN
```

On disconnect: reconnect with one new socket, resend all subscribes. Track active subscriptions in memory so you can resubscribe.

## Subscribe methods

### `subscribeNewToken`
Streams every new token creation (all `create` / `create_v2` events).
```json
{"method": "subscribeNewToken"}
```

### `subscribeTokenTrade`
Streams trades (buys + sells) on specific token mints.
```json
{"method": "subscribeTokenTrade", "keys": ["mint1", "mint2"]}
```
You can add more mints dynamically by sending additional subscribe messages with more keys.

### `subscribeAccountTrade`
Streams trades initiated by specific wallets. Primary use: **copytrade**.
```json
{"method": "subscribeAccountTrade", "keys": ["wallet1", "wallet2"]}
```

### `subscribeMigration`
Streams graduation events — when tokens complete bonding and migrate to PumpSwap.
```json
{"method": "subscribeMigration"}
```

## Unsubscribe

Same payload, `unsubscribe` prefix:
```json
{"method": "unsubscribeNewToken"}
{"method": "unsubscribeTokenTrade", "keys": ["mint1"]}
{"method": "unsubscribeAccountTrade", "keys": ["wallet1"]}
```

## Message format

Messages arrive as JSON. Fields vary by event type. Typical shapes:

### New token event
```json
{
  "txType": "create",
  "signature": "...",
  "mint": "<mint_address>",
  "traderPublicKey": "<creator>",
  "name": "...",
  "symbol": "...",
  "uri": "<metadata URI>",
  "initialBuy": <bool or amount>,
  "solAmount": 0.5,
  "tokenAmount": ...,
  "newTokenBalance": ...,
  "marketCapSol": ...,
  "timestamp": 1712345678
}
```

### Token/account trade event
```json
{
  "txType": "buy",    // or "sell"
  "signature": "...",
  "mint": "<mint>",
  "traderPublicKey": "<wallet>",
  "solAmount": 0.1,
  "tokenAmount": 12345.67,
  "newTokenBalance": 8765.43,
  "marketCapSol": 45.6,
  "timestamp": ...
}
```

### Migration event
```json
{
  "txType": "migration",
  "mint": "<mint>",
  "signature": "...",
  "pool": "pump-amm",     // or "raydium" depending on era
  "timestamp": ...
}
```

Exact field names may drift — always log full event once and inspect to confirm.

## Pattern: robust WS client

```python
import asyncio, json, websockets

SUBSCRIPTIONS = [
    {"method": "subscribeNewToken"},
    {"method": "subscribeAccountTrade", "keys": ["WALLET1", "WALLET2"]},
    {"method": "subscribeMigration"},
]

async def run():
    while True:
        try:
            async with websockets.connect("wss://pumpportal.fun/api/data") as ws:
                # Re-subscribe all on reconnect
                for sub in SUBSCRIPTIONS:
                    await ws.send(json.dumps(sub))
                async for raw in ws:
                    msg = json.loads(raw)
                    handle(msg)
        except Exception as e:
            print(f"WS error: {e}, reconnecting in 3s")
            await asyncio.sleep(3)

def handle(msg):
    tx_type = msg.get("txType")
    if tx_type == "create":
        print(f"NEW: {msg['name']} [{msg['mint'][:8]}]")
    elif tx_type == "buy":
        print(f"BUY: {msg['traderPublicKey'][:6]} → {msg['solAmount']} SOL on {msg['mint'][:8]}")
    # ...

asyncio.run(run())
```

See `examples/ws_monitor.py` for a more complete version.

## Rate limits

Not published officially. Empirical: free tier supports hundreds of subscribed keys simultaneously on one connection. Beyond that, filter server-side with fewer keys or aggregate on your side.

## Alternative streams

- **Direct RPC WebSocket subscription** (Helius Enhanced WebSockets or QuickNode) — filter by `programId=6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P`, parse raw tx. More effort, no third party.
- **LaserStream gRPC** (Helius) — lowest latency for serious trading bots
- **Yellowstone Geyser gRPC** (QuickNode dedicated nodes) — equivalent to LaserStream

PumpPortal is the simplest. For sub-100ms-latency sniping, LaserStream/Yellowstone is better but requires more engineering.
