# ADHDme website

Static marketing site: six HTML pages styled with Tailwind (CDN), shared `site.css` / `site.js`, and locally hosted images in `assets/`.

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

## Deploy

It's plain static files: upload the whole folder to Netlify, Vercel, GitHub Pages, Cloudflare Pages, or any web host.

## Analytics, attribution and privacy (ported from `Stef-01/ADHD`)

- `analytics.js` carries the closed event taxonomy: `landing-viewed`, `landing-cta` (five named controls), `deck-viewed`, `profile-viewed`, `booking-outbound`. Every event and property value is checked against the declaration; anything else is refused and logged as `analytics-refused`. Nothing is sent anywhere until `analytics-config.js` carries a GA4 ID; when it does, events go cookieless with advertising signals off, and `privacy.html`'s "Cookies and local storage" section must be updated the same day.
- Attribution: every Healthengine link gets `utm_source=adhd-me&utm_medium=referral&utm_campaign=<surface>` at click time, a `booking-outbound` event, and a row in this device's local tally (clinician, surface, day; never identifying). Sending never delays the click. `measurement.html` lists the channels and what cannot be observed (whether a booking followed).
- Privacy: `privacy-consent.js` shows the notice bar on first arrival, with the dialog's three sentences lifted from the policy; the agreement is one value in local storage. `privacy.html`, `terms.html` and `automated-decisions.html` are the source's pages rewritten for what is true of this static site (GitHub Pages, no forms, no database, no recall engine). Footer links point at them.
