# Relay tips and priority fees — neutral terminology

This reference defines public fee signals used in Solana transaction and bundle research. It is descriptive, not an execution guide.

## Priority fee

A standard Solana transaction may set a compute-unit price. The observed priority-fee amount depends on compute usage and the configured price per compute unit.

Research notes:

- Normalize all observations into lamports/SOL and compute-unit terms.
- A high fee can indicate congestion sensitivity, but it does not prove a specific strategy.
- Compare against same-period network baselines rather than hard-coded thresholds.

## Relay tip

Some block-engine/relay flows include a transfer to a published tip account. Jito exposes public tip-account and tip-floor information.

Research notes:

- Relay-tip transfers are observable signals when the relevant accounts are known.
- The presence of a tip does not prove bundle inclusion, intent, or successful landing.
- Relay coverage and validator participation vary over time.
- Keep provider, region, time window, and source freshness in the methodology.

## Combined transaction cost

For descriptive analysis, separate:

```text
base network fee
+ priority fee
+ relay tip
+ provider/service fee where observable
```

Do not collapse these into an intent label. Report missing components and uncertainty.

## Public tip-floor data

Jito publishes a public tip-floor distribution. Treat it as a historical distribution for a defined observation period, not as an automatic live recommendation.

Example response shape:

```json
{
  "landed_tips_25th_percentile": 10000,
  "landed_tips_50th_percentile": 50000,
  "landed_tips_75th_percentile": 200000,
  "landed_tips_95th_percentile": 2000000
}
```

Values and schema can change. Record access time and verify current official documentation.

## Analysis workflow

1. Define the sample period and transaction cohort.
2. Retrieve public transaction data and known public tip accounts.
3. Normalize fee units and identify missing records.
4. Compare the cohort distribution with a same-period baseline.
5. Report percentiles and outliers without assigning intent from fees alone.
6. State indexer/RPC coverage, label confidence, and alternative explanations.

## Common analytical mistakes

- treating a tip transfer as proof of malicious behavior;
- comparing fees across different congestion regimes without normalization;
- hard-coding stale percentile thresholds;
- ignoring transactions missing from the chosen indexer;
- assuming temporal proximity proves bundle membership;
- publishing wallet-owner labels without independent evidence.

Any transaction submission or fee-setting workflow is outside the default scope of this research skill and requires separate explicit safety review.
