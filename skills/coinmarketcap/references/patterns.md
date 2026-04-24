# CoinMarketCap — Patterns & Optimization

## 1. Resolve symbols → IDs once, cache forever

Symbols are unstable (BTC could map to multiple CMC IDs; symbols can change). IDs are permanent.

```python
# Once at app start
r = httpx.get(
    "https://pro-api.coinmarketcap.com/v1/cryptocurrency/map",
    params={"symbol": "BTC,ETH,SOL,USDC,BONK"},
    headers={"X-CMC_PRO_API_KEY": KEY},
)
# Cache {symbol: id} map in a local file or Redis
```

**Cache invalidation:** refresh the map monthly at most. IDs don't change.

## 2. Batch IDs — up to 100 per call for most endpoints

Never:
```python
# DON'T — 100 credits
for sym in ["BTC","ETH","SOL",...,]:
    quote = httpx.get(f"{BASE}/v2/cryptocurrency/quotes/latest?symbol={sym}", ...)
```

Always:
```python
# DO — 1 credit
ids = ",".join(map(str, coin_ids))  # up to 100 IDs
quote = httpx.get(f"{BASE}/v2/cryptocurrency/quotes/latest?id={ids}", ...)
```

`listings/latest` accepts `limit` up to 5000 but each 200 slice = 1 credit — use `limit=200` for top-tier and batch through `start` cursor if you need more.

## 3. Cache aggressively on your side

Typical data freshness:
- Listings / quotes: updated once per minute server-side. Cache 30-60s on client.
- Historical OHLCV: immutable past data. Cache indefinitely.
- Trending: updates slowly. Cache 5-15 min.
- Fear & Greed: daily update. Cache 1h+.
- Global metrics: minute-level updates. Cache 60s.
- Exchange metadata (info, map): monthly refresh.

Every cached hit is a credit saved.

```python
from functools import lru_cache
import time

@lru_cache(maxsize=256)
def get_map_for_symbol(symbol: str) -> int:
    # Once per symbol per process lifetime
    r = httpx.get(f"{BASE}/v1/cryptocurrency/map?symbol={symbol}", headers=HEADERS)
    return r.json()["data"][0]["id"]

_quotes_cache: dict[tuple, tuple[float, dict]] = {}

def get_quotes(ids: tuple[int, ...], ttl: int = 60) -> dict:
    key = tuple(sorted(ids))
    now = time.time()
    if key in _quotes_cache and now - _quotes_cache[key][0] < ttl:
        return _quotes_cache[key][1]
    r = httpx.get(f"{BASE}/v2/cryptocurrency/quotes/latest",
                  params={"id": ",".join(map(str, key))}, headers=HEADERS)
    data = r.json()["data"]
    _quotes_cache[key] = (now, data)
    return data
```

## 4. Avoid `convert=` unless you need it

Every extra currency beyond the first adds 1 credit. If you only use USD, don't pass `convert=USD,EUR,GBP` "just in case".

```python
# Default is already USD — no need to specify for most cases
params = {"id": ids}                           # 1 credit
# params = {"id": ids, "convert": "USD,EUR"}   # 2 credits
```

## 5. Paginate listings with `start` cursor

For > 200 coins:
```python
page = 1
while True:
    r = httpx.get(f"{BASE}/v1/cryptocurrency/listings/latest",
                  params={"start": (page - 1) * 200 + 1, "limit": 200},
                  headers=HEADERS)
    data = r.json()["data"]
    if not data:
        break
    process(data)
    page += 1
# 1 credit per page of 200
```

Avoid `limit=5000` in a single call unless you really need all 5000 points — it's 25 credits vs 1-25 paginated.

## 6. Use `/v1/key/info` as the first call of any session

Costs 0 credits. Tells you:
- Remaining monthly budget (plan ahead)
- Current rate-limit window
- Plan details

```python
def check_budget():
    r = httpx.get(f"{BASE}/v1/key/info", headers=HEADERS)
    data = r.json()["data"]
    used = data["usage"]["current_month"]["credits_used"]
    limit = data["plan"]["credit_limit_monthly"]
    print(f"CMC: {used:,}/{limit:,} credits used ({100*used/limit:.1f}%)")
    return data
```

Stop batch jobs if `credits_left` drops below threshold (e.g., 5% of monthly).

## 7. Use `listings/historical` snapshots, not loops over `quotes/historical`

If you need "top 100 by mcap on a specific past date":
```python
# ONE call: 1 credit per 100 cryptos (since historical is 100 not 200)
r = httpx.get(f"{BASE}/v1/cryptocurrency/listings/historical",
              params={"date": "2024-01-15", "limit": 100},
              headers=HEADERS)
# = 1 credit, done
```

Don't loop `quotes/historical` over 100 coins — that's 100 calls.

## 8. Retry with exponential backoff on 500

```python
import time, httpx

def fetch_with_retry(url, params, max_retries=5):
    for attempt in range(max_retries):
        r = httpx.get(url, params=params, headers=HEADERS, timeout=30)
        if r.status_code in (500, 502, 504):
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429:
            time.sleep(60)  # wait full minute window
            continue
        r.raise_for_status()
        return r.json()
    raise RuntimeError("Max retries exceeded")
```

## 9. Log `status.credit_count` on every call

Production bots should track running credit spend per session:

```python
total_spent = 0

def cmc_get(path, **params):
    global total_spent
    r = httpx.get(f"{BASE}{path}", params=params, headers=HEADERS).json()
    spent = r["status"]["credit_count"]
    total_spent += spent
    print(f"[cmc] {path} → {spent} credits (session total {total_spent})", file=sys.stderr)
    return r["data"]
```

Helps catch unexpected expensive calls early.

## 10. When to use CMC MCP / CLI / x402 instead of Pro API

Alternatives listed in official docs:

| Option | When |
|--------|------|
| Pro API (this skill) | Production apps, custom integrations |
| CMC MCP (`/api/mcp/`) | AI agents with tool-use (Claude, Cursor, Windsurf, ChatGPT, Codex) |
| CMC CLI | Interactive terminal exploration |
| x402 (USDC pay-per-call) | One-off queries, no API key, no subscription |

This skill focuses on the Pro API (REST) path. For MCP integration, see `docs/coinmarketcap/llms-full.txt` sections "CMC MCP", "CMC MCP for Claude Code" etc.
