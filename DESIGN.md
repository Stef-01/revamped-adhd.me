---
name: ADHDme
description: The appointment letter you never got. One yellow tile, ink type, cream ground, hairlines for structure.
colors:
  yellow: "#f5ba13"
  yellow-deep: "#e2ac24"
  ink: "#141414"
  ink-2: "#222222"
  cream: "#fafaf7"
  white: "#ffffff"
  line: "#e8e6df"
  muted: "#5f5e59"
  muted-on-yellow: "#5a4100"
  muted-on-ink: "#bab6ab"
  line-on-ink: "#2f2d28"
  line-on-yellow: "rgba(20, 20, 20, 0.18)"
typography:
  display:
    fontFamily: "Plus Jakarta Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(2.25rem, 0.86rem + 5.7vw, 6rem)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "Plus Jakarta Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.875rem, 1.2rem + 2.8vw, 3rem)"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.03em"
  title:
    fontFamily: "Plus Jakarta Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.25rem, 1.1rem + 0.6vw, 1.5rem)"
    fontWeight: 800
    lineHeight: 1.15
    letterSpacing: "-0.02em"
  lead:
    fontFamily: "Plus Jakarta Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "clamp(1.125rem, 1rem + 0.7vw, 1.4375rem)"
    fontWeight: 500
    lineHeight: 1.4
  body:
    fontFamily: "Plus Jakarta Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.5
  small:
    fontFamily: "Plus Jakarta Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 600
    lineHeight: 1.5
  meta:
    fontFamily: "Plus Jakarta Sans, ui-sans-serif, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.5
rounded:
  sm: "0.625rem"
  tile: "1.5rem"
  pill: "999px"
spacing:
  s-1: "0.25rem"
  s-2: "0.5rem"
  s-3: "0.75rem"
  s-4: "1rem"
  s-5: "1.5rem"
  s-6: "2rem"
  s-7: "3rem"
  s-8: "4rem"
  s-9: "6rem"
  s-10: "8rem"
  page-margin: "clamp(0.5rem, 1.5vw, 1.25rem)"
  tile-pad: "clamp(1.25rem, 0.4rem + 3.6vw, 4.5rem)"
  gap-tiles: "clamp(0.75rem, 1.5vw, 1.25rem)"
components:
  button-primary:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    typography: "{typography.small}"
    rounded: "{rounded.pill}"
    padding: "0.85em 1.5em"
    height: "2.75rem"
  button-primary-hover:
    backgroundColor: "{colors.ink-2}"
    textColor: "{colors.white}"
  button-yellow:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.ink}"
    typography: "{typography.small}"
    rounded: "{rounded.pill}"
    padding: "0.85em 1.5em"
    height: "2.75rem"
  button-yellow-hover:
    backgroundColor: "{colors.yellow-deep}"
    textColor: "{colors.ink}"
  button-ghost:
    backgroundColor: "transparent"
    textColor: "{colors.ink}"
    typography: "{typography.small}"
    rounded: "{rounded.pill}"
    padding: "0.85em 1.5em"
    height: "2.75rem"
  button-ghost-hover:
    backgroundColor: "rgba(20, 20, 20, 0.08)"
    textColor: "{colors.ink}"
  button-lg:
    typography: "{typography.body}"
    padding: "1em 1.6em"
    height: "3.25rem"
  button-sm:
    typography: "{typography.meta}"
    padding: "0.6em 1.1em"
    height: "2.25rem"
  tile-white:
    backgroundColor: "{colors.white}"
    textColor: "{colors.ink}"
    rounded: "{rounded.tile}"
    padding: "{spacing.tile-pad}"
  tile-ink:
    backgroundColor: "{colors.ink}"
    textColor: "{colors.white}"
    rounded: "{rounded.tile}"
    padding: "{spacing.tile-pad}"
  tile-yellow:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.ink}"
    rounded: "{rounded.tile}"
    padding: "{spacing.tile-pad}"
  numeral-disc:
    backgroundColor: "{colors.yellow}"
    textColor: "{colors.ink}"
    typography: "{typography.small}"
    rounded: "{rounded.pill}"
    size: "2.25rem"
  floating-nav:
    backgroundColor: "color-mix(in srgb, #fafaf7 82%, transparent)"
    textColor: "{colors.ink}"
    typography: "{typography.small}"
    rounded: "{rounded.pill}"
    padding: "0.5rem 0.5rem 0.5rem 1.5rem"
---

# Design System: ADHDme

## Overview

**Creative North Star: "The Appointment Letter"**

The page reads like the letter a tired adult should have received: it says what happens, in order, in as few words as it can, and it puts nothing on the page that could go stale or that nobody said. The visual system follows that stance. One saturated yellow owns the first viewport with ink type set directly on it; the rest of the page is a stack of flat tiles (white, then ink) laid on a cream desk inside a single narrow page margin. Structure comes from hairlines and generous padding, never from shadow, gradient, imagery or decoration.

Density is low and deliberate. Display type is set heavy (800) at line-height 1.0 with tight tracking, so headings carry weight without needing size alone. Body copy is 17px at 1.5 and capped around 60 characters. There is exactly one drawn gesture on the page: a hand-drawn ink stroke under a phrase in the headline. Everything else is set in type, including the wordmark and the numerals.

**Key Characteristics:**
- Flat: no drop shadows anywhere; depth is tile-on-ground plus hairlines.
- One accent (yellow), one radius (24px), one typeface (Plus Jakarta Sans).
- Secondary text is tinted from its ground, never a neutral grey.
- Motion has one verb: things arrive by travelling down 24px into place.
- Copy is short; the system is built for 20 to 60 words per screen.

## Colors

A three-tone palette (yellow, ink, cream) with white for tiles and one hairline; nothing else.

### Primary
- **Yellow** (`{colors.yellow}`): the hero tile's ground, the CTA on ink, numeral discs, FAQ toggle discs, the arrow glyph inside ink buttons, and text selection. It is a surface colour, not a text colour; ink always sits on it.
- **Yellow Deep** (`{colors.yellow-deep}`): hover state of the yellow button only.

### Neutral
- **Ink** (`{colors.ink}`): all headings and body text on light grounds, the primary button, the closing tile, focus rings, the caret and form accent.
- **Ink 2** (`{colors.ink-2}`): hover state of the ink button only.
- **Cream** (`{colors.cream}`): the page ground (the desk). Also the floating nav's frosted fill at 82% opacity.
- **White** (`{colors.white}`): the section tiles, and text on ink.
- **Line** (`{colors.line}`): the hairline. Step dividers, list dividers, FAQ dividers, the floating nav's 1px inset ring.
- **Muted** (`{colors.muted}`): secondary text on cream and white (6.3:1).
- **Muted on Yellow** (`{colors.muted-on-yellow}`): the hero lead (6.7:1 on yellow).
- **Muted on Ink** (`{colors.muted-on-ink}`): secondary text inside the ink tile (8.7:1).
- **Line on Yellow** (`{colors.line-on-yellow}`): the hairline above the hero fact row.
- **Line on Ink** (`{colors.line-on-ink}`): the hairline token for ink grounds (declared for use inside ink tiles).

### Named Rules
**The Tinted Secondary Rule.** Secondary text takes the muted token for its ground: `muted` on cream and white, `muted-on-yellow` on yellow, `muted-on-ink` on ink. No grey from outside the palette, no opacity-faded ink.

**The Yellow Is Ground Rule.** Yellow is painted, never typed. It appears as a tile, a disc, a button fill or an icon glyph; it is never used for text or gradients.

## Typography

**Display Font:** Plus Jakarta Sans (with ui-sans-serif, system-ui fallback)
**Body Font:** Plus Jakarta Sans (same family; weights 400, 500, 600, 700, 800 loaded from Google Fonts)

**Character:** One geometric humanist sans doing every job. Weight and tracking carry hierarchy: headings are 800 and tight, body is 400 and open, controls and metadata are 600 or 700. Kerning, ligatures and contextual alternates are on; headings use `text-wrap: balance`, paragraphs `text-wrap: pretty`.

### Hierarchy
- **Display** (800, `{typography.display.fontSize}`, 36px at 390 to 96px at 1440, line-height 1.0, tracking -0.035em): the hero h1 and the closing tile's h2 only.
- **Headline** (800, `{typography.headline.fontSize}`, line-height 1.0, tracking -0.03em): section h2s inside tiles.
- **Title** (800, `{typography.title.fontSize}`, line-height 1.15, tracking -0.02em): step headings (h3) and the "Before your first consult" heading.
- **Lead** (500, `{typography.lead.fontSize}`, line-height 1.4): the hero's one paragraph, max 52ch.
- **Body** (400, 17px, line-height 1.5): all running text; measure 60ch, with narrower caps per context (38ch aside notes, 46ch step copy, 56ch answers).
- **Small** (600 or 700, 15px): buttons, nav links, the fact row, list items, footer.
- **Meta** (400, 13px): small button, acknowledgement and legal lines.
- **Wordmark**: "ADHDme" set in the same family at 800, 24px (18px in the floating nav), tracking -0.04em, followed by a 0.3em ink dot. No image asset.

### Named Rules
**The One Face Rule.** Plus Jakarta Sans is the only typeface. No mono, no second sans, no eyebrow face.

**The Solid Leading Rule.** Display and headline sit at line-height 1.0; body at 1.5. Do not loosen headings or tighten body.

## Layout

The body has a single page margin (`{spacing.page-margin}`, 8px to 20px) and every section is a tile inside it, separated by `{spacing.gap-tiles}`. Tiles carry their own padding (`{spacing.tile-pad}`, 20px at 390 to 72px at 1440); the two untiled sections ("Before your first consult", footer) reuse the same value as inline padding so their content lines up with the tiles' content.

Inside tiles the recurring grid is a 5/7 split: `minmax(0, 5fr) minmax(0, 7fr)` with a column gap of `clamp(2rem, 6vw, 6rem)`. The left column holds the heading and any note; the right column holds the content list (steps, checklist, questions, footer copy). Above 900px the left column of the steps tile is sticky at `page-margin + 4.5rem`. At and below 899px every 5/7 grid collapses to one column. At and below 599px the in-hero text nav and the floating nav's text links are hidden, leaving wordmark and button.

The hero is a flex column with `min-height: min(100svh - 2 * page-margin, 46rem)`; the bar sits at top, the headline block is pushed to the bottom, and a hairline fact row closes the tile. Spacing runs on a 4px base scale (`{spacing.s-1}` to `{spacing.s-10}`); vertical rhythm between untiled sections is `{spacing.s-9}` on desktop and `{spacing.s-8}` below 900px. `scroll-padding-top` is 5.5rem so anchors clear the floating nav.

## Elevation & Depth

Flat by construction. There are no drop shadows anywhere on the page. Depth is expressed by a tile sitting on the cream ground and by hairlines (1px `{colors.line}`) drawing structure inside the tile. The only `box-shadow` declarations in the stylesheet are inset strokes standing in for borders: a 1.5px `currentColor` ring on the ghost button and a 1px `{colors.line}` ring on the floating nav. The floating nav is the one translucent surface: cream at 82% with `backdrop-filter: blur(14px) saturate(1.2)`.

### Named Rules
**The No Shadow Rule.** Nothing casts. If an element needs an edge, it gets a hairline; if it needs separation, it gets a tile.

## Shapes

One tile radius, pills for controls, circles for marks. Tiles (hero, white sections, the ink close) use `{rounded.tile}` (24px). Buttons, the skip link and the floating nav use `{rounded.pill}`. Numeral discs, FAQ toggles, the wordmark dot and fact-row bullets are true circles. `{rounded.sm}` (10px) appears only on focus outlines and FAQ summaries so the focus ring follows the shape. Borders are 1px hairlines, top-and-bottom on lists (each row `border-top`, last row also `border-bottom`); nothing is boxed on all four sides except by being a tile.

## Components

### Buttons
One shape, three grounds. Inline-flex pill, 700 weight, line-height 1, tracking -0.005em, `gap: 0.6em` before an optional 24-viewBox arrow icon (stroke 2.4, sized 1.05em).
- **Shape:** pill (`{rounded.pill}`), min-height 2.75rem, padding `0.85em 1.5em`, 15px text.
- **Ink (default):** ink fill, white text, yellow arrow. Hover: ink-2 fill, `scale(0.98)`, arrow shifts 3px right. Active: `scale(0.96)`.
- **Yellow:** yellow fill, ink text, ink arrow. Hover: yellow-deep. Used on the ink tile.
- **Ghost:** transparent, ink text, 1.5px inset `currentColor` ring. Hover: 8% ink wash.
- **Sizes:** `--lg` (17px, min 3.25rem, `1em 1.6em`) for hero and close; `--sm` (13px, min 2.25rem, `0.6em 1.1em`) for the floating nav.
- **Transitions:** transform and background 200ms `cubic-bezier(0.32, 0.72, 0, 1)`.

### Wordmark
"ADHDme" in type (800, 24px, -0.04em) with a 0.3em circular dot in `currentColor` after it, raised 0.02em. Small variant 18px. Inherits colour from its ground, so it works on yellow, cream and ink without variants.

### Tiles / Containers
- **Corner Style:** `{rounded.tile}` (24px), all four corners.
- **Background:** white (`.panel--white`), ink with white text (`.panel--ink`), yellow (the hero).
- **Shadow Strategy:** none (see Elevation & Depth).
- **Border:** none.
- **Internal Padding:** `{spacing.tile-pad}` on all sides; the hero uses `s-5` top and `tile-pad` sides; the close tile uses `clamp(4rem, 10vw, 8rem)` block padding.

### Numeral Discs
A 2.25rem yellow circle with the step number in ink, 800 weight, 15px, tracking -0.02em, nudged up 0.1rem to sit on the heading's cap line. Laid out as a `2.25rem 1fr` grid with the step body; each step is separated by a hairline and padded `s-5` block.

### Ink Mark
A single hand-drawn stroke under one phrase in the hero headline. Inline SVG (`viewBox 0 0 400 26`, `preserveAspectRatio="none"`), absolutely positioned at `bottom: -0.18em`, 0.3em tall, 104% wide, filled `currentColor` at 0.94 opacity. On load it wipes in left to right via a `clip-path` animation. Use once per page.

### Floating Nav
A fixed pill at `top: page-margin`, centred, hidden while the hero is in view and slid in once less than 8% of the hero remains. Frosted cream (82%) with blur, 1px hairline ring, 15px 600 text, `s-5` gaps, padding `s-2` all round with `s-5` on the left so the wordmark breathes. Holds the small wordmark, two text links (hidden below 600px) and a small ink button. Text links underline on hover.

### Hero Fact Row
An unordered list at the tile's foot: 15px 700 items with a 0.5em ink bullet, wrapping with `s-2` by `s-6` gaps, a hairline (`{colors.line-on-yellow}`) above.

### Questions (details / summary)
Native `<details>` grouped by `name="faq"` so one opens at a time. Each item is separated by a hairline. Summary: flex row, 700 weight, 17px, min-height 3.5rem, `s-4` block padding, marker removed, followed by a 1.75rem yellow disc drawn with two 2px ink bars (a plus) that rotates 45 degrees to a cross when open, 320ms ease-out. The body animates open with `grid-template-rows: 0fr` to `1fr` over 360ms; answers are `{colors.muted}`, max 56ch, with `s-5` bottom padding when open.

### Checklist
Rows of 600-weight text separated by hairlines, `s-3` block padding, no bullets, no icons.

### Links
Inherit colour. Underline 1.5px, offset 0.22em, drawn at 35% of `currentColor` and rising to full on hover over 200ms.

### Skip Link
Ink pill, white 700 text, top-left, revealed on focus with a yellow focus ring.

## Motion

One vocabulary: arrivals travel down 24px into place on an exponential ease-out.

- **Easing:** `--ease-out: cubic-bezier(0.22, 1, 0.36, 1)` for arrivals, draws and reveals; `--ease-ui: cubic-bezier(0.32, 0.72, 0, 1)` for hover, opacity and control transitions. `--dur: 200ms`, `--dur-arrive: 720ms`.
- **Arrive (hero load):** `opacity 0 to 1`, `translateY(-24px) to 0`, 720ms ease-out, `both` fill, delayed `140ms + i * 90ms` where `--i` is set inline (headline lines 0 and 1, lead 2, actions 3, fact row 4). Runs only when `.js` is on the root.
- **Draw (ink mark):** `clip-path: inset(-20% 100% -20% 0)` to `inset(-20% 0 -20% 0)`, 900ms ease-out, starting at 720ms so it follows the second headline line.
- **Reveal (scroll):** elements with `data-reveal` start at `opacity 0`, `translateY(-16px)`; an IntersectionObserver (threshold 0.25, rootMargin `0 0 -8% 0`) adds `.is-in` once, transitioning opacity 560ms ease-ui and transform 640ms ease-out with a stagger of `i * 80ms`. Applied to the four steps and the two close-tile blocks.
- **Floating nav:** an IntersectionObserver on the hero (threshold 0.08) toggles `.is-on`; the pill slides from `translate(-50%, -24px)` and opacity 0 over 600ms ease-out / 400ms ease-ui, with `visibility` deferred 400ms on the way out.
- **Press:** buttons scale to 0.98 on hover and 0.96 on active; the arrow icon shifts 3px right on hover. FAQ discs rotate 45 degrees; FAQ bodies open via grid rows.
- **Reduced motion:** under `prefers-reduced-motion: reduce`, the base layer clamps every animation and transition to 0.01ms and disables smooth scrolling; the motion layer removes the arrive and draw animations, sets reveals to visible with no transition, and drops the floating nav transition. The script also short-circuits: it marks all reveals `is-in` and shows the floating nav immediately. Without JavaScript (`.no-js`), nothing is hidden and nothing animates.

### Named Rules
**The Down-Into-Place Rule.** Everything that enters does so from 24px above (16px on scroll reveals), settling on `cubic-bezier(0.22, 1, 0.36, 1)`. Nothing slides up, fades in place, or scales in.

## Accessibility

The floor the page is built to:
- Colour: secondary text meets at least 6.3:1 on every ground (`muted` 6.3:1, `muted-on-yellow` 6.7:1, `muted-on-ink` 8.7:1); primary text is ink on light or white on ink.
- Focus: `:focus-visible` draws a 3px ink outline offset 3px with a 10px radius; the skip link's ring is yellow on ink. Nothing removes outlines.
- Targets: buttons, nav links and FAQ summaries are at least 2.75rem tall (summaries 3.5rem).
- Structure: one h1, `<main id="main">` with a skip link, sections labelled by their headings via `aria-labelledby`, lists marked `role="list"` when bullets are removed, decorative SVG and numerals `aria-hidden`, navs named with `aria-label`.
- FAQ is native `<details>`; no custom ARIA disclosure.
- Motion respects `prefers-reduced-motion` in CSS and JS; content is never gated behind an animation.
- `lang="en-AU"`, `color-scheme: light` declared, `text-size-adjust: 100%`, text remains selectable with yellow selection.

## Do's and Don'ts

### Do:
- **Do** put every new section in a tile with `{rounded.tile}` (24px) and `{spacing.tile-pad}`, or in an untiled block that borrows `tile-pad` as inline padding.
- **Do** use the 5/7 grid (`minmax(0, 5fr) minmax(0, 7fr)`, gap `clamp(2rem, 6vw, 6rem)`) for heading-left, content-right sections, collapsing to one column at 899px.
- **Do** separate list rows with 1px `{colors.line}` hairlines, top on every row and bottom on the last.
- **Do** pick secondary text by ground: `muted`, `muted-on-yellow`, `muted-on-ink`.
- **Do** set headings at 800, line-height 1.0, tracking -0.03em (display -0.035em), and body at 17px / 1.5 with a measure of 60ch or less.
- **Do** animate entrances with the arrive vocabulary (24px down, `cubic-bezier(0.22, 1, 0.36, 1)`, 720ms, 90ms stagger) and honour reduced motion.
- **Do** set the wordmark and numerals in type; no logo or icon assets.
- **Do** keep controls as pills with a minimum 2.75rem height.

### Don't:
- **Don't** add box-shadows, drop shadows, glows or gradients, including gradient text.
- **Don't** add eyebrows, uppercase labels or tag pills above headings.
- **Don't** nest cards inside tiles; a tile is the only container.
- **Don't** introduce a second typeface, a mono face, or weights outside 400 to 800.
- **Don't** use emoji or icon fonts; the only glyph is the inline arrow SVG in buttons and the plus in FAQ discs.
- **Do** use photography only as anonymous, uncaptioned imagery: the brand hero over a bottom gradient, and the three tilted white-framed cards. **Don't** show a named person, a patient, a clinician or a testimonial face, and don't add imagery anywhere else; the rest of the page is type on tiles.
- **Don't** use yellow as a text colour or a second accent colour of any hue.
- **Don't** use em-dashes, exclamation marks or ALL CAPS in visible copy.
- **Don't** draw a second ink mark; the stroke under the headline is the page's one gesture.
