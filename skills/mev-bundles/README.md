# MEV Bundles & Bribes Skill

Claude Code skill for MEV-protected tx delivery on Solana — Jito (primary) plus alternative relays, with built-in bundle analysis tools for reverse-engineering others' bundles.

## What it does

- **Send txs / bundles via Jito** block engine (region-aware, 8 tip accounts, auction timing)
- **Price tips correctly** using live `tip_floor` percentiles instead of guessing
- **Route via alternative relays** (Helius Sender, Bloxroute, Paladin, NextBlock — stubs to be filled as user supplies details)
- **Analyze others' bundles** — detect sandwich attacks, profile KOL tipping, reverse-engineer competitor bot strategies
- **Explain "bribes"** precisely — priority fee vs Jito tip vs relay tip; 70/30 split; when each applies

## When it triggers

User mentions: bundle, Jito, bribe, tip, priority fee, MEV, sandwich attack, sniper bot, copytrade tier, landing rate, block engine, atomic tx, sendBundle.

## Files

| File | Purpose |
|------|---------|
| [`SKILL.md`](SKILL.md) | Workflow, four hard rules (rotation / percentile / region / Jito-leader fallback) |
| [`references/bribes.md`](references/bribes.md) | Precise terminology, when to use what, common mistakes |
| [`references/jito.md`](references/jito.md) | Full Jito Block Engine API: endpoints, regions, auth, limits |
| [`references/other-relays.md`](references/other-relays.md) | Helius Sender + stubs for Bloxroute/Paladin/NextBlock |
| [`references/bundle-analysis.md`](references/bundle-analysis.md) | Reverse-engineering bundles, sandwich detection |
| [`references/examples/tip_advisor.py`](references/examples/tip_advisor.py) | Live tip-floor → recommended tip |
| [`references/examples/send_tx_jito.py`](references/examples/send_tx_jito.py) | Submit signed tx via Jito with polling |
| [`references/examples/bundle_analyzer.py`](references/examples/bundle_analyzer.py) | Find bundle siblings + sandwich detection |
| [`references/examples/kol_tip_analysis.py`](references/examples/kol_tip_analysis.py) | Statistical profile of KOL's tip behavior |

## Key rules

1. **Random-rotate across 8 tip accounts** to reduce contention
2. **Tip by percentile**, not by guess (pull `tip_floor` API)
3. **Pick region-closest endpoint** (save 10-100 ms RTT)
4. **Jito doesn't always land** — fall back to Helius Sender or parallel-submit via multiple relays

## Quick examples

```bash
# Get recommended tip amount
python references/examples/tip_advisor.py --urgency hot

# Analyze a KOL's tip behavior over last 500 tx
SOLANA_RPC_URL=... python references/examples/kol_tip_analysis.py <wallet>

# Look up a bundle and detect sandwich
SOLANA_RPC_URL=... python references/examples/bundle_analyzer.py <signature>

# Send your own signed tx via Jito (Frankfurt region)
python references/examples/send_tx_jito.py <base64_tx> --region frankfurt --poll
```

## Setup

```bash
pip install httpx
```

For bundle analysis / KOL profiling — set `SOLANA_RPC_URL` (see [`solana-rpc-skill`](../solana-rpc)).
For submission via Jito — no auth required on free tier (1 rps per IP per region); paid UUID gets more.

## Status of other relays

- ✅ **Jito** — fully covered
- ✅ **Helius Sender** — covered in [`solana-rpc-skill`](../solana-rpc/references/helius-extensions.md)
- 🟡 **Bloxroute** — stub; waiting for details
- 🟡 **Paladin / Nozomi** — stub
- 🟡 **NextBlock** — stub

When user supplies relay details, update `references/other-relays.md` and commit with `docs(mev-bundles): add <relay>`.

## Related skills

- [`pumpfun-skill`](../pumpfun) — sniping pump.fun tokens (heavy Jito use case)
- [`solana-rpc-skill`](../solana-rpc) — base RPC + Helius Sender
- [`solscan-skill`](../solscan) — wallet tx history for KOL analysis
- [`dune-skill`](../dune) — historical `jito_solana.*` SQL for macro analysis
