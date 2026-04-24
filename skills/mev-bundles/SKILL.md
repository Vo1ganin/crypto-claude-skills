---
name: mev-bundles
description: |
  Expert assistant for MEV bundles and "bribes" on Solana — what they are, how to
  find them on-chain, how to identify different types (sandwich, back-run, snipe,
  mass-deploy), and how to analyze them. Covers Jito + 8 other MEV-protected
  relays (Bloxroute, Nozomi/Temporal, Astralane, BlockRazor, Stellium, Falcon,
  Flashblocks, 1node).

  Use this skill when the user wants to: understand what a "bribe" or "bundle"
  actually is on Solana, find which transactions are bundled on-chain, detect a
  sandwich attack, analyze a KOL's or competitor bot's tipping strategy, explore
  who uses Jito vs other relays, or submit their own MEV-protected transactions.

  This skill is PRIMARILY EDUCATIONAL: its job is to explain and detect, not just
  to submit. Code examples are illustrative.
compatibility:
  tools:
    - Bash
    - Write
    - Read
---

# MEV Bundles & Bribes Skill

**Primary purpose:** explain bribes and bundles on Solana, teach agents how to **find** them on-chain, and how to **identify** their type (sandwich, back-run, snipe, mass-deploy).

Reference files:
- [`references/bribes.md`](references/bribes.md) — **READ THIS FIRST**: what "bribe" means precisely, 3 mechanisms (priority fee / Jito tip / relay tip)
- [`references/bundle-analysis.md`](references/bundle-analysis.md) — **READ FOR ANALYSIS**: how to find bundles on-chain, detect sandwich, profile KOLs
- [`references/jito.md`](references/jito.md) — Jito Block Engine API (for submission)
- [`references/other-relays.md`](references/other-relays.md) — all 9 MEV relays (Jito, Bloxroute, Nozomi, Astralane, BlockRazor, Stellium, Falcon, Flashblocks, 1node)
- [`references/examples/`](references/examples/) — runnable Python analysis + submission

---

## 🎯 Part 1: What is a "bribe" on Solana?

Trading slang. Mechanically it's **one of three things** (or a combination):

### 1. Priority fee (standard)
- Microlamports per compute unit, set via `ComputeBudgetProgram.setComputeUnitPrice`
- Goes to: the validator producing your block
- Works with: any RPC (public, Helius, QuickNode, etc.)
- Typical: 1000–1,000,000 microlamports/CU depending on urgency

### 2. Jito tip
- `SystemProgram.transfer` instruction inside your tx to one of Jito's 8 tip accounts
- Goes to: Jito block engine + participating validators (shared)
- Works with: **only when submitted via a Jito-enabled endpoint** (Jito block engine, or Helius Sender which routes through Jito)
- Typical: 1000 lamports minimum, 100k-10M+ for competitive sniping

### 3. Alternative relay tip
- Similar mechanic for Bloxroute, Nozomi, Stellium, etc. — each has own tip addresses
- Works with: that specific relay's API only

**When someone says "bribe" in trading context**, they usually mean **Jito tip** (that's where the competitive auction happens). In copytrade/pump.fun lingo: `bribe = priority_fee + jito_tip` (combined per-tx budget).

See [`references/bribes.md`](references/bribes.md) for deep treatment including 70/30 split, percentile pricing, common mistakes.

---

## 🎯 Part 2: What is a "bundle"?

A bundle is a **group of up to 5 Solana transactions** submitted together to Jito (or another relay with bundle support) that execute **atomically in order, in the same block** — all succeed or all revert.

**Key properties:**
- Up to 5 txs per bundle
- Sequential and atomic — position 1 runs first, then 2, etc.
- If any tx fails, entire bundle reverts
- Tips (usually in the last tx) compete in a 50ms auction
- Only land when a Jito-enabled validator produces the block (95%+ of slots)

**Why bundles exist:**
- Atomic multi-step MEV (arb, sandwich, liquidation+swap)
- Ordering guarantees (you're first or don't exist)
- Protection from front-running within your own tx group

See [`references/jito.md`](references/jito.md) for the submission API.

---

## 🎯 Part 3: How to FIND bundles on-chain

You have a tx signature. You want to know: was this part of a bundle? What other txs were in it?

### Method A: Fingerprint by Jito tip transfer (fastest, no external service)

Any tx with a `SystemProgram.transfer` to one of Jito's 8 tip accounts is Jito-bundled:

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

For other relays, look for their tip addresses:
- **Bloxroute**: `HWEoBxYs7ssKuudEjzjmpfJVX7Dvi7wescFsVx2L5yoY` (primary; more listed in their docs)
- **Stellium, Nozomi, etc.**: see [`references/other-relays.md`](references/other-relays.md)

### Method B: Jito Explorer
https://explorer.jito.wtf/ — paste signature OR bundle ID → see all txs in bundle with tip amount, validator, slot.

### Method C: Block-level analysis (for reverse-engineering)
1. `getTransaction(sig)` → extract `slot`
2. `getBlock(slot, transactionDetails: "full")` → all txs in that slot
3. Filter txs with tip-account transfers
4. Group by block position + signers to identify bundle boundaries

See `references/examples/bundle_analyzer.py` for a working implementation.

### Method D: External indexers
- **Bitquery Jito Bundle API** — GraphQL queries over historical bundles
- **Dune** — tables `jito_solana.*` (verify with `searchTables`)

---

## 🎯 Part 4: How to IDENTIFY bundle types

Given you've found a bundle, what kind is it? Pattern recognition:

### Simple single-tx + tip
Just one tx with a tip transfer. User submitted via Jito's `sendTransaction` for MEV protection + fast landing. Most common bundle type.

### Sandwich attack
Three txs, same pool, same block:
- **Position 1:** attacker buys token X on pool P (price goes up)
- **Position 2:** victim swaps on pool P (buys at the inflated price)
- **Position 3:** attacker sells X on pool P (profits from price move)

Signature: positions 1 and 3 have same signer (different from position 2), opposite directions, same pool. Position 2 is typically a naïve user without MEV protection.

Detection in code: `references/examples/bundle_analyzer.py` has sandwich_detector function.

### Back-run / arbitrage
Two txs:
- **Position 1:** victim's large swap (moves price)
- **Position 2:** attacker arbs the price difference on another pool

Signature: position 2 executes immediately after a large swap, taking advantage of the move.

### Snipe bundle (pump.fun or token launch)
Single tx buy on fresh token creation, often with high tip. Identifying:
- The tx happens within milliseconds of the token's `create` event
- High tip relative to tx value (e.g. 0.1 SOL tip on 0.1 SOL buy = 100% tip ratio)
- Multiple competitors sniping the same new token in the same slot

### Mass-deploy bundle
Single creator wallet submitting multiple `create`/`create_v2` instructions atomically:
- Same signer on 2-5 token creates in one slot
- Each create with a tip (or combined tip on last tx)
- Useful for pump-and-dump operators who want many candidates in one shot

### Liquidation bundle
2-3 txs: setup instructions + the liquidation call + (optional) cleanup. Common on Drift, Solend, Marginfi.

---

## 🎯 Part 5: How to ANALYZE bundles (beyond identifying type)

### KOL / competitor tip profiling
Given a wallet, compute: tipped-tx ratio, median/p95 tip amount, tip budget per SOL traded. Reveals their priority budget and sophistication.

See `references/examples/kol_tip_analysis.py`.

### Historical tip-floor study
Jito publishes live percentiles (25/50/75/95/99th) at https://bundles.jito.wtf/api/v1/bundles/tip_floor. Collect over time or via Dune `jito_solana.*` tables to understand competitive windows.

### Validator adoption
Which validators run Jito client? 95%+ of stake does (as of 2026). Query via `getClusterNodes` + Jito Tip Distribution Accounts — see https://jito-foundation.gitbook.io/mev/jito-solana/data-tracking/tracking-jito-solana-validators.

### Mass-deploy creator detection
Scan pump.fun `create` events grouped by slot + signer. If one wallet does 3+ creates in same slot with tip transfers → mass-deploy operator.

See `references/bundle-analysis.md` for full analysis recipes.

---

## 🎯 Part 6: Submission (secondary — for when user is the bot operator)

If the user wants to submit their own MEV-protected txs:

| Goal | Approach |
|------|----------|
| Simple MEV protection on a single tx | Jito `sendTransaction` with 70/30 priority/tip split |
| Atomic multi-step MEV | Jito `sendBundle` (up to 5 txs) |
| Maximum reliability | Helius Sender (dual-routes) |
| Defensive (anti-sandwich) | Astralane or Paladin/Nozomi staked path |
| Competitive sniping | Jito + Bloxroute in parallel via fastest region |

See [`references/jito.md`](references/jito.md) for the API and [`references/other-relays.md`](references/other-relays.md) for alternatives.

### Four rules for submission

1. **Random-rotate tip accounts** (applies to any relay that offers multiple) — reduces contention
2. **Tip by live percentile**, not hardcoded — pull `tip_floor` before each session, use 75th for normal / 95th for hot / 99th for critical
3. **Region-closest endpoint** saves 10-100 ms RTT
4. **Jito doesn't always land** — parallel-submit across multiple relays for critical tx

---

## Workflow for common questions

### "Was this tx bundled?"
1. Fetch the tx with `getTransaction`
2. Scan instructions for transfer to any known tip account
3. Yes → report tip amount, destination, likely relay

### "Was this tx sandwiched?"
1. Fetch tx + its block
2. Find all jito-tipped txs in the same slot
3. Look for same-signer pre/post pair with opposite swap direction on same pool
4. If found → report suspects, link to explorer

### "How much does this wallet pay in bribes?"
1. Fetch last N signatures (`getSignaturesForAddress`)
2. Batch-fetch all with JSON-RPC array `getTransaction`
3. Extract tips, compute statistics (mean/median/p95/frequency)
4. Report profile

### "What's a reasonable tip for right now?"
1. `curl https://bundles.jito.wtf/api/v1/bundles/tip_floor`
2. Report 25/50/75/95/99 percentiles in lamports + SOL
3. Recommend 75th for normal, 95th for competitive, 99th for critical

## Reference files

- [`references/bribes.md`](references/bribes.md) — **theory: what bribes are**
- [`references/bundle-analysis.md`](references/bundle-analysis.md) — **how to find and identify bundles**
- [`references/jito.md`](references/jito.md) — Jito API (submission details)
- [`references/other-relays.md`](references/other-relays.md) — all 9 MEV relays with what we know so far
- [`references/examples/tip_advisor.py`](references/examples/tip_advisor.py) — live tip-floor → recommended tip
- [`references/examples/bundle_analyzer.py`](references/examples/bundle_analyzer.py) — find siblings + sandwich detection
- [`references/examples/kol_tip_analysis.py`](references/examples/kol_tip_analysis.py) — KOL/competitor tip stats
- [`references/examples/send_tx_jito.py`](references/examples/send_tx_jito.py) — Jito submission with polling

## Related skills

- [`pumpfun-skill`](../pumpfun) — pump.fun specifically, heavy Jito use case
- [`solana-rpc-skill`](../solana-rpc) — base RPC, JSON-RPC batching, Helius Sender details
- [`solscan-skill`](../solscan) — wallet tx history for KOL analysis
- [`dune-skill`](../dune) — historical `jito_solana.*` SQL for macro analysis
