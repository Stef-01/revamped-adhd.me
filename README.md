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

To add a clinician: add the entry, the six portrait files, a `sitemap.xml` line, the clinician in `analytics.js`, and `::view-transition-group(portrait-<id>)` in `site.css`, then rebuild. The script refuses to write until all of those are in place, until `index.html` still carries the count region, and until the category's panel on `the-doctors.html` has a `<ul>` to hold the card (the "Expected soon" placeholder for a new category is replaced by hand once; the error message gives the markup). A brand-new category also needs its tab button beside the others and its name in the `categories` array in `the-doctors.html`’s script, or the tab will not switch to it.

Two fields carry more than they look like:

- `telehealth` is a bool, and the only thing that draws the telehealth pill. The pill is one fixed marker — same icon, same wording, always first in the chip row, on the deck card and the profile — so "can I be seen remotely?" is answered by scanning `the-doctors.html` rather than opening every profile. Set it from what the clinician actually declares; `dr-anu-saxena` is `False` because she declares practice appointments only.
- `fees['figures']` may be empty, for a clinic that does not publish a fee. The figure row is then skipped and the `notes` carry the explanation instead. Don't fill it with an estimate: the whole point of the section is that the number is settled before the appointment, and a wrong number is worse than an honest "the clinic quotes it when you book". GOALS Psychology is the current example, and its Medicare wording differs by registration, so there are three note sets (`GOALS_FEES`, `GOALS_FEES_PROVISIONAL`, `GOALS_FEES_OT`) rather than one.

## Service map

The hand-drawn map of Australia on the Our Story page is generated SVG: a sketched, double-inked coastline with pencil hatching, and a looped dot for each city. The drawing is seeded, so it is identical on every build. To add or move a city, edit `CITIES` in `scripts/build-map.py` and rebuild:

```bash
python3 scripts/build-map.py
```

## Blog

The "From the blog" section on Our Story and the individual post pages (`blog-*.html`) are generated from `POSTS` in `scripts/build-blog.py`. Add or edit a post there, then rebuild:

```bash
python3 scripts/build-blog.py
```

`python3 scripts/build-blog.py --check` exits non-zero and names any page on disk that differs from what the data would produce. Run it before committing a hand edit to Our Story's blog section or a post page, because the next build overwrites them; the fix is to move the edit into `POSTS`.

Four fields per post are worth knowing:

- `title` is the headline, on the card and as the page's `<h1>`, with its terminal punctuation.
- `seo` is the same headline for `<title>`, `og:title` and `twitter:title`, without the trailing full stop and phrased to read as a link. Each post page starts from Our Story's `<head>` and rewrites every tag that names the page, so a post cannot ship Our Story's title, description and canonical URL to crawlers and share cards.
- `description` is the meta and share-card description. It is not the opening line of the post; write it for someone deciding whether to click.
- `hook` is the short line under the title on a card, and the lede on the post page itself. Aim for four or five words.

Cards come in two shapes, on purpose. On Our Story they carry no chrome — image, title, hook — matching the Learn tiles. The "More from the blog" pair at the foot of a post keeps its box, because there it is a genuine aside rather than the page's own content. Icons are inline SVG; this site ships no icon font.

### The invitation dialog

`newsletter-invite.js` offers ADHDme Weekly once, in a native `<dialog>`, and only to somebody who
has shown they are reading: a minute of attention counted only while the page is actually visible,
fifteen clicks, or the foot of a page — whichever comes first. The evidence is that time-only
triggers underperform; an engagement gate filters out the drive-by traffic that was never going to
subscribe.

It stays away from the policy pages, from anyone who has already dismissed it, from the first visit
until the privacy notice is answered, and from anyone who has scrolled a signup form into view —
they have had the offer without being interrupted for it. Dismissal is one value in `localStorage`
and it is permanent.

It uses the **footer** beehiiv form rather than the primary one, with `utm_content=popup`. That
form's button reads `Join`, which is what fits beside the field once the dialog's padding comes out
of a phone's width; the longer label only repeats the heading anyway.

`newsletter-invite` events record `shown` and `dismissed` with what triggered them. Whether anybody
subscribed is beehiiv's to answer — that is what `utm_content=popup` is for.

## Search pages

The pages that answer a high-intent search (ADHD doctor Gold Coast, ADHD GP Brisbane, ADHD assessment Queensland, ADHD treatment after diagnosis, ADHD exercise physiologist, ADHD psychologist, and so on) are generated from `PAGES` in `scripts/build-seo-pages.py`, along with `adhd-services.html`, the index that links them. Edit the data there, then rebuild:

```bash
python3 scripts/build-seo-pages.py
```

`python3 scripts/build-seo-pages.py --check` exits non-zero and names any page on disk that differs from what the data would produce. Run it before committing a hand edit to one of those pages, because the next rebuild overwrites them; the fix is to move the edit into the data.

They are kept out of the way on purpose: not in the header, not in the mobile menu. The one route to them from the rest of the site is the "ADHD care near you" link in every footer, which points at `adhd-services.html`; that link is what stops them being orphans a crawler never reaches. Each page carries a breadcrumb, an FAQ with `FAQPage` JSON-LD, and links to its neighbours, and every one is in `sitemap.xml` and named `service` in `analytics.js`.

Three things keep them honest. The clinician lists are selected from `CLINICIANS` in `scripts/build-profiles.py` by discipline, state and telehealth, so a page cannot name a clinician the network does not have, and a page whose filter matches nobody refuses to build. The fee figures are the same constants the profiles use. And where the network has nothing for the query yet (an exercise physiologist, a Gold Coast clinician, a Brisbane GP), the page says so in the first screen and points at what exists, rather than implying otherwise. The page shell is lifted from `how-it-works.html` at build time, so header and footer changes reach these pages on the next rebuild.

## Care navigator

`care-navigator.html` is a two-level bubble map: pick where ADHD gets in the way (School, Work, Home, Relationships, Health), then the part of it, and the clinicians whose profiles say they work on exactly that appear underneath. It is generated from `DOMAINS` in `scripts/build-navigator.py`; edit the tree there and rebuild:

```bash
python3 scripts/build-navigator.py
```

`--check` exits non-zero if the page on disk differs. Each clinician under an aspect is named by id with the reason quoted from their own profile (a chip or an experience line), and the build refuses an id that is not in `CLINICIANS`, so the map cannot claim a focus a profile does not declare. Every result panel is in the HTML; the page's own script only chooses which one shows and where the bubbles sit, and with JavaScript off the whole tree reads as a list. It has its own item in the header, Navigator, and the landing page also links to it under "Four ways in".

## Styles, scripts and fonts

Every page loads one stylesheet and one script bundle:

- `assets/css/site.min.css` is `assets/css/fonts.css` + `site.css` + `motion.css` + `privacy.css` + the compiled Tailwind utilities (`assets/css/tailwind.css`, built from `tailwind.config.js`), in that order, minified. It is linked last in `<head>` so utilities keep winning over each page's inline styles, as they did when the Tailwind CDN injected its CSS at the end of the head.
- `assets/js/site.min.js` is `site.js` + `motion.js` + `analytics.js` + `privacy-consent.js` + `newsletter-invite.js`, minified. `analytics-config.js` stays a separate, unminified file so the analytics ID can be set without a rebuild. The academy login page loads only `site.js` and `motion.js`, on purpose.

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

## Clinical Academy: training by discipline

The six discipline tracks in `academy.html` (general practice, psychology, occupational therapy, exercise physiology, nutrition, naturopathy) are generated. Each is one 10-minute module: at most 6 minutes of learning (2-minute lessons, plus a 2-minute visual map where a scene exists) and 4 minutes of knowledge checks. The builder enforces both caps. Edit `scripts/academy_tracks_content.py`, then rebuild:

```bash
python3 scripts/build-academy-tracks.py
```

## Deploy

It's plain static files: upload the whole folder to Netlify, Vercel, GitHub Pages, Cloudflare Pages, or any web host. GitHub Pages serves `main` as is. A Vercel project is also connected to the repository; `vercel.json` tells it the output is the repository root and that there is nothing to build, because the bundles are committed (without it Vercel runs `npm run build` and then fails looking for a `public` folder).

## Analytics, attribution and privacy

The question this setup exists to answer: **who is on the site, and how many of them clicked through to book with each psychologist, allied health clinician, GP or coach.** PostHog holds the people, the closed taxonomy in `analytics.js` holds the events, and `scripts/posthog-dashboard.py` builds the tiles that read them back.

### Switching it on

1. In PostHog, copy the **project API key** (`phc_…`) from Settings → Project. It is meant to be public; it only lets a browser write events.
2. Put it in `analytics-config.js` — that file stays unminified and outside the bundle on purpose, so a key can be set on the live site without a rebuild:

   ```js
   window.ADHDME = { posthogKey: 'phc_…', posthogHost: 'https://us.i.posthog.com', /* … */ };
   ```

3. Build the dashboard. This needs a **personal** API key (`phx_…`, Settings → Personal API keys, read+write), which never goes near the browser:

   ```bash
   export POSTHOG_PERSONAL_API_KEY=phx_…
   export POSTHOG_HOST=https://us.posthog.com     # the app host, not the ingestion host
   python3 scripts/posthog-dashboard.py           # --dry-run prints every payload and sends nothing
   ```

4. Update `privacy.html`'s "Cookies and local storage" section and `measurement.html`'s channel list the same day if what is counted has changed.

`gaId` still works alongside it: set a GA4 measurement ID and the same declared events go there too, cookieless and with advertising signals off. Leave every key empty and events are still validated and then dropped — no request leaves the page.

### Seeing each person

`posthogPersonProfiles: 'always'` gives every browser a person row, so PostHog's Persons list has somebody in it without this site ever calling `identify()`. Each row carries a random label (`Visitor 3f9a21`), when it first arrived and what referred it, how many profiles it has read, how many booking links it has followed, and who the last one was for. No name, no email, nothing typed into anything — there is nothing on these pages to type into. Session replay is off by default, deliberately; turning it on is a decision, not a default.

`scripts/posthog-dashboard.py` also creates cohorts, which are the literal "show me each person" lists: everybody who clicked a booking link, everybody who did that for a psychologist, for allied health, for a GP, for a coach, and everybody who read a profile and did not book. It is idempotent — it matches insights and cohorts by name and updates them in place, so re-running it after editing the tile list never leaves a second copy behind.

### The taxonomy

`analytics.js` declares every event and every property value. Anything else is refused and logged as `analytics-refused` rather than becoming a row that looks real. `?debug=analytics` on any page prints both to the console.

| Event | Says |
|---|---|
| `page-viewed` | which page of the site was opened |
| `landing-viewed` | somebody arrived at the front door |
| `landing-cta` | which named control was pressed (the header's four, the landing page's doors) |
| `deck-viewed` | The Network was opened, and how many cards it held |
| `deck-card-opened` | which clinician card was pressed, and their discipline |
| `profile-viewed` | whose page, their discipline, their practice, which surface they came from |
| `booking-outbound` | who they went to book with, their discipline, their practice, where the link lands, which surface, and which named link |

### Expertise, and what the network is short of

Each clinician in the `analytics.js` registry carries `expertise` and `ages` alongside their discipline and practice, derived from the `chips` and `experience` in `scripts/build-profiles.py`. They ride along on `profile-viewed`, `booking-outbound` and `profile-engaged` as lists, so a breakdown counts a clinician once under each thing they are sought for. The point is the gap: *What the network is asked for* reads how many people opened somebody with a given expertise against how many went on to book, and a wide gap there is a discipline the network is thin on rather than a page that reads badly. Keep the two registries in step when a clinician's focus changes.

### Where a visit came from, and which post produced it

Tag anything you publish: `?utm_source=<channel>&utm_campaign=<theme>&utm_content=<post>`. The channel and theme are closed vocabularies in `analytics.js`, so a dashboard reads words the team agreed on and an unrecognised one lands as `other` rather than breaking the row. The post is a token — validated as a short lowercase slug, but not a fixed list, because posts are made faster than code is deployed. An untagged visit still gets a channel, inferred from the referrer.

The tag is held in `sessionStorage` for the length of the visit, so a booking three pages later is still credited to the post that started it rather than to the last internal link. *Which post produced the handoff* and *Content theme against bookings, by week* are the two tiles that read it back.

### The SQL tiles

Trends answer "how many". The questions with a ratio or a join in them are HogQL tiles in `scripts/posthog-dashboard.py`: the clinician scorecard, who is starved of referrals, what the network is asked for, and who read the fee table and left anyway. Two things to know if you edit them: every property comes out of the store as a string, so a number needs `toFloat()` before `avg`; and a list property is a JSON string in a nullable column, so it needs `JSONExtract(ifNull(properties.x, '[]'), 'Array(String)')` rather than going straight into `arrayJoin`.

The clinician, discipline, practice and destination vocabularies are generated from the registry at the top of `analytics.js`, so a dashboard cannot show a clinician this site does not have. `scripts/build-profiles.py --check` refuses to build a profile page that registry does not declare. Adding a clinician means adding them in both places.

A page that grows a second booking link should mark it with `data-booking-link="<name>"` and add that name to `BOOKING_LINKS`; otherwise the link is attributed to the page it sits on (`profile-cta` on a profile, `deck-card` on The Network).

### Attribution

Every booking link (Healthengine, Halaxy, or a clinic's own page, as declared per clinician) gets `utm_source=adhd-me&utm_medium=referral&utm_campaign=<surface>&utm_content=<clinician>` rewritten onto it at click time, so the practice can see the referral from their own side. Sending never delays the click: the browser follows the link immediately and the event travels on its own. Each handoff also lands in a local tally in that browser's storage (clinician, discipline, practice, surface, day), which `measurement.html` reads back and which never leaves the device.

### Privacy and the opt-out

`privacy-consent.js` shows the notice bar on first arrival, with the dialog's sentences lifted from the policy; the agreement is one value in local storage, and pressing Agree dispatches `adhdme-privacy-ack` on `window`. Setting `requireConsent: true` in `analytics-config.js` holds every sink until that moment, queueing events meanwhile and flushing them in order on agreement, so a gated first visit is not lost. It ships `false`, which is how the bar reads today.

The opt-out is real and works either way: a button on `measurement.html`, `?analytics=off` on any page, or a browser sending Global Privacy Control, which is honoured without being asked and cannot be overridden from the page. Opting out stops PostHog and GA on that device; the practice's own reporting is the practice's to run.

`privacy.html`, `terms.html` and `automated-decisions.html` are the source's pages rewritten for what is true of this static site (no forms, no database, no recall engine). Footer links point at them. `measurement.html` lists every channel, what each one holds, and what cannot be observed from here — whether a booking actually followed, which neither Healthengine nor Halaxy nor a clinic form will tell a third party.
