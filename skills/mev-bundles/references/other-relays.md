# Solana relay landscape — research comparison

This document provides neutral terminology for comparing public relay/block-engine claims and observable data. It is not an execution or routing guide.

## Comparison dimensions

For each provider, record only sourced and time-bounded facts:

- service model: RPC, block engine, staked connection, encrypted/private relay, or tooling library;
- public documentation URL;
- public status/analytics data available;
- stated network/validator coverage;
- authentication category without exposing credentials;
- public fee/tip terminology;
- data-retention and rate-limit statements;
- verification date;
- unknown/TBD fields.

Do not rank providers by execution quality without a reproducible benchmark.

## Providers commonly discussed

### Jito

Publicly documents bundle/block-engine concepts, tip accounts, status terminology, and tip-floor data. See `jito.md` for research-safe usage.

### Helius Sender

A managed transaction-delivery product in the Helius ecosystem. For research, use public documentation to describe the service model and avoid claiming comparative landing performance without a controlled benchmark.

### bloXroute

Publishes Solana Trader API documentation. Record public service-model and fee terminology only; do not embed signed transaction payloads or low-latency submission recipes in this skill.

### Nozomi / Temporal

Described publicly as transaction-delivery infrastructure. Endpoint, authentication, coverage and current product status must be verified against current official documentation.

### Astralane, BlockRazor, Stellium and other services

Treat as provider entries requiring source verification. Do not fill missing fields from memory or private notes.

### Falcon / Flashbots / similarly named tools

Disambiguate transport libraries, Solana services and non-Solana products before including them in a comparison. Similar names do not imply equivalent functionality.

## Research template

```yaml
provider: ""
verified_at: "YYYY-MM-DD"
official_sources: []
service_model: ""
public_research_data: []
auth_category: "unknown"
fee_terms: []
coverage_claims: []
rate_limit_claims: []
unknowns: []
confidence: low
```

## Benchmarking requirements

A credible comparison needs:

1. a fixed time window and workload;
2. identical transaction/data cohorts where lawful and safe;
3. controlled geography/network conditions;
4. observed failures and missing responses;
5. clear metric definitions;
6. no signer material in logs;
7. no live execution from this read-only skill.

Without that design, use wording such as “provider-stated,” “not independently benchmarked,” and “current status unverified.”

## Safety boundary

Do not include or generate:

- signed transaction examples;
- live submission endpoints/payloads intended for execution;
- region/latency optimization recipes;
- parallel multi-relay submission code;
- fee/tip recommendations;
- credential values or credential-bearing URLs;
- instructions for exploiting transaction ordering.

Any execution-specific implementation belongs in a separate private, explicitly approved and safety-reviewed project.
