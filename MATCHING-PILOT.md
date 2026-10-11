# Matching pilot: implementation note

A manual patient–clinician matching pilot inside the existing site. A visitor leaves an email address; the
team sends them a five-minute survey; a founder matches them to clinicians by hand. Nothing here is an
algorithm, an assessment or a waitlist.

**State on this branch: built, tested in the browser and in `node --test`, and switched on through the
mail-app route only.** That route opens the person's own mail app with a fixed message to info@adhdme.au
(the same address as the site's Contact link), so the site stores nothing. A site-held endpoint route is
built but closed until the blockers in section 7 are resolved.

## 1. Repository findings

- **Stack:** hand-written HTML plus Python generators (`scripts/build-*.py`), Tailwind compiled to a
  committed bundle (`npm run build`), vanilla JS (`site.js`, `analytics.js`, `privacy-consent.js`), no
  framework, no router: every page is a file. Hosted on **Vercel as static files** (`vercel.json` sets
  `framework: null`, no build, no `api/` directory, no serverless functions).
- **Backend:** none. The only forms are the Beehiiv newsletter embeds (third-party iframes) and the
  Academy login, which is a client-side `sessionStorage` gate, not authentication.
- **Staff access or admin:** none exists. Nothing in this repository can authenticate a founder or
  restrict a record to staff.
- **Design system:** Plus Jakarta Sans, `#1a1c1c` ink on `#FAFAF7` cream, brand yellow `#f1bc31`, pill
  buttons (`btn-press … rounded-full bg-[#1a1c1c]`), white `rounded-3xl` cards with `#e8e6df` borders,
  Tailwind utilities. The pilot reuses all of these and adds no CSS of its own.
- **Privacy:** `privacy-consent.js` shows an informational bar (`requireConsent: false` in
  `analytics-config.js`), and `privacy.html` says in terms that there is nothing on the site to fill in.
  Neither covers a request form, so there is no approved collection notice yet.
- **PostHog (`analytics.js`, `analytics-config.js`):** autocapture **on**, session replay **on** with all
  inputs masked, `person_profiles: 'always'`, `persistence: 'localStorage+cookie'`, pageviews with the full
  URL, Web Vitals on, console capture off, no `identify()` calls, sends only from `www.adhdme.au`. Every
  declared event is validated against a vocabulary and anything undeclared is refused.

## 2. What was built (changed files)

| File | Change |
|---|---|
| `matching-config.js` | New. The flags and approved-text slots, **all off/empty**. Unminified so they can be set live without a rebuild, like `analytics-config.js`. |
| `matching.js` | New. Reveals the calls-to-action when the pilot is on; runs the one-field form (validation, the mail-app route, and for a future endpoint: loading, duplicate prevention, failure/retry, success only on server acceptance). Pure logic exported for tests. |
| `matching-help.html` | New. The request page (one email field and a consent box), built from the `how-it-works.html` shell so header and footer stay identical to the rest of the site. `noindex` for now, and marked `data-private-page`. |
| `index.html` | A matching card after the "No wrong door" list, hidden until the flag is on. Loads the two scripts. |
| `the-doctors.html` | A compact card above the listings and a link in the no-results state, both hidden until the flag is on. Loads the two scripts. |
| `analytics.js` | Declares the four pilot events with their two allowed properties; names the page; switches autocapture and replay off on any page marked `data-private-page`. |
| `tests/matching.test.js`, `scripts/check-matching.py`, `package.json` | Tests (`npm run test:matching`). |

Routes added: `/matching-help.html`. Nothing else moved; the directory, profiles and booking links are untouched.

## 3. Data flow

Two routes, chosen by `matching-config.js`:

```
mail-app route (on now)   visitor's own mail app ──▶ info@adhdme.au ──▶ founder replies with the survey, matches by hand
                          the site stores nothing; the only thing it writes is a fixed subject and body

endpoint route (closed)   visitor ──(HTTPS POST {email})──▶ cfg.requestEndpoint (none exists) ──▶ staff-only store
```

Third-party services touched: **none**. PostHog receives only the four events below. The survey itself is
sent by the team by email; whichever tool is used for it is a separate decision and is not in this repository.

The only storage key the page uses is `adhdme-matching-seen:<placement>` (a `1`, so a call-to-action is
counted once per session). The email address never touches `localStorage`, `sessionStorage`, the URL, the
console or analytics.

## 4. Analytics

Declared in `analytics.js`, hyphenated to match the site's existing names:

| Event | Fires when |
|---|---|
| `matching-cta-viewed` | a call-to-action is at least half on screen, once per placement per session |
| `matching-cta-clicked` | its button is pressed |
| `matching-form-started` | first input or change on the form, once per attempt |
| `matching-request-submitted` | the endpoint returned 2xx (never on button press) |

Properties: `placement` (`homepage` / `directory` / `no_results` / `navigator`) and `copy_version`. The validator refuses
any other property, so an answer cannot be sent by mistake.

Not implemented, deliberately: `matching_shortlist_sent`, `matching_option_clicked`,
`matching_booking_confirmed`. None is observable from the browser; they belong in the founder queue
(section 7) and should be recorded there with an evidence source.

Replay and autocapture are **off on `matching-help.html`** via the `data-private-page` attribute. The
pageview still goes out, with a URL that carries no answers (`?from=` names a placement only). Tracking on
every other page is unchanged.

## 5. Tests

`npm run test:matching` runs:

- `node --test tests/matching.test.js` (11 tests): the committed configuration opens only the mail-app
  route; off, no-route, paused and the endpoint route's approvals; a valid email and ticked box pass;
  missing consent alone blocks; a bad email is named; the mailto message carries nothing typed; the
  endpoint payload holds only the email, consent and labels; success only on server acceptance; server
  error and network failure both yield retry; a second press mid-flight does not send; a hung request
  times out into retry.
- `scripts/check-matching.py`: endpoint empty and notice unapproved; the email labelled and tied to its
  error; exactly two controls; consent starts unticked; no storage, URL or console use for answers (the
  fixed mailto navigation is the one allowed URL); events carry only the two properties; the page is
  private and noindex; the three calls-to-action exist with the approved copy; no disallowed wording.

Checked by hand in the browser (393px and 1280px): disabled and paused states, validation summary with
per-field errors, the mail-app route reaching the success screen with the form cleared, and (with the
preview endpoint) loading label, duplicate press ignored, failure with the address kept and the button
re-enabled; all three calls-to-action and their `viewed` events; no horizontal overflow.

**Not tested, because it does not exist:** server-side validation, rate limiting, unauthorised staff
access, notification emails, logs. See section 8.

## 6. Founder setup, in order

### The Google Meet route (the one asked for)

The site cannot create calendar events itself (no backend, no Google credentials), so the booking is done by
**Google Calendar's own appointment schedule** on the info@adhdme.au account. The person picks a time and
types their email on Google's page; Google puts a Meet invite in both calendars. The site only embeds the page.

1. Sign in to Google Calendar as info@adhdme.au. Click **Create → Appointment schedule**.
2. Name it (e.g. "ADHDme matching call"), set the duration (15 minutes), your availability, and a buffer.
3. Under **Booking page options**, require the booker's email; turn on **Add Google Meet video conferencing**
   (it is on by default); set the booking form to ask for name and email only.
4. Save, then **Share → Embed** (or **Share → Open booking page**) and copy the URL. It looks like
   `https://calendar.google.com/calendar/appointments/schedules/AcZss…?gv=true`.
5. Paste it into `matching-config.js` as `appointmentUrl`. Deploy. The page switches to the booking view;
   the email form stays as the fallback if the URL is ever emptied.
6. Each booking is a calendar event with the person's email. That event is the queue (section 7's fields
   can live in the event's description) and the evidence source for "booking confirmed".

If info@adhdme.au is a personal Gmail rather than Google Workspace, appointment schedules are still
available with Google's free-tier limits (one schedule); check before relying on it.


1. Decide where requests live. Options that fit this repository, cheapest first:
   - **Vercel serverless function + a managed Postgres with row-level security (e.g. Supabase) and
     Supabase Auth for the two founders.** The function validates, rate-limits by IP, inserts, emails
     "New matching request received. Sign in to review." A tiny staff page behind that login is the queue.
   - A form product with Australian data residency and staff login, if a founder approves adding a third
     party (the brief says not to add one without approval).
2. Approve the collection notice on `matching-help.html` (the bullet list under "What happens with what you
   tell us"), decide the retention rule, and update `privacy.html`, which currently says there is nothing to
   fill in on the site.
3. Agree who owns the queue, the response target (if any), and the reply channel.
4. Fill `matching-config.js`: `requestEndpoint`, `collectionNoticeApproved: true`,
   `approvedCollectionNoticeVersion`, `retentionPolicyText`, optionally `approvedResponseTimeText`.
5. Remove `<meta name="robots" content="noindex">` from `matching-help.html` and add the page to
   `sitemap.xml` if it should be found.
6. Turn on `pilotEnabled`, then `intakeOpen`. Each is one line and takes effect on the next deploy.

### Queue fields (for whichever store is chosen)

Pseudonymous request ID · received · owner · response due · status (New / clarification needed /
reviewing / shortlist sent / no network fit / follow-up due / closed) · shortlist sent · follow-up due ·
outcome (booked / contacted, not booked / deciding / no fit / no response / withdrawn) · outcome evidence
source · closed. Identifiable details stay in the restricted record; exports and analytics get the ID only.

## 7. Launch blockers (explicit)

For the mail-app route that is on now: none beyond agreeing who reads info@adhdme.au and sends the survey. For the endpoint route:

1. **No backend or storage.** Nothing can receive a request. Building one is a hosting and data decision, not a code change on this branch.
2. **No staff authentication.** Without it there is no safe way to read requests. Not improvised here.
3. **Collection notice is a draft** and `privacy.html` contradicts it.
4. **Retention rule not set.**
5. **No spam control** on the site to reuse; rate limiting must be done server-side.
6. **Owner and capacity not agreed.**

## 8. Enable, disable, roll back

- **Enable:** section 6. Pilot on, intake off shows the cards and a form whose button is disabled with
  "The pilot isn't open yet."; both on accepts requests.
- **Pause:** `intakeOpen: false`. The page says the pilot is at capacity and browsing stays available. It is
  not a waitlist: nothing is stored.
- **Disable:** `pilotEnabled: false`. Every call-to-action disappears, the page shows the closed message.
- **Roll back:** revert the branch's commit; no data or schema is involved on the site side.
- **Local preview:** on localhost only, `?matchingPreview=1` (mock endpoint that accepts), `?matchingPreview=fail`
  (retry state), `?matchingPreview=paused`, `?matchingPreview=mailto`. Ignored on any other host.

This note describes what is built and tested. It is not a claim that the feature is compliant or ready for
real requests; that depends on the decisions in section 6.
