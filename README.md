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
| `index.html` | Landing (the practitioner count is generated — see below) |
| `how-it-works.html` | How it works |
| `the-doctors.html` | The Network (the file name predates the rename) |
| `<slug>.html`, one per entry in `CLINICIANS` | Clinician profiles (generated) |
| `learn.html` | Learn (micro-modules) |
| `our-story.html` | Our Story |

## Clinician profiles

One profile page per entry in `CLINICIANS`, plus the cards inside each category panel on `the-doctors.html` and the practitioner count on the landing page, are generated from one data set, so they stay structurally identical and cannot drift apart as the network grows. Edit `CLINICIANS` in `scripts/build-profiles.py` (plain-text fields; the script escapes them), then rebuild:

```bash
python3 scripts/build-profiles.py
```

`python3 scripts/build-profiles.py --check` exits non-zero and names any generated page on disk that differs from what the data would produce. Run it before committing a hand edit to one of those pages, because the next rebuild overwrites them; the fix is to move the edit into the data.

The page shell (head, header, footer) is `scripts/profile-shell.html`, with `{{TOKENS}}` the script fills in. Portraits are square JPEG and WebP at 320, 640 and full size in `assets/clinicians/` (`<id>.jpg`, `<id>-640.jpg`, `<id>-320.jpg` and the `.webp` equivalents); the full size is read from the file, so `srcset` descriptors and the og:image size cannot go stale.

On `index.html` the script owns exactly one thing: the practitioner count, between a `<!-- BEGIN:GENERATED count-all -->` / `<!-- END:GENERATED count-all -->` pair. The landing page routes people to a door; it deliberately does not list the network, so there is no roster to keep in step. Everything else on that page is left alone.

To add a clinician: add the entry, the six portrait files, a `sitemap.xml` line, the clinician in `analytics.js`, and `::view-transition-group(portrait-<id>)` in `site.css`, then rebuild. The script refuses to write until all of those are in place, until `index.html` still carries the count region, and until the category's panel on `the-doctors.html` has a `<ul>` to hold the card (the "Expected soon" placeholder for a new category is replaced by hand once; the error message gives the markup).

Two fields carry more than they look like:

- `telehealth` is a bool, and the only thing that draws the telehealth pill. The pill is one fixed marker — same icon, same wording, always first in the chip row, on the deck card and the profile — so "can I be seen remotely?" is answered by scanning `the-doctors.html` rather than opening every profile. Set it from what the clinician actually declares; `dr-anu-saxena` is `False` because she declares practice appointments only.
- `fees['figures']` may be empty, for a clinic that does not publish a fee. The figure row is then skipped and the `notes` carry the explanation instead. Don't fill it with an estimate: the whole point of the section is that the number is settled before the appointment, and a wrong number is worse than an honest "the clinic quotes it when you book". GOALS Psychology is the current example, and its Medicare wording differs by registration, so there are three note sets (`GOALS_FEES`, `GOALS_FEES_PROVISIONAL`, `GOALS_FEES_OT`) rather than one.

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

**Do not run it yet.** Its templates have fallen behind the pages on disk: the cards on Our Story and the post pages were refined by hand after the last build, and the script still holds the older markup, so running it reverts all four pages. Reconcile the templates in `scripts/build-blog.py` with the current `our-story.html` and `blog-*.html` first, then rebuild and check the diff is only what you meant to change. Until then, edit those pages directly. (`build-profiles.py` has a `--check` mode that catches exactly this; `build-blog.py` does not yet.)

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
| Landing hero title | 32 → 40 → 56 → 64px | `index.html` only. The marked phrase is pinned to one line (`motion.css`), so the type has to fit the column rather than overflow it; under 380px the mark unpins and wraps. |
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
- Attribution: every booking link (Healthengine, or a clinic’s own booking page, as declared per clinician in `analytics.js`) gets `utm_source=adhd-me&utm_medium=referral&utm_campaign=<surface>` at click time, a `booking-outbound` event, and a row in this device's local tally (clinician, surface, day; never identifying). Sending never delays the click. `measurement.html` lists the channels and what cannot be observed (whether a booking followed).
- Privacy: `privacy-consent.js` shows the notice bar on first arrival, with the dialog's three sentences lifted from the policy; the agreement is one value in local storage. `privacy.html`, `terms.html` and `automated-decisions.html` are the source's pages rewritten for what is true of this static site (GitHub Pages, no forms, no database, no recall engine). Footer links point at them.
