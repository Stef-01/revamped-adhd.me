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
| `dr-anubhav-saxena.html`, `dr-anu-saxena.html`, `dr-maya-lin.html`, `julian-vance.html`, `sarah-jenkins.html`, `claire-brennan.html` | Clinician profiles (generated) |
| `learn.html` | Learn (micro-modules) |
| `our-story.html` | Our Story |

## Clinician profiles

The six profile pages are generated from one data set so they stay structurally identical. Edit the `CLINICIANS` list (bio, fees, booking link, articles) in `scripts/build-profiles.py`, then rebuild:

```bash
python3 scripts/build-profiles.py
```

Article thumbnails live in `assets/articles/` and are keyed by the article slug in the `ARTICLES` table.

## Service map

The dotted map of Australia behind the logo on The Doctors page is generated SVG. To add or move a city, edit `CITIES` in `scripts/build-map.py` and rebuild:

```bash
python3 scripts/build-map.py
```

## Deploy

It's plain static files: upload the whole folder to Netlify, Vercel, GitHub Pages, Cloudflare Pages, or any web host.
