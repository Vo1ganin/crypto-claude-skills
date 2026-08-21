"""Describe public Jito-tip transfers observed for a wallet's recent transactions.

This read-only report does not infer ownership, intent, strategy, bundle membership,
or a recommended live fee.

Usage:
    SOLANA_RPC_URL=... python wallet_tip_distribution.py <wallet> [--limit 500]
"""

import argparse
import math
import os
import statistics

import httpx

RPC_URL = os.environ["SOLANA_RPC_URL"]
BATCH_SIZE = 50

JITO_TIP_ACCOUNTS = {
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
    "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
}


def rpc_single(method: str, params: list):
    response = httpx.post(
        RPC_URL,
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(payload["error"])
    return payload.get("result")


def rpc_batch(method: str, params_list: list[list]) -> list:
    body = [
        {"jsonrpc": "2.0", "id": index, "method": method, "params": params}
        for index, params in enumerate(params_list)
    ]
    response = httpx.post(RPC_URL, json=body, timeout=60)
    response.raise_for_status()
    ordered = [None] * len(params_list)
    for row in response.json():
        if not row.get("error"):
            ordered[row["id"]] = row.get("result")
    return ordered


def signatures(wallet: str, limit: int) -> list[str]:
    result: list[str] = []
    before = None
    while len(result) < limit:
        options = {"limit": min(1000, limit - len(result))}
        if before:
            options["before"] = before
        rows = rpc_single("getSignaturesForAddress", [wallet, options]) or []
        if not rows:
            break
        result.extend(row["signature"] for row in rows)
        before = rows[-1]["signature"]
        if len(rows) < options["limit"]:
            break
    return result[:limit]


def observed_tip_lamports(transaction: dict | None) -> int:
    if not transaction:
        return 0
    message = transaction.get("transaction", {}).get("message", {})
    total = 0
    for instruction in message.get("instructions", []):
        parsed = instruction.get("parsed")
        if not isinstance(parsed, dict) or parsed.get("type") != "transfer":
            continue
        info = parsed.get("info", {})
        if info.get("destination") in JITO_TIP_ACCOUNTS:
            total += int(info.get("lamports", 0))
    return total


def percentile(values: list[int], percentile_value: int) -> int:
    if not values:
        return 0
    index = math.ceil((percentile_value / 100) * len(values)) - 1
    return sorted(values)[max(0, min(index, len(values) - 1))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wallet")
    parser.add_argument("--limit", type=int, default=500)
    args = parser.parse_args()
    if args.limit <= 0:
        parser.error("--limit must be positive")

    sigs = signatures(args.wallet, args.limit)
    tips: list[int] = []
    for offset in range(0, len(sigs), BATCH_SIZE):
        chunk = sigs[offset : offset + BATCH_SIZE]
        params = [
            [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}]
            for signature in chunk
        ]
        tips.extend(observed_tip_lamports(tx) for tx in rpc_batch("getTransaction", params))

    tipped = sorted(value for value in tips if value > 0)
    print(f"Wallet: {args.wallet}")
    print(f"Transactions analyzed: {len(tips)}")
    print(f"Transactions with observed public Jito-tip transfers: {len(tipped)}")
    print(f"Observed ratio: {100 * len(tipped) / max(len(tips), 1):.1f}%")
    if tipped:
        print("Observed tip distribution (lamports):")
        print(f"  min={min(tipped):,}")
        print(f"  median={statistics.median(tipped):,.0f}")
        print(f"  mean={statistics.mean(tipped):,.0f}")
        print(f"  p75={percentile(tipped, 75):,}")
        print(f"  p95={percentile(tipped, 95):,}")
        print(f"  max={max(tipped):,}")
    print("Limitations: known-account matching is incomplete and does not prove bundle membership or intent.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
