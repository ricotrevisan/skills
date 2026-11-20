# Report guide

The reader is the site's owner or manager, not a developer. Every finding must make sense to someone who has never seen an HTTP header. Name the technical thing once, in brackets, for the developer who gets the report forwarded.

## Skeleton

The first lines feed the PDF cover; keep them exactly in this shape.

```markdown
# <site>: website check

**Date:** <d Month yyyy>
**Scope:** Security, findability on Google and in AI assistants, and whether the text is clear to the people it's written for.

## In one paragraph
## The five things to do first        (numbered, each pointing to its point number)
---
## Part 1: Security                   ("What you can relax about" bullets first, then numbered points)
---
## Part 2: Technical SEO and AI findability
   (one-line definition of SEO/AEO in italics, Lighthouse images + score table, then numbered points)
---
## Part 3: Humans: is the text clear?
   (method in 5 lines, "What works", first-screen screenshot, reader table, numbered points with "(n of 7 readers)")
---
## Suggested order of work            (table: When | Task | Who | Effort)
---
## How we checked (methodology)
### Models and tools used             (table: Role | AI model | Run in | What it did)
---
*Assembled by <model> on behalf of <preparer>.*
```

`---` before a `## Part` heading becomes a page break in the PDF. Point numbers run 1..n through the whole report; after inserting or removing a point, renumber and fix every "(point n)" reference, in "The five things" and in the order-of-work table too.

## A finding

```markdown
### 6. Google only reads the first part of the page (most important)

**What we found:** <the fact, in plain words, with the number that proves it>

**Example:** <one concrete scene: who does what, and what goes wrong for them>

**Why it matters:** <only when the example doesn't already make it obvious>

**What to do:** <the fix, in plain words>. *Who:* <you | developer | hosting provider | lawyer>, <effort>.
```

- Headings say what is wrong, in the owner's words: "Most pages can be shown inside another website", not "Missing X-Frame-Options".
- Mark items that need the owner's decision rather than a developer's hour: "(needs a decision)".
- Group cheap low-severity items into one "Smaller items" point per part.
- Every reader-test point carries a count ("4 of 7 readers") and quotes readers in italics.
- Quote the site verbatim when it contradicts itself; contradictions between the site's own pages are findings.
- Say plainly what is fine. The "What you can relax about" lists are part of the value.
- People are "they" unless the persona brief gave a gender; reader personas may keep the gender the brief gave them.

## Reader table

| Reader | What they understood, in their words | Where they got stuck | Clarity (1–5) |
|---|---|---|---|

"Clarity" is the persona's own confidence score.

## Methodology must state

- Passive only: what we did not do (break in, overload, sign in, submit forms, message bots).
- Each check family with its tools.
- Lighthouse version, browser version, date, runs per form factor, spread of scores.
- Which models verified the claims, that they confirmed or corrected, and what they added.
- Reader-test limits: AI simulations, not real people; extraction caveats (e.g. language banners the readers could not see).
- Limits: no access to hosting, Search Console, analytics or code (unless the owner gave it). Not legal advice when legal topics come up.
