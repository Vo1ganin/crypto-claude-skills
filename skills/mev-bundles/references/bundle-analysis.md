# Bundle-pattern analysis — evidence and limitations

Use this reference for cautious, read-only analysis of public Solana transactions. Do not equate same-slot activity, known tip-account transfers, or temporal proximity with confirmed bundle membership or intent.

## Evidence levels

### Confirmed bundle relation

Use an authoritative public bundle identifier or provider/explorer record that explicitly groups the transactions. Record the source and access time.

### Candidate relation

When an authoritative identifier is unavailable, describe a **candidate relation** supported by multiple signals:

- same slot with actual transaction indices;
- shared signer/account/program/pool relationships;
- known public relay-tip transfer;
- compatible asset direction and amounts;
- timing/order consistent with the hypothesis.

Never call candidate relations confirmed bundles.

### Weak signal only

Any one of these alone is weak:

- same slot;
- transfer to a known tip account;
- touching the same program;
- similar fee amount;
- repeated wallet activity.

## Ordering-pattern research

For a protective analysis of a suspected adverse ordering pattern:

1. Fetch the target transaction and block with full ordered transaction data.
2. Locate the target's exact transaction index.
3. Identify the exact pool/program/assets and swap direction.
4. Inspect transactions immediately before and after the target.
5. Require evidence of the same actor or coordinated accounts, opposite trade directions, and economically coherent asset changes.
6. Check an authoritative bundle source where available.
7. Report alternative explanations and confidence.

Do not label an event as an attack from same-slot adjacency alone.

## Public relay-tip distribution

For a wallet cohort or time window:

1. Fetch bounded public transaction history.
2. Match transfers to a versioned list of known public tip accounts.
3. Normalize lamports/SOL and record missing/unparsed transactions.
4. Report observed ratio and descriptive percentiles.
5. Do not infer automation, sophistication, strategy, or intent from tip frequency alone.

Use `references/examples/wallet_tip_distribution.py` for a neutral descriptive report.

## Historical aggregate analysis

Dune, Bitquery, public Jito data, and RPC blocks may support aggregate research. Document:

- table/API and query version;
- sample period;
- provider/indexer coverage;
- whether failed/private submissions are missing;
- deduplication and unit normalization;
- freshness/access time.

## Attribution checklist

Before attaching any interpretation to a wallet or transaction, ask:

- Is the account label independently verified?
- Is bundle membership authoritative or inferred?
- Are transaction indices known?
- Are pool, asset and direction relationships established?
- Could unrelated transactions create the same pattern?
- What data is unobserved?
- Is the confidence label explicit?

## Safe output language

Prefer:

- “candidate same-slot relation”
- “observed transfer to a known public tip account”
- “pattern consistent with, but not proof of…”
- “authoritative bundle ID not available”
- “low/medium/high confidence based on…”

Avoid:

- unsupported wallet-owner labels;
- claims of intent or malicious behavior without independent evidence;
- execution recommendations;
- instructions for exploiting ordering patterns;
- strategy attribution from public fees alone.
