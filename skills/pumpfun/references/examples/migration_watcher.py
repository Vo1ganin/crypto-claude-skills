"""
Pump.fun migration watcher — detect tokens graduating to PumpSwap (or Raydium).

Migration event fires when bonding curve completes (100%). Useful for:
  - Triggering "post-graduation" trading strategies (liquidity is fresh)
  - Analytics: daily graduation rate, which creators graduate
  - Alerts

Usage:
    python migration_watcher.py                        # stream to stdout
    python migration_watcher.py --out migrations.jsonl # append to file
"""
import asyncio, json, sys, argparse, time
import websockets

WS_URL = "wss://pumpportal.fun/api/data"


async def run(out_path: str | None):
    out = open(out_path, "a") if out_path else None
    count = 0
    start = time.time()
    try:
        while True:
            try:
                async with websockets.connect(WS_URL, ping_interval=20) as ws:
                    await ws.send(json.dumps({"method": "subscribeMigration"}))
                    print("→ subscribed to migrations", file=sys.stderr)
                    async for raw in ws:
                        try:
                            msg = json.loads(raw)
                        except Exception:
                            continue
                        if msg.get("txType") != "migration":
                            continue
                        count += 1
                        mint = msg.get("mint", "?")
                        pool = msg.get("pool", "?")
                        sig = msg.get("signature", "?")[:16]
                        elapsed = int(time.time() - start)
                        rate_per_h = count / max(elapsed / 3600, 0.001)
                        print(f"[{count}] {mint} → {pool}  sig={sig}  "
                              f"(rate: {rate_per_h:.1f}/hr)")
                        if out:
                            out.write(json.dumps(msg) + "\n")
                            out.flush()
            except Exception as e:
                print(f"× WS error: {e}; reconnecting in 3s", file=sys.stderr)
                await asyncio.sleep(3)
    finally:
        if out:
            out.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", help="append events as JSONL to this file")
    asyncio.run(run(p.parse_args().out))


if __name__ == "__main__":
    main()
