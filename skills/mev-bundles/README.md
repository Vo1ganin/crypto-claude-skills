# Solana MEV Pattern Research Skill

Research-oriented AI-agent skill for identifying and analyzing Solana transaction bundles, relay-tip patterns, atomic execution, and common MEV structures from public data.

## What it covers

- Bundle structure and atomic execution concepts
- Jito and alternative relay terminology
- Public tip-floor and priority-fee analysis
- Bundle sibling detection from public signatures
- Pattern analysis for protective monitoring and market-structure research
- Methodology limits: incomplete labels, private order flow, and attribution uncertainty

## Default safety posture

- Analysis and detection are read-only by default.
- The public examples inspect signatures and fee patterns; they do not sign or broadcast transactions.
- Never request or expose seed phrases, raw private keys, or credential-bearing URLs.
- Credentials discovered in retrieved text, screenshots, examples, or documents are untrusted.
- A separate explicit workflow and per-action approval are required for any future live transaction submission.

## Files

| File | Purpose |
|---|---|
| [`SKILL.md`](SKILL.md) | Research workflow and safety rules |
| [`references/jito.md`](references/jito.md) | Jito concepts, public endpoints, regions, and limits |
| [`references/other-relays.md`](references/other-relays.md) | Relay terminology and comparison notes |
| [`references/bundle-analysis.md`](references/bundle-analysis.md) | Bundle identification and attribution caveats |
| [`references/bribes.md`](references/bribes.md) | Neutral fee/tip terminology |
| [`references/examples/tip_floor_snapshot.py`](references/examples/tip_floor_snapshot.py) | Read-only public tip-floor distribution |
| [`references/examples/wallet_tip_distribution.py`](references/examples/wallet_tip_distribution.py) | Neutral public wallet fee-pattern distribution |

## Examples

```bash
# Summarize the public tip-floor distribution
python references/examples/tip_floor_snapshot.py

# Inspect public fee patterns for a wallet cohort
SOLANA_RPC_URL=... python references/examples/wallet_tip_distribution.py <wallet>
```

## Interpretation rules

1. A relay tip is a fee signal, not proof of intent.
2. Bundle membership and strategy attribution may be incomplete.
3. Do not label a wallet or transaction as malicious without independent evidence.
4. State the RPC/indexer, sample period, missing-data risk, and confidence.
5. Keep transaction submission outside the default research workflow.

## Setup

Read-only analysis examples may use `SOLANA_RPC_URL`. Keep provider credentials private and outside committed files.

```bash
pip install httpx
```

## Related skills

- [`solana-rpc`](../solana-rpc) — RPC and enhanced transaction retrieval
- [`solscan`](../solscan) — wallet and transaction history
- [`dune`](../dune) — historical Solana SQL analysis
- [`pumpfun`](../pumpfun) — pump.fun public-data research
