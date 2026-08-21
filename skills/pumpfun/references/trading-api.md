# PumpPortal transaction API — safety boundary

This reference explains the distinction between managed and local transaction APIs so an analyst can interpret public activity and provider documentation. It is **not** a default execution workflow.

## Modes

### Managed / Lightning

The provider constructs, signs, and submits a requested transaction using a provider-managed credential. This introduces provider fees and custody/trust assumptions.

### Local transaction construction

The provider returns an unsigned serialized transaction for inspection. Signing and broadcasting remain outside this skill's default read-only workflow.

## Required safety controls for any future execution workflow

1. Separate research from execution in both code and user interaction.
2. Default to dry-run and testnet/devnet where supported.
3. Use an external signer or local keypair-path interface; never place a raw private key or seed phrase in environment variables, source code, prompts, screenshots, or logs.
4. Decode and display the transaction before approval:
   - network/cluster;
   - wallet/public key;
   - program IDs and accounts;
   - action and asset mint;
   - amount/max spend;
   - recipient;
   - slippage;
   - priority fee and relay tip;
   - recent blockhash/expiry.
5. Simulate/preflight unless the user explicitly accepts the documented risk of skipping it.
6. Require explicit approval for each signing/broadcast action; never reuse blanket approval.
7. Record only public signatures and sanitized metadata, never signer material.
8. Apply rate, spend, slippage, and allowlist limits in deterministic code.

## Research-safe request shape

For schema analysis, use placeholder values only and do not send the request:

```json
{
  "publicKey": "<PUBLIC_KEY_ONLY>",
  "action": "<buy-or-sell>",
  "mint": "<TOKEN_MINT>",
  "amount": "<AMOUNT>",
  "denominatedInSol": "<true-or-false>",
  "slippage": "<PERCENT>",
  "priorityFee": "<SOL>",
  "pool": "auto"
}
```

Provider parameters, fees, pools, and supported routes can change. Verify against current official documentation before citing them.

## What this skill may do automatically

- read public documentation;
- explain fields and trust boundaries;
- inspect an already public transaction signature;
- decode an unsigned transaction without signing;
- estimate fees/costs from public data;
- produce a dry-run checklist.

## What requires a separate explicit workflow

- loading signer material;
- constructing a live order;
- signing;
- broadcasting;
- retrying or fee-bumping a transaction;
- creating a token or claiming fees.
