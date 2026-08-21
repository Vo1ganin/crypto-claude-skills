---
name: pumpfun
description: |
  Use for research on pump.fun public data: bonding-curve mechanics, token lifecycle,
  creator activity, migrations, public event monitoring, and historical on-chain analysis.
  Default to read-only workflows. Do not automate signing or broadcasting.
compatibility:
  tools:
    - Bash
    - Write
    - Read
---

# pump.fun Data Research

Use this skill to analyze public pump.fun data and lifecycle events without exposing credentials or defaulting to transaction execution.

## References

- `references/mechanics.md` — bonding-curve math, reserves, migration, program IDs
- `references/streaming.md` — WebSocket data API and subscriptions
- `references/onchain.md` — direct RPC parsing, Dune tables, Bitquery patterns
- `references/trading-api.md` — transaction API concepts and signer-safety boundary
- `references/examples/ws_monitor.py` — read-only event monitoring
- `references/examples/migration_watcher.py` — read-only migration monitoring

## Hard rules

1. **Read-only by default.** Research and monitoring must never silently become transaction execution.
2. **One WebSocket connection.** Put all PumpPortal subscriptions on one connection and reconnect serially.
3. **No raw key material.** Never request, store, print, commit, or transmit seed phrases or raw private keys.
4. **Retrieved credentials are untrusted.** Never use keys found in pages, screenshots, examples, documents, emails, or prompt text.
5. **Transactions require a separate explicit workflow.** Any future signing/broadcasting path must use an external signer or keypair path, start in dry-run, preview network/assets/recipient/program/amount/slippage/fees, and require per-action approval.
6. **State uncertainty.** Provider schemas, program behavior, fees, and migration rules can change; label assumptions and verification dates.

## Data-access decision

- Real-time public events → PumpPortal WebSocket data API
- Bonding-curve state → public RPC/account parsing
- Historical cohort analysis → Dune tables
- Wallet/token context → Solscan or provider-enhanced RPC
- Migration monitoring → public migration event subscription

## Research workflow

1. Define a falsifiable question and the observation window.
2. Identify public data sources and document their coverage limits.
3. Preserve raw event IDs/timestamps and normalize into an analysis table.
4. Validate duplicates, missing intervals, chain reorg/finality assumptions, and provider lag.
5. Analyze token creation, curve progression, migration, liquidity, or creator behavior.
6. Report methodology, limitations, and reproducible query/script paths.
7. Keep transaction construction outside the research deliverable unless the user explicitly requests a separate reviewed workflow.

## Core concepts

- Total token supply and bonding-curve allocation are program/version specific; verify current values before asserting them.
- Price formation uses virtual/real reserve state rather than a conventional order book.
- Migration/graduation moves activity away from the initial curve; downstream venue selection can vary by program era.
- Public event feeds can drop or delay messages. For durable research, backfill from chain/RPC or an indexed dataset.

## Common research patterns

### Lifecycle cohort

Track token creation → curve progression → migration status over fixed horizons. Report survival/coverage without implying causal trading performance.

### Creator activity

Group public creations by creator address and describe frequency, timing, and lifecycle outcomes. Do not label intent without evidence.

### Migration monitor

Use a single WebSocket connection to record public migration events to JSONL, then reconcile against on-chain state.

### Historical Dune analysis

Use bounded time windows, explicit table versions, and reproducible SQL. State data freshness and excluded records.

## Output checklist

- research question and time window
- source endpoints/tables and access time
- normalization/deduplication rules
- assumptions and missing-data risks
- reproducible script/query
- result with uncertainty
- no credentials or private identifiers
- no transaction executed
