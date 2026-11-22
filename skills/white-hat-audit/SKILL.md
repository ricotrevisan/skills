---
name: white-hat-audit
description: Passive white-hat audit of a website or web app (security, privacy, SEO and AI findability, whether visitors understand it, design critique), ending in a plain-language PDF report for the owner. Use when asked for a white hat audit or a website check.
---

# White-hat audit

You run an outsider's audit: you see only what any browser or crawler sees. Security, privacy, findability, message and design, each **claim** re-checked by two models from other makers, the message tested on seven simulated readers, the screens rebuilt in Paper and critiqued, then one plain-language report for the site's owner.

**Passive** means: GET/HEAD requests, DNS, certificate logs, TLS handshakes, reading HTML/JS/JSON, Lighthouse, screenshots, loading pages in a browser without clicking anything that sends data. No POSTs (no login, no form, no email code), no messaging bots, no fuzzing, no brute force, no load. One harmless probe string in a public search box is fine. Owner-only checks (Search Console, logs, code) enter only when the user gives that access.

Work in the current directory: `raw/` for downloads, `reading/` for reader inputs, `personas/` for their answers, `img/` for report images, `claims.md`, `ledger.md`, `<site>-website-report.md` and `.pdf`. Scripts live in this skill's `scripts/`; run downloaded material through Python with `python3 -I`, scripts outside the download dir. Browser work on lab goes through `browserq` (see that skill); plain headless `chromium` is fine for screenshots.

Steps 2–5 feed `claims.md`; start the reviewers (step 6), readers (step 7) and screen rebuild (step 8) as soon as their inputs exist, and keep working while they run.

## 1. Map the surface

List every host and page type a visitor reaches: apex, `www`, subdomains linked from pages, demo or staging hosts, language versions, login, help/privacy/legal, a content page, a deep page someone would share, public data feeds (`.json`, `llms.txt`, `/.well-known/*`). Follow redirects from `http://` and `https://` on each host, with and without `Accept-Language`, and as Googlebot.

Then the hosts nobody links to: every name in the certificate logs (`curl -sS "https://crt.sh/?q=%25.<domain>&output=json"`, collect `name_value`, note each name's first `not_before`). Resolve each with `dig` (A, AAAA, CNAME). A name that resolves joins the host list; a CNAME pointing at a service that answers "no such site" (an unclaimed bucket, app or page) is a takeover risk. Names from before the current owner's first certificate are history, not findings. crt.sh can miss live hosts (on one audit it lacked a linked, live subdomain): it adds to the linked-host list, never replaces it.

**Exit:** a page-type list with one URL each, every host's redirect chain, and every certificate-log name marked live, dangling or history.

## 2. Security

Per host and per page type: response headers (HSTS, CSP, frame-ancestors / X-Frame-Options, nosniff, Referrer-Policy, Permissions-Policy), cookies and their flags, TLS versions and certificate, TRACE, a wrong `Host` header, ~10 forgotten-file paths (`/.env`, `/.git/HEAD`, `/wp-login.php`, `/server-status`, …). Domain: SPF, DKIM, DMARC, MX, CAA, DNSSEC, `security.txt`. Read every first-party script and every public data feed: comments, internal names, tester switches, what personal data a feed exposes and to whom (`Access-Control-Allow-Origin`).

**Exit:** each header/record checked on every page type and live host, each script and feed read, each finding with the command output that proves it.

## 3. Privacy: does the site do what its notice says?

Open each page type in a fresh browser session (agent-browser through browserq on lab) and touch nothing: list the cookies set (`cookies get`), the storage keys (`storage local`), and every outside origin contacted (`network requests`). Note whether a consent banner exists and what was set or contacted before anyone answered it. Then read the privacy notice, cookie notice and legal notice, and check them line by line against what you saw: undeclared cookies or processors, trackers before consent, promises the site breaks ("no SMS", "your location stays on your device"), a missing controller name or address.

**Exit:** a table per page type of cookies and outside origins before consent, and every notice claim marked kept, broken or unverifiable.

## 4. Findability

Title, description, canonical, hreflang, `x-default`, robots meta and `X-Robots-Tag`, JSON-LD per page type, Open Graph per page type (what a shared deep link previews as), `robots.txt`, sitemap, `llms.txt`, real 404s, HTML weight against Google's 2 MB read limit, AI crawler user agents (Googlebot, GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, PerplexityBot, CCBot, Bytespider). Crawl every internal link on the main pages and list non-200s; test each link on the host that serves it. One web search for the brand name, and one for what a customer would type.

Run Lighthouse in the background while you work: `scripts/lighthouse.sh img name=https://… [name=https://…]` (3 runs × mobile/desktop, median kept, score images cropped, outside origins listed).

**Ask AI assistants.** Write five questions a customer would ask, without naming the site in at least three ("best croissant in Brussels", "how much is a desk near the European Parliament"). Put them to assistants from three makers that search the web: one `delegate_task` each (e.g. Codex GPT, Claude, OpenCode), `role: research`, told to answer as a consumer assistant would, with web search, citing every source. Each assistant must have a working web search tool: a subagent worker may not, and one that only opens URLs it was given tests the site, not its findability; record that per maker. Record per answer: is the site cited, is what it says about the site correct, which competitors appear instead. Methodology states these are models with web search, not the consumer apps.

**Exit:** every item above checked per host, link crawl done, Lighthouse table printed, 15 assistant answers scored.

## 5. Does the site agree with itself?

Write `ledger.md`: every factual claim the site makes about itself (what it is, who runs it, prices, dates, how to sign up or take part, what happens to data, where it operates, addresses, contact), with the page it appears on, from the home, help, FAQ, privacy, terms, legal pages, `llms.txt` and structured data. Group by topic and mark every topic where two sources disagree, quoting both verbatim.

On a repeat audit, also diff each page's text against the previous run's copy in `raw/`: what the owner already changed decides which findings are fixed, and every earlier finding is re-checked before it is reused.

**Exit:** each listed page read in full, each disagreement quoted with both URLs.

## 6. Second and third opinion

Write `claims.md`: numbered claims (S… security, P… privacy, E… findability, M… contradictions from the ledger) with the evidence you saw, positives included, and the passive rules at the top. Call `orchestrator_capabilities`, then start two `delegate_task` reviewers on models from two makers other than yours (e.g. GPT-6 Astra on pi, DeepSeek V4.1 Flash on opencode), `role: review`, each told: read `claims.md`, passive checks only, fresh dir under `/tmp`, verdict per claim CONFIRMED / WRONG / PARTLY / UNVERIFIABLE with one line of evidence, challenge severity, list what was missed, short table.

When they return, re-check every WRONG, every PARTLY and every addition on the live site yourself before it enters the report. Adopt severity changes you agree with; note the ones you rejected and why in your reply.

**Exit:** every reviewer point is adopted with your own evidence, or rejected with a reason.

## 7. Reader test

1. Save each landing page's HTML to `raw/`, run `scripts/extract.py page.html` to get its visible text, collapse the language menu, and write one `reading/page-*.md` per page a reader lands on, in the language they would actually get. Write `reading/page-skim.md` for **the impatient one**: the first phone screen plus headings and first sentences only.
2. Screenshot the first phone screen of each landing page (`chromium --headless=new --window-size=390,844 --force-device-scale-factor=2 --screenshot=…`); wait a second before reading the PNG.
3. Choose seven personas for this site and fill `{SITE}` and `{PERSONAS}` in [`persona-brief.md`](persona-brief.md) → `reading/persona-brief.md`. Always include: the impatient one (30 seconds, second-language reader); a visitor who lands in a language that isn't theirs; a privacy or trust skeptic; the person on the other side of the market (the business, the buyer, the partner); someone who arrives on a deep link shared in a chat. Each persona names its page file.
4. Run them in parallel, three makers: your own model via `subagent` worker calls, the other two makers via `delegate_task` (`role: review`). Prompt: "Read `<brief>` and follow it as **Persona N (name)**. Read only that brief and `<page file>`. Open no other files, no web, start no subagents. Write your answer to `personas/pN-<slug>.md` (model name: <model>) and return the same text."
5. Check every confusion a reader reports against the screenshot. Drop the ones your extraction caused (glued words, hidden or unseen elements); mention the extraction limits in the methodology.

**Exit:** seven answers on disk, each reported confusion traced to the real page or dropped.

## 8. Screens: fit, rebuild, critique

1. **Fit.** At 320, 390, 768 and 1440 wide, per page type: `document.documentElement.scrollWidth <= window.innerWidth` (agent-browser `set viewport`, then `eval`), plus a screenshot. Tab through the main path from a fresh load: focus always visible, order follows the page, every control reachable and named.
2. **Rebuild** every public page type in Paper, phone and laptop, light and dark, following [`paper-rebuild.md`](paper-rebuild.md). Paper runs only on office and the laptop: you capture the screenshots and tokens, an agent there builds, and the exports come back to you. More than eight page types: rebuild the eight a visitor meets first (home, a landing page, sign-in, a key content page, the deep page people share, help, pricing if any, privacy) and list the rest as not rebuilt.
3. **Critique.** Fill [`design-critique.md`](design-critique.md) → `reading/design-critique.md` and give it to one `delegate_task` on a maker other than the one that built the screens (`role: review`), with the paths to the real and Paper PNGs and the token list; output to `design-critique-result.md`. Check each issue it raises against the real screenshot before it enters the report.

**Exit:** fit and keyboard results per page type, the Paper file URL with every artboard exported to `img/screens/paper/`, and a critique whose issues are each confirmed or dropped.

## 9. Report

Write `<site>-website-report.md` following [`report-guide.md`](report-guide.md). Then:

```bash
uv run -q --with markdown-it-py python -I <skill>/scripts/build-pdf.py <site>-website-report.md <site>-website-report.pdf \
  --site <site> --for "<Recipient role>,<br><Organisation>"
pdftoppm -r 50 -png <site>-website-report.pdf /tmp/<site>-p   # then tile and look at every page
```

Look at every page: cover, page breaks before each Part, tables not split mid-row, images present. Brand (name, logo, preparer contact) comes from `~/.config/white-hat-audit/brand.json`.

**Exit:** every "(point n)" reference resolves, the PDF pages look right, pronouns follow the report guide.

## Reply

Paths to the PDF, the Markdown and the Paper file, the verdict in three lines, what the reviewers changed, which reviewer or critic points you rejected, any step skipped and why, the recipient line on the cover for the user to confirm, and links to the delegate threads.
