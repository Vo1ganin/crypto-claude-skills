# Other MEV-Protected Relays on Solana

Jito dominates, but other providers exist. This file is a **living reference** — the user may have detailed notes to add on some of these. Keep structure consistent as more are filled in.

## Quick comparison table

| Provider | Model | Tip account(s) | Auth | Status in this skill |
|----------|-------|----------------|------|----------------------|
| **Jito** | Bundle auction | 8 rotating | Optional UUID | ✅ Full coverage in `jito.md` |
| **Helius Sender** | Dual-route (validators + Jito) | N/A (handled internally) | Helius key | ✅ Covered in `solana-rpc-skill/references/helius-extensions.md` |
| **Bloxroute** | Direct validator delivery | TBD | API key | 🟡 Stub — user to supply |
| **Paladin (formerly Nozomi)** | Jito fork, anti-sandwich | TBD | TBD | 🟡 Stub — user to supply |
| **NextBlock** | MEV protection | TBD | TBD | 🟡 Stub — user to supply |
| **Temporal** | Historical (possibly defunct) | N/A | N/A | 🟡 Verify if still active |

## Helius Sender

Already covered in `solana-rpc-skill/references/helius-extensions.md`. Key points:

- **What it is:** Tx submission service that dual-routes through staked validator connections AND Jito bundles simultaneously
- **Advantage:** Higher landing rate than either alone, because if Jito leader isn't up, your tx still lands via the staked path
- **Auth:** Your Helius API key (same as regular RPC)
- **Setup:** Point tx submission at a specific Helius Sender endpoint (documented in Helius docs — not the standard RPC URL)
- **Cost:** Included in Helius plan quota; counts as credits
- **When to use:** Production trading bots where latency AND reliability both matter. Generally the simplest drop-in replacement for `sendTransaction`.

Docs: https://www.helius.dev/docs/api-reference/sender

## Bloxroute (stub)

Bloxroute provides infrastructure for MEV-protected tx delivery on Solana (and other chains). Details to fill when user supplies:

- Exact endpoint URL
- Auth mechanism (API key? wallet signature?)
- Tip account address(es)
- Pricing model
- Sample code

Rough shape (to verify): POST to a Bloxroute endpoint with signed tx + tip instruction → enters their proprietary auction → delivered to validators.

**Known strengths:** Historically good for competitive MEV, direct relationships with validators, low-latency co-located nodes.

## Paladin / Nozomi (stub)

Paladin is a validator client fork (Jito-Solana derivative) that adds anti-sandwich protection. Previously known as Nozomi. Details to fill:

- Endpoint(s)
- Auth
- Specific features vs plain Jito
- Tip mechanics (likely similar to Jito)
- When to prefer over Jito

**Known positioning:** "anti-sandwich" — if a Paladin-enabled validator is producing your block, it won't include sandwich attacks against your tx. Useful for users who are frequently victimized.

## NextBlock (stub)

Another MEV-protected delivery provider. Details TBD.

## Temporal / other

Verify if still operational before using. Once the user supplies notes, fill in.

## Multi-relay production pattern

When reliability is critical, submit the **same tx** across multiple relays in parallel:

```
tx = build_and_sign(...)  # fresh blockhash, signed once

asyncio.gather(
    jito.send(tx, region="frankfurt"),
    jito.send(tx, region="amsterdam"),
    helius_sender.send(tx),
    public_rpc.send(tx),
    # ...add more once configured
)
```

Only one will actually land (nonce/sig-unique). Others error silently. Latency = `min(all)`. Reliability ≈ 1 - product(all failure probs).

Downside: you pay tips to each relay if you include tip per relay. Smart pattern: only include Jito tip in the Jito version of the tx; submit tip-less versions elsewhere.

## Update instructions

When the user provides details for a relay, fill the corresponding section with:
1. Endpoint URL(s)
2. Auth
3. Tip account(s) if applicable
4. Python example of submission
5. When to prefer it over Jito
6. Commit with message `docs(mev-bundles): add <relay> details` if umbrella, then sync to standalone.
