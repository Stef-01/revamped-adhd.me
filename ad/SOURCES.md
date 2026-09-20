# Sources and licences

Nothing in this film is borrowed artwork. Every mark is drawn at render time by
the code in this folder, and the score is synthesised from oscillators and
generated noise. There are no photographs, no video, no stock illustration, no
sampled audio and no third-party imagery of any kind.

## Typeface

**Plus Jakarta Sans** (variable, latin subset) — SIL Open Font License 1.1.
Copied from the site's own `assets/fonts/plus-jakarta-sans-latin.woff2` and
inlined as a base64 data URL in `fonts.js`, so the film renders identically on
any machine and the canvas is never tainted by a cross-origin request. The OFL
permits embedding; the font is not sold or distributed on its own here.

## Copy

Every line of text in the film is ADHDme's own wording, taken from `index.html`
in this repository. See the table in `README.md` for line-by-line provenance.
No claim in the film goes beyond what the site already states.

`adhdme.au` on the end card comes from the site's contact address,
`info@adhdme.au`.

## Engine

`core.js`, `studio.js`, `cels.js`, `materials.js`, `render.mjs` and
`package.json` are unmodified copies from the `hand-drawn-canvas-animation`
skill vendored at `.claude/skills/hand-drawn-canvas-animation/`, which in turn
came from `alesha-pro/tools`. Runtime dependency: `puppeteer-core` (Apache-2.0),
used only by the offline renderer.

## Score

`score.js` is original, written for this cut. It is generated live through Web
Audio — oscillators, an impulse response built from seeded noise, and a noise
buffer for the clock tick and the breaths. Nothing is sampled or licensed.

## The person in the film

The woman is an invented character drawn from an authored skeleton. She is not
a likeness of any real person, and she is not any practitioner in the network.
