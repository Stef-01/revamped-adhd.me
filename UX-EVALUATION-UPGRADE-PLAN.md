# UX Evaluation v1 → Phased Upgrade Plan

Source: *ADHDme Web App Evaluation v1* (6 pages, 13 findings across Homepage, How it works, Learn,
Our Story, The Network and the profile pages). Every finding was checked against this repo at
`84b50f3` and, where it mattered, against the live site on 2026-09-21. Nothing here is taken on
the evaluator's word alone; where the code disagrees with the evaluation, or shows something the
evaluation missed, that is said.

## Status (2026-09-21)

Shipped: 1.2–1.6, Phase 2 (labels are **Book** / **Enquire**, driven by `books_online()` in
`build-profiles.py`; each list on The Network puts online diaries first, by order alone), 3.1, 3.3, 3.4,
5.1, 5.2 (Featured deleted: every section fits one row, so any Featured card was a repeat), 5.3 (a quiet
text link on Learn rather than a footer link on every page).
Staged, needs one click: 1.1. Cause found: both beehiiv forms had `form_field_height: 0px` and a unitless
`form_width: 400`, so field and button collapsed to 26px. Corrected values are saved as **drafts**;
publish each from its beehiiv form editor.
Also shipped: 0.2 (`python scripts/check-site.py`: stray attribute text, dead internal links, a second
typeface, Book/Enquire honesty and ordering; proven against the original X-03 markup) and 5.4 (the map and
the list under it are both written by `build-map.py`: filled dot = available now, hollow = planned, live
places first, with a key; Perth and the Snowy Mountains added). D4 still decides which hollow dots stay.
Phase 4, the part that needs nobody's permission: How it works now shows one real psychology example
(Paula Garrido's published $253, less the $149 rebate, $104 to pay) and Medicare's own rebate figures with
a link to the schedule; the GOALS profiles carry the same rebate figures. No range was invented. Rebates
are indexed each 1 July: update `MBS_REBATE_*` and the page together; `check-site.py` fails if they drift.
Since then: the beehiiv form fixes are published and verified live (fields 48px and 44px tall); the header
button reads "Find your clinician" on every page (D1); the booking blog post explains Book and Enquire; How
it works covers occupational therapy and coaching costs (4.1); on phones the homepage photograph keeps its
faces, with the sentence and buttons beneath it; `.vercelignore` keeps these notes off the public site;
the fee and response-time email to the practices is drafted in `FEE-REQUEST-EMAIL-DRAFT.md`, unsent (D2, D3).
Reversed on Stefan's direction: 3.3 and 3.4. The four cards with descriptions and cost lines were too much
to read on a landing page for this audience. They are now four words (Assessment, Therapy, Daily life,
Coaching), each a full-width row that fills with its colour under the pointer while the others step back.
Costs and eligibility stay on How it works and the profiles, one click in. The hero sentence was cut to nine
words for the same reason. Rule for the landing page from here: vision first, detail behind a click.
The rest of the homepage followed: "The wait was never the care." stands alone as one large line, the
closing call to action (a repeat of the hero buttons) is gone, and the newsletter block is a heading, the
form and one line. The homepage is now hero, four words, one statement, one form.
Open, and why: 0.1 needs a PostHog personal API key, which is not on this machine; 0.3 and 5.5 need people;
4.3 waits on 0.1; D4 (which hollow dots stay) is Stefan's call. One beehiiv draft is waiting for Publish:
the main form's button label shortened to "Join free" so it stops wrapping on phones.
per-category counts, so there is nothing to generate).

## House rules (consistency pass, 2026-09-21)

One of each, on every page and in every generator:
- **Page width and gutter:** `max-w-[1200px] mx-auto px-5 md:px-8 lg:px-12`, the header's. Logo, headline and
  content share a left edge. Reading columns (legal, blog, 760px) stay narrow by design.
- **Page colour:** `#FAFAF7` (also the `surface` and `background` tokens). No white or off-white `<main>`.
- **Headings:** H1 `text-[36px] sm:text-[44px] lg:text-[52px]`; section H2 `text-[32px] sm:text-[40px] leading-[1.1]`;
  both extrabold, tracking-tight, Plus Jakarta Sans. The homepage's display lines are the only exception.
- **Muted text:** `#5f5e59`.
- **In-page button:** `h-12 px-7 rounded-full text-[15px] font-bold`, ink `#1a1c1c` or yellow `#f1bc31`.
  Hero buttons are 52px; card buttons 44px. (`h-13` was never a real Tailwind class.)
- **Category pills:** the Network's white pill group, `rounded-[28px]` so it survives wrapping; Learn uses the same.

## How to read this

- **IDs**: `HP` homepage, `HIW` how it works, `LRN` learn, `OS` our story, `NET` network and profiles.
  `X` marks a problem the evaluation did not raise but the audit found while checking it.
- Each phase ships on its own, in order. Earlier phases are cheaper and carry less risk; later ones
  depend on decisions listed under [Decisions needed](#decisions-needed).
- Each task names the file that owns the change. Profile pages, the network deck and the homepage
  practitioner count are **generated** by `scripts/build-profiles.py`; the map by
  `scripts/build-map.py`. Edit the generator, never the 18 outputs.
- After any HTML/CSS change: `npm run build`, because `vercel.json` ships the committed bundles.

## What the audit found (the short version)

| # | Finding | Verdict | Evidence |
|---|---|---|---|
| HP-01 | Hero doesn't say what the service is | **Confirmed** | `index.html:80-83` H1 is "Not just focus. Life returned to you." The first sentence describing the product is at `index.html:100`, below the fold. |
| HP-02 | Costs shown for GP only; "Two ways in" lists a third | **Confirmed, and understated** | `index.html:95,101,108,112`. There are now **four** categories (GPs, psychologists, allied health, coaches: `PANELS`, `build-profiles.py:38`), and the coaches are not on the homepage at all. |
| HP-03 | ADHDme Weekly form broken (section and footer) | **Confirmed live** | Both iframes report `height: 26px` from beehiiv while the wrapper holds 52/48px (`site.css:159-172`). The form is not drawing its field and button. |
| HIW-01 | Hero content sits low | Confirmed | Hero heights differ per page; no shared rule. |
| HIW-02 | Two-step explainer covers booking, not enquiries | **Confirmed, and understated** | 9 of 18 practitioners do not take a booking at all (see X-01). `how-it-works.html:83-84`. |
| HIW-03 | $498 reads as a third option; "receives no part of it" is a grey footnote | **Confirmed** | `how-it-works.html:91-95`. The profile pages already do this correctly (`GP_FEES`, `build-profiles.py:43-52`: $498 is a note, the disclosure is `<strong>`). The page just drifted from the generator. |
| LRN-01 | Typography changes on Learn | **Confirmed** | `learn.html` is the only page using `font-serif` (9 uses, `font-normal`). Every other H1 is extrabold Plus Jakarta Sans. |
| LRN-02 | Featured repeats ADHD strengths | **Confirmed** | Featured cards 1-2 are byte-for-byte the first two Strengths cards (`learn.html:113-115` vs `:124`). |
| LRN-03 | Category nav sits below Featured | Confirmed | `learn.html:121`. |
| LRN-04 | Clinician training portal at page bottom | Confirmed | `learn.html:144` → `academy-login.html`. |
| OS-01 | Current vs planned coverage unclear | **Confirmed, and worse than stated** | See X-02. |
| OS-02 | "Ready to walk with us?" unclear; CTA differs | Confirmed | `our-story.html:153-157`: a `<form>` wrapping a black "Book" submit button, unlike any other page. |
| NET-01 | Booking CTAs inconsistent in wording and position | **Confirmed** | Census of booking-intent labels across the site: "Book now" ×32, "Book" ×18, "Find your clinician" ×4, "Book an assessment" ×2, "Book a psychologist" ×2, "Book with {name}" ×18, "See the clinicians", "Meet the GPs", "Meet the psychologists". |
| **X-01** | Enquiry-only practitioners are labelled "Book" | **New** | Paula Garrido, Meera Lakhani, Lara Schulz and all six REACH coaches open a contact or request form (`book_hint` says so), yet the button says "Book with …". 9 of 18. |
| **X-02** | The map contradicts the network | **New** | The map shows Cairns, Townsville, Brisbane, Gold Coast, Sydney, Melbourne (`build-map.py:12`), four of which have nobody. Perth (6 coaches) and Jindabyne (1) are live and absent. The homepage hero says "Sydney, Brisbane, Perth, the Snowy Mountains"; Our Story says "starting with the east coast". |
| **X-03** | Malformed HTML on the How it works CTA banner | **New** | `how-it-works.html:100`: the `style="…"` attribute closes, then `flex flex-col lg:flex-row …"` sits outside any attribute. Those layout classes never apply. |

One recommendation cannot be done as written. **"Show a cost range for psychologists"** (HIW-03): the
clinics publish no fees, and `goals_fees()` (`build-profiles.py:81-107`) records that this was checked
on 2026-09-19 and that "a guess would be worse than nothing". Phase 4 shows how to answer the user's
real question ("can I afford this?") with sourced public figures instead of invented ranges.

---

## Phase 0: Baseline and guardrails (½ day)

Nothing visible changes. This makes every later phase checkable.

| Task | Owner file | Verify |
|---|---|---|
| 0.1 Record the PostHog baseline for the existing `data-landing-control` events (hero, door, final CTAs), newsletter submits, and profile → outbound booking clicks. 14 days back. | `scripts/posthog-dashboard.py` | Numbers written into this file under "Baseline". |
| 0.2 Add `scripts/check-site.py`: a plain assertion script, no framework. Starts with checks that pass today; each later phase adds its own failing check first, then makes it pass. Initial checks: every `*.html` parses with no stray text inside tags (catches X-03); every internal `href` resolves; generated regions match a fresh generator run. | new | `python scripts/check-site.py` exits 0 except for X-03, which it must catch. |
| 0.3 Screenshot every page at 375 / 768 / 1280 into `qa-packs/baseline/`. | — | Files exist; used for before/after in every phase. |

## Phase 1: Broken and misleading things (1 day)

Pure fixes. No design decisions, no dependencies.

| Task | Finding | Change | Verify |
|---|---|---|---|
| 1.1 Fix the newsletter embeds | HP-03 | Diagnose first, do not restyle blind: load both form URLs directly and compare with the embed. Likely causes, in order: the beehiiv form's own published design collapsed (see `BEEHIIV-UPGRADE-TRACKER.md`, forms republished 09-19/20); the loader's inline `width: fit-content` fighting `width:100% !important`. If beehiiv's embed cannot be made reliable, replace the iframe with a native `<form>` (one email field, one button, site tokens) posting to a Vercel function that calls beehiiv's subscription API. That also removes the third-party iframe the privacy page has to account for. | Field and button visible and usable at 375 and 1280, in section, footer and invite dialog; a test address arrives in beehiiv with the right `utm_content`. |
| 1.2 Repair the CTA banner markup | X-03 | Move the orphaned classes into `class`. | `check-site.py` passes; banner lays out in a row at `lg`. |
| 1.3 Stop $498 reading as a third price | HIW-03 | Two rows ($299, $199), then a total line visually distinct from a price row: "= $498 for the full assessment and diagnosis". Copy the wording from `GP_FEES.notes`. | Side by side with a profile page, the two say the same thing. |
| 1.4 Promote the differentiating claim | HIW-03 | "The practice sets and charges the fee. ADHDme receives no part of it." becomes its own statement: body-size, `#1a1c1c`, semibold, above the fine print. Same treatment on the homepage GP door. | Passes contrast AA; readable in the 375 screenshot without zooming. |
| 1.5 One typeface | LRN-01 | Replace the 9 `font-serif … font-normal` headings in `learn.html` with the site heading classes used by `the-doctors.html:54`. If nothing else uses the serif afterwards, drop it from `assets/css/fonts.css` and the font preload. | `check-site.py`: no `font-serif` in any page. |
| 1.6 Our Story closing card | OS-02 | Title → "Ready to find your clinician?" (already used on How it works). Replace the `<form>` + black submit with the standard primary anchor from Phase 2's vocabulary. | Visual match with `how-it-works.html` banner. |

## Phase 2: One booking language, generated (1–2 days)

The root cause of NET-01 and X-01 is that the label is hard-coded in three templates and knows
nothing about how the practitioner is actually reached.

**The vocabulary** (D1 below confirms it):

| Intent | Label | Where |
|---|---|---|
| Go and choose someone | **Find your clinician** | header button, 404, blog, How it works, Our Story, legal pages (replaces "Book now" ×32, "See the clinicians", "Book") |
| Choose within a category | **Meet the GPs / psychologists / …** | homepage doors only |
| Leave the site to a live diary | **Book with {first name}** | profile, deck card |
| Leave the site to a form | **Request an appointment with {first name}** | profile, deck card |

"Book now" in the header currently leads to a list, not a booking. That is the mismatch the evaluator
felt; the label should promise what the click delivers.

| Task | Owner file | Verify |
|---|---|---|
| 2.1 Add `book_mode: 'book' \| 'request'` to each entry in `CLINICIANS`. `book` = Healthengine, Halaxy (9). `request` = WPC appointment form, GOALS contact, NCAU contact, REACH enquiry (9). | `build-profiles.py:175+` | Generator fails loudly if the field is missing. |
| 2.2 Drive both profile CTAs and the deck card label from `book_mode`. Put a one-line expectation under request-mode buttons using the existing `book_hint`. | `build-profiles.py:1070,1152`, `profile-shell.html:84` | Regenerate; diff shows only label/hint changes on the 9 request profiles. |
| 2.3 Same position on every profile: primary CTA directly under the name block, repeated once after fees. The generator already guarantees this; assert it. | `check-site.py` | Each profile has exactly two primary CTAs with identical label. |
| 2.4 Replace header/footer/hand-written page labels per the table. | all hand-written pages | `check-site.py` allow-list: any booking-intent label outside the vocabulary fails. |
| 2.5 Rewrite the two-step explainer: **1. Choose a clinician → 2. Book a time, or request an appointment.** Under step 2, two short lines: what happens when you book (diary opens, you pick a time) and when you request (the practice replies, typically within X; see D2). Give the steps real weight: numbered, heading-size, the first thing after the hero. | `how-it-works.html:80-85` | HIW-02 screenshot review; the word "request" appears above the fold at 1280. |

## Phase 3: The homepage says what this is (2 days)

| Task | Finding | Change | Verify |
|---|---|---|---|
| 3.1 Name the product in the hero | HP-01 | Keep the H1 (it is the brand line). Add one plain sentence directly beneath it, above the buttons: what it is, who it is for, what you do here. Draft: *"A network of Australian clinicians who understand ADHD. Read how each one works, see the price, and book with their practice directly. No referral, no account."* | 5-second test (Phase 5): ≥4 of 5 people can say what the site offers. |
| 3.2 Raise the hero content | HP-01, HIW-01 | One shared rule for hero height and text position used by every page, so the fix is consistent rather than per-page. Content should start in the upper-middle of the image, not the last 15%. | At 1280×720 the H1, sentence and both buttons are fully visible without scrolling, on every page. |
| 3.3 "Ways in" tells the truth about the count | HP-02 | Retitle (e.g. "Ways in.") and give all four categories an equal card: GP, psychologist, allied health, coaching. Same structure each: what it is, **cost line**, button. Buttons bottom-aligned (`flex flex-col` + `mt-auto`) to fix the alignment the evaluator saw. | No orphan pill link; four buttons share a baseline at `md`+. |
| 3.4 A cost line on every card | HP-02 | GP: "$299 initial · $199 follow-up · no Medicare rebate". Others, until Phase 4 lands: "Each practice sets its own fee. Medicare rebates may apply with a GP referral." (psychology) / "NDIS, private health or a GP care plan may cover it." (OT) / "Quoted by the practice; JobAccess may fund it." (coaching). All four statements already exist, verified, in the generator. | Every card has a cost line; none contains an invented figure. |
| 3.5 Generate the counts | HP-02 | Per-category counts from the generator, like the existing `count-all` marker. | Adding a clinician updates the homepage with no hand edit. |

## Phase 4: Cost transparency without guessing (2–3 days, needs D3)

The user's question is "can I afford this?". Three sourced ways to answer it, best first:

1. **Ask the practices.** A two-line email to WPC, GOALS, NCAU and REACH: "may we publish your standard
   session fee, or a from-price?" Any yes goes into `fees.figures` and appears everywhere automatically.
2. **Public reference figures, clearly labelled as such.** The current Medicare rebate for a
   psychology session under a Mental Health Treatment Plan, and the APS recommended fee, each with its
   source and an "as at" date. Framed as "what these sessions typically involve in Australia", never as
   this clinic's price. Figures must be looked up and cited at build time, not written from memory.
3. **The free first step.** GOALS offers a free 15-minute call to ask the fee (`build-profiles.py:97`).
   Surface it as the zero-cost way in.

| Task | Verify |
|---|---|
| 4.1 Add a "What it costs" comparison block to How it works covering all four categories, reusing the generator's fee data so page and profiles cannot drift again (the cause of HIW-03). | One source of truth; `check-site.py` confirms parity. |
| 4.2 Add an optional `fee_guide` (figure, source URL, as-at date) per category; render only when present. | No figure renders without a source link. |
| 4.3 Test whether a range helps (the evaluator's open question): ship 4.2 behind a PostHog flag, measure profile → outbound click rate for psychologists over 3–4 weeks. | Decision recorded here with the numbers. |

## Phase 5: Learn, Our Story, and asking real people (2 days)

| Task | Finding | Change | Verify |
|---|---|---|---|
| 5.1 Category nav first | LRN-03 | Move the pill nav directly under the intro, above Featured. Make it sticky under the header on scroll. | First tab stop in `<main>` reaches the nav; it stays visible at 375. |
| 5.2 Featured earns its place | LRN-02 | Rule: Featured never repeats a card from the first row of any section, and holds one card from each of three different sections. Rotate monthly alongside the newsletter. If that is more upkeep than it is worth, delete Featured; the strengths-first order already does its job. | `check-site.py`: no `href` appears in both Featured and a section's first row. |
| 5.3 Clinician portal out of the reader's path | LRN-04 | Remove from Learn's body. One quiet "For clinicians" link in the site footer on every page. Clinicians are told about it in onboarding, not by stumbling on a patient page. | Link present in footer; absent from `learn.html` main. |
| 5.4 The map shows the real network | OS-01, X-02 | `build-map.py` reads places from `CLINICIANS` and marks each city **Available now** (has ≥1 practitioner: Sydney, Brisbane, Perth, Snowy Mountains, plus a telehealth note) or **Planned** (D4 decides which remain). Visible text label and distinct dot style, not only the aria-label. Heading and intro rewritten to match; "Six cities" and "east coast" go. | Every city in the hero line is on the map as Available; status is readable without a screen reader. |
| 5.5 Lightweight UX tests, as the evaluation asks | HP-01, HIW-03 | (a) 5-second test of the new hero with 5 people who have never seen the site: "what does this site offer, and who is it for?" (b) First-click test: "you want therapy, not a diagnosis: where do you click?" (c) Ask 5 people whether a typical-cost guide would change their decision. | Results appended here; any failed test reopens its phase. |

---

## Decisions needed

Recommendation first in each case. None blocks Phase 0 or 1.

| # | Decision | Recommendation |
|---|---|---|
| D1 | Approve the four-label vocabulary, including retiring "Book now" from the header. | Approve. It is the single highest-leverage change in the evaluation. |
| D2 | What response time can we promise for appointment requests? | Ask each practice; say nothing until they answer. Do not publish a guess. |
| D3 | May we email the four practices for publishable fees, and may we show cited public reference figures? | Yes to both; fall back to the free-call route where a practice declines. |
| D4 | Which of Cairns, Townsville, Gold Coast and Melbourne are real plans? | Keep only cities with a named clinician in conversation. An empty "Planned" dot is a promise. |
| D5 | Keep or delete Learn's Featured row? | Keep with the rotation rule for one quarter; delete if it isn't maintained. |

## Sequence and effort

| Phase | Effort | Depends on | Risk |
|---|---|---|---|
| 0 Baseline | ½ day | — | none |
| 1 Fixes | 1 day | — | low (1.1 may grow if beehiiv's embed is the fault) |
| 2 Booking language | 1–2 days | D1 | low; generator-driven |
| 3 Homepage | 2 days | Phase 2 | medium; most-visited page, watch baseline metrics for 7 days |
| 4 Costs | 2–3 days + waiting on practices | D3 | medium; every figure needs a source |
| 5 Learn, map, testing | 2 days | D4, D5 | low |

## Traceability

Every evaluation finding, and where it is closed:

HP-01 → 3.1, 3.2, 5.5 · HP-02 → 3.3, 3.4, 3.5, 4.1 · HP-03 → 1.1 · HIW-01 → 3.2 · HIW-02 → 2.1, 2.2, 2.5 ·
HIW-03 → 1.3, 1.4, 4.1–4.3 · LRN-01 → 1.5 · LRN-02 → 5.2 · LRN-03 → 5.1 · LRN-04 → 5.3 · OS-01 → 5.4 ·
OS-02 → 1.6 · NET-01 (both pages) → 2.2, 2.3, 2.4 · X-01 → 2.1, 2.2 · X-02 → 5.4 · X-03 → 1.2

## Not in this plan

Deliberately left alone, because the evaluation did not ask and nothing is broken: the Academy, the
blog templates, analytics and consent code, the visual identity, and any move off static HTML.
