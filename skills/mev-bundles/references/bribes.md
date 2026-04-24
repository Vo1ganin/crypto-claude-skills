# Bribes, Tips, Priority Fees — Terminology

Trading culture uses "bribe" loosely. This file pins down what it actually means mechanically, and when to use which mechanism.

## Three things people call "bribe"

### 1. Priority fee (standard Solana)
Microlamports per compute unit. Charged by the validator producing your block. Any Solana tx can set this via `ComputeBudgetProgram.setComputeUnitPrice`.

**Mechanism:**
- Block-leader validator orders txs in its block by priority fee per CU (descending), within CU limits.
- You pay in lamports: `total_priority_fee = compute_unit_price_microlamports × cu_consumed / 1_000_000`
- For a typical 200k CU swap: 1000 micro-lamports/CU = 200 lamports = **0.0000002 SOL**
- For aggressive sniping: 1,000,000 micro-lamports/CU = 200,000 lamports = **0.0002 SOL**

Goes to: whoever the validator is.

**Works with any RPC.** No third party.

### 2. Jito tip (MEV relay tip)
SOL transfer instruction inside your tx targeting one of Jito's 8 tip accounts. Only meaningful when submitted via Jito block engine (not plain RPC).

**Mechanism:**
- Jito block engine runs a tip-auction every 50ms
- Top-N highest-tipping bundles get priority slots with Jito-enabled validators
- Tip goes to: Jito shares with block-producing validator + Jito Foundation (roughly 50/50)

**Magnitude:** Minimum 1000 lamports. Competitive sniping: 100k-10M lamports. Whale-snipe-during-rug: 50M+ lamports occasionally seen.

**Works only with Jito-enabled RPC / block engine endpoint.**

### 3. Alternative relay tip
Bloxroute, Paladin (formerly Nozomi), NextBlock, etc. each have their own endpoints + tip accounts + pricing. Same idea, different infrastructure. Use when Jito isn't optimal (non-Jito leader slot, regional latency, specific validator preferences).

## "Bribe" in copytrade / pump.fun bot context

When someone says "our bot uses X SOL bribe per trade", they almost always mean:
```
bribe_total = priority_fee + jito_tip
```
Combined per-tx cost beyond the base Solana fee (~0.000005 SOL).

**Example: pump.fun snipe bot tier**
- Free tier: 0 priority, 0 tip → many losses
- Normal tier: 0.0001 priority + 0.0001 tip = 0.0002 SOL bribe
- Sweat tier: 0.001 priority + 0.001 tip = 0.002 SOL bribe
- Alpha tier: 0.005 priority + 0.005 tip = 0.01 SOL bribe (+ Jito bundle with front-run slot)

Your copytrade bribe tier choice depends on KOL's volatility and how many competitors are shadowing the same KOLs.

## Which mechanism when

| Scenario | Use |
|----------|-----|
| Casual wallet-to-wallet tx | Just priority fee (1000-5000 lamports/CU) |
| Standard DEX swap, normal market | Priority fee (5000-50000 lamports/CU) |
| Competitive sniping on hot token | Priority fee + Jito tip (bundle or sendTransaction) |
| Sandwich / multi-step MEV | Jito bundle (atomic execution required) |
| High-freq arb, non-Jito leader slots | Helius Sender (dual-routes Jito + staked connections) |
| Reliable copytrade execution | Helius Sender or Jito sendTransaction 70/30 |
| Maximum reliability, fan out | Submit via multiple relays in parallel; nonce/signature-unique prevents double spend |

## 70/30 split (Jito sendTransaction recommendation)

When using Jito `sendTransaction` (not bundle):
- 70% of your fee budget → priority fee (via `setComputeUnitPrice`)
- 30% → Jito tip (SOL transfer to tip account in same tx)

Example — 1 SOL total:
```
priority_fee_microlamports_per_cu = 0.7 * 1e9 / estimated_cu   // calculate to hit 0.7 SOL
jito_tip = 0.3 * 1e9 = 300_000_000 lamports = 0.3 SOL
```

Guidance specifically for Jito. For bundles, only tip matters (no split — no priority-fee benefit in bundle auction).

## Tip percentile pricing (dynamic)

Jito publishes live percentiles:
```
https://bundles.jito.wtf/api/v1/bundles/tip_floor
```

Response:
```json
{
  "time": "2026-04-24T00:00:00Z",
  "landed_tips_25th_percentile": 10000,
  "landed_tips_50th_percentile": 50000,
  "landed_tips_75th_percentile": 200000,
  "landed_tips_95th_percentile": 2000000,
  "landed_tips_99th_percentile": 10000000
}
```

Interpretation: "if you pay X lamports, historically Y% of bundles at that tip actually landed".

**Strategy:**
- Set `target_percentile = 75` for normal ops → tip = `landed_tips_75th_percentile`
- During competitive moments (hot pump.fun, migration): `95th` or `99th`
- Off-hours, low competition: `50th` fine

Poll this endpoint every 30-60 seconds or subscribe to `wss://bundles.jito.wtf/api/v1/bundles/tip_stream`.

## Common mistakes

1. **Paying tip without going through Jito** — useless. A transfer to a Jito tip account in a plain `sendTransaction` to public RPC doesn't trigger the auction. Tip must be submitted **via** Jito's `/api/v1/transactions` or `/api/v1/bundles`.
2. **Paying huge priority fee, zero tip** — works if validator isn't Jito-enabled that slot, wastes budget if it is.
3. **Hardcoding a tip amount** — tip-floor moves. Always poll the percentile API.
4. **Using the same tip account every tx** — increases contention. Random-rotate across the 8.
5. **Putting tip transfer as first instruction of bundle** — works, but convention is last tx. Some tooling assumes last-tx pattern.
