#!/usr/bin/env python3
"""Fetch and parse robots.txt + sitemap.xml (including nested & gzipped indexes)."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (compatible; CompetitorSeoGapBot/1.0)"
TIMEOUT = 20
MAX_SITEMAPS = 60


def fetch_bytes(url: str) -> tuple[bytes | None, str | None]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = resp.read()
            ct = (resp.headers.get("Content-Type") or "").lower()
            ce = (resp.headers.get("Content-Encoding") or "").lower()
            if ce == "gzip" or url.endswith(".gz") or data[:2] == b"\x1f\x8b":
                try:
                    data = gzip.decompress(data)
                except OSError:
                    pass
            return data, None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001
        return None, str(exc)


def strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def discover_sitemaps(domain: str) -> list[str]:
    base = domain if domain.startswith(("http://", "https://")) else f"https://{domain}"
    base = base.rstrip("/")
    found: list[str] = []
    robots_bytes, _ = fetch_bytes(f"{base}/robots.txt")
    if robots_bytes:
        for line in robots_bytes.decode("utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("sitemap:"):
                sm_url = stripped.split(":", 1)[1].strip()
                if sm_url and sm_url not in found:
                    found.append(sm_url)
    for fallback in (f"{base}/sitemap.xml", f"{base}/sitemap_index.xml", f"{base}/sitemap-index.xml"):
        if fallback not in found:
            found.append(fallback)
    return found


def parse_sitemap_tree(seed_urls: list[str]) -> tuple[list[dict], list[str], list[str]]:
    visited: set[str] = set()
    queue = list(seed_urls)
    entries: dict[str, dict] = {}
    ok_sitemaps: list[str] = []
    errors: list[str] = []

    while queue and len(visited) < MAX_SITEMAPS:
        sm_url = queue.pop(0)
        if sm_url in visited:
            continue
        visited.add(sm_url)

        data, err = fetch_bytes(sm_url)
        if err or not data:
            errors.append(f"{sm_url}: {err}")
            continue

        try:
            root = ET.fromstring(data)
        except ET.ParseError as exc:
            errors.append(f"{sm_url}: XML parse error ({exc})")
            continue

        root_name = strip_ns(root.tag).lower()
        if root_name == "sitemapindex":
            ok_sitemaps.append(sm_url)
            for child in root:
                if strip_ns(child.tag).lower() != "sitemap":
                    continue
                loc = next((c.text.strip() for c in child if strip_ns(c.tag).lower() == "loc" and c.text), None)
                if loc and loc not in visited:
                    queue.append(loc)
        elif root_name == "urlset":
            ok_sitemaps.append(sm_url)
            for child in root:
                if strip_ns(child.tag).lower() != "url":
                    continue
                loc = None
                lastmod = None
                for field in child:
                    fname = strip_ns(field.tag).lower()
                    if fname == "loc" and field.text:
                        loc = field.text.strip()
                    elif fname == "lastmod" and field.text:
                        lastmod = field.text.strip()
                if loc and loc not in entries:
                    parsed = urllib.parse.urlparse(loc)
                    segs = [s for s in parsed.path.split("/") if s]
                    prefix = f"/{segs[0]}" if segs else "/"
                    entries[loc] = {
                        "url": loc,
                        "path": parsed.path or "/",
                        "prefix": prefix,
                        "lastmod": lastmod,
                        "source_sitemap": sm_url,
                    }
        else:
            errors.append(f"{sm_url}: unexpected root tag <{root_name}>")

        # Once we found real sitemaps from robots.txt, drop default fallbacks if unused
        if ok_sitemaps and sm_url == seed_urls[0] and len(queue) > 0:
            pass

    return list(entries.values()), ok_sitemaps, errors


def clean_domain(raw: str) -> str:
    raw = raw.strip()
    if "://" in raw:
        return urllib.parse.urlparse(raw).netloc.lower()
    return raw.strip("/").lower()


def main() -> int:
    parser = argparse.ArgumentParser(description="Fetch and summarize XML sitemaps for one or more domains.")
    parser.add_argument("domains", nargs="+", help="Domains or base URLs (e.g. whoistyping.wtf liveblocks.io)")
    parser.add_argument("--out", required=True, help="Output directory")
    parser.add_argument("--prefix", help="Optional comma-separated path prefixes to keep (e.g. /blog,/guides,/docs)")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    prefixes = [p.strip() for p in args.prefix.split(",") if p.strip()] if args.prefix else []

    summary_lines = ["# Sitemap Crawl Summary", ""]
    for raw in args.domains:
        domain = clean_domain(raw)
        seeds = discover_sitemaps(domain)
        urls, ok_sitemaps, errors = parse_sitemap_tree(seeds)
        if prefixes:
            urls = [u for u in urls if any(u["path"].startswith(p) for p in prefixes)]

        urls.sort(key=lambda u: ((u["lastmod"] or ""), u["url"]), reverse=True)
        prefix_counts = Counter(u["prefix"] for u in urls).most_common(15)

        payload = {
            "domain": domain,
            "sitemaps_ok": ok_sitemaps,
            "errors": errors,
            "total_urls": len(urls),
            "top_prefixes": [{"prefix": p, "count": c} for p, c in prefix_counts],
            "urls": urls,
        }
        out_file = out_dir / f"{domain}.json"
        out_file.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

        summary_lines.append(f"## {domain}")
        summary_lines.append(f"- **Total URLs:** {len(urls)} (from {len(ok_sitemaps)} sitemap file(s))")
        if prefix_counts:
            top_str = ", ".join(f"`{p}` ({c})" for p, c in prefix_counts[:10])
            summary_lines.append(f"- **Top sections:** {top_str}")
        recent = [u for u in urls if u["lastmod"]][:5]
        if recent:
            summary_lines.append("- **Most recently updated:**")
            for u in recent:
                summary_lines.append(f"  - `{u['lastmod']}` — {u['url']}")
        if not ok_sitemaps and errors:
            summary_lines.append(f"- **Errors:** {'; '.join(errors[:3])}")
        summary_lines.append("")
        print(f"{domain}: {len(urls)} URLs -> {out_file}", file=sys.stderr)

    (out_dir / "summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
