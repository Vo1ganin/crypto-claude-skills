# Solana MEV-Protected Relays (all 9)

Ranked roughly by current-market adoption. Details partially filled from public docs; sections marked **TBD** are waiting for user-supplied notes (exact endpoints, tip addresses, empirical pricing).

## Quick comparison table

| Provider | Model | Tip required | Bundle support | Key differentiator |
|----------|-------|--------------|----------------|--------------------|
| **Jito** | Public auction | Yes (1000 lam min) | Yes (atomic up to 5) | Dominant; 95%+ of Solana MEV flows through it |
| **Helius Sender** | Dual-route (staked + Jito) | Internal | Via Jito path | Managed; high landing rate without configuration |
| **Bloxroute** | Private relay network | Yes (0.001 SOL min) | Yes | Global low-latency network; tipping address rotation |
| **Nozomi / Temporal** | Staked connections + TPU routing | API-key based | Combines self-hosted + staked + Jito | Direct TPU knowledge for timing |
| **Astralane** | Private encrypted relay | TBD | TBD | Hides intent from validators until last moment |
| **BlockRazor** | Multi-mode (RPC, Fast, Bundle, Gas Sponsor) | TBD | Yes | Flexibility; real-time rebates; cross-chain |
| **Stellium** | Fast Landing + validator ops | Yes (0.001 SOL min) | TBD | Validator yield optimization + tip rotation |
| **Falcon** | QUIC client for tx submission | TBD | TBD | Low-level QUIC transport (not bundle relay per se) |
| **Flashblocks** | Rollup streaming layer | N/A | N/A | **Not a Solana service** — EVM/rollup oriented |
| **1node** | TBD | TBD | TBD | **Stub — user to supply** |

**Advice:** Start with Jito. Add Helius Sender for managed reliability. Bloxroute/Nozomi for competitive edge. Others situationally.

---

## Jito

See [`jito.md`](jito.md) for the full reference.

- URL pattern: `https://{region}.mainnet.block-engine.jito.wtf`
- 8 tip accounts (random-rotate)
- 70/30 split for `sendTransaction`, pure tip for `sendBundle`
- Minimum tip: 1000 lamports
- Free tier: 1 rps per IP per region

---

## Helius Sender

Covered in `solana-rpc-skill/references/helius-extensions.md`.

- Dual-routes through staked validator connections AND Jito bundles simultaneously
- Managed — higher landing rate than either alone
- Auth via your Helius API key (same as regular RPC)
- Counts as credits on your Helius plan
- No separate tip account — priority fee and Jito tip handled internally

Good default if you already use Helius. Simplest drop-in replacement for `sendTransaction`.

---

## Bloxroute

Docs: https://docs.bloxroute.com/solana/trader-api/

### Endpoints
| Region | URL |
|--------|-----|
| Global | `http://global.solana.dex.blxrbdn.com/api/v2/submit` |
| NY | `http://ny.solana.dex.blxrbdn.com/api/v2/submit` |
| Additional regional endpoints exist — check docs |

Note: HTTP (not HTTPS) is recommended for lowest latency. They also support HTTPS.

### Tip
- **Primary tip wallet:** `HWEoBxYs7ssKuudEjzjmpfJVX7Dvi7wescFsVx2L5yoY`
- Minimum tip: **0.001 SOL (1,000,000 lamports)**
- Official list of tipping addresses in Bloxroute docs (multiple available; alternate for contention)
- Tip goes as `SystemProgram.transfer` instruction inside your tx

### Submission
POST signed base64 tx:
```
POST http://{region}.solana.dex.blxrbdn.com/api/v2/submit
Content-Type: application/json
{
  "transaction": {"content": "<base64_signed_tx>"},
  "useStakedRPCs": true,
  "fastBestEffort": false
}
```

Requires Bloxroute auth header (Trader API subscription).

### Recommended pattern
Submit to both `global.*` endpoint and nearest regional endpoint in parallel for resilience + best landing. Bloxroute scores upcoming validators for sandwich risk and adjusts delivery — high-risk leaders delayed/skipped.

---

## Nozomi / Temporal

Docs: https://use.temporal.xyz/nozomi/

### How it works
Routes transactions through:
1. Self-hosted Solana nodes
2. Staked connections (higher QoS from validators)
3. Jito bundles (when beneficial)

Key feature: Nozomi times deliveries to each validator's TPU (Transaction Processing Unit) based on current leader schedule. Does not simulate transactions.

### Endpoint
```
POST https://<region>.nozomi.temporal.xyz/?c=<API_KEY>
```
(Exact regional URL list: TBD — user or official docs via `llms-full.txt`)

### Auth
API key passed as query param `?c=<API_KEY>`.

### Supported methods
`sendTransaction` with `encoding: "base64"` (must set explicitly, otherwise malformed).

### Tip
TBD — not found in public excerpts. User to supply tip account and minimum.

### When to use
When Jito leader isn't up and you still need competitive landing. Production bots typically dual-submit to Jito + Nozomi and take whichever lands.

---

## Astralane

Website: https://astralane.io/

### How it works
Private relay network with **encrypted transaction channels**. Your tx intent is hidden from:
- The mempool
- The validator (until the last possible moment before inclusion)

Goal: anti-front-running / anti-sandwich.

### Endpoint / Auth / Tip
TBD — user to supply. Astralane publishes detailed articles on Solana MEV defense but exact trader-API details require account.

### When to use
When sandwich protection matters more than raw speed. Less competitive-sniping-oriented, more defensive.

---

## BlockRazor

Docs: https://blockrazor.gitbook.io/blockrazor

### How it works
Multi-mode transaction infrastructure:
- **RPC** — standard JSON-RPC with MEV protection baked in
- **Fast** — low-latency submission
- **Bundle** — atomic bundles
- **Gas Sponsor** — 3rd party pays fees (useful for UX)

Supports real-time validator rebates. Cross-chain (Ethereum, BSC, Solana, Base).

### Endpoint / Auth / Tip
TBD — page scraping didn't surface details. Consult their `llms-full.txt` or request Solana-specific config from BlockRazor.

### When to use
When you need multiple submission modes through one provider or want rebate revenue on routine tx flow.

---

## Stellium

Docs: https://docs.stellium.dev/

### How it works
Fast landing service with validator-side yield optimization. 0% MEV commission, 0% inflation commission on staked SOL (marketing — verify current terms).

### Endpoint
```
POST https://<STELLIUM_ENDPOINT>/<APIKEY>
```
Standard `sendTransaction` JSON-RPC with `encoding: "base64"`.

### Tip
- Minimum tip: **0.001 SOL**
- **Alternate between different tip addresses** for consecutive transactions (their recommendation — like Jito's 8-account rotation)
- Exact tip address list: TBD — in their API reference

### When to use
Value proposition is yield-optimized validators + fast landing. Competitive with Bloxroute/Nozomi on latency.

---

## Falcon

Context: Falcon is described in the ecosystem as a **QUIC client** for Solana transaction submission (Rust crate `falcon-client`). Lower-level than a relay — it's the transport protocol library.

### What it actually is
- QUIC over UDP client for direct TPU delivery to validator leaders
- Used by other relays / bots as the transport layer, not as a MEV auction itself
- Not a direct competitor to Jito / Bloxroute — more like the plumbing they use

### When to use
If you're building custom infrastructure and want direct validator QUIC delivery without going through a third-party relay. Requires leader schedule awareness and own validator keys/tokens.

TBD: is this the same "Falcon" the user means? **User to confirm** — might be different service.

---

## Flashblocks

Context: Flashblocks is **not a Solana service**. It's a block-building platform for EVM rollups (Ethereum L2s like Unichain) using Trusted Execution Environments. Unrelated to Solana MEV infrastructure.

If the user meant something else by "Flashblocks" in a Solana context, **they should clarify** — possibly confused with:
- **Flashbots** (Ethereum MEV — not Solana)
- Some newer Solana service named similarly

Section kept here as explicit "not applicable" so agents don't try to use it.

---

## 1node

**Stub — user to supply.**

Not a widely-indexed Solana MEV service as of 2026-04 public searches. May be:
- A custom/private relay
- Very new
- Internal / limited-access

User to provide: endpoint, auth, tip accounts, minimum tip, when to use.

---

## Multi-relay production pattern

When reliability is critical, submit the **same signed tx** across multiple relays in parallel:

```python
import asyncio

async def submit_everywhere(tx_base64):
    results = await asyncio.gather(
        send_jito(tx_base64, region="frankfurt"),
        send_jito(tx_base64, region="amsterdam"),
        send_helius_sender(tx_base64),
        send_bloxroute(tx_base64, region="ny"),
        send_nozomi(tx_base64),
        # ...add more as relays get configured
        return_exceptions=True,
    )
    # Only one can actually land (nonce/sig-unique). Others 4xx harmlessly.
    return results
```

Latency = `min(all)`. Reliability increases with the number of paths. Cost: per-relay tips (if relay-specific) are real; for Jito-tip-only txs, the Jito tip doesn't pay other relays.

**Smart pattern:** include only Jito tip in the tx version sent to Jito; send tip-free versions to Bloxroute/Nozomi (their auth alone is usually enough). Validators on their staked paths don't require tips — they land on reliability, not bidding.

## Update instructions

When filling TBD sections:
1. Edit this file with endpoint URL, auth format, tip account(s), min tip
2. Add a small Python example to `references/examples/send_<relay>.py`
3. Commit with `docs(mev-bundles): add <relay> details`
4. Sync standalone repo via `scripts/sync-to-standalone.sh mev-bundles`
