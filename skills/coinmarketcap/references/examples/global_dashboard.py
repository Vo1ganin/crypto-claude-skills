"""
Print a dashboard: global metrics + Fear & Greed + trending.

Shows total market cap, BTC dominance, 24h volume, current F&G index,
trending tokens — in one go. ~3 credits total.

Usage:
    CMC_API_KEY=... python global_dashboard.py
"""
import os, sys
import httpx

BASE = "https://pro-api.coinmarketcap.com"
KEY = os.environ["CMC_API_KEY"]
HEADERS = {"X-CMC_PRO_API_KEY": KEY, "Accept": "application/json"}


def cmc_get(path: str, **params) -> dict:
    r = httpx.get(f"{BASE}{path}", params=params, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.json()


def log_credits(label, response):
    print(f"  [{label}] {response['status']['credit_count']} credits", file=sys.stderr)


def main():
    total_spent = 0

    # 1. Global metrics
    r = cmc_get("/v1/global-metrics/quotes/latest")
    log_credits("global", r)
    total_spent += r["status"]["credit_count"]
    g = r["data"]["quote"]["USD"]

    print("=" * 60)
    print("  GLOBAL MARKET")
    print("=" * 60)
    print(f"  Total market cap:  ${g['total_market_cap']:>20,.0f}")
    print(f"  24h volume:        ${g['total_volume_24h']:>20,.0f}")
    print(f"  BTC dominance:     {r['data']['btc_dominance']:>20.2f}%")
    print(f"  ETH dominance:     {r['data']['eth_dominance']:>20.2f}%")
    print(f"  Active cryptos:    {r['data']['active_cryptocurrencies']:>20,}")
    print(f"  Active exchanges:  {r['data']['active_exchanges']:>20,}")

    # 2. Fear & Greed
    try:
        r = cmc_get("/v3/fear-and-greed/latest")
        log_credits("fear-and-greed", r)
        total_spent += r["status"]["credit_count"]
        fg = r["data"]
        classification = fg.get("value_classification", "?")
        value = fg.get("value", "?")
        print()
        print("=" * 60)
        print(f"  FEAR & GREED:  {value}  ({classification})")
        print("=" * 60)
    except Exception as e:
        print(f"  [fear-and-greed unavailable: {e}]", file=sys.stderr)

    # 3. Trending (requires Startup+ plan)
    try:
        r = cmc_get("/v1/cryptocurrency/trending/latest", limit=10)
        log_credits("trending", r)
        total_spent += r["status"]["credit_count"]
        print()
        print("=" * 60)
        print("  TRENDING TOP 10")
        print("=" * 60)
        print(f"  {'Rank':<5}{'Sym':<10}{'Price USD':>14}{'24h %':>9}")
        for item in r["data"]:
            sym = item.get("symbol", "?")
            rank = item.get("cmc_rank", "?")
            usd = (item.get("quote") or {}).get("USD") or {}
            price = usd.get("price") or 0
            pct24 = usd.get("percent_change_24h") or 0
            print(f"  {str(rank):<5}{sym:<10}{price:>14,.4f}{pct24:>8.2f}%")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            print("\n  [trending: requires Startup+ plan]", file=sys.stderr)
        else:
            raise

    print()
    print(f"Total credits spent: {total_spent}")


if __name__ == "__main__":
    main()
