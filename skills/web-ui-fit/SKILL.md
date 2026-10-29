---
name: web-ui-fit
description: Make a web screen fit from a 320px phone to a large desktop. Use when building or changing a page, layout, or component, or when adding a repo's fit check.
---

# Web UI fit

Every screen ships from a 320px phone to a large desktop. A layout that only fits a laptop is not finished.

- Write the narrow layout first, then widen with `sm:` / `md:` / `lg:`.
- Long unbreakable values (keys, URLs, emails, JSON, error bodies) get `break-all` or their own `overflow-x-auto` box. The page stays within the viewport width. Tables get a scroll wrapper; grids collapse to one column; rows of controls wrap.
- Measure it: at 320px and 1440px, `document.documentElement.scrollWidth <= window.innerWidth` (T3 `preview_resize`, or devtools device mode). Done when both widths pass.

## CI fit check

Each UI repo gets one automated fit check in CI. A repo without one gets that as its next ticket; the rule alone does not catch regressions.

Reference implementation (bubble_wtf): `mix test test/wtf_web/ui/fit_pages_test.exs` writes page snapshots, `mix tailwind wtf`, then `npm run fit --prefix priv/browser` measures them in headless Chromium at 320/375/768/1440 and fails when a page is wider than the viewport.
