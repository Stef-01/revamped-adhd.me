# revamped-adhd.me

The site for ADHDme, an ADHD assessment service for adults in Australia. Static HTML, no build step, no dependencies beyond a Google Fonts stylesheet.

- **GitHub Pages:** https://stef-01.github.io/revamped-adhd.me/ (serves `main` / root)
- **Current app (unchanged):** https://adhdme.vercel.app, repo `Stef-01/adhd.me`

## What is here

```
index.html            the landing page. Semantic HTML, the direction contract as the first comment in <body>
book/                 "Where are you?" the state picker; the one action every Book button leads to
states/<code>/        the GPs in that state (NSW), or "No GPs in X yet" with the GP invitation (the other seven)
network/<id>/         one page per GP: their own match line, experience, about, details, disclosure, booking
sitemap.xml, robots.txt
assets/css/site.css   the whole stylesheet, in cascade layers: tokens, base, components, sections, motion
assets/js/site.js     30 lines: floating nav arrival, step reveals, reduced-motion opt-out
assets/img/           hero.jpg (1376px) and card-1..3.jpg (896px), the only images on the page
PRODUCT.md            product truth the copy was written from, with every undecided fact recorded
DESIGN.md             the visual system as built (tokens, type, tiles, motion vocabulary)
.nojekyll             tells GitHub Pages to serve the tree as-is
.claude/launch.json   local preview config
```

Four photographs ship under `assets/img/`: the brand hero (the founder-approved "ADHD me." image from the original design) and three candid photographs generated in the Stitch project. None is captioned or presented as a patient, clinician or staff member, and none carries a name.

The "Allied care" section lists the professions around the clinician, with each description taken verbatim from the `adhd.me` app's profession vocabulary (`src/support/professions.ts`). It names kinds of support, never individual providers: the allied providers in that app are example profiles.

## The booking flow

Book now → choose your state → the GPs there → Book (the practice's own Healthengine page). A GP's name opens their profile for anyone who wants to read first. Every string about a doctor is their own declaration from the `adhd.me`/`ADHD` roster; the deck shows the three declarations that tell the two GPs apart, never the one they share.

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
