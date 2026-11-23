#!/usr/bin/env python3
"""Export Google Search Console queries and pages via Loggie."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import urllib.parse
from pathlib import Path

LOGGIE_ACCOUNT = Path.home() / ".local" / "bin" / "loggie-account"


def gsc_query(account: str, site: str, body: dict) -> dict:
    encoded = urllib.parse.quote(site, safe="")
    path = f"/webmasters/v3/sites/{encoded}/searchAnalytics/query"
    cmd = [
        str(LOGGIE_ACCOUNT),
        account,
        "call",
        "google-search-console",
        "POST",
        path,
        "--body",
        json.dumps(body),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Loggie GSC call failed ({proc.returncode}): {proc.stderr.strip() or proc.stdout.strip()}")
    return json.loads(proc.stdout)


def fetch_all_rows(account: str, site: str, start_date: str, end_date: str, dimensions: list[str], max_rows: int) -> list[dict]:
    rows: list[dict] = []
    start_row = 0
    page_size = min(25000, max_rows)
    while len(rows) < max_rows:
        data = gsc_query(
            account,
            site,
            {
                "startDate": start_date,
                "endDate": end_date,
                "dimensions": dimensions,
                "rowLimit": min(page_size, max_rows - len(rows)),
                "startRow": start_row,
            },
        )
        batch = data.get("rows") or []
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start_row += len(batch)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Google Search Console queries and pages via Loggie.")
    parser.add_argument("--account", required=True, choices=["personal", "work", "unblocklabs"], help="Loggie account")
    parser.add_argument("--site", required=True, help="GSC property (e.g. sc-domain:whoistyping.wtf)")
    parser.add_argument("--days", type=int, default=90, help="Lookback window in days (default: 90)")
    parser.add_argument("--max-rows", type=int, default=25000, help="Max rows per export (default: 25000)")
    parser.add_argument("--out", required=True, help="Output directory")
    args = parser.parse_args()

    end = dt.date.today() - dt.timedelta(days=2)  # GSC data lags ~2 days
    start = end - dt.timedelta(days=args.days)
    start_s, end_s = start.isoformat(), end.isoformat()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    qp_rows = fetch_all_rows(args.account, args.site, start_s, end_s, ["query", "page"], args.max_rows)
    page_rows = fetch_all_rows(args.account, args.site, start_s, end_s, ["page"], args.max_rows)

    queries_out = {
        "site": args.site,
        "account": args.account,
        "startDate": start_s,
        "endDate": end_s,
        "rowCount": len(qp_rows),
        "rows": [
            {
                "query": r["keys"][0],
                "page": r["keys"][1],
                "clicks": r.get("clicks", 0),
                "impressions": r.get("impressions", 0),
                "ctr": round(r.get("ctr", 0.0), 4),
                "position": round(r.get("position", 0.0), 2),
            }
            for r in qp_rows
        ],
    }
    pages_out = {
        "site": args.site,
        "account": args.account,
        "startDate": start_s,
        "endDate": end_s,
        "rowCount": len(page_rows),
        "rows": [
            {
                "page": r["keys"][0],
                "clicks": r.get("clicks", 0),
                "impressions": r.get("impressions", 0),
                "ctr": round(r.get("ctr", 0.0), 4),
                "position": round(r.get("position", 0.0), 2),
            }
            for r in page_rows
        ],
    }

    (out_dir / "gsc-queries.json").write_text(json.dumps(queries_out, indent=2) + "\n", encoding="utf-8")
    (out_dir / "gsc-pages.json").write_text(json.dumps(pages_out, indent=2) + "\n", encoding="utf-8")
    print(f"GSC {args.site} ({start_s}..{end_s}): {len(qp_rows)} query-page rows, {len(page_rows)} pages", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
