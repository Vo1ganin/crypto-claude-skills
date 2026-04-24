"""
Batch-fetch current prices for N token addresses on a chain via DexScreener.

Uses /tokens/v1/{chain}/{addresses} which accepts up to ~30 addresses per call.
Single request per 30 tokens = maximum throughput, minimum rate limit spend.

Usage:
    python batch_prices.py solana tokens.txt out.csv

tokens.txt: one mint/contract address per line.
"""
import sys, csv, argparse, time
import httpx

API = "https://api.dexscreener.com"
CHUNK = 30  # max addresses per call


def chunks(seq, n):
    for i in range(0, len(seq), n):
        yield seq[i:i + n]


def fetch_batch(chain: str, addresses: list[str]) -> list[dict]:
    csv_addrs = ",".join(addresses)
    r = httpx.get(f"{API}/tokens/v1/{chain}/{csv_addrs}", timeout=20)
    r.raise_for_status()
    data = r.json()
    # Response can be array of pairs or object with .pairs — handle both
    return data if isinstance(data, list) else (data.get("pairs") or [])


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("chain", help="e.g. solana, ethereum, base")
    p.add_argument("tokens_file")
    p.add_argument("out_csv")
    args = p.parse_args()

    tokens = [t.strip() for t in open(args.tokens_file) if t.strip()]
    print(f"Fetching {len(tokens)} tokens in batches of {CHUNK}…")

    with open(args.out_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["address", "symbol", "price_usd", "liquidity_usd",
                    "volume_24h_usd", "price_change_24h", "pair_address", "dex"])
        for i, batch in enumerate(chunks(tokens, CHUNK), 1):
            pairs = fetch_batch(args.chain, batch)
            # Map by base token address for reverse-lookup
            by_addr = {}
            for pr in pairs:
                base = (pr.get("baseToken") or {}).get("address", "")
                if base and base not in by_addr:
                    by_addr[base.lower()] = pr
            for addr in batch:
                pr = by_addr.get(addr.lower())
                if not pr:
                    w.writerow([addr, "", "", "", "", "", "", ""])
                    continue
                w.writerow([
                    addr,
                    pr.get("baseToken", {}).get("symbol", ""),
                    pr.get("priceUsd", ""),
                    (pr.get("liquidity") or {}).get("usd", ""),
                    (pr.get("volume") or {}).get("h24", ""),
                    (pr.get("priceChange") or {}).get("h24", ""),
                    pr.get("pairAddress", ""),
                    pr.get("dexId", ""),
                ])
            print(f"  batch {i}: {len(pairs)} pairs")
            time.sleep(0.25)  # stay under 300 rpm comfortably

    print(f"Done → {args.out_csv}")


if __name__ == "__main__":
    main()
