#!/usr/bin/env python3
"""Query DataForSEO Labs endpoints for competitor pages, ranked keywords, and search volume.

Expects DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD in the environment
(invoke via: varlock run --path ~/.agents/skills/ -- python3 -I ...).
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

API_BASE = "https://api.dataforseo.com/v3"


def auth_header() -> str:
    login = os.environ.get("DATAFORSEO_LOGIN", "").strip()
    password = os.environ.get("DATAFORSEO_PASSWORD", "").strip()
    token = os.environ.get("DATAFORSEO_AUTH_BASE64", "").strip()
    if token:
        return f"Basic {token}"
    if login and password:
        raw = f"{login}:{password}".encode("utf-8")
        return "Basic " + base64.b64encode(raw).decode("ascii")
    raise SystemExit(
        "Missing DataForSEO credentials: set DATAFORSEO_LOGIN + DATAFORSEO_PASSWORD "
        "(or DATAFORSEO_AUTH_BASE64) via `varlock run --path ~/.agents/skills/ --`."
    )


def api_request(method: str, path: str, payload: list | dict | None = None) -> dict:
    url = f"{API_BASE}{path}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {
        "Authorization": auth_header(),
        "Content-Type": "application/json",
    }
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise SystemExit(f"DataForSEO HTTP {exc.code}: {detail}") from exc

    cost = body.get("cost", 0)
    status_code = body.get("status_code")
    status_msg = body.get("status_message")
    print(f"[DataForSEO {path}] status={status_code} ({status_msg}) cost=${cost:.4f}", file=sys.stderr)
    if status_code != 20000:
        raise SystemExit(f"DataForSEO error: {status_code} {status_msg}")
    return body


def cmd_balance(_args: argparse.Namespace) -> int:
    data = api_request("GET", "/appendix/user_data")
    task = (data.get("tasks") or [{}])[0]
    res = (task.get("result") or [{}])[0]
    money = res.get("money") or {}
    out = {
        "login": res.get("login"),
        "balance": money.get("balance"),
        "total_deposited": money.get("total"),
        "limits_day_total": ((money.get("limits") or {}).get("day") or {}).get("total"),
    }
    print(json.dumps(out, indent=2))
    return 0


def cmd_relevant_pages(args: argparse.Namespace) -> int:
    task_body: dict = {
        "target": args.domain,
        "location_name": args.location,
        "language_code": args.language,
        "limit": args.limit,
        "order_by": ["metrics.organic.etv,desc"],
    }
    if args.min_etv > 0:
        task_body["filters"] = ["metrics.organic.etv", ">=", args.min_etv]

    data = api_request("POST", "/dataforseo_labs/google/relevant_pages/live", [task_body])
    task = (data.get("tasks") or [{}])[0]
    if task.get("status_code") != 20000:
        raise SystemExit(f"Task failed: {task.get('status_code')} {task.get('status_message')}")
    res = (task.get("result") or [{}])[0]
    items = res.get("items") or []

    path_filters = [p.strip() for p in (args.path_contains or "").split(",") if p.strip()]
    pages = []
    for item in items:
        addr = item.get("page_address") or ""
        if path_filters and not any(pf in addr for pf in path_filters):
            continue
        org = (item.get("metrics") or {}).get("organic") or {}
        pages.append(
            {
                "url": addr,
                "etv": round(float(org.get("etv") or 0), 2),
                "keyword_count": int(org.get("count") or 0),
                "pos_1": int(org.get("pos_1") or 0),
                "pos_2_3": int(org.get("pos_2_3") or 0),
                "pos_4_10": int(org.get("pos_4_10") or 0),
                "pos_11_20": int(org.get("pos_11_20") or 0),
            }
        )

    out = {
        "domain": args.domain,
        "location": args.location,
        "language": args.language,
        "cost": data.get("cost", 0),
        "total_count": res.get("total_count", len(pages)),
        "returned": len(pages),
        "pages": pages,
    }
    write_json(args.out, out)
    return 0


def cmd_ranked_keywords(args: argparse.Namespace) -> int:
    filters: list = []
    if args.max_rank:
        filters.append(["ranked_serp_element.serp_item.rank_group", "<=", args.max_rank])
    if args.min_volume:
        if filters:
            filters.append("and")
        filters.append(["keyword_data.keyword_info.search_volume", ">=", args.min_volume])

    task_body: dict = {
        "target": args.domain,
        "location_name": args.location,
        "language_code": args.language,
        "limit": args.limit,
        "order_by": ["ranked_serp_element.serp_item.etv,desc"],
    }
    if filters:
        task_body["filters"] = filters if len(filters) > 1 else filters[0]

    data = api_request("POST", "/dataforseo_labs/google/ranked_keywords/live", [task_body])
    task = (data.get("tasks") or [{}])[0]
    if task.get("status_code") != 20000:
        raise SystemExit(f"Task failed: {task.get('status_code')} {task.get('status_message')}")
    res = (task.get("result") or [{}])[0]
    items = res.get("items") or []

    path_filters = [p.strip() for p in (args.path_contains or "").split(",") if p.strip()]
    keywords = []
    for item in items:
        kd = item.get("keyword_data") or {}
        ki = kd.get("keyword_info") or {}
        kp = kd.get("keyword_properties") or {}
        si = kd.get("search_intent_info") or {}
        serp = (item.get("ranked_serp_element") or {}).get("serp_item") or {}
        rel_url = serp.get("relative_url") or ""
        full_url = serp.get("url") or (f"https://{args.domain}{rel_url}" if rel_url else "")
        if path_filters and not any(pf in full_url for pf in path_filters):
            continue
        keywords.append(
            {
                "keyword": kd.get("keyword") or "",
                "search_volume": int(ki.get("search_volume") or 0),
                "cpc": round(float(ki.get("cpc") or 0), 2),
                "kd": kp.get("keyword_difficulty"),
                "intent": si.get("main_intent"),
                "rank": int(serp.get("rank_group") or serp.get("rank_absolute") or 0),
                "etv": round(float(serp.get("etv") or 0), 2),
                "url": full_url,
                "relative_url": rel_url,
                "domain": args.domain,
            }
        )

    out = {
        "domain": args.domain,
        "location": args.location,
        "language": args.language,
        "cost": data.get("cost", 0),
        "total_count": res.get("total_count", len(keywords)),
        "returned": len(keywords),
        "keywords": keywords,
    }
    write_json(args.out, out)
    return 0


def cmd_search_volume(args: argparse.Namespace) -> int:
    kws = [k.strip() for k in args.keywords if k.strip()]
    if not kws:
        raise SystemExit("Provide at least one keyword.")
    task_body = {
        "keywords": kws[:700],
        "location_name": args.location,
        "language_code": args.language,
    }
    data = api_request("POST", "/dataforseo_labs/google/historical_search_volume/live", [task_body])
    task = (data.get("tasks") or [{}])[0]
    if task.get("status_code") != 20000:
        raise SystemExit(f"Task failed: {task.get('status_code')} {task.get('status_message')}")
    res = (task.get("result") or [{}])[0]
    items = res.get("items") or []

    rows = []
    for item in items:
        ki = item.get("keyword_info") or {}
        si = item.get("search_intent_info") or {}
        rows.append(
            {
                "keyword": item.get("keyword") or "",
                "search_volume": int(ki.get("search_volume") or 0),
                "cpc": round(float(ki.get("cpc") or 0), 2),
                "competition_level": ki.get("competition_level"),
                "intent": si.get("main_intent"),
            }
        )
    out = {
        "location": args.location,
        "language": args.language,
        "cost": data.get("cost", 0),
        "returned": len(rows),
        "keywords": rows,
    }
    write_json(args.out, out)
    return 0


def write_json(out_path: str | None, payload: dict) -> None:
    text = json.dumps(payload, indent=2) + "\n"
    if out_path:
        p = Path(out_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
        print(f"Wrote {p}", file=sys.stderr)
    else:
        print(text)


def main() -> int:
    parser = argparse.ArgumentParser(description="DataForSEO Labs client for competitor SEO gap analysis.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_bal = sub.add_parser("balance", help="Check DataForSEO account balance (free).")
    p_bal.set_defaults(func=cmd_balance)

    p_pages = sub.add_parser("relevant-pages", help="Top organic-traffic pages for a competitor domain.")
    p_pages.add_argument("--domain", required=True)
    p_pages.add_argument("--location", default="United States")
    p_pages.add_argument("--language", default="en")
    p_pages.add_argument("--limit", type=int, default=100)
    p_pages.add_argument("--min-etv", type=float, default=0)
    p_pages.add_argument("--path-contains", help="Optional comma-separated URL substrings to keep")
    p_pages.add_argument("--out", help="Output JSON file path")
    p_pages.set_defaults(func=cmd_relevant_pages)

    p_kw = sub.add_parser("ranked-keywords", help="Keywords a competitor domain ranks for.")
    p_kw.add_argument("--domain", required=True)
    p_kw.add_argument("--location", default="United States")
    p_kw.add_argument("--language", default="en")
    p_kw.add_argument("--limit", type=int, default=300)
    p_kw.add_argument("--max-rank", type=int, default=20)
    p_kw.add_argument("--min-volume", type=int, default=50)
    p_kw.add_argument("--path-contains", help="Optional comma-separated URL substrings to keep")
    p_kw.add_argument("--out", help="Output JSON file path")
    p_kw.set_defaults(func=cmd_ranked_keywords)

    p_vol = sub.add_parser("search-volume", help="Search volume for explicit keywords.")
    p_vol.add_argument("keywords", nargs="+")
    p_vol.add_argument("--location", default="United States")
    p_vol.add_argument("--language", default="en")
    p_vol.add_argument("--out", help="Output JSON file path")
    p_vol.set_defaults(func=cmd_search_volume)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
