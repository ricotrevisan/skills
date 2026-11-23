#!/usr/bin/env python3
"""Join competitor sitemaps, DataForSEO ranked keywords, and your GSC export into a gap matrix."""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path


def norm_kw(s: str) -> str:
    return " ".join(s.lower().strip().split())


def load_sitemaps(sitemaps_dir: Path) -> dict[str, str | None]:
    lastmod_by_url: dict[str, str | None] = {}
    if not sitemaps_dir.exists():
        return lastmod_by_url
    for f in sorted(sitemaps_dir.glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        for entry in data.get("urls") or []:
            url = (entry.get("url") or "").rstrip("/")
            lastmod_by_url[url] = entry.get("lastmod")
    return lastmod_by_url


def load_gsc(gsc_path: Path) -> dict[str, dict]:
    by_kw: dict[str, dict] = {}
    data = json.loads(gsc_path.read_text(encoding="utf-8"))
    for row in data.get("rows") or []:
        kw = norm_kw(row.get("query") or "")
        if not kw:
            continue
        cur = by_kw.get(kw)
        if not cur or row.get("impressions", 0) > cur["impressions"]:
            by_kw[kw] = {
                "query": row.get("query"),
                "page": row.get("page"),
                "clicks": row.get("clicks", 0),
                "impressions": row.get("impressions", 0),
                "position": row.get("position", 0),
            }
    return by_kw


def main() -> int:
    parser = argparse.ArgumentParser(description="Build competitor SEO gap matrix.")
    parser.add_argument("--your-domain", required=True)
    parser.add_argument("--sitemaps", required=True, help="Directory with sitemap-fetch.py JSON files")
    parser.add_argument("--gsc", required=True, help="Path to gsc-queries.json")
    parser.add_argument("--dataforseo", required=True, help="Directory with *-keywords.json files")
    parser.add_argument("--out", required=True, help="Output directory for gap-matrix.json and gap-matrix.md")
    args = parser.parse_args()

    lastmod_by_url = load_sitemaps(Path(args.sitemaps))
    gsc_by_kw = load_gsc(Path(args.gsc))

    kw_rows: list[dict] = []
    total_cost = 0.0
    for f in sorted(Path(args.dataforseo).glob("*.json")):
        data = json.loads(f.read_text(encoding="utf-8"))
        total_cost += float(data.get("cost") or 0)
        if not f.name.endswith("-keywords.json") or "keywords" not in data:
            continue
        for item in data["keywords"]:
            kw = norm_kw(item.get("keyword") or "")
            if not kw:
                continue
            gsc = gsc_by_kw.get(kw)
            if not gsc:
                status = "gap"
                your_pos = None
                your_impr = 0
                your_page = None
            elif gsc["position"] > 10:
                status = "striking_distance"
                your_pos = gsc["position"]
                your_impr = gsc["impressions"]
                your_page = gsc["page"]
            else:
                status = "covered"
                your_pos = gsc["position"]
                your_impr = gsc["impressions"]
                your_page = gsc["page"]

            comp_url = (item.get("url") or "").rstrip("/")
            vol = int(item.get("search_volume") or 0)
            rank = int(item.get("rank") or 100)
            etv = float(item.get("etv") or 0)
            kd = item.get("kd")
            kd_factor = max(0.2, 1.0 - (float(kd) / 120.0)) if kd is not None else 0.7
            rank_bonus = 1.5 if rank <= 3 else (1.2 if rank <= 10 else 0.8)
            score = round(vol * kd_factor * rank_bonus * (1.0 if status == "gap" else 0.85), 1)

            kw_rows.append(
                {
                    "keyword": item.get("keyword"),
                    "status": status,
                    "opportunity_score": score,
                    "search_volume": vol,
                    "kd": kd,
                    "cpc": item.get("cpc"),
                    "intent": item.get("intent"),
                    "competitor": item.get("domain"),
                    "competitor_rank": rank,
                    "competitor_etv": etv,
                    "competitor_url": item.get("url"),
                    "competitor_lastmod": lastmod_by_url.get(comp_url),
                    "your_position": your_pos,
                    "your_impressions": your_impr,
                    "your_page": your_page,
                }
            )

    # Deduplicate same keyword across multiple competitors: keep highest ETV competitor row, track others
    by_kw_rows: dict[str, list[dict]] = defaultdict(list)
    for r in kw_rows:
        by_kw_rows[norm_kw(r["keyword"])].append(r)

    deduped = []
    for k, group in by_kw_rows.items():
        group.sort(key=lambda x: (x["competitor_etv"], x["search_volume"]), reverse=True)
        best = dict(group[0])
        best["also_ranked_by"] = [g["competitor"] for g in group[1:] if g["competitor"] != best["competitor"]]
        deduped.append(best)

    deduped.sort(key=lambda x: (x["status"] == "covered", -x["opportunity_score"], -x["search_volume"]))

    # Group by competitor URL to surface winning pages (the ~3% pages)
    by_page: dict[str, list[dict]] = defaultdict(list)
    for r in deduped:
        if r["status"] != "covered" and r["competitor_url"]:
            by_page[r["competitor_url"]].append(r)

    page_clusters = []
    for url, items in by_page.items():
        items.sort(key=lambda x: (-x["search_volume"], x["competitor_rank"]))
        page_clusters.append(
            {
                "competitor_url": url,
                "competitor": items[0]["competitor"],
                "lastmod": items[0]["competitor_lastmod"],
                "gap_keywords": len(items),
                "total_volume": sum(i["search_volume"] for i in items),
                "total_etv": round(sum(i["competitor_etv"] for i in items), 1),
                "top_keyword": items[0]["keyword"],
                "top_volume": items[0]["search_volume"],
                "sample_keywords": [i["keyword"] for i in items[:5]],
            }
        )
    page_clusters.sort(key=lambda p: (-p["total_etv"], -p["total_volume"]))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    result = {
        "your_domain": args.your_domain,
        "total_dataforseo_cost": round(total_cost, 4),
        "counts": {
            "gap": sum(1 for r in deduped if r["status"] == "gap"),
            "striking_distance": sum(1 for r in deduped if r["status"] == "striking_distance"),
            "covered": sum(1 for r in deduped if r["status"] == "covered"),
        },
        "page_clusters": page_clusters,
        "keywords": deduped,
    }
    (out_dir / "gap-matrix.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# SEO Gap Matrix — {args.your_domain}",
        "",
        f"- **Net-new gaps:** {result['counts']['gap']}",
        f"- **Striking distance (GSC pos > 10):** {result['counts']['striking_distance']}",
        f"- **Already covered (GSC pos <= 10):** {result['counts']['covered']}",
        f"- **DataForSEO spend:** ${result['total_dataforseo_cost']:.4f}",
        "",
        "## Top Competitor Pages You Don't Rank For",
        "",
        "| Competitor URL | Lastmod | Gap KWs | Combined Vol | ETV | Top Keyword |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for p in page_clusters[:30]:
        lm = p["lastmod"] or "—"
        lines.append(
            f"| {p['competitor_url']} | {lm} | {p['gap_keywords']} | {p['total_volume']:,} | {p['total_etv']:.1f} | `{p['top_keyword']}` ({p['top_volume']:,}) |"
        )

    lines.extend(
        [
            "",
            "## Top Keyword Gaps (Unfiltered — Curate for Product Fit)",
            "",
            "| Keyword | Status | Vol | KD | Intent | Comp Rank | Competitor URL | Your GSC Pos |",
            "| --- | --- | ---: | ---: | --- | ---: | --- | ---: |",
        ]
    )
    for r in [x for x in deduped if x["status"] != "covered"][:60]:
        kd = "—" if r["kd"] is None else str(r["kd"])
        ypos = "—" if r["your_position"] is None else f"{r['your_position']:.1f}"
        intent = r["intent"] or "—"
        lines.append(
            f"| `{r['keyword']}` | {r['status']} | {r['search_volume']:,} | {kd} | {intent} | #{r['competitor_rank']} | {r['competitor_url']} | {ypos} |"
        )

    (out_dir / "gap-matrix.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out_dir / 'gap-matrix.md'} ({len(deduped)} unique keywords, {len(page_clusters)} page clusters)", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
