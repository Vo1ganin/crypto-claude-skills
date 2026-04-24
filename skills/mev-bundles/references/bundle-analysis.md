# Bundle Analysis — Reverse-Engineering Others' Bundles

Why analyze bundles that aren't yours:

- **Detect sandwich attacks** on your own trades → protect or relocate
- **Reverse-engineer competitor sniper bots** → learn their tip strategies
- **Analyze KOL wallet tip profiles** → understand how much you need to bribe
- **Study mass-deploy patterns** → creator wallets spawning many tokens atomically
- **Historical MEV research** → token launch windows, volatility periods

## Identify that a tx was part of a bundle

### On-chain fingerprint
Any Solana tx with a **SOL transfer to one of the 8 Jito tip accounts** in its instructions is very likely part of a Jito bundle. Check:
1. Fetch the tx via `getTransaction`
2. Look at inner instructions / top-level `SystemProgram::Transfer` instructions
3. Check if destination matches:
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

### Via Jito explorer
`https://explorer.jito.wtf/` — paste a signature or bundle ID → see all txs in the bundle, tip amount, validator, slot.

### Via Bitquery GraphQL (`jito_bundles` dataset)
See https://docs.bitquery.io/docs/blockchain/Solana/Solana-Jito-Bundle-api/ — query bundles by slot, signer, token, etc.

### Via Dune SQL
`jito_solana.*` tables (verify exact names with `searchTables`). Good for historical aggregate analysis.

## Sandwich detection

### Pattern
A sandwich attack against YOUR tx looks like this, all in the same bundle/slot:

```
Position 1: attacker_tx_A  (buys token X on pool P)
Position 2: victim_tx      (YOUR swap on pool P, same token, moves price up)
Position 3: attacker_tx_B  (sells token X on pool P at higher price)
```

Attacker profits from price slippage your swap caused.

### Detection algorithm
For a suspect tx:

1. Fetch `getTransaction` → get `slot`
2. Fetch the block: `getBlock(slot)` with `transactionDetails: "full"`
3. Find all txs touching the same **pool** as your swap, in the same block, with signers different from you
4. If you find two txs by the same wallet bracketing yours (one buy before, one sell after the same pool) → sandwich confirmed
5. Verify bundle grouping — are the three part of same bundle_id? (via Jito explorer or bundle inflight status if recent)

### Mitigation
- Use **Paladin** (anti-sandwich validator) when possible
- Use **Helius Sender** — it routes through staked validators where sandwiching is less common
- Use **Jito bundle with your own tx at front** — attacker can't insert before you in your own bundle
- Keep **slippage tight** — makes sandwich less profitable for attacker

See `examples/sandwich_detector.py` for runnable detection.

## KOL tip analysis (how much do they pay?)

For a KOL wallet (e.g. from kolscan), compute their tipping patterns:

1. Fetch recent 1000 txs via `getSignaturesForAddress` → batch `getTransaction`
2. For each tx, look for Jito tip-account transfers in instructions
3. Aggregate:
   - Mean / median / p95 tip amount
   - Frequency (pct of txs with any tip)
   - Correlation with token type (pump.fun vs other)
   - Correlation with trade size (SOL spent)

High tip frequency → KOL is actively competing for slot placement → probably a bot/semi-bot.
No tips → either manual trader or unsophisticated.

See `examples/kol_tip_analysis.py`.

## Mass-deploy bundle detection

Creator wallets spawning many tokens atomically (BWAM / mass deploy) often use Jito bundles:

1. Find creator wallet (e.g. from pump.fun creator stats via Dune)
2. Fetch all their create/create_v2 instructions
3. Group by slot → if multiple creates in the same slot from same wallet → likely bundle
4. Verify via bundle_id lookup

Useful for: reverse-engineering how massdeploy bots sequence their launches, finding pump.fun creator clusters.

## Tip-floor historical analysis

Jito publishes live tip-floor, but you can reconstruct historical via:

1. Query on-chain: all Jito-tip transfers over time window
2. Group by slot, pick max tip per slot
3. Percentile analysis per hour of day, per day of week, per event (pump.fun migration rush, etc.)

Reveals when competition is hot vs calm — plan your own tipping strategy accordingly.

Bitquery and Dune have `jito_tips` tables (or derivable) that make this a SQL query instead of manual aggregation.

## Competitor bot reverse-engineering

For a competitor's bot wallet:

1. Gather all their recent Jito-using txs (sig transfer detection)
2. Look at what mints they snipe first
3. Look at tip levels they set — scatter vs consistent → adaptive vs fixed
4. Look at how many txs per slot — are they fanning out across regions?
5. Look at token selection — do they filter by creator? Market cap? Socials?

Often you can infer their strategy in a day of analysis and either adapt defensively or incorporate their edge.

## Example: full bundle lookup flow

```python
# Given a tx signature, find the bundle it was in and list all sibling txs
import httpx, os
RPC = os.environ["SOLANA_RPC_URL"]

def post_rpc(method, params):
    r = httpx.post(RPC, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
    return r.json()["result"]

def find_bundle_siblings(sig: str):
    # 1. Get tx info
    tx = post_rpc("getTransaction", [sig, {
        "encoding": "jsonParsed",
        "maxSupportedTransactionVersion": 0,
    }])
    if not tx:
        return []
    slot = tx["slot"]

    # 2. Fetch block
    block = post_rpc("getBlock", [slot, {
        "encoding": "jsonParsed",
        "maxSupportedTransactionVersion": 0,
        "transactionDetails": "full",
        "rewards": False,
    }])

    # 3. Find all txs in this block that transfer to a Jito tip account
    JITO_TIPS = {"96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5", "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe", "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY", "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49", "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh", "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt", "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL", "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT"}
    bundle_txs = []
    for btx in block.get("transactions", []):
        msg = btx.get("transaction", {}).get("message", {})
        for ix in msg.get("instructions", []):
            parsed = ix.get("parsed", {})
            if parsed.get("type") == "transfer":
                dest = parsed.get("info", {}).get("destination")
                if dest in JITO_TIPS:
                    bundle_txs.append(btx)
                    break
    return bundle_txs
```

Limitations: block ordering isn't a perfect proxy for bundle grouping (multiple bundles can land in same slot). For authoritative bundle IDs use Jito explorer or Bitquery. But this approach works for most analysis and needs no extra service.
