"""
Analyze how a KOL wallet tips Jito — mean, median, p95 per tx; tipped ratio.

Useful for understanding a competitor bot's or KOL's landing-priority budget.

Usage:
    SOLANA_RPC_URL=... python kol_tip_analysis.py <wallet> [--limit 500]
"""
import os, sys, argparse, statistics
import httpx

RPC_URL = os.environ["SOLANA_RPC_URL"]

JITO_TIPS = {
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
    "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
}

BATCH_SIZE = 50  # getTransaction via JSON-RPC batch array


def rpc_single(method, params):
    r = httpx.post(RPC_URL, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                   timeout=30)
    r.raise_for_status()
    return r.json()["result"]


def rpc_batch(method: str, params_list: list[list]) -> list:
    body = [
        {"jsonrpc": "2.0", "id": i, "method": method, "params": p}
        for i, p in enumerate(params_list)
    ]
    r = httpx.post(RPC_URL, json=body, timeout=60)
    r.raise_for_status()
    rows = r.json()
    ordered = [None] * len(params_list)
    for row in rows:
        ordered[row["id"]] = row.get("result")
    return ordered


def get_sigs(wallet: str, limit: int) -> list[str]:
    all_sigs = []
    before = None
    while len(all_sigs) < limit:
        batch = rpc_single("getSignaturesForAddress", [
            wallet, {"limit": min(1000, limit - len(all_sigs)), "before": before}
        ]) or []
        if not batch:
            break
        all_sigs.extend(x["signature"] for x in batch)
        before = batch[-1]["signature"]
        if len(batch) < 1000:
            break
    return all_sigs[:limit]


def extract_tip(tx: dict) -> int:
    if not tx:
        return 0
    msg = tx.get("transaction", {}).get("message", {})
    for ix in msg.get("instructions", []):
        parsed = ix.get("parsed")
        if not isinstance(parsed, dict):
            continue
        if parsed.get("type") == "transfer":
            info = parsed.get("info", {})
            if info.get("destination") in JITO_TIPS:
                return int(info.get("lamports", 0))
    return 0


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("wallet")
    p.add_argument("--limit", type=int, default=500)
    args = p.parse_args()

    print(f"Fetching signatures for {args.wallet[:8]}… (target {args.limit})")
    sigs = get_sigs(args.wallet, args.limit)
    print(f"Got {len(sigs)} signatures, fetching tx details in batches of {BATCH_SIZE}…")

    tips = []
    for i in range(0, len(sigs), BATCH_SIZE):
        chunk = sigs[i:i + BATCH_SIZE]
        params = [[sig, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}] for sig in chunk]
        txs = rpc_batch("getTransaction", params)
        for tx in txs:
            tip = extract_tip(tx)
            tips.append(tip)
        print(f"  …processed {i + len(chunk)}/{len(sigs)}")

    tipped = [t for t in tips if t > 0]
    print(f"\n═══ Summary for {args.wallet} ═══")
    print(f"Total tx analyzed: {len(tips)}")
    print(f"Tipped (Jito):     {len(tipped)}  ({100*len(tipped)/max(len(tips),1):.1f}%)")
    if tipped:
        tipped.sort()
        def pct(p): return tipped[int(len(tipped) * p / 100)]
        print(f"Tip amount (lamports):")
        print(f"  min    = {min(tipped):>12,}")
        print(f"  median = {statistics.median(tipped):>12,.0f}")
        print(f"  mean   = {statistics.mean(tipped):>12,.0f}")
        print(f"  p75    = {pct(75):>12,}")
        print(f"  p95    = {pct(95):>12,}")
        print(f"  max    = {max(tipped):>12,}")
        print(f"\nTip amount (SOL):")
        print(f"  median = {statistics.median(tipped) / 1e9:.9f}")
        print(f"  mean   = {statistics.mean(tipped) / 1e9:.9f}")
        print(f"  p95    = {pct(95) / 1e9:.9f}")


if __name__ == "__main__":
    main()
