"""
Pump.fun copytrade watcher — mirror trades from N KOL wallets via PumpPortal WS.

Strategy:
  - Subscribe to subscribeAccountTrade with KOL wallet list
  - On every buy/sell event from KOL → fire same-direction trade with your sizing
  - De-dup by signature (don't double-fire on replays)
  - Optional delay to avoid front-running the KOL himself

Environment:
    SOLANA_RPC_URL
    SOLANA_PRIVATE_KEY

Usage:
    SOLANA_RPC_URL=... SOLANA_PRIVATE_KEY=... python copytrade_watcher.py \\
        --kols kols.txt --amount-sol 0.05 --delay-ms 300 --slippage 25

kols.txt: one wallet address per line.

⚠️ Copytrading is high-risk — KOLs lose money too. Dry-run with --dry-run first.
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

SEEN_SIGS: set[str] = set()


def mirror_trade(event: dict, args) -> tuple[bool, str]:
    if args.dry_run:
        return True, "DRY_RUN"
    try:
        r = HTTP.post(TRADE_LOCAL, json={
            "publicKey": str(KP.pubkey()),
            "action": event["txType"],           # mirror side (buy/sell)
            "mint": event["mint"],
            "amount": args.amount_sol if event["txType"] == "buy" else "100%",
            "denominatedInSol": "true" if event["txType"] == "buy" else "false",
            "slippage": args.slippage,
            "priorityFee": args.priority_fee,
            "pool": "auto",
        })
        r.raise_for_status()
        raw = r.content
        tx_bytes = raw if raw[:1] != b"{" else base64.b64decode(json.loads(raw)["transaction"])
        tx = VersionedTransaction.from_bytes(tx_bytes)
        signed = VersionedTransaction(tx.message, [KP])
        sig_resp = RPC.send_raw_transaction(
            bytes(signed),
            opts={"skip_preflight": True, "preflight_commitment": "processed"},
        )
        return True, str(sig_resp.value)
    except Exception as e:
        return False, str(e)


async def run(args):
    kols = [l.strip() for l in open(args.kols) if l.strip()]
    print(f"Copytrade watching {len(kols)} KOL(s)")
    print(f"Mirror: {args.amount_sol} SOL buys, 100% sells, delay {args.delay_ms}ms")

    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=20) as ws:
                await ws.send(json.dumps({
                    "method": "subscribeAccountTrade",
                    "keys": kols,
                }))
                print("→ subscribed; watching KOL trades")
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue
                    sig = msg.get("signature")
                    tx_type = msg.get("txType")
                    if sig in SEEN_SIGS or tx_type not in ("buy", "sell"):
                        continue
                    SEEN_SIGS.add(sig)

                    kol = msg.get("traderPublicKey", "?")[:6]
                    mint = msg.get("mint", "?")[:8]
                    sol = msg.get("solAmount", "?")
                    print(f"→ KOL {kol} {tx_type.upper()} {sol} SOL on {mint}")

                    if args.delay_ms > 0:
                        await asyncio.sleep(args.delay_ms / 1000)

                    t0 = time.time()
                    ok, result = mirror_trade(msg, args)
                    dt = int((time.time() - t0) * 1000)
                    tag = "✓" if ok else "×"
                    print(f"  {tag} mirror {dt}ms → {result[:60]}")
        except Exception as e:
            print(f"× WS error: {e}; reconnecting in 3s", file=sys.stderr)
            await asyncio.sleep(3)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--kols", required=True, help="file with KOL wallet addresses (one per line)")
    p.add_argument("--amount-sol", type=float, required=True, help="SOL to mirror on each buy")
    p.add_argument("--delay-ms", type=int, default=300, help="delay before firing mirror")
    p.add_argument("--slippage", type=int, default=25)
    p.add_argument("--priority-fee", type=float, default=0.0005)
    p.add_argument("--dry-run", action="store_true", help="just log, don't trade")
    asyncio.run(run(p.parse_args()))


if __name__ == "__main__":
    main()
