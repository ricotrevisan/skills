---
name: white-hat-audit
description: Passive white-hat audit of a website or web app (security, SEO and AI findability, whether visitors understand it), ending in a plain-language PDF report for the owner. Use when asked for a white hat audit or a website check.
---

# White-hat audit

You run an outsider's audit: you see only what any browser or crawler sees. Three parts (security, findability, message), each **claim** re-checked by two models from other makers, the message tested on seven simulated readers, then one plain-language report for the site's owner.

**Passive** means: GET/HEAD requests, DNS, TLS handshakes, reading HTML/JS/JSON, Lighthouse, screenshots. No POSTs (no login, no form, no email code), no messaging bots, no fuzzing, no brute force, no load. One harmless probe string in a public search box is fine. Owner-only checks (Search Console, logs, code) enter only when the user gives that access.

Work in the current directory: `raw/` for downloads, `reading/` for reader inputs, `personas/` for their answers, `img/` for report images, `claims.md`, `<site>-website-report.md` and `.pdf`. Scripts live in this skill's `scripts/`; run downloaded material through Python with `python3 -I`, scripts outside the download dir.

## 1. Map the surface

List every host and page type a visitor reaches: apex, `www`, subdomains linked from pages, demo or staging hosts, language versions, login, help/privacy/legal, a content page, a deep page someone would share, public data feeds (`.json`, `llms.txt`, `/.well-known/*`). Follow redirects from `http://` and `https://` on each host, with and without `Accept-Language`, and as Googlebot.

**Exit:** a page-type list with one URL each, and every host's redirect chain.

## 2. Security

Per host and per page type: response headers (HSTS, CSP, frame-ancestors / X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy), cookies and their flags, TLS versions and certificate, TRACE, a wrong `Host` header, ~10 forgotten-file paths (`/.env`, `/.git/HEAD`, `/wp-login.php`, `/server-status`, …). Domain: SPF, DKIM, DMARC, MX, CAA, DNSSEC, `security.txt`. Read every first-party script and every public data feed: comments, internal names, tester switches, what personal data a feed exposes and to whom (`Access-Control-Allow-Origin`). Note every third-party origin a page loads and on which page. Read the privacy notice and check it against what the site visibly does.

**Exit:** each header/record checked on every page type, each script and feed read, each finding with the command output that proves it.

## 3. Findability

Title, description, canonical, hreflang, `x-default`, robots meta and `X-Robots-Tag`, JSON-LD per page type, Open Graph per page type (what a shared deep link previews as), `robots.txt`, sitemap, `llms.txt`, real 404s, HTML weight against Google's 2 MB read limit, AI crawler user agents (Googlebot, GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, PerplexityBot, CCBot, Bytespider). Crawl every internal link on the main pages and list non-200s; test each link on the host that serves it. One web search for the brand name, and one for what a customer would type.

Run Lighthouse in the background while you work: `scripts/lighthouse.sh img name=https://… [name=https://…]` (3 runs × mobile/desktop, median kept, score images cropped).

**Exit:** every item above checked per host, link crawl done, Lighthouse table printed.

## 4. Second and third opinion

Write `claims.md`: numbered claims (S1… security, E1… findability, M1… message contradictions) with the evidence you saw, positives included, and the passive rules at the top. Call `orchestrator_capabilities`, then start two `delegate_task` reviewers on models from two makers other than yours (e.g. GPT-6 Astra on pi, DeepSeek V4.1 Flash on opencode), `role: review`, each told: read `claims.md`, passive checks only, fresh dir under `/tmp`, verdict per claim CONFIRMED / WRONG / PARTLY / UNVERIFIABLE with one line of evidence, challenge severity, list what was missed, short table. Continue with step 5 while they run.

When they return, re-check every WRONG, every PARTLY and every addition on the live site yourself before it enters the report. Adopt severity changes you agree with; note the ones you rejected and why in your reply.

**Exit:** every reviewer point is adopted with your own evidence, or rejected with a reason.

## 5. Reader test

1. Save each landing page's HTML to `raw/`, run `scripts/extract.py page.html` to get its visible text, collapse the language menu, and write one `reading/page-*.md` per page a reader lands on, in the language they would actually get. Write `reading/page-skim.md` for **the impatient one**: the first phone screen plus headings and first sentences only.
2. Screenshot the first phone screen of each landing page (`chromium --headless=new --window-size=390,844 --force-device-scale-factor=2 --screenshot=…`); wait a second before reading the PNG.
3. Choose seven personas for this site and fill `{SITE}` and `{PERSONAS}` in [`persona-brief.md`](persona-brief.md) → `reading/persona-brief.md`. Always include: the impatient one (30 seconds, second-language reader); a visitor who lands in a language that isn't theirs; a privacy or trust skeptic; the person on the other side of the market (the business, the buyer, the partner); someone who arrives on a deep link shared in a chat. Each persona names its page file.
4. Run them in parallel, three makers: your own model via `subagent` worker calls, the other two makers via `delegate_task` (`role: review`). Prompt: "Read `<brief>` and follow it as **Persona N (name)**. Read only that brief and `<page file>`. Open no other files, no web, start no subagents. Write your answer to `personas/pN-<slug>.md` (model name: <model>) and return the same text."
5. Check every confusion a reader reports against the screenshot. Drop the ones your extraction caused (glued words, hidden or unseen elements); mention the extraction limits in the methodology.

**Exit:** seven answers on disk, each reported confusion traced to the real page or dropped.

## 6. Report

Write `<site>-website-report.md` following [`report-guide.md`](report-guide.md). Then:

```bash
uv run -q --with markdown-it-py python -I <skill>/scripts/build-pdf.py <site>-website-report.md <site>-website-report.pdf \
  --site <site> --for "<Recipient role>,<br><Organisation>"
pdftoppm -r 50 -png <site>-website-report.pdf /tmp/<site>-p   # then tile and look at every page
```

Look at every page: cover, page breaks before each Part, tables not split mid-row, images present. Brand (name, logo, preparer contact) comes from `~/.config/white-hat-audit/brand.json`.

**Exit:** every "(point n)" reference resolves, the PDF pages look right, pronouns follow the report guide.

## Reply

Paths to the PDF and Markdown, the verdict in three lines, what the reviewers changed, which reviewer points you rejected, the recipient line on the cover for the user to confirm, and links to the delegate threads.
