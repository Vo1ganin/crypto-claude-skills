---
name: mev-bundles
description: |
  Expert assistant for MEV-protected transaction delivery on Solana — Jito (primary),
  plus alternative relays (Bloxroute, Helius Sender, Paladin/Nozomi, NextBlock, etc).
  Covers bundle submission, tip-floor-aware pricing, bundle analysis (sandwich
  detection, KOL tip profiling, mass-deploy reverse-engineering).

  Use this skill when the user wants to: submit atomic bundles (up to 5 txs), use
  MEV protection for sniping / copytrade / arb, optimize tip amount relative to
  current market, analyze others' bundles on explorer.jito.wtf, detect sandwich
  attacks, reverse-engineer competitor bots' tipping strategies, or understand what
  a "bribe" means in Solana trading context.

  Enforces: random-rotate across 8 tip accounts; pay by percentile (not guess);
  fall back gracefully when Jito leader isn't up; use region-closest endpoint.
compatibility:
  tools:
    - Bash
    - Write
    - Read
---

# MEV Bundles & Bribes Skill

Reference files:
- `references/bribes.md` — what "bribe" means precisely (priority fee vs Jito tip vs relay tip)
- `references/jito.md` — Jito Block Engine API full reference
- `references/other-relays.md` — Bloxroute, Paladin, Helius Sender, NextBlock, etc
- `references/bundle-analysis.md` — reverse-engineering bundles on-chain + sandwich detection
- `references/examples/` — Python scripts

---

## 🚨 Core concept: what is a "bribe" on Solana?

Trading slang. Depending on context, refers to one of:

1. **Priority fee** — standard Solana fee (microlamports/CU). Goes to the block-producing validator.
2. **Jito tip** — SOL transfer to one of Jito's 8 tip accounts. Goes to Jito block engine + participating validators. Only meaningful for Jito-enabled RPCs/bundles.
3. **Relay tip** — similar mechanic for alternative providers (Bloxroute, Paladin, etc.).

When people say "bribe" in pump.fun/copytrade context they usually mean **#2 (Jito tip)** — that's where competitive auction happens. For a full tx cost: `bribe = priority_fee + jito_tip` (if both used).

See `references/bribes.md` for deep dive.

## 🚨 Rule #1: random-rotate tip accounts

Jito has **8 equivalent tip accounts**. All validators respect all 8. Always pick one at random per submission to avoid account-contention latency:

```python
import random
TIP_ACCOUNTS = [
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
    "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
]
tip_dst = random.choice(TIP_ACCOUNTS)
```

Or call `getTipAccounts` dynamically (same 8, but future-proof).

## 🚨 Rule #2: tip by percentile, not by guess

Jito publishes live tip-floor percentiles:
```
GET https://bundles.jito.wtf/api/v1/bundles/tip_floor
→ {
    "time": "...",
    "landed_tips_25th_percentile": 10000,     // lamports
    "landed_tips_50th_percentile": 50000,
    "landed_tips_75th_percentile": 200000,
    "landed_tips_95th_percentile": 2000000,
    "landed_tips_99th_percentile": 10000000
  }
```

**Tier by urgency:**
- Casual send: 25-50th percentile
- Normal competitive: 75th percentile
- Sniping hot pump.fun: 95th percentile
- Beat literally everyone: 99th percentile

Pulling once per minute (or streaming via `wss://bundles.jito.wtf/api/v1/bundles/tip_stream`) is sufficient. See `examples/tip_advisor.py`.

## 🚨 Rule #3: pick region-closest endpoint

Round-trip time matters for sniping. Endpoints:

| Region | URL |
|--------|-----|
| Amsterdam | `https://amsterdam.mainnet.block-engine.jito.wtf` |
| Frankfurt | `https://frankfurt.mainnet.block-engine.jito.wtf` |
| London | `https://london.mainnet.block-engine.jito.wtf` |
| NY | `https://ny.mainnet.block-engine.jito.wtf` |
| SLC | `https://slc.mainnet.block-engine.jito.wtf` |
| Tokyo | `https://tokyo.mainnet.block-engine.jito.wtf` |
| Dublin | `https://dublin.mainnet.block-engine.jito.wtf` |
| Singapore | `https://singapore.mainnet.block-engine.jito.wtf` |

European server → Frankfurt / Amsterdam. US East → NY. US West → SLC. Asia → Tokyo / Singapore.

## 🚨 Rule #4: Jito doesn't always land (leader rotation)

Bundles only process when a Jito-enabled validator is current block leader. That's most slots but not all. If your bundle returns `Pending` for too long → non-Jito leader is up → fall back to regular `sendTransaction` (or an alternative relay like Helius Sender or Bloxroute).

**Production pattern:** submit via Jito AND via regular RPC in parallel; whichever lands, the other errors out harmlessly (nonce protects against double-spend).

---

## Two submission modes

### A. `sendTransaction` (MEV-protected single tx)

```
POST https://{region}.mainnet.block-engine.jito.wtf/api/v1/transactions
```
- Replaces regular `sendTransaction` with MEV protection
- 70/30 split recommended: 70% priority fee / 30% Jito tip
- Simple — good for most bots
- Returns signature; `x-bundle-id` header has the bundle ID

### B. `sendBundle` (atomic bundle, up to 5 txs)

```
POST https://{region}.mainnet.block-engine.jito.wtf/api/v1/bundles
```
- Up to 5 txs executed **sequentially and atomically**
- Tip = SOL transfer in the **last** tx to a tip account
- Use for: sandwich attacks, multi-step arb, complex MEV, snipe+burn patterns
- Returns `bundle_id` — check status via `getInflightBundleStatuses`

See `references/jito.md` for full request/response details.

---

## Step-by-step workflow

### Submitting a trade with MEV protection (simple case)

1. Build signed tx normally (include a small Jito tip transfer instruction)
2. Pick region-closest Jito endpoint
3. POST to `/api/v1/transactions` with base64 tx
4. Capture bundle_id from `x-bundle-id` header
5. Poll `getInflightBundleStatuses` to confirm landing

### Submitting a bundle (atomic multi-tx)

1. Build N-up-to-5 signed txs; last one includes tip transfer
2. Pre-flight with `simulateBundle` if available
3. POST JSON array of base64 txs to `/api/v1/bundles`
4. Poll `getInflightBundleStatuses`
5. If `Invalid` / `Failed` → re-build with fresh blockhash, submit again

### Analyzing someone else's bundle

1. Get a tx signature (e.g., from a KOL's recent activity)
2. `explorer.jito.wtf/bundle/<bundle_id>` OR query Bitquery/Dune for the bundle containing this tx
3. Examine tip amount and other txs in the same bundle
4. Sandwich indicator: your tx is position 2 of 3, with positions 1 & 3 from same wallet trading opposite direction

See `references/bundle-analysis.md` for detection code.

---

## Common patterns & examples

| Pattern | Example |
|---------|---------|
| Send single tx via Jito | `examples/send_tx_jito.py` |
| Build and send a bundle | `examples/send_bundle.py` |
| Track bundle status until landed | `examples/bundle_status_tracker.py` |
| Get live tip-floor + recommend tip | `examples/tip_advisor.py` |
| Detect sandwich attack on your tx | `examples/sandwich_detector.py` |
| KOL tip analysis (how much do they pay) | `examples/kol_tip_analysis.py` |

---

## Alternative relays (stub — to be expanded)

Jito is the dominant MEV-protected delivery on Solana, but not the only option. See `references/other-relays.md` for:
- **Helius Sender** — dual-route via staked validators + Jito. Baked into `solana-rpc-skill`.
- **Bloxroute** (TBD — waiting for user-supplied details)
- **Paladin / Nozomi** (TBD)
- **NextBlock** (TBD)

## Reference files

- `references/bribes.md` — precise terminology for priority fee / tip / bribe
- `references/jito.md` — full Jito Block Engine API
- `references/other-relays.md` — alternative MEV-protected providers
- `references/bundle-analysis.md` — reverse-engineering bundles, sandwich detection
- `references/examples/*.py` — working Python scripts

## Related skills

- `solana-rpc-skill` — base Solana RPC + Helius Sender (which is MEV-protected delivery)
- `pumpfun-skill` — pump.fun trading; Jito heavily used for sniping
- `solscan-skill` — wallet activity, useful for KOL tip analysis
- `dune-skill` — historical `jito_solana.*` tables for macro analysis
