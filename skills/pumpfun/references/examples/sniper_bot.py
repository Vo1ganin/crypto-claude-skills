"""
Pump.fun sniper bot — buy new tokens automatically via PumpPortal Local API + own RPC.

Flow:
  1. Subscribe to WS subscribeNewToken
  2. On event: request unsigned buy tx from PumpPortal Local API
  3. Sign with your wallet
  4. Submit via your own RPC (ideally Helius Sender or direct Jito for best landing)
  5. Log result, move on

Filters (customize for your strategy):
  - Min initial market cap
  - Max initial market cap
  - Creator blacklist/whitelist
  - Name/symbol regex filters

Environment:
    SOLANA_RPC_URL       — your RPC (Helius/QuickNode)
    SOLANA_PRIVATE_KEY   — base58 private key of your hot wallet

Usage:
    SOLANA_RPC_URL=... SOLANA_PRIVATE_KEY=... python sniper_bot.py \\
        --amount-sol 0.02 --slippage 30 --priority-fee 0.001

⚠️ REAL MONEY — test on devnet first. Start with tiny amounts.
"""
import asyncio, json, os, sys, base64, argparse, time
import websockets, httpx
from solders.keypair import Keypair
from solders.transaction import VersionedTransaction
from solana.rpc.api import Client

WS_URL = "wss://pumpportal.fun/api/data"
TRADE_LOCAL = "https://pumpportal.fun/api/trade-local"

RPC_URL = os.environ["SOLANA_RPC_URL"]
PRIVATE_KEY = os.environ["SOLANA_PRIVATE_KEY"]

KP = Keypair.from_base58_string(PRIVATE_KEY)
RPC = Client(RPC_URL)
HTTP = httpx.Client(timeout=10)

# De-duplication: remember mints we've already acted on
SEEN: set[str] = set()


def should_snipe(event: dict, args) -> tuple[bool, str]:
    """Return (should_buy, reason). Customize your strategy here."""
    mcap = event.get("marketCapSol", 0)
    creator = event.get("traderPublicKey", "")
    name = event.get("name", "") or ""

    if args.min_mcap and mcap < args.min_mcap:
        return False, f"mcap {mcap} < min {args.min_mcap}"
    if args.max_mcap and mcap > args.max_mcap:
        return False, f"mcap {mcap} > max {args.max_mcap}"
    if args.blacklist and creator in args.blacklist:
        return False, "creator in blacklist"
    if args.whitelist and creator not in args.whitelist:
        return False, "creator not in whitelist"
    # Add your own filters here:
    #   - check name regex
    #   - check if creator graduated previous tokens (via Dune)
    #   - check social links in metadata
    return True, "pass"


def build_and_submit(mint: str, args) -> tuple[bool, str]:
    try:
        # Request unsigned tx from PumpPortal Local
        r = HTTP.post(TRADE_LOCAL, json={
            "publicKey": str(KP.pubkey()),
            "action": "buy",
            "mint": mint,
            "amount": args.amount_sol,
            "denominatedInSol": "true",
            "slippage": args.slippage,
            "priorityFee": args.priority_fee,
            "pool": "pump",  # fresh coins are always on bonding curve
        })
        r.raise_for_status()
        raw = r.content
        tx_bytes = raw if raw[:1] != b"{" else base64.b64decode(json.loads(raw)["transaction"])
        tx = VersionedTransaction.from_bytes(tx_bytes)
        signed = VersionedTransaction(tx.message, [KP])

        # Submit via own RPC
        sig_resp = RPC.send_raw_transaction(
            bytes(signed),
            opts={"skip_preflight": True, "preflight_commitment": "processed"},
        )
        return True, str(sig_resp.value)
    except Exception as e:
        return False, str(e)


async def run(args):
    print(f"Sniper started. Wallet: {KP.pubkey()}")
    print(f"Strategy: {args.amount_sol} SOL buys, slippage {args.slippage}%, priority {args.priority_fee}")
    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=20) as ws:
                await ws.send(json.dumps({"method": "subscribeNewToken"}))
                print("→ subscribed to new tokens, watching…")
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue
                    if msg.get("txType") != "create":
                        continue
                    mint = msg.get("mint")
                    if not mint or mint in SEEN:
                        continue
                    SEEN.add(mint)

                    ok, reason = should_snipe(msg, args)
                    name = (msg.get("name") or "")[:20]
                    if not ok:
                        print(f"× skip {mint[:8]} ({name}): {reason}")
                        continue

                    # Fire
                    t0 = time.time()
                    success, result = build_and_submit(mint, args)
                    dt_ms = int((time.time() - t0) * 1000)
                    status = "✓" if success else "×"
                    print(f"{status} {mint[:8]} ({name}) {dt_ms}ms → {result[:60]}")
        except Exception as e:
            print(f"× WS/loop error: {e}; reconnecting in 3s", file=sys.stderr)
            await asyncio.sleep(3)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--amount-sol", type=float, required=True, help="SOL per snipe")
    p.add_argument("--slippage", type=int, default=30, help="slippage %% (default 30 for snipes)")
    p.add_argument("--priority-fee", type=float, default=0.001, help="priority fee SOL")
    p.add_argument("--min-mcap", type=float, help="min initial market cap SOL")
    p.add_argument("--max-mcap", type=float, help="max initial market cap SOL")
    p.add_argument("--blacklist", action="append", default=[], help="creator address to skip")
    p.add_argument("--whitelist", action="append", default=[], help="only these creators")
    asyncio.run(run(p.parse_args()))


if __name__ == "__main__":
    main()
