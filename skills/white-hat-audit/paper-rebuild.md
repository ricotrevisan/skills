# Rebuild the screens in Paper

Each public page type from step 1 becomes four editable **artboards** in Paper: phone light, phone dark, laptop light, laptop dark. The rebuild is a faithful copy, not a redesign: same copy, same order, same colours and type. It gives the critic something to mark up and the owner something to iterate on.

Paper works only where Paper Desktop runs: **office** (Mac mini) and the laptop. The auditing agent captures the inputs, hands the build to an agent on that machine, and takes the exports back. On office or the laptop itself, skip the hand-off and run the build steps directly.

## 1. Capture the truth (auditing agent)

Per page type, four full-page screenshots into `paper-in/real/`:

```bash
# light = 1, dark = 0; phone 390 wide, laptop 1440 wide; tall window = full page
chromium --headless=new --no-sandbox --disable-gpu --hide-scrollbars --force-device-scale-factor=2 \
  --blink-settings=preferredColorScheme=1 --window-size=390,3000 --virtual-time-budget=6000 \
  --screenshot=paper-in/real/<page>-phone-light.png <url>
```

A site without a dark theme gets identical light and dark shots: record "no dark mode" and build dark artboards only if the site has one. Read the site's CSS for `:root` custom properties and `@media (prefers-color-scheme: dark)` overrides; those values are the tokens.

Write `paper-in/brief.md`: the site, the Paper file name `<site> screens <yyyy-mm-dd>`, each page type with its URL and screenshot files, the token table (name, light value, dark value, plus fonts, sizes, spacing, radius), the shared parts (header, footer, banners), and "no dark mode" if so.

**Exit:** four PNGs per page type (or the note), and `paper-in/brief.md`.

## 2. Hand off

1. **Pick the machine.** `t3_environment_links`: use office ("Mac mini") when it is reachable, else the laptop ("MacBook").
2. **Find its scratch project.** Office: `t3_threads.py --host office --allow-non-loopback inspect` (from the `t3-thread-management` skill) and take the project whose `workspaceRoot` ends in `/.t3/scratch`. The laptop is not reachable over SSH from lab: if it is the only choice, ask the user for its scratch project id.
3. **Delegate.** One `delegate_task`, `role: design`, `target: {environmentId, projectId, providerInstanceId: "pi"}` (Pi is the provider signed in there), `mode: async`. The task, with `<dir>` the absolute path of the audit folder on this machine and `<host>` this machine's SSH name (`hostname -s`):

   > Rebuild the screens of `<site>` in Paper Desktop. Copy the inputs: `mkdir -p ~/.t3/scratch/wha-<site> && scp -rq <host>:<dir>/paper-in/. ~/.t3/scratch/wha-<site>/`. Read `brief.md` there, then follow steps 3–6 of `~/.agents/skills/white-hat-audit/paper-rebuild.md`. Send the exports back: `ssh <host> mkdir -p <dir>/img/screens/paper && scp -q ~/.t3/scratch/wha-<site>/out/* <host>:<dir>/img/screens/paper/` (lab has no rsync). Reply with the Paper file URL, the artboards built, the fidelity differences you left, and anything you skipped.

Keep auditing while it runs. When it returns, check that `img/screens/paper/` holds one PNG per artboard.

**Exit:** the exports are on this machine and the Paper file URL is recorded, or the reason it failed is.

## 3. File, pages, tokens (Paper machine)

- `get_basic_info` first. "Open a Paper file" means Paper is signed in and ready; a sign-in or account-setup error stops the rebuild: reply with Paper's exact message.
- `create_file` with the name from the brief, then `open_file`.
- One Paper page per page type (`create_page`, `update_pages` to name it "Home", "Sign in", …), plus a first page "Tokens".
- `create_tokens`: Paper tokens have no modes, so every colour gets two tokens, `--<name>-light` and `--<name>-dark`. Shared tokens (font families, sizes, spacing, radius) get one. Use the site's own names. On the Tokens page, show each colour pair as swatches.

**Exit:** `get_tokens` lists every colour in the brief, in both modes.

## 4. Build (Paper machine)

Per page type, in this order:

1. **Phone light** (`create_artboard` 390×844 with the mobile status bar from `get_guide({topic: "mobile-status-bar"})`). Write incrementally, one section per `write_html` call, inline styles, token variables for every colour, flex + gap (no margin, no grid, no tables). Name layers after the page's sections. Images become neutral placeholders named after what they show. When content runs past 844, set `height: fit-content`.
2. **Laptop light**: a 1440×900 artboard built the same way, following the real laptop layout (columns, nav), not a stretched phone.
3. **Dark twins**: `duplicate_nodes` each light artboard, then swap every `var(--x-light)` to `var(--x-dark)` with one batched `update_styles` (find the nodes with `get_jsx`). Name the artboards "<Page> · phone · dark" etc.
4. Place the four artboards in a row: phone light, phone dark, laptop light, laptop dark.

Shared parts (header, footer, banners) are built once on the first page and cloned with `<x-paper-clone node-id="…">` everywhere else, so a cross-screen inconsistency shows up as a real difference rather than a rebuild slip.

**Exit:** four artboards per page type (two when there is no dark mode), every colour a token.

## 5. Check fidelity, once (Paper machine)

`get_screenshot` each artboard and compare it with its real PNG in `real/`: copy, order, colours, type scale, spacing, alignment. List every difference, fix them in one batch, compare once more, and stop. Differences left (icons, photos, fonts Paper lacks) go into the reply.

**Exit:** a difference list, fixed or recorded.

## 6. Export (Paper machine)

`export` every artboard as PNG into `out/`, named `<page>-<phone|laptop>-<light|dark>.png`, and tile one contact sheet per form factor (`out/sheet-phone.png`, `out/sheet-laptop.png`) with Pillow (`uv run -q --with pillow python -I …`).

**Exit:** one PNG per artboard plus the two sheets in `out/`.
