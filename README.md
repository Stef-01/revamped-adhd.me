# revamped-adhd.me

The ground-up rebuild of [ADHD.ME](https://github.com/Stef-01/adhd.me). Right now this repository
holds a **placeholder page only** — no product code has been ported across.

- **Live placeholder:** https://stef-01.github.io/revamped-adhd.me/
- **Current site (unchanged):** https://adhdme.vercel.app — repo `Stef-01/adhd.me`

## What is here

```
index.html    the whole placeholder: one file, no build step, no dependencies, no network requests
.nojekyll     tells GitHub Pages to serve the tree as-is
```

The page uses the platform's blue palette from `adhd.me/DESIGN.md` (paper `#F7F8FC`, ink `#172033`,
blue `#4C5F9C`, the `#D47839`→`#6679B9` signature band as a 4px rule), the brand's serif for the
wordmark with a system fallback so nothing is fetched, a dark-mode variant, and a focus ring on the
one link.

## Deployment

GitHub Pages, serving `/` from the `main` branch. Any push to `main` republishes; there is no
workflow and no build.

Pages settings: **Settings → Pages → Source: Deploy from a branch → `main` / `/ (root)`**.

## Deliberately not done

These are founder or legal calls, and a placeholder should not answer one on your behalf. Each is a
small, isolated change when you want it:

| Left out | Why | To enable |
|---|---|---|
| Any clinical claim, figure, wait time or cost | `adhd.me/README.md` records that every public figure is indicative and unconfirmed, and that the **name itself** needs an Ahpra advertising review | write the copy once the review lands |
| `noindex, nofollow` is **on** | so a placeholder does not start ranking on ADHD terms before that advertising review | delete the `robots` meta in `index.html` |
| Email / waitlist capture | collecting an address is a privacy-policy and data-handling decision | needs a form endpoint and a privacy notice |
| `CNAME` for the `adhd.me` apex | would repoint live DNS away from the current site | add a `CNAME` file plus the DNS records, once you want the cutover |
| A licence | the `adhd.me` tree carries none; adding one here is a legal choice | add `LICENSE` |

The footer states the page is not a health service and offers no assessment, advice, directory or
booking. Keep a line to that effect for as long as the page is public and the name review is open.

## Local preview

No tooling needed — open `index.html` in a browser, or:

```bash
python -m http.server 4000
```
