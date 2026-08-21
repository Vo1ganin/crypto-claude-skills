# Solana bundle and relay-tip research — summary

Compiled from public documentation. Verify provider schemas, limits and addresses against current official sources before use.

## Scope

This document supports read-only analysis of:

- priority fees and relay tips as public fee signals;
- atomic bundle structure;
- public tip-floor distributions;
- bundle-status terminology;
- attribution and missing-data limitations;
- protective monitoring of common ordering patterns.

It is not a transaction-submission guide.

## Fee terminology

### Priority fee

Standard Solana compute-unit pricing paid as part of a transaction. Normalize by compute usage and compare within the same congestion regime.

### Relay tip

A transfer to a published relay/block-engine tip account. The presence of a tip is observable but does not by itself prove intent, bundle membership, or successful landing.

### Total observable cost

For analysis, keep separate:

```text
base network fee
+ priority fee
+ public relay tip
+ provider/service fee where observable
```

## Public Jito data

Jito documents public block-engine concepts, bundle-status APIs, tip accounts, and a public tip-floor distribution. Endpoint availability and rate limits can change.

Research-safe uses:

- record tip-floor percentiles with access time;
- inspect public bundle-status terminology;
- identify known public tip-account transfers;
- compare fee distributions across bounded cohorts;
- describe atomic bundle semantics and uncertainty.

Do not convert public percentiles into automatic live fee settings.

## Bundle mechanics

A bundle is an ordered set of transactions intended for atomic/sequential handling by a block-engine flow. Public data may expose only part of the lifecycle.

Common status concepts include pending, failed, landed, confirmed and finalized. Exact response schemas are provider-specific.

## Attribution limits

- Temporal proximity does not prove common ownership or bundle membership.
- A transfer to a known tip account does not prove strategy or malicious intent.
- Private order flow and unobserved failed submissions bias the sample.
- RPC/indexer completeness and label quality vary.
- Program/account reuse can create false positives.

## Defensive analysis workflow

1. Define a signature, wallet cohort, program/pool, and time window.
2. Record RPC/indexer/provider and access time.
3. Retrieve public transactions and normalize fees/accounts/programs/timing.
4. Identify candidate relationships using more than one signal.
5. Compare against a documented same-period baseline.
6. Report alternative explanations and confidence.
7. Save reproducible scripts/queries and limitations.

## Public tools and sources

- Jito explorer and official low-latency/bundle documentation
- public Jito tip-floor distribution
- Bitquery public documentation for Solana/Jito data
- Dune `jito_solana.*` tables where available
- Solana RPC transaction/block data

Sources:

- https://docs.jito.wtf/lowlatencytxnsend/
- https://jito-foundation.gitbook.io/mev/mev-payment-and-distribution/on-chain-addresses
- https://docs.bitquery.io/docs/blockchain/Solana/Solana-Jito-Bundle-api/
- https://bundles.jito.wtf/api/v1/bundles/tip_floor

Any signing, broadcasting, fee-setting, or relay-submission workflow requires a separate explicit safety review and is outside this summary.
