"""
Send a single tx through Jito with MEV protection.

Template: takes a pre-built signed tx (base64), picks a random tip account,
routes to region-closest block engine. For bundle version see send_bundle.py.

Usage:
    python send_tx_jito.py <base64_signed_tx> [--region frankfurt] [--urgency hot]

Tips:
    - Build the tx yourself with proper priority_fee + tip_transfer instruction
    - Sign locally, serialize to base64, pass to this script
    - Region closest to your current server reduces latency
"""
import argparse, random, sys, time
import httpx

TIP_ACCOUNTS = [
    "96gYZGLnJYVFmbjzopPSU6QiEV5fGqZNyN9nmNhvrZU5",
    "HFqU5x63VTqvQss8hp11i4wVV8bD44PvwucfZ2bU7gRe",
    "Cw8CFyM9FkoMi7K7Crf6HNQqf4uEMzpKw6QNghXLvLkY",
    "ADaUMid9yfUytqMBgopwjb2DTLSokTSzL1zt6iGPaS49",
    "DfXygSm4jCyNCybVYYK6DwvWqjKee8pbDmJGcLWNDXjh",
    "ADuUkR4vqLUMWXxW9gh6D6L8pMSawimctcNZ5pGwDcEt",
    "DttWaMuVvTiduZRnguLF7jNxTgiMBZ1hyAumKUiL2KRL",
    "3AVi9Tg9Uo68tJfuvoKvqKNWKkC5wPdSSdeBnizKZ6jT",
]

REGIONS = {
    "global": "https://mainnet.block-engine.jito.wtf",
    "amsterdam": "https://amsterdam.mainnet.block-engine.jito.wtf",
    "dublin": "https://dublin.mainnet.block-engine.jito.wtf",
    "frankfurt": "https://frankfurt.mainnet.block-engine.jito.wtf",
    "london": "https://london.mainnet.block-engine.jito.wtf",
    "ny": "https://ny.mainnet.block-engine.jito.wtf",
    "slc": "https://slc.mainnet.block-engine.jito.wtf",
    "singapore": "https://singapore.mainnet.block-engine.jito.wtf",
    "tokyo": "https://tokyo.mainnet.block-engine.jito.wtf",
}


def pick_tip_account() -> str:
    return random.choice(TIP_ACCOUNTS)


def send_jito_tx(base64_tx: str, region: str = "global") -> dict:
    url = f"{REGIONS[region]}/api/v1/transactions"
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "sendTransaction",
        "params": [base64_tx, {"encoding": "base64"}],
    }
    r = httpx.post(url, json=body, timeout=10)
    r.raise_for_status()
    data = r.json()
    bundle_id = r.headers.get("x-bundle-id")
    return {
        "signature": data.get("result"),
        "bundle_id": bundle_id,
        "error": data.get("error"),
    }


def check_inflight(bundle_id: str, region: str = "global") -> dict:
    url = f"{REGIONS[region]}/api/v1/getInflightBundleStatuses"
    body = {
        "jsonrpc": "2.0", "id": 1,
        "method": "getInflightBundleStatuses",
        "params": [[bundle_id]],
    }
    r = httpx.post(url, json=body, timeout=10)
    r.raise_for_status()
    values = r.json().get("result", {}).get("value") or []
    return values[0] if values else {}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("base64_tx", help="pre-built signed tx, base64-encoded")
    p.add_argument("--region", default="global", choices=list(REGIONS))
    p.add_argument("--poll", action="store_true", help="poll inflight status until Landed/Failed")
    args = p.parse_args()

    print(f"→ Tip account (random): {pick_tip_account()}", file=sys.stderr)
    print(f"→ Submitting via {args.region}…", file=sys.stderr)
    result = send_jito_tx(args.base64_tx, region=args.region)
    print(result)

    if args.poll and result.get("bundle_id"):
        print(f"→ polling bundle {result['bundle_id']}…", file=sys.stderr)
        for i in range(60):
            status = check_inflight(result["bundle_id"], region=args.region)
            print(f"  [{i+1}] status: {status}")
            if status.get("status") in ("Landed", "Failed", "Invalid"):
                break
            time.sleep(1)


if __name__ == "__main__":
    main()
