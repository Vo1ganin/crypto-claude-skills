"""
Fetch current prices for N tokens from CoinMarketCap in batched calls.

Resolves symbols → CMC IDs once via /v1/cryptocurrency/map (1 credit),
then batches 100 IDs per /v2/cryptocurrency/quotes/latest call (1 credit each).

Usage:
    CMC_API_KEY=... python fetch_prices_batch.py BTC ETH SOL USDC BONK
    CMC_API_KEY=... python fetch_prices_batch.py --ids 1 1027 5426 3408 23095
    CMC_API_KEY=... python fetch_prices_batch.py --file symbols.txt --out prices.csv
"""
import os, sys, csv, argparse
import httpx

BASE = "https://pro-api.coinmarketcap.com"
KEY = os.environ["CMC_API_KEY"]
HEADERS = {"X-CMC_PRO_API_KEY": KEY, "Accept": "application/json"}


def cmc_get(path: str, **params) -> dict:
    r = httpx.get(f"{BASE}{path}", params=params, headers=HEADERS, timeout=30)
    r.raise_for_status()
    body = r.json()
    if body["status"]["error_code"] != 0:
        raise RuntimeError(f"{path}: {body['status']['error_message']}")
    return body


def resolve_symbols(symbols: list[str]) -> dict[str, int]:
    """symbol → CMC id (1 credit for all symbols in one call)."""
    r = cmc_get("/v1/cryptocurrency/map", symbol=",".join(symbols))
    print(f"[resolve] {r['status']['credit_count']} credits", file=sys.stderr)
    return {e["symbol"].upper(): e["id"] for e in r["data"]}


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def fetch_quotes(ids: list[int]) -> dict[str, dict]:
    """Up to 100 ids per call = 1 credit."""
    result = {}
    for chunk in chunks(ids, 100):
        r = cmc_get("/v2/cryptocurrency/quotes/latest", id=",".join(map(str, chunk)))
        print(f"[quotes chunk {len(chunk)}] {r['status']['credit_count']} credits", file=sys.stderr)
        for id_str, item in r["data"].items():
            if isinstance(item, list):
                item = item[0]   # sometimes wrapped in array
            result[id_str] = item
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("symbols", nargs="*", help="symbols like BTC ETH")
    p.add_argument("--ids", nargs="+", type=int, help="direct CMC IDs")
    p.add_argument("--file", help="file with one symbol per line")
    p.add_argument("--out", help="write CSV here (default: stdout table)")
    args = p.parse_args()

    symbols = list(args.symbols)
    if args.file:
        symbols += [s.strip() for s in open(args.file) if s.strip()]

    if args.ids:
        ids = args.ids
        sym_for_id = {i: str(i) for i in ids}  # no symbol info available
    else:
        if not symbols:
            p.error("Provide symbols, --ids, or --file")
        sym_to_id = resolve_symbols([s.upper() for s in symbols])
        missing = [s for s in symbols if s.upper() not in sym_to_id]
        if missing:
            print(f"⚠ not found: {missing}", file=sys.stderr)
        ids = list(sym_to_id.values())
        sym_for_id = {v: k for k, v in sym_to_id.items()}

    quotes = fetch_quotes(ids)

    rows = []
    for id_str, q in quotes.items():
        sym = sym_for_id.get(int(id_str), q.get("symbol", "?"))
        usd = q["quote"]["USD"]
        rows.append({
            "id": id_str,
            "symbol": sym,
            "name": q.get("name"),
            "price_usd": usd.get("price"),
            "volume_24h_usd": usd.get("volume_24h"),
            "market_cap_usd": usd.get("market_cap"),
            "pct_change_24h": usd.get("percent_change_24h"),
            "pct_change_7d": usd.get("percent_change_7d"),
            "updated": usd.get("last_updated"),
        })

    if args.out:
        with open(args.out, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys())
            w.writeheader()
            w.writerows(rows)
        print(f"→ {args.out} ({len(rows)} rows)")
    else:
        print(f"\n{'Sym':<8}{'Price USD':>14}{'Vol 24h USD':>18}{'MCap USD':>20}{'24h %':>9}")
        for r in sorted(rows, key=lambda x: x["market_cap_usd"] or 0, reverse=True):
            print(f"{r['symbol']:<8}"
                  f"{(r['price_usd'] or 0):>14,.4f}"
                  f"{(r['volume_24h_usd'] or 0):>18,.0f}"
                  f"{(r['market_cap_usd'] or 0):>20,.0f}"
                  f"{(r['pct_change_24h'] or 0):>8.2f}%")


if __name__ == "__main__":
    main()
