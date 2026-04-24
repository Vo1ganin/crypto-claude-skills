"""
Fetch historical daily OHLCV for a coin from CoinMarketCap.

One call for up to 100 days = 1 credit. Writes CSV.

Usage:
    CMC_API_KEY=... python historical_ohlcv.py BTC 90 btc_90d.csv
    CMC_API_KEY=... python historical_ohlcv.py ETH 30 eth_30d.csv --interval daily

Intervals: yearly, monthly, weekly, daily, hourly, 30m, 15m, 10m, 5m, 1m.
Tier gating: historical beyond 1 month requires Startup+ (30 days) / Standard+ (90 days).
"""
import os, sys, csv, argparse
import httpx

BASE = "https://pro-api.coinmarketcap.com"
KEY = os.environ["CMC_API_KEY"]
HEADERS = {"X-CMC_PRO_API_KEY": KEY, "Accept": "application/json"}


def cmc_get(path: str, **params) -> dict:
    r = httpx.get(f"{BASE}{path}", params=params, headers=HEADERS, timeout=60)
    r.raise_for_status()
    return r.json()


def resolve_symbol(symbol: str) -> tuple[int, str]:
    r = cmc_get("/v1/cryptocurrency/map", symbol=symbol)
    print(f"[resolve] {r['status']['credit_count']} credits", file=sys.stderr)
    e = r["data"][0]
    return e["id"], e["name"]


def fetch_ohlcv(cmc_id: int, count: int, interval: str) -> list[dict]:
    r = cmc_get("/v2/cryptocurrency/ohlcv/historical",
                id=cmc_id, count=count, interval=interval)
    print(f"[ohlcv] {r['status']['credit_count']} credits "
          f"({count} points, interval={interval})", file=sys.stderr)
    data = r["data"]
    # For single id, data is {id_str: {quotes: [...]}}
    item = next(iter(data.values())) if isinstance(data, dict) and not data.get("quotes") else data
    quotes = item.get("quotes", item if isinstance(item, list) else [])
    return quotes


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("symbol", help="e.g. BTC, ETH, SOL")
    p.add_argument("count", type=int, help="number of periods (max 100 for 1 credit)")
    p.add_argument("out_csv")
    p.add_argument("--interval", default="daily")
    args = p.parse_args()

    if args.count > 100:
        print(f"⚠ count={args.count} > 100 → {(args.count + 99) // 100} credits", file=sys.stderr)

    cmc_id, name = resolve_symbol(args.symbol.upper())
    print(f"[{args.symbol.upper()}] CMC id={cmc_id}, name={name}", file=sys.stderr)

    quotes = fetch_ohlcv(cmc_id, args.count, args.interval)

    with open(args.out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["time_open", "time_close", "open", "high", "low", "close",
                    "volume", "market_cap"])
        for q in quotes:
            usd = q["quote"]["USD"]
            w.writerow([
                q.get("time_open"),
                q.get("time_close"),
                usd.get("open"),
                usd.get("high"),
                usd.get("low"),
                usd.get("close"),
                usd.get("volume"),
                usd.get("market_cap"),
            ])

    print(f"→ {args.out_csv} ({len(quotes)} rows)")


if __name__ == "__main__":
    main()
