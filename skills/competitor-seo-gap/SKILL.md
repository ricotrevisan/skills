---
name: competitor-seo-gap
description: Reverse-engineer competitor SEO from sitemaps, DataForSEO traffic/keyword data, and your Google Search Console to find content gaps and build a prioritized content calendar. Use when asked to audit competitor SEO, find keyword or content gaps against Search Console, or turn competitor pages into scheduled articles.
---

# Competitor SEO gap

Reverse-engineer the ~3% of competitor pages that actually earn Google traffic, cross-reference against your Google Search Console, filter for product fit, and turn real gaps into a content calendar (and optionally drafts or scheduled publishes).

Scripts live in [`scripts/`](scripts/) next to this file; each has `--help`. Run them with `python3 -I` and keep all outputs in one working directory (e.g. `~/audits/<site>-seo-gap-YYYY-MM-DD/`).

## Prerequisites

- **Google Search Console** via Loggie (`~/.local/bin/loggie-account <account> setup` to confirm `google-search-console` is `ready`; see `loggie` skill).
- **DataForSEO** credentials in `~/.agents/skills/.env.schema` (`DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` from 1Password), invoked via `varlock run --path ~/.agents/skills/ -- ...`. Never call `op read` directly or print credentials.
- Check balance first (`dataforseo-gap.py balance`, free) and confirm spend stays modest (a typical 3-competitor run costs ~$0.15–$0.40 total).

## 1. Ground in the product and pick competitors

Read the target site's own sitemap and product docs (`PRODUCT.md`, `CONTEXT.md`, `README.md`, or landing page) before touching competitors. Write down:
- What the product actually does and does **not** do (used in step 4 to drop off-product keywords).
- Your existing URLs and target buyer personas.
- 2–5 direct competitors (same search intent, not necessarily giant portals unless filtered to their relevant path prefix).

**Exit:** target domain, GSC property (`sc-domain:...` or URL prefix), Loggie account, product-fit boundary, and competitor list written to `scope.md`.

## 2. Crawl sitemaps and export your Search Console

Run both in parallel:

```bash
python3 -I <skill>/scripts/sitemap-fetch.py --out raw/sitemaps <your-domain> <competitor-1> <competitor-2> ...
python3 -I <skill>/scripts/gsc-export.py --account <personal|work> --site <gsc-property> --days 90 --out raw/gsc
```

`sitemap-fetch.py` follows `robots.txt` and nested/gzipped sitemap indexes, writing per-domain `<domain>.json` (`url`, `lastmod`, `path_prefix`) and `summary.md`. `gsc-export.py` paginates Search Console queries and pages into `raw/gsc/gsc-queries.json` and `raw/gsc/gsc-pages.json`.

**Exit:** every domain's sitemap parsed (or blocked status recorded), `raw/sitemaps/summary.md` and `raw/gsc/gsc-queries.json` on disk.

## 3. Pull competitor winning pages and keywords (DataForSEO)

Check balance first, then pull each competitor's highest-traffic pages and top ranking keywords:

```bash
varlock run --path ~/.agents/skills/ -- python3 -I <skill>/scripts/dataforseo-gap.py balance

varlock run --path ~/.agents/skills/ -- python3 -I <skill>/scripts/dataforseo-gap.py relevant-pages \
  --domain <competitor> --limit 100 --out raw/dataforseo/<competitor>-pages.json

varlock run --path ~/.agents/skills/ -- python3 -I <skill>/scripts/dataforseo-gap.py ranked-keywords \
  --domain <competitor> --limit 300 --max-rank 20 --min-volume 50 \
  --out raw/dataforseo/<competitor>-keywords.json
```

Use `--path-contains /blog,/guides,/docs` when a competitor is huge so you only pay for and analyze relevant sections. Each call logs its exact DataForSEO `cost` to stderr; stop and ask if cumulative cost will exceed $2.

Optional: for specific sitemap slugs not in `ranked-keywords`, verify demand with `dataforseo-gap.py search-volume --out raw/dataforseo/extra-volume.json "kw 1" "kw 2"`.

**Exit:** `relevant-pages` and `ranked-keywords` JSON saved for every competitor, total API spend recorded.

## 4. Build the gap matrix and filter for product fit

Join sitemaps, DataForSEO rankings, and your GSC export:

```bash
python3 -I <skill>/scripts/gap-matrix.py \
  --your-domain <your-domain> \
  --sitemaps raw/sitemaps \
  --gsc raw/gsc/gsc-queries.json \
  --dataforseo raw/dataforseo \
  --out .
```

This writes `gap-matrix.json` and `gap-matrix.md`, grouping competitor keywords by ranking page and tagging each keyword as:
- **Gap (unranked):** competitor ranks top 20, you have 0 GSC impressions.
- **Striking distance:** you have GSC impressions at position > 10 (optimize an existing page before writing a new one).
- **Covered:** you already rank top 10.

Now **curate by hand** against `scope.md` — never feed raw output straight into a calendar:
1. Drop competitor navigational/branded queries unless it is a genuine `"X alternative"` / `"X vs Y"` commercial comparison.
2. Drop topics outside your product's actual capability (mark why in `dropped.md` so you don't revisit them).
3. Merge overlapping competitor pages into one canonical target topic (avoid cannibalizing your own existing pages).

**Exit:** `gap-matrix.md` generated, curated shortlist separated into **New pages** and **Optimize existing pages**, every dropped cluster accounted for.

## 5. Content calendar and publishing

Write `content-calendar.md` with the prioritized queue:

| Priority | Action (`New` / `Update`) | Target URL / slug | Primary keyword (vol) | Secondary keywords | Competitor URL to beat (`lastmod`, ETV) | Product angle / proof | Target date |
| --- | --- | --- | --- | --- | --- | --- | --- |

Present `content-calendar.md` to the user before drafting or scheduling. Once approved:
- **Draft / PR mode (default):** write each page on a git branch/PR matching the repo's exact content format (routes, metadata, canonical, JSON-LD, `sitemap.xml`, `llms.txt`), grounded in real product facts — no unverified claims.
- **Scheduled / autopilot mode:** only when explicitly requested, schedule publication dates via Drummer on `openclaw` or a T3 scheduled task, one item per cadence slot, and record the job IDs in `content-calendar.md`.

**Exit:** `content-calendar.md` on disk, total DataForSEO cost reported, and (if approved) PRs or scheduled jobs linked.
