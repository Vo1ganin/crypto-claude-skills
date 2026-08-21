"""Fetch and print the public Jito tip-floor percentile distribution.

This is a read-only descriptive snapshot. It does not recommend a live fee.

Usage:
    python tip_floor_snapshot.py
    python tip_floor_snapshot.py --poll 60
    python tip_floor_snapshot.py --json
"""

import argparse
import json
import sys
import time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import httpx

TIP_FLOOR = "https://bundles.jito.wtf/api/v1/bundles/tip_floor"
PERCENTILES = (25, 50, 75, 95, 99)


def fetch_tip_floor() -> dict:
    response = httpx.get(TIP_FLOOR, timeout=5)
    response.raise_for_status()
    data = response.json()
    if isinstance(data, list):
        if not data:
            raise ValueError("empty tip-floor response")
        data = data[0]
    if not isinstance(data, dict):
        raise TypeError("unexpected tip-floor response shape")
    return data


def normalized_snapshot(data: dict) -> dict:
    snapshot = {"time": data.get("time")}
    for percentile in PERCENTILES:
        field = f"landed_tips_{percentile}th_percentile"
        try:
            sol_value = Decimal(str(data.get(field, 0)))
        except InvalidOperation as exc:
            raise ValueError(f"invalid SOL value for {field}") from exc
        if sol_value < 0:
            raise ValueError(f"negative SOL value for {field}")
        lamports = int((sol_value * Decimal(1_000_000_000)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
        snapshot[str(percentile)] = {"lamports": lamports, "sol": float(sol_value)}
    return snapshot


def print_snapshot(snapshot: dict) -> None:
    print(f"Public landed-tip distribution at {snapshot.get('time') or '?'}:")
    for percentile in PERCENTILES:
        value = snapshot[str(percentile)]
        print(
            f"  {percentile:>3}th percentile: {value['lamports']:>12,} lamports "
            f"({value['sol']:.9f} SOL)"
        )
    print("\nDescriptive data only; verify freshness and do not treat a percentile as an execution recommendation.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--poll", type=int, default=0, help="refresh every N seconds")
    parser.add_argument("--json", action="store_true", help="emit normalized JSON")
    args = parser.parse_args()

    while True:
        try:
            snapshot = normalized_snapshot(fetch_tip_floor())
            if args.json:
                print(json.dumps(snapshot, sort_keys=True))
            else:
                print_snapshot(snapshot)
        except (httpx.HTTPError, TypeError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        if args.poll <= 0:
            break
        time.sleep(args.poll)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
