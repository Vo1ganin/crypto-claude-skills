"""
Poll DexScreener trending categories + boosted tokens periodically.

Useful for discovering pump candidates early: intersect organic trending
(metas/trending) with paid-boosted tokens — divergence can signal pump/rug patterns.

Usage:
    python trending_monitor.py                    # one-shot snapshot
    python trending_monitor.py --interval 300     # every 5 min to stdout
    python trending_monitor.py --interval 300 --out trends.jsonl  # append JSONL
"""
import argparse, time, json, sys
import httpx

API = "https://api.dexscreener.com"


def fetch_trending() -> list:
    r = httpx.get(f"{API}/metas/trending/v1", timeout=10)
    r.raise_for_status()
    return r.json() or []


def fetch_boosts_top() -> list:
    r = httpx.get(f"{API}/token-boosts/top/v1", timeout=10)
    r.raise_for_status()
    return r.json() or []


def snapshot():
    trending = fetch_trending()
    boosts = fetch_boosts_top()
    return {
        "ts": int(time.time()),
        "trending": trending[:20],
        "boosted_top": boosts[:20],
    }


def format_trending(snap: dict):
    print(f"=== Snapshot {time.ctime(snap['ts'])} ===")
    print("\nTrending categories:")
    for m in snap["trending"][:10]:
        name = m.get("name") or m.get("slug", "?")
        vol = m.get("volume", {}).get("h24", 0) or 0
        count = m.get("pairCount") or len(m.get("pairs", []) or [])
        print(f"  {name:<30}  pairs={count:<5}  vol24h=${vol:,.0f}")

    print("\nTop boosted tokens:")
    for b in snap["boosted_top"][:10]:
        chain = b.get("chainId", "?")
        addr = (b.get("tokenAddress") or "?")[:10]
        desc = (b.get("description") or "")[:40]
        print(f"  [{chain}] {addr}…  {desc}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--interval", type=int, default=0, help="poll every N seconds (0 = once)")
    p.add_argument("--out", help="append JSONL to this file")
    args = p.parse_args()

    while True:
        try:
            snap = snapshot()
            format_trending(snap)
            if args.out:
                with open(args.out, "a") as f:
                    f.write(json.dumps(snap) + "\n")
            if args.interval <= 0:
                break
            print(f"\n…sleeping {args.interval}s\n", file=sys.stderr)
            time.sleep(args.interval)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"× error: {e}", file=sys.stderr)
            if args.interval <= 0:
                break
            time.sleep(30)


if __name__ == "__main__":
    main()
