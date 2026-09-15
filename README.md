# revamped-adhd.me

The landing page for ADHDme, an ADHD assessment service for adults in Australia. One static page, no build step, no dependencies beyond a Google Fonts stylesheet.

- **GitHub Pages:** https://stef-01.github.io/revamped-adhd.me/ (serves `main` / root)
- **Current app (unchanged):** https://adhdme.vercel.app, repo `Stef-01/adhd.me`

## What is here

```
index.html            the page. Semantic HTML, the direction contract as the first comment in <body>
assets/css/site.css   the whole stylesheet, in cascade layers: tokens, base, components, sections, motion
assets/js/site.js     30 lines: floating nav arrival, step reveals, reduced-motion opt-out
PRODUCT.md            product truth the copy was written from, with every undecided fact recorded
DESIGN.md             the visual system as built (tokens, type, tiles, motion vocabulary)
.nojekyll             tells GitHub Pages to serve the tree as-is
.claude/launch.json   local preview config
```

No images ship. The page is typographic by design: the only photographs available were AI-generated people, which a health service cannot present as patients or staff.

## Local preview

```bash
python3 -m http.server 4173
```

Then open http://localhost:4173/.

## Deployment

GitHub Pages from `main`, root. Any push republishes; there is no workflow and no build. Vercel or Netlify also work with no build command and `.` as the output directory.

## Where the copy comes from

Every visible sentence traces to a source in `PRODUCT.md`: the 2026 film content inventory and studio script (the provider pathway, the format promise, the age rule, the AHPRA and state-variation lines, the crisis numbers, the two end lines), the `adhd.me` app (the no-referral fact, the Acknowledgement of Country, the writing rules) or the founder's direction on 2026-09-15 (this page describes the assessment service, not a membership and not the GP finder).

Lines that still need a clinician's sign-off before launch, because their source is marked as a clinician draft:

- "There is no blood test and no scan. The assessment is your history, taken properly."
- "There is no test you can fail, and nothing you need to prepare an argument for."
- The "Before your first consult, find:" list.

## Deliberately not on the page

| Left out | Why |
|---|---|
| A price, a wait time, a clinician count, a state list | none is confirmed in any source; the film briefs say to explain the shape, never a figure |
| Testimonials, ratings, named clinicians, team | prohibited for a regulated health service (Ahpra advertising guidelines, s 133 National Law); the team page is gated by the founder |
| A booking button or waitlist form | no booking system or form endpoint exists yet, so the action is `mailto:info@adhdme.au`, the one public address |
| A legal entity in the footer | which entity is named is with counsel |
| `robots` indexing | `noindex, nofollow` stays on until the Ahpra review of the name lands; delete the meta tag in `index.html` to open it |
| Privacy and terms links | the drafts on the live app describe the finder, not this service; add links once counsel returns the new documents |

## Design reference

The visual system borrows its discipline from kina.co (one 24px tile radius, no drop shadows, a single spring-like arrival for motion, a floating nav that appears once the hero has gone) and nothing of its brand, imagery or membership framing. The measured teardown that informed it is kept outside the repo.
