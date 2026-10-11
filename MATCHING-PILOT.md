# Matching pilot: implementation note

A manual patient–clinician matching pilot inside the existing site. Visitors ask for help; a founder reviews
and replies by hand. Nothing here is an algorithm, an assessment or a waitlist.

**State on this branch: built, tested in the browser and in `node --test`, and switched off.** Live intake
cannot be turned on until the blockers in section 8 are resolved, because this repository has nowhere
approved to put a request.

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
| `matching.js` | New. Reveals the calls-to-action when the pilot is on; runs the form (scope gate, validation, loading, duplicate prevention, failure/retry, success on server acceptance). Pure logic exported for tests. |
| `matching-help.html` | New. The request page, built from the `how-it-works.html` shell so header and footer stay identical to the rest of the site. `noindex`, and marked `data-private-page`. |
| `index.html` | A matching card after the "No wrong door" list, hidden until the flag is on. Loads the two scripts. |
| `the-doctors.html` | A compact card above the listings and a link in the no-results state, both hidden until the flag is on. Loads the two scripts. |
| `analytics.js` | Declares the four pilot events with their two allowed properties; names the page; switches autocapture and replay off on any page marked `data-private-page`. |
| `tests/matching.test.js`, `scripts/check-matching.py`, `package.json` | Tests (`npm run test:matching`). |

Routes added: `/matching-help.html`. Nothing else moved; the directory, profiles and booking links are untouched.

## 3. Data flow

```
visitor ──(form, HTTPS POST, JSON)──▶  cfg.requestEndpoint   ◀── EMPTY: nothing is sent today
                                        │  must: validate, rate-limit, store where only staff can read,
                                        │  email founders only "New matching request received. Sign in to review."
                                        ▼
                                   founder reviews by hand, replies through an approved channel
```

Third-party services touched by this feature: **none** (no form platform, no new SDK). PostHog receives
only the four events below. In local preview mode (`?matchingPreview=1` on localhost only) the endpoint is
a mock inside the browser; nothing leaves the machine.

The request body, when an endpoint exists: `service`, `state`, `locality`, `mode`, `budget`, up to two
`priorities`, `first_name`, `email`, `consent: true`, `collection_notice_version`, `copy_version`. No
free-text box exists; suburb and first name are capped at 40 plain characters, so a medical history has
nowhere to go.

Answers never touch `localStorage`, `sessionStorage`, the URL, the console or analytics. The only storage
key is `adhdme-matching-seen:<placement>` (a `1`, so a call-to-action is counted once per session).

## 4. Analytics

Declared in `analytics.js`, hyphenated to match the site's existing names:

| Event | Fires when |
|---|---|
| `matching-cta-viewed` | a call-to-action is at least half on screen, once per placement per session |
| `matching-cta-clicked` | its button is pressed |
| `matching-form-started` | first input or change on the form, once per attempt |
| `matching-request-submitted` | the endpoint returned 2xx (never on button press) |

Properties: `placement` (`homepage` / `directory` / `no_results`) and `copy_version`. The validator refuses
any other property, so an answer cannot be sent by mistake.

Not implemented, deliberately: `matching_shortlist_sent`, `matching_option_clicked`,
`matching_booking_confirmed`. None is observable from the browser; they belong in the founder queue
(section 7) and should be recorded there with an evidence source.

Replay and autocapture are **off on `matching-help.html`** via the `data-private-page` attribute. The
pageview still goes out, with a URL that carries no answers (`?from=` names a placement only). Tracking on
every other page is unchanged.

## 5. Tests

`npm run test:matching` runs:

- `node --test tests/matching.test.js` (14 tests): committed flags are off; each missing approval keeps
  intake closed; a full in-scope request validates; out-of-scope is explained, not errored; every required
  field is named; missing consent alone blocks; priorities capped at two; no invented budget bands; free
  text cannot carry a history; payload has only the collected fields; success only on server acceptance;
  server error and network failure both yield retry; a second press mid-flight does not send; a hung
  request times out into retry.
- `scripts/check-matching.py`: flags off and endpoint empty; every control labelled and tied to its error;
  consent starts unticked; no storage, URL or console use for answers; events carry only the two
  properties; the page is private and noindex; the three calls-to-action exist, hidden, with the approved
  copy; no disallowed wording.

Checked by hand in the browser (393px and 1280px): disabled state, paused state, out-of-scope message,
validation summary with focus and per-field errors, loading label, duplicate press ignored, success screen
with focus on its heading and the form cleared, failure state with answers kept and the button re-enabled,
all three calls-to-action and their `viewed` events, no horizontal overflow.

**Not tested, because it does not exist:** server-side validation, rate limiting, unauthorised staff
access, notification emails, logs. See section 8.

## 6. Founder setup, in order

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
- **Local preview:** on localhost only, `?matchingPreview=1` (accepts), `?matchingPreview=fail` (retry
  state), `?matchingPreview=paused`. Ignored on any other host.

This note describes what is built and tested. It is not a claim that the feature is compliant or ready for
real requests; that depends on the decisions in section 6.
