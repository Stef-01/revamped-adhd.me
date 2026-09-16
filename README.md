# ADHDme website

Static marketing site: HTML pages styled with a compiled Tailwind stylesheet, shared `site.css` / `site.js`, self-hosted fonts, and locally hosted images in `assets/`.

## Run locally

Requires Node 18 or newer. No install step.

```bash
npm run dev
```

Opens at http://localhost:5173 with live reload (the page refreshes when you save a file). Use `PORT=3000 npm run dev` to change the port, or `npm start` for a plain server without live reload.

## Pages

| File | Page |
| --- | --- |
| `index.html` | Landing |
| `how-it-works.html` | How it works |
| `the-doctors.html` | The Doctors |
| `dr-anubhav-saxena.html`, `dr-anu-saxena.html` | GP profiles (generated) |
| `learn.html` | Learn (micro-modules) |
| `our-story.html` | Our Story |

## Clinician profiles

The GP profile pages are generated from one data set so they stay structurally identical. Edit the `CLINICIANS` list (bio, fees, booking link, articles) in `scripts/build-profiles.py`, then rebuild:

```bash
python3 scripts/build-profiles.py
```

Article thumbnails live in `assets/articles/` and are keyed by the article slug in the `ARTICLES` table.

## Service map

The dotted map of Australia behind the logo on the Our Story page is generated SVG. To add or move a city, edit `CITIES` in `scripts/build-map.py` and rebuild:

```bash
python3 scripts/build-map.py
```

## Blog

The "From the blog" section on Our Story and the individual post pages (`blog-*.html`) are generated from `POSTS` in `scripts/build-blog.py`. Add or edit a post there, then rebuild:

```bash
python3 scripts/build-blog.py
```

## Styles, scripts and fonts

Every page loads one stylesheet and one script bundle:

- `assets/css/site.min.css` is `assets/css/fonts.css` + `site.css` + `motion.css` + `privacy.css` + the compiled Tailwind utilities (`assets/css/tailwind.css`, built from `tailwind.config.js`), in that order, minified. It is linked last in `<head>` so utilities keep winning over each page's inline styles, as they did when the Tailwind CDN injected its CSS at the end of the head.
- `assets/js/site.min.js` is `site.js` + `motion.js` + `analytics.js` + `privacy-consent.js`, minified. `analytics-config.js` stays a separate, unminified file so the analytics ID can be set without a rebuild. The academy login page loads only `site.js` and `motion.js`, on purpose.

Edit the source files, never the bundles, then rebuild:

```bash
npm run build
```

(`npm run build:css` and `npm run build:js` run the halves.) After adding or changing utility classes in any HTML file, the CSS build is required.

Fonts are self-hosted from `assets/fonts/`, one variable file per family: Plus Jakarta Sans (weights 200 to 800, 27 KB, Google's own latin file) and Newsreader (38 KB: Google's variable file instanced to weights 400 to 500 with the optical size pinned at 36, the display sizes this site uses). Both are under the SIL Open Font License. No page requests Google Fonts; the few icons on Our Story and the blog are inline SVG.

Photographs ship as WebP with a JPEG fallback inside `<picture>`, with 320, 640 and full-size candidates where the rendered size warrants it.

## Type scale

One scale, applied as Tailwind classes in the HTML (phone size first, then from the `sm` breakpoint):

| Role | Size | Where |
|---|---|---|
| Landing hero title | 30 → 36 → 60 → 72px | `index.html` only |
| Page title (h1) | 36 → 44 → 52px, line-height 1.05 | every other page; Learn's serif title is 40 → 48px |
| Section heading (h2) | 32 → 40px | all section headings, including Learn's serif ones |
| Subsection heading (h2) | 24px | inside articles, profiles and legal pages |
| Card or step title | 22px, line-height 1.25 | Learn cards, GP deck names, How it works steps |
| Lede | 19px | the paragraph under a page title |
| Body | 17px, line-height 1.6 to 1.7 | paragraphs, lists, definitions |
| Small | 15px | card lines, navigation, buttons, chips' neighbours |
| Label | 14px | chips |
| Caption | 13px | dates, read times, footnotes, the copyright line |

Keep new text on one of these steps. Fee figures (36 → 48px) are display numbers and sit outside the scale on purpose.

## Deploy

It's plain static files: upload the whole folder to Netlify, Vercel, GitHub Pages, Cloudflare Pages, or any web host. GitHub Pages serves `main` as is. A Vercel project is also connected to the repository; `vercel.json` tells it the output is the repository root and that there is nothing to build, because the bundles are committed (without it Vercel runs `npm run build` and then fails looking for a `public` folder).

## Analytics, attribution and privacy (ported from `Stef-01/ADHD`)

- `analytics.js` carries the closed event taxonomy: `landing-viewed`, `landing-cta` (five named controls), `deck-viewed`, `profile-viewed`, `booking-outbound`. Every event and property value is checked against the declaration; anything else is refused and logged as `analytics-refused`. Nothing is sent anywhere until `analytics-config.js` carries a GA4 ID; when it does, events go cookieless with advertising signals off, and `privacy.html`'s "Cookies and local storage" section must be updated the same day.
- Attribution: every Healthengine link gets `utm_source=adhd-me&utm_medium=referral&utm_campaign=<surface>` at click time, a `booking-outbound` event, and a row in this device's local tally (clinician, surface, day; never identifying). Sending never delays the click. `measurement.html` lists the channels and what cannot be observed (whether a booking followed).
- Privacy: `privacy-consent.js` shows the notice bar on first arrival, with the dialog's three sentences lifted from the policy; the agreement is one value in local storage. `privacy.html`, `terms.html` and `automated-decisions.html` are the source's pages rewritten for what is true of this static site (GitHub Pages, no forms, no database, no recall engine). Footer links point at them.
