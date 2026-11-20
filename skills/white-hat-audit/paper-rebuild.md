# Rebuild the screens in Paper

Each public page type from step 1 becomes four editable **artboards** in Paper: phone light, phone dark, laptop light, laptop dark. The rebuild is a faithful copy, not a redesign: same copy, same order, same colours and type. It gives the critic something to mark up and the owner something to iterate on.

## Preflight

Call `get_basic_info`. If Paper answers with a sign-in or account-setup error, stop this step, tell the user what Paper asked for, and carry on with the rest of the audit; the report then says the rebuild was skipped. Paper Desktop (office) serves local files; the hosted server (lab) cannot read local paths, so reference screenshots stay outside Paper there.

**Exit:** Paper answers, or the skip is recorded.

## 1. Capture the truth

Per page type, four full-page screenshots into `img/screens/real/`:

```bash
# light = 1, dark = 0; phone 390 wide, laptop 1440 wide; tall window = full page
chromium --headless=new --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
  --blink-settings=preferredColorScheme=1 --window-size=390,3000 --virtual-time-budget=6000 \
  --screenshot=img/screens/real/<page>-phone-light.png <url>
```

A site without a dark theme gets identical light and dark shots: record "no dark mode" once and build dark artboards only if the site has one. Read the site's CSS for `:root` custom properties and `@media (prefers-color-scheme: dark)` overrides; those values are the tokens.

**Exit:** four PNGs per page type (or the no-dark-mode note), and a token list with light and dark values.

## 2. File, pages, tokens

- `create_file` named `<site> screens <yyyy-mm-dd>`, then `open_file`.
- One Paper page per page type (`create_page`, `update_pages` to name it "Home", "Sign in", …), plus a first page "Tokens".
- `create_tokens`: Paper tokens have no modes, so every colour gets two tokens, `--<name>-light` and `--<name>-dark`. Shared tokens (font families, sizes, spacing, radius) get one. Use the site's own names where it has them. On the Tokens page, show each colour pair as swatches.

**Exit:** `get_tokens` lists every colour the screenshots use, in both modes.

## 3. Build

Per page type, in this order:

1. **Phone light** (`create_artboard` 390×844 with the mobile status bar from `get_guide({topic: "mobile-status-bar"})`). Write incrementally, one section per `write_html` call, inline styles, token variables for every colour, flex + gap (no margin, no grid, no tables). Name layers after the page's sections. Images become neutral placeholders named after what they show. When content runs past 844, set `height: fit-content`.
2. **Laptop light**: build a 1440×900 artboard the same way, following the real laptop layout (columns, nav), not a stretched phone.
3. **Dark twins**: `duplicate_nodes` each light artboard, then swap every `var(--x-light)` to `var(--x-dark)` with one batched `update_styles` (find the nodes with `get_jsx`). Rename the artboards "<Page> · phone · dark" etc.
4. Place the four artboards in a row: phone light, phone dark, laptop light, laptop dark.

Shared parts (header, footer, cookie banner) are built once on the first page and cloned with `<x-paper-clone node-id="…">` everywhere else, so a cross-screen inconsistency shows up as a real difference rather than a rebuild slip.

**Exit:** four artboards per page type (two when there is no dark mode), every colour a token.

## 4. Check fidelity, once

`get_screenshot` each artboard and compare it with its real PNG: copy, order, colours, type scale, spacing, alignment. List every difference, fix them in one batch, compare once more, and stop. Differences you chose not to fix (icons, photos, fonts Paper lacks) go into the report's methodology.

**Exit:** a difference list, fixed or recorded.

## 5. Export

`export` every artboard as PNG into `img/screens/paper/` (on the hosted server, download each returned link with `curl` within 24 hours). Tile one contact sheet per form factor for the report with Pillow.

**Exit:** one PNG per artboard on disk, contact sheets built, the Paper file URL noted.
