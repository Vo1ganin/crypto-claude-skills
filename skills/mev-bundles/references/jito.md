# Jito public data for bundle research

This reference covers public Jito concepts and data useful for read-only research. It intentionally omits transaction-submission payloads, live fee-setting recommendations, low-latency optimization, and multi-region execution guidance.

## Research concepts

### Bundle

An ordered group of transactions handled through a block-engine flow. Public visibility may be incomplete, especially for failed/private submissions.

### Relay tip

A transfer to a published tip account. It is an observable fee signal, not proof of intent, strategy, malicious behavior, bundle membership, or successful landing.

### Bundle status

Public/provider data may expose statuses such as pending, failed, landed, confirmed, or finalized. Exact schemas and retention windows change; verify current official documentation.

## Public research sources

- Jito documentation: bundle concepts, status terminology, public tip accounts
- Jito public tip-floor distribution
- Jito explorer for public bundle/signature lookup
- Dune or Bitquery indexed historical tables where available
- Solana RPC block and transaction data

Record the source, access time, region/provider context where relevant, and known retention/coverage limits.

## Tip-floor distribution

The public tip-floor endpoint reports a historical distribution of landed tips. Values are SOL-denominated decimals in the currently observed schema; validate the schema before conversion.

Use it to:

- describe same-period fee distributions;
- compare bounded cohorts;
- monitor changes over time;
- document congestion context.

Do not treat a percentile as an automatic live recommendation.

The read-only example `references/examples/tip_floor_snapshot.py` normalizes the public response into both SOL and lamports and states its descriptive limitation.

## Tip-account matching

A versioned list of documented public tip accounts can support descriptive matching. Requirements:

1. Record the account-list source and verification date.
2. Sum all matching transfer instructions in a transaction.
3. Track unparsed/missing transactions separately.
4. Do not infer intent or bundle membership from the transfer alone.
5. Prefer an authoritative bundle identifier when available.

## Bundle-status research

When analyzing a known public bundle identifier:

- preserve the identifier and source;
- record transaction signatures and reported slot/status;
- distinguish provider status from chain confirmation;
- handle missing/expired status data explicitly;
- avoid treating absence from one endpoint as proof the bundle never existed.

## Rate and freshness limits

Public endpoints can be rate-limited and can change without notice. Use bounded requests, backoff on 429/5xx, cache research snapshots with access time, and avoid high-frequency polling unless explicitly permitted.

## Safety boundary

This research skill does not:

- construct, sign, submit, retry, or fee-bump transactions;
- recommend a live fee/tip amount;
- optimize region/latency for execution;
- provide multi-relay submission code;
- accept signed payloads or signer material.

Any future execution workflow requires separate safety review, dry-run, deterministic limits, full transaction preview, and explicit per-action approval.

## Sources

- https://docs.jito.wtf/lowlatencytxnsend/
- https://jito-foundation.gitbook.io/mev/mev-payment-and-distribution/on-chain-addresses
- https://explorer.jito.wtf/
- https://bundles.jito.wtf/api/v1/bundles/tip_floor
