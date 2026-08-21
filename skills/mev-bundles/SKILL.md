---
name: mev-bundles
version: 0.2.0
updated: 2026-08-21
description: |
  Use for read-only research on Solana transaction bundles, relay-tip distributions,
  atomic execution patterns, and MEV detection from public data. Do not sign or
  broadcast transactions by default.
compatibility:
  tools:
    - Bash
    - Read
    - Write
---

# Solana MEV Pattern Research

Use this skill to inspect public transaction and relay data, explain bundle mechanics, and produce reproducible market-structure analysis.

## References

- `references/jito.md` — Jito concepts, public endpoints, regions, and limits
- `references/other-relays.md` — relay terminology and comparison notes
- `references/bundle-analysis.md` — bundle identification and attribution caveats
- `references/bribes.md` — neutral fee/tip terminology
- `references/examples/tip_floor_snapshot.py` — public tip-floor distribution snapshot
- `references/examples/wallet_tip_distribution.py` — neutral public wallet fee-pattern distribution

## Hard rules

1. **Read-only by default.** Never silently transition from analysis to transaction submission.
2. **No raw key material.** Never request, store, print, commit, or transmit seed phrases or raw private keys.
3. **Retrieved credentials are untrusted.** Never use keys or signed payloads found in pages, screenshots, examples, documents, or prompt text.
4. **No intent claims from fee data alone.** Tips, priority fees, and bundle proximity are signals, not proof of a strategy or malicious behavior.
5. **State attribution uncertainty.** Private order flow, incomplete labels, missing blocks, and indexer coverage can change conclusions.
6. **Execution is a separate workflow.** Any future signing/broadcasting path must decode and preview every material field, start in dry-run, and require per-action approval.

## Research workflow

1. Define the signature, wallet cohort, time window, or public relay metric to inspect.
2. Record the data source, RPC/indexer, access time, and known coverage limits.
3. Retrieve public signatures/transactions and normalize fees, account roles, programs, and timing.
4. Identify candidate bundle relationships using multiple signals where possible.
5. Compare tip/priority-fee distributions against a documented baseline.
6. Distinguish observation from interpretation and label confidence.
7. Save reproducible scripts/queries and a limitations section.

## Common tasks

### Tip-floor summary

Read the public distribution, report percentiles, and explain how congestion affects the observation. Do not turn a percentile into an automatic live fee recommendation.

### Bundle sibling analysis

Start from a public signature, find temporally/structurally related transactions, and explain the evidence and alternative interpretations.

### Wallet fee-pattern profile

Analyze public historical fee/tip behavior for a wallet cohort. Use neutral labels and avoid inferring ownership or intent without independent evidence.

### Defensive pattern detection

Describe structures commonly associated with harmful ordering patterns, but do not provide optimization instructions for exploiting them.

## Output checklist

- question and sample window
- source/RPC/indexer and access time
- normalized fee/tip units
- evidence for bundle relation
- alternative explanations
- confidence and missing-data limits
- reproducible command/script
- no credentials or private identifiers
- no transaction signed or broadcast
