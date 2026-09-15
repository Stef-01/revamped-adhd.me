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
| `dr-anubhav-saxena.html` | Clinician profile |
| `learn.html` | Learn (micro-modules) |
| `our-story.html` | Our Story |

## Deploy

It's plain static files: upload the whole folder to Netlify, Vercel, GitHub Pages, Cloudflare Pages, or any web host.
