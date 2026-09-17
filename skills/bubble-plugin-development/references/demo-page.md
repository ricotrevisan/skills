# Demo page guidance

Keep one demo page that shows the plugin through real Bubble elements and
workflows. The plugin repo's `AGENTS.md` supplies the app, login, URL, and copy
voice. If the page points at the marketplace plugin version, say so: it will not
reflect unpublished local plugin changes.

## Layout

Match the existing Modern Dropdown and Tiptap visual language unless the target
repo specifies another system:

- Backdrop `#F1F5F9`; centered content column; `maxWidthPx` 960.
- Page padding: 32 top, 96 bottom, 20 horizontal.
- Section stack: `rowGapPx` 28.
- Hero: `#0F172A`, padding 40×44; eyebrow 12px/700 `#60A5FA` with 1.4 letter
  spacing; H1 44px/800 `#F8FAFC`; description 18px `#CBD5E1`; proof points
  14px/600 `#93C5FD`.
- Section cards: white, padding 32; heading 28px/800 `#0F172A`; description
  15px `#475569`.
- Final callout: `#1D4ED8`, padding 40; heading 32px/800 white; description
  16px `#DBEAFE`.

Copy an established demo page rather than recreating this visual system from
scratch.

## Copy

Write for a medior Bubble developer choosing a plugin for a SaaS app.
Plain, straightforward, clear. No flourish.

- Name what the section demonstrates. Headings are plain feature names:
  "Single select with search", "Selection limits".
- State concrete facts: what it does, what publishes back to Bubble, what it
  avoids.
- Use concrete proof where it changes a decision: dependencies, placements,
  states, events, workflows.
- No slogans, no "pain/seam" storytelling, no fragment-style headings
  ("One field. Lots of placements."), no decorative bullet-separated proof
  lines, no em-dash asides.
- Give each section one job a Bubble builder already recognizes.

## Structure

1. Hero: what the plugin is and what it needs from Bubble.
2. Three to five interactive playgrounds using real elements and workflows.
3. One before/after showing the native Bubble failure and the plugin behavior.
4. A closing callout explaining how to wire the plugin.

Avoid property dumps, tutorial voice, and screenshots standing in for working
interactions. The page should sell the plugin and remain a useful test surface.
