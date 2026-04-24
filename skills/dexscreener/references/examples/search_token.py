"""
Search for tokens by symbol, name, or address.

DexScreener search returns max 30 pairs sorted by relevance + liquidity.
Output shows top N with key metrics.

Usage:
    python search_token.py BONK
    python search_token.py "pump fun" --limit 10
    python search_token.py 0xdac17f958d2ee523a2206206994597c13d831ec7  # USDT contract
"""
import sys, argparse
import httpx

API = "https://api.dexscreener.com"


def search(query: str) -> list[dict]:
    r = httpx.get(f"{API}/latest/dex/search", params={"q": query}, timeout=10)
    r.raise_for_status()
    return r.json().get("pairs") or []


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=15)
    args = p.parse_args()

    results = search(args.query)
    if not results:
        print(f"No results for '{args.query}'")
        sys.exit(1)

    print(f"{'Chain':<12}{'DEX':<12}{'Symbol':<10}{'Price USD':>12}"
          f"{'Liquidity':>14}{'Vol 24h':>14}  Pair")
    for r in results[:args.limit]:
        base = r.get("baseToken", {})
        liq_usd = r.get("liquidity", {}).get("usd", 0) or 0
        vol_usd = r.get("volume", {}).get("h24", 0) or 0
        price_usd = r.get("priceUsd", "?")
        print(f"{r.get('chainId', '?'):<12}"
              f"{r.get('dexId', '?'):<12}"
              f"{base.get('symbol', '?')[:9]:<10}"
              f"${str(price_usd)[:10]:>11}"
              f"${liq_usd:>12,.0f}"
              f"${vol_usd:>12,.0f}  "
              f"{r.get('pairAddress', '?')[:16]}…")


if __name__ == "__main__":
    main()
