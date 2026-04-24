# pump.fun Mechanics & Program Details

## Token economy

### Supply (every pump.fun token, fixed)
| | Value |
|--|------|
| Total supply | 1,000,000,000 (1B) |
| On bonding curve | 793,100,000 (79.31%) |
| Reserved for migration | 206,900,000 (20.69%) |

The 206.9M is not tradeable on the curve — it's locked and used to seed the AMM pool (PumpSwap) when the curve completes.

### Bonding curve progress

Given `tokens_in_curve` (raw token reserve, scaled to 6 decimals typically):

```
progress_pct = 100 - (((tokens_in_curve - 206_900_000) * 100) / 793_100_000)
```

- `tokens_in_curve = 1,000,000,000` → 0% progress (fresh token)
- `tokens_in_curve = 206,900,000` → 100% progress → migration triggers

### Price (constant-product AMM with virtual reserves)

```
price_per_token = (virtualSol + realSol) / (virtualTokens + realTokens)
```

**Classic initial virtual reserves at token creation** (values used historically; may vary per era — always verify from the bonding curve account state):
- `virtualSol = 30` (in SOL)
- `virtualTokens = 1_073_000_000`

Early buyers get cheapest tokens because `realSol` is low. As curve fills, effective price rises non-linearly.

### Market cap at migration

When the curve completes (~793M tokens sold), accumulated SOL is historically ≈ **85 SOL** raised (subject to protocol tuning). Market cap on graduation = current price × total supply (incl. reserved). Thresholds have shifted over time — check `pump_evt_complete` events in Dune for current era.

## Program IDs

| Account | Address |
|---------|---------|
| **pump.fun main program** | `6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P` |
| Mayhem (paid/premium mode) | `MAyhSmzXzV1pTf7LsNkrNwkWKTo4ougAJ1PPg47MD4e` |
| Global Params PDA | `13ec7XdrjF3h3YcqBTFDSReRcUFwbCnJaAQspM4j6DDJ` |
| SOL Vault | `BwWK17cbHxwWBKZkUYvzxLcNQ1YVyaFezduWbtm2de6s` |

### Mayhem fee recipients
Seven rotating accounts used for load-balancing fees in Mayhem mode:
```
GesfTA3X2arioaHp8bbKdjG9vJtskViWACZoYvxp4twS
4budycTjhs9fD6xw62VBducVTNgMgJJ5BgtKq7mAZwn6
8SBKzEQU4nLSzcwF4a74F2iaUDQyTfjGndn6qUWBnrpR
4UQeTP1T39KZ9Sfxzo3WR5skgsaP6NZa87BAkuazLEKH
8sNeir4QsLsJdYpc9RZacohhK1Y5FLU3nC5LXgYB4aa6
Fh9HmeLNUMVCvejxCtCL2DbYaRyBFVJ5xrWkLnMH6fdk
463MEnMeGyJekNZFQSTUABBEbLnvMTALbT6ZmsxAbAdq
```

(These are relevant if you're parsing fees/rewards or analyzing creator economics.)

## Account structures

### Bonding Curve account
- Min size 82 bytes (post-Mayhem update)
- Fields include: `virtualSolReserves`, `virtualTokenReserves`, `realSolReserves`, `realTokenReserves`, `tokenTotalSupply`, `complete` (bool), `is_mayhem_mode` (bool)

To read: `getAccountInfo` with the bonding curve PDA address, decode via borsh (layout in `pump-public-docs` or infer from IDL).

### Pool account (PumpSwap side, post-migration)
- 244 bytes
- Includes `is_mayhem_mode`
- Standard AMM fields after migration

### Associated Bonding Curve Account
Token account owned by **Token2022 program** (not legacy SPL Token) since `create_v2`. Holds the bonding curve's token balance.

## Instructions

### Main program
- `create` — legacy creation (pre-v2)
- `create_v2` — new creation, uses Token2022 for mint & metadata
- `buy` — swap SOL → tokens on bonding curve
- `sell` — swap tokens → SOL on bonding curve
- (internal) migration when curve completes

### PumpSwap program (post-graduation AMM)
- `create_pool` — initialize AMM pool on migration
- Swap instructions for trading bonded tokens

## create_v2 specifics

- Uses Token2022 program ID, not legacy SPL Token
- Metadata handled via Token2022 Metadata extension (not Metaplex)
- Fee configuration locked after first `updateFeeShares` / `updateSharingConfigWithSocialRecipients` — one-time only

## Useful data points

- **Historical SOL raised at graduation:** ≈ 85 SOL (era-dependent, verify from fresh `pump_evt_complete` events)
- **Graduation probability from creation:** typically ~1-5% of tokens graduate (vast majority die in the bonding curve)
- **Token lifespan distribution:** median is minutes-to-hours for non-graduating; graduated tokens live indefinitely on PumpSwap

Use Dune queries on `pumpdotfun_solana.pump_evt_*` for precise current-era numbers.

## Sources

- https://github.com/pump-fun/pump-public-docs
- https://docs.bitquery.io/docs/blockchain/Solana/Pumpfun/Pump-Fun-Marketcap-Bonding-Curve-API/
