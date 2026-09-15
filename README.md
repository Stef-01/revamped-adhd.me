# revamped-adhd.me

The ground-up rebuild of [ADHD.ME](https://github.com/Stef-01/adhd.me). This repository now holds the
**new landing page** (`index.html`) and the design system extracted from it (`DESIGN.md`). It is still a
static site: one HTML file, no build step.

- **GitHub Pages:** https://stef-01.github.io/revamped-adhd.me/ (serves `main` / root)
- **Current site (unchanged):** https://adhdme.vercel.app — repo `Stef-01/adhd.me`

## What is here

```
index.html            the landing page — Tailwind (Play CDN) + Plus Jakarta Sans / Space Grotesk (Google Fonts)
DESIGN.md             the design system extracted from the page: colours, type scale, shape, elevation,
                      spacing, components, motion — also loaded into the Stitch project below
.nojekyll             tells GitHub Pages to serve the tree as-is
.claude/launch.json   preview config (python http.server on 4173)
```

## Local preview

No tooling needed — open `index.html` in a browser, or:

```bash
python -m http.server 4173
```

## Deployment

GitHub Pages, serving `/` from the `main` branch. Any push to `main` republishes; there is no workflow
and no build. (Pages on a **private** repository requires GitHub Pro; on Free it is unpublished when the
repo goes private.)

Pages settings: **Settings → Pages → Source: Deploy from a branch → `main` / `/ (root)`**.

Vercel / Netlify also work: import the repo, no build command, output directory `.`.

## Stitch design project

Redesign screens are generated in Google Stitch against the design system in `DESIGN.md`, then ported
into `index.html` by hand.

- Project **ADHD Landing Site redesign** — `projects/8849238073950735440`
- Design system **ADHDme Brand** — `assets/13123093908323446532` (built from `DESIGN.md`)
- First generated screen **ADHDme Desktop Landing Page** — `screens/b1518fdf91fe4d4d8d9d3008c4241ab0`
- MCP endpoint `https://stitch.googleapis.com/mcp`, auth via `X-Goog-Api-Key`. The key is **not** in
  this repo; it lives in the local Claude Code MCP config.

## Deliberately not done / needs a decision

These are founder or legal calls, carried over from the placeholder. Each is a small, isolated change
when you want it:

| Left out | Why | To enable |
|---|---|---|
| `noindex, nofollow` is **on** | kept from the placeholder so the page does not rank on ADHD terms before the Ahpra advertising review of the name | delete the `robots` meta in `index.html` |
| Waitlist form does not submit | the form is visual only (`onsubmit` prevents default); collecting an address is a privacy-policy and data-handling decision | wire a form endpoint and add a privacy notice |
| Copy and figures are unreviewed | "Join thousands of adults with ADHD", "The Doctors", the member names/photos and stats are design placeholders, not confirmed figures | review every claim before going public |
| `CNAME` for the `adhd.me` apex | would repoint live DNS away from the current site | add a `CNAME` file plus the DNS records, once you want the cutover |
| A licence | the `adhd.me` tree carries none; adding one here is a legal choice | add `LICENSE` |

The footer keeps the line that the page is not a health service and offers no assessment, advice,
directory or booking. Keep it for as long as the page is public and the name review is open.

## Known caveats

- Image `src` URLs point at Stitch-generated assets on `lh3.googleusercontent.com`; they are not
  guaranteed to be permanent. Move the images under `assets/` before launch.
- Tailwind is loaded from the Play CDN — fine for previews, replace with a compiled stylesheet for
  production.
- The "Join Us" button still carries the legacy purple `bg-[#8C52FF]` class, overridden inline by
  yellow; clean it up when moving to compiled CSS.
