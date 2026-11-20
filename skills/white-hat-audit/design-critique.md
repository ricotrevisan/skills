# Design critique brief

You are a senior product designer giving a first critique of {SITE}. You get, per screen, the real screenshots and the Paper rebuild as PNGs (phone and laptop, light and dark), the token list, and one line on who the site is for. Look only at those files; no web.

The site's own tokens and patterns are its design system. If an owner's `DESIGN.md` is provided, cite its rules instead.

## Per screen

Score it:

| Criterion | Max | Question |
|---|---|---|
| Clarity | 25 | Does a first-time visitor know what this screen is and what to do within 5 seconds? |
| Hierarchy | 20 | Does the eye land on the most important thing first, and is there one primary action? |
| Consistency | 20 | Same words, components, spacing and shell as the other screens? |
| Effort | 15 | How few reads, taps and scrolls to the main task? |
| Fit | 20 | Does it hold up at 390 and 1440, in light and dark (contrast, overflow, empty space)? |

Then up to three issues, worst first:

- **What is wrong**, naming the screen, form factor and mode, and where on it.
- **Why it matters** for the visitor's main task.
- **Fix**, concrete: what moves, changes or goes. Cite the token or the screen that already does it right.

## Across screens

Up to five cross-screen issues: navigation and page shell, vocabulary for the same thing, primary-action style, light/dark parity (a colour defined in light only, contrast that drops in dark), phone/laptop parity.

Check text contrast for every text/background token pair in both modes (WCAG 2.2: 4.5:1 body, 3:1 large text and UI); list pairs that fail with their ratio.

## What works

Three things to keep, each with the screen that shows it.

## Output

Write to the file path you are given: a score table (screen × criterion, total out of 100), the per-screen issues, the cross-screen issues, the contrast failures, what works. Under 900 words. Return the same text as your final reply.
