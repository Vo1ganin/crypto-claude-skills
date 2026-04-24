"""
Jito tip advisor — pull live tip-floor percentiles and recommend a tip.

Policy: set tip at specified percentile of recently-landed bundles.
Polls the public endpoint (no auth needed); caches briefly.

Usage:
    python tip_advisor.py                    # snapshot, recommend 75th
    python tip_advisor.py --percentile 95    # for competitive sniping
    python tip_advisor.py --poll 30          # refresh every 30s
    python tip_advisor.py --urgency critical # alias for 99th percentile
"""
import argparse, time, sys
import httpx

TIP_FLOOR = "https://bundles.jito.wtf/api/v1/bundles/tip_floor"

URGENCY = {
    "casual": 25,
    "normal": 50,
    "competitive": 75,
    "hot": 95,
    "critical": 99,
}


def fetch_tip_floor() -> dict:
    r = httpx.get(TIP_FLOOR, timeout=5)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list):
        data = data[0]
    return data


def recommend(percentile: int) -> tuple[int, dict]:
    data = fetch_tip_floor()
    field = f"landed_tips_{percentile}th_percentile"
    tip_lamports = int(data.get(field, 0))
    return tip_lamports, data


def format_snapshot(data: dict, recommended_pct: int):
    print(f"Tip floor at {data.get('time', '?')}:")
    for pct in (25, 50, 75, 95, 99):
        key = f"landed_tips_{pct}th_percentile"
        val = int(data.get(key, 0))
        marker = " ← recommend" if pct == recommended_pct else ""
        print(f"  {pct:>3}th pctl: {val:>12,} lamports  ({val / 1e9:.9f} SOL){marker}")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--percentile", type=int, default=75, choices=[25, 50, 75, 95, 99])
    p.add_argument("--urgency", choices=list(URGENCY), help="alias for percentile")
    p.add_argument("--poll", type=int, default=0, help="refresh every N seconds")
    args = p.parse_args()

    pct = URGENCY[args.urgency] if args.urgency else args.percentile

    while True:
        try:
            tip, data = recommend(pct)
            format_snapshot(data, pct)
            print(f"\n→ Use tip = {tip:,} lamports ({tip / 1e9:.9f} SOL)")
        except Exception as e:
            print(f"× error: {e}", file=sys.stderr)

        if args.poll <= 0:
            break
        print(f"\n…sleeping {args.poll}s\n", file=sys.stderr)
        time.sleep(args.poll)


if __name__ == "__main__":
    main()
