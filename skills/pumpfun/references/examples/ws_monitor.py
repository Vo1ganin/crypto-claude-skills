"""
PumpPortal WebSocket monitor — robust client with auto-reconnect.

Single connection, all subscriptions multiplexed. Handles disconnects by
reconnecting and re-sending saved subscriptions.

Usage:
    python ws_monitor.py              # stream everything new
    python ws_monitor.py --wallet WALLET1 --wallet WALLET2   # copytrade watch
    python ws_monitor.py --mint MINT1                        # token watch
    python ws_monitor.py --migration                         # migrations only

No API key needed — Data API is free.
"""
import asyncio, json, argparse, sys
import websockets

WS_URL = "wss://pumpportal.fun/api/data"


def build_subscriptions(args) -> list[dict]:
    subs = []
    if args.new or (not args.wallet and not args.mint and not args.migration):
        subs.append({"method": "subscribeNewToken"})
    if args.wallet:
        subs.append({"method": "subscribeAccountTrade", "keys": args.wallet})
    if args.mint:
        subs.append({"method": "subscribeTokenTrade", "keys": args.mint})
    if args.migration:
        subs.append({"method": "subscribeMigration"})
    return subs


def format_event(msg: dict) -> str:
    tx = msg.get("txType", "?")
    mint = (msg.get("mint") or "?")[:8]
    trader = (msg.get("traderPublicKey") or "?")[:6]
    sol = msg.get("solAmount", "?")
    mcap = msg.get("marketCapSol", "?")
    name = msg.get("name", "")
    if tx == "create":
        return f"[CREATE] {name:<20} [{mint}] by {trader}  mcap={mcap} SOL"
    elif tx in ("buy", "sell"):
        side = tx.upper()
        return f"[{side}]   {mint}  {trader}  {sol} SOL  mcap={mcap}"
    elif tx == "migration":
        return f"[MIGRATE] {mint} → {msg.get('pool', '?')}"
    return f"[{tx}] {json.dumps(msg)[:200]}"


async def run(subscriptions: list[dict]):
    attempt = 0
    while True:
        try:
            async with websockets.connect(WS_URL, ping_interval=20) as ws:
                attempt = 0
                for sub in subscriptions:
                    await ws.send(json.dumps(sub))
                    print(f"→ subscribed: {sub}", file=sys.stderr)
                async for raw in ws:
                    try:
                        msg = json.loads(raw)
                    except Exception:
                        continue
                    if "message" in msg and "method" not in msg:
                        # subscription ack
                        print(f"  ack: {msg}", file=sys.stderr)
                        continue
                    print(format_event(msg))
        except Exception as e:
            attempt += 1
            delay = min(2 ** attempt, 30)
            print(f"× WS error: {e}; reconnecting in {delay}s", file=sys.stderr)
            await asyncio.sleep(delay)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--new", action="store_true", help="subscribe to new tokens")
    p.add_argument("--wallet", action="append", default=[], help="wallet(s) for subscribeAccountTrade")
    p.add_argument("--mint", action="append", default=[], help="mint(s) for subscribeTokenTrade")
    p.add_argument("--migration", action="store_true", help="subscribe to migrations")
    args = p.parse_args()
    subs = build_subscriptions(args)
    if not subs:
        p.error("specify at least one of --new / --wallet / --mint / --migration (or pass none for default --new)")
    asyncio.run(run(subs))


if __name__ == "__main__":
    main()
