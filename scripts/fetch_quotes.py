#!/usr/bin/env python3
"""
Delayed-quote refresher for the Screener 500 data repo.

Runs inside GitHub Actions (see .github/workflows/quotes.yml). Reads the
universe from latest.json, pulls one FMP batch quote per 100 symbols, and
writes quotes.json next to the bundle. The API key comes ONLY from the
FMP_API_KEY environment variable (a repository secret) — never from a file
in this repo and never echoed.

quotes.json shape (schema 1):
{
  "schema_version": 1,
  "as_of_utc": "2026-09-11T14:35:02Z",
  "source": "fmp batch-quote",
  "n": 493,
  "quotes": { "AAPL": {"p": 326.3, "c": -0.26, "cp": -0.08, "v": 69820744, "ts": 1789070401}, ... }
}
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LATEST = ROOT / "latest.json"
OUT = ROOT / "quotes.json"
BASE = "https://financialmodelingprep.com/stable/batch-quote"
CHUNK = 100


def _get(symbols: list[str], key: str) -> list[dict]:
    q = urllib.parse.urlencode({"symbols": ",".join(symbols), "apikey": key})
    req = urllib.request.Request(f"{BASE}?{q}", headers={"accept": "application/json", "user-agent": "screener500-quotes/1"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            if isinstance(data, list):
                return data
            raise RuntimeError(f"unexpected shape: {type(data).__name__}")
        except Exception as e:  # noqa: BLE001
            if attempt == 2:
                raise
            print(f"retry {attempt + 1}: {type(e).__name__}", file=sys.stderr)
            time.sleep(2 + attempt * 3)
    return []


def main() -> int:
    key = os.environ.get("FMP_API_KEY", "").strip()
    if not key:
        print("FMP_API_KEY is not set", file=sys.stderr)
        return 1
    if not LATEST.exists():
        print(f"missing {LATEST}", file=sys.stderr)
        return 1
    latest = json.loads(LATEST.read_text(encoding="utf-8"))
    tickers = sorted({r["ticker"] for r in latest.get("rows", []) if r.get("ticker")})
    if not tickers:
        print("no tickers in latest.json", file=sys.stderr)
        return 1

    quotes: dict[str, dict] = {}
    for i in range(0, len(tickers), CHUNK):
        for row in _get(tickers[i:i + CHUNK], key):
            sym = str(row.get("symbol", "")).upper()
            if not sym or row.get("price") is None:
                continue
            quotes[sym] = {
                "p": row.get("price"),
                "c": row.get("change"),
                "cp": row.get("changePercentage", row.get("changesPercentage")),
                "v": row.get("volume"),
                "ts": row.get("timestamp"),
            }

    if len(quotes) < len(tickers) * 0.5:
        print(f"only {len(quotes)}/{len(tickers)} quotes returned — not overwriting", file=sys.stderr)
        return 1

    out = {
        "schema_version": 1,
        "as_of_utc": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": "fmp batch-quote",
        "n": len(quotes),
        "quotes": quotes,
    }
    OUT.write_text(json.dumps(out, separators=(",", ":")), encoding="utf-8")
    print(f"wrote {OUT.name}: {len(quotes)} quotes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
