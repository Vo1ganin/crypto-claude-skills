"""
Bundle analyzer — given a tx signature, find bundle siblings in the same slot,
detect sandwich patterns, and show tip amounts.

Works without Jito auth — uses your own Solana RPC to pull block data and
identify Jito tip transfers.

Usage:
    SOLANA_RPC_URL=... python bundle_analyzer.py <signature>
"""
import os, sys, json, argparse
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


def rpc(method: str, params: list):
    r = httpx.post(RPC_URL, json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params},
                   timeout=30)
    r.raise_for_status()
    data = r.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result")


def has_jito_tip(tx: dict) -> tuple[bool, str | None, int]:
    """Returns (is_tipped, tip_dest, tip_lamports)."""
    msg = tx.get("transaction", {}).get("message", {})
    for ix in msg.get("instructions", []):
        parsed = ix.get("parsed")
        if not isinstance(parsed, dict):
            continue
        if parsed.get("type") == "transfer":
            info = parsed.get("info", {})
            dest = info.get("destination")
            if dest in JITO_TIPS:
                return True, dest, int(info.get("lamports", 0))
    return False, None, 0


def get_signers(tx: dict) -> list[str]:
    msg = tx.get("transaction", {}).get("message", {})
    keys = msg.get("accountKeys", [])
    # jsonParsed returns list of {pubkey, signer, writable, source}
    return [k.get("pubkey") for k in keys if isinstance(k, dict) and k.get("signer")]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("signature")
    args = p.parse_args()

    print(f"Looking up {args.signature[:16]}…")
    tx = rpc("getTransaction", [args.signature, {
        "encoding": "jsonParsed",
        "maxSupportedTransactionVersion": 0,
    }])
    if not tx:
        print("tx not found — may be too old or invalid")
        sys.exit(1)

    slot = tx["slot"]
    print(f"Slot: {slot}")
    is_tipped, tip_dest, tip = has_jito_tip(tx)
    print(f"Jito-tipped: {is_tipped}  tip={tip:,} lamports  dest={tip_dest}")
    my_signers = get_signers(tx)
    print(f"Signers: {', '.join(s[:8] + '…' for s in my_signers)}")

    # Pull full block
    print(f"\nFetching block {slot}…")
    block = rpc("getBlock", [slot, {
        "encoding": "jsonParsed",
        "maxSupportedTransactionVersion": 0,
        "transactionDetails": "full",
        "rewards": False,
    }])

    txs = block.get("transactions", [])
    print(f"Block has {len(txs)} txs")

    # Find all jito-tipped txs in this slot (likely multiple bundles co-located)
    tipped = [(btx, has_jito_tip(btx)) for btx in txs]
    tipped = [(b, t) for b, t in tipped if t[0]]
    print(f"Jito-tipped txs in slot: {len(tipped)}")

    # Find our tx's position
    for i, (btx, (_, dest, amt)) in enumerate(tipped):
        sigs = [s for s in btx.get("transaction", {}).get("signatures", [])]
        if args.signature in sigs:
            print(f"\n→ Your tx is position {i+1}/{len(tipped)} among Jito-tipped txs in slot")
            break

    # Simple sandwich heuristic: if among tipped txs in this slot, two with
    # same signer bracket ours — suspicious
    my_set = set(my_signers)
    for i, (btx_before, _) in enumerate(tipped):
        signers_before = set(get_signers(btx_before))
        if my_set & signers_before:
            continue
        sigs_before = btx_before.get("transaction", {}).get("signatures", [])
        if args.signature in sigs_before:
            continue
        for btx_after, _ in tipped[i+1:]:
            signers_after = set(get_signers(btx_after))
            sigs_after = btx_after.get("transaction", {}).get("signatures", [])
            if args.signature in sigs_after:
                continue
            if signers_before & signers_after and not (signers_before & my_set):
                # Both before and after tx by same non-us wallet → potential sandwich
                print(f"\n⚠ POTENTIAL SANDWICH suspect:")
                print(f"  pre-tx signer:  {list(signers_before)[0][:8]}…  sig {sigs_before[0][:16]}…")
                print(f"  your tx:        sig {args.signature[:16]}…")
                print(f"  post-tx signer: {list(signers_after)[0][:8]}…  sig {sigs_after[0][:16]}…")

    print(f"\nCheck: https://explorer.jito.wtf/")


if __name__ == "__main__":
    main()
