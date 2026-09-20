# ADHDme Weekly — beehiiv setup

Configured 2026-09-20. Everything below is **live in the beehiiv account** unless marked
*pending* or *manual*.

- Workspace: `Info's Hiiv` (`work_ea45e0fd…`), owner `info@adhdme.au`
- Publication: **ADHDme Weekly** — `pub_be8cb1ba-ecdc-40a3-80d3-775f1e61185e`
- Public URL: <https://adhdme.beehiiv.com/>

> **Plan reality check.** The beehiiv API reports this workspace's plan as **`launch`**, not
> Max. `private_branding` (remove beehiiv branding) is not even offered in the settings
> document the API returns, which is what a Launch account looks like. If a Max trial was
> started, it is not reflected on the workspace. Everything below was therefore built to be
> free-safe by default. See [Trial-only](#trial-only) for the one exception.

---

## The free-safe core

This is the chain that must keep working on Launch, and does:

```
adhdme.au embed  →  beehiiv subscriber  →  weekly issue  →  unsubscribe + analytics
```

None of it depends on automations, the Send API, MCP write access, surveys, polls, dynamic
content, RSS-to-Send, paid tiers, extra team members, or removing beehiiv branding.

---

## What is configured

### Publication

| Setting | Value |
|---|---|
| Name | ADHDme Weekly |
| Description | ADHD science, made useful. |
| Logo | `assets/brand/icon-512.png` (uploaded to beehiiv) |
| Social/share thumbnail | `assets/brand/og.png` (uploaded to beehiiv) |
| Category tags | mental health, neuroscience, psychology |
| Language | English |
| Time zone | Sydney — **was** US Eastern; see [Open questions](#open-questions) |
| Subscribe button text | Join ADHDme Weekly |
| Sender name | ADHDme |
| Footer copyright | ADHDme |
| Automatic UTM tagging | On |
| Double opt-in | Off (beehiiv default; left alone deliberately) |

The longer description — *"A weekly publication translating interesting ADHD research,
emerging ideas and practical strategies into something people can actually use."* — has no
home in beehiiv's publication settings, which only take a single one-line description. It
is carried by the subscribe form's supporting copy instead, and belongs on the publication
website's about/hero section when that is built.

### Subscribe form

Internal name **ADHDme.au — Website Embed** · id `76750273-b34d-4b54-ad52-5fa242ea671b`

- Inline render, direct trigger (always present, no popup/interstitial behaviour)
- **Email only.** The `first_name` / `last_name` custom fields that beehiiv seeds by default
  are explicitly unbound from this form. No new custom fields were created.
- Title: `ADHDme Weekly`
- Subtitle: `ADHD science, made useful.` + the supporting paragraph
- Button: `Join ADHDme Weekly` (submitting state: `Joining…`)
- Consent/disclosure line: `Free. One thoughtful issue each week. Unsubscribe anytime.`
  with a privacy-policy link to <https://www.adhdme.au/privacy.html>. This doubles as the
  compliant disclosure, so there is no second line of legal text cluttering the form.
- Success message: `You're in. The next ADHDme Weekly will arrive in your inbox.`

Styling is mapped to the site's own tokens rather than beehiiv's defaults (which are
PT Serif, black, square corners, centred):

| | |
|---|---|
| Type | Plus Jakarta Sans — 32px/700 title, 16px/400 subtitle |
| Ink | `#1a1c1c` · secondary `#5f5e61` · placeholder `#817662` |
| Surface | `#FAFAF7` on `1px #E8E6DF`, `20px` radius, no shadow |
| Controls | 44px tall, fully pilled, matching `.btn-press` on the site |
| Button | `#1a1c1c` on white text — not a bright growth-hack colour |
| Layout | Left-aligned, 40px padding, 24px gap |

### Signup-source attribution

No custom field was added for this. Two mechanisms, either of which is sufficient:

1. **Native.** beehiiv records which external embed a subscriber came through, and this form
   is used only on adhdme.au. The form's internal name appears on the subscriber profile
   under acquisition details.
2. **UTM.** The embed URL carries `utm_source=adhdme.au`, captured at signup.

A dynamic segment **ADHDme.au — Website Signups** (`seg_84ebe410-bad1-49fe-8fa7-20392472e5d1`)
matches `external_embed = '<form id>' OR utm_source = 'adhdme.au'`, so attribution survives
losing either mechanism.

### Subscriber registry

Deliberately minimal, and all of it is either beehiiv-native or free-safe:

- email
- subscription status (active / inactive / pending)
- signup source (embed + UTM, per above)
- signup date
- engagement beehiiv generates on its own — opens, clicks, bounces, unsubscribe date

**No identifiable health information is stored in beehiiv**, and the form collects nothing
that could carry any. Email is the only field.

---

## Trial-only

### `TRIAL TEST - ADHDme Weekly Welcome`

`aut_fc706289-e260-4585-9a8d-5ecbab9d462f` — **state: draft, not published**

- Trigger: `email_submission` scoped to the ADHDme.au embed (not "any form")
- One step: send email. No wait, no branch, no sequence.
- Subject: `Welcome to ADHDme Weekly`
- Body: the four-line welcome, ending `ADHDme`

**This stops functioning on Launch.** Automations are a paid-tier feature. If the account
returns to (or stays on) Launch, this automation simply will not run, and *nothing in the
free-safe core depends on it*. A subscriber who joins with the automation off still gets:
added to the list, beehiiv's own confirmation behaviour, and the next weekly issue.

It exists only to answer "does an automated welcome measurably improve the experience". If
the answer is no, delete it and lose nothing.

> If you want a welcome email that survives Launch, use beehiiv's built-in **Welcome Email**
> (Settings → Publication → Welcome email) instead of an automation. That is a different
> feature and it is free-safe. Not set up — say the word.

### MCP

The beehiiv MCP server is connected to Claude at user scope over HTTP
(`https://mcp.beehiiv.com/mcp`), OAuth'd as `info@adhdme.au`. Every change described in this
document was made through it.

**The operating model does not depend on MCP write access.** On Launch, MCP is read-only.
Everything configured here is ordinary publication state that persists regardless — the
writes were a setup convenience, not a runtime dependency.

---

## Site integration

Both placements are live in this repo. All the copy lives in the page as real HTML —
the beehiiv iframe supplies **only** the email field and the button. That is deliberate:
it keeps beehiiv's fonts, borders and padding out of the design, and keeps the words
indexable instead of buried in a third-party iframe.

| | Form | Placement |
|---|---|---|
| Primary | `76750273-b34d-4b54-ad52-5fa242ea671b` | `index.html`, new `NewsletterSection` after the booking CTA, before `</main>` |
| Footer | `882d54e5-58fd-458f-b045-38318b963983` | Shared footer, above the copyright row, on all 25 pages that have a footer |

Two forms rather than one because a beehiiv form has a single layout and single button
label, and the footer needs `Join` rather than `Join ADHDme Weekly`. They feed the same
audience and both carry `utm_content` (`primary` / `footer`) so the placements can be
told apart.

`index.html` also lost its `pb-24 lg:pb-32` on the booking CTA section — the newsletter
section now carries the page's bottom padding, preserving the existing vertical rhythm.
That is the only pre-existing markup that changed.

The wrapper CSS is at the end of `site.css` under *ADHDme Weekly: beehiiv subscribe
embeds*. It pins the iframe width, because beehiiv's loader momentarily writes
`width: 5000px` onto the iframe while it measures the child — unpinned, that widens the
page and flashes a horizontal scrollbar.

Remember `site.css` and the HTML are compiled: run `npm run build` after editing, since
Vercel does not build and the committed bundles are what ship.

### The raw embed

For reference, the snippet pattern used:

```html
<!-- ADHDme Weekly — beehiiv subscribe form -->
<iframe
  class="beehiiv-embed"
  src="https://subscribe-forms.beehiiv.com/76750273-b34d-4b54-ad52-5fa242ea671b?utm_source=adhdme.au&utm_medium=website&utm_campaign=site_embed"
  title="Subscribe to ADHDme Weekly"
  loading="lazy"
  style="width:100%;border:0;margin:0;display:block;background:transparent"></iframe>
<script async src="https://subscribe-forms.beehiiv.com/embed.js"></script>
```

The script auto-sizes any `iframe.beehiiv-embed` via `postMessage`, so no fixed height is
needed; it also handles the bot-challenge resize. Include the script **once per page**, no
matter how many forms are on it.

This was derived from beehiiv's actual `embed.js` (it queries `iframe.beehiiv-embed` and
messages `beehiiv:styles` / `beehiiv:child-loaded`), and the iframe URL is confirmed live
(HTTP 200, with and without the UTM query). Before shipping, still click **Get embed code**
in the form builder and diff it against the above — beehiiv regenerates the snippet on save
and may add parameters this does not have.

---

## The newsletter itself (email aesthetics)

Template **ADHDme Weekly** — `post_template_59b2aa21-572e-4e8b-a03f-155da57f46cc`,
theme `c4e1dca5-4078-4e52-8d21-f9d33ef254b6`. Start every issue from it.

beehiiv's own onboarding template, *Weekly newsletter (1)*, is **read-only** — the API
refuses to theme it ("this template is read-only because it was created during
onboarding"), which is why a second one exists. Delete it in the dashboard so nobody
picks the unbranded one by mistake.

The email is built from the same tokens as the site, not an approximation of them:

| | |
|---|---|
| Type | Plus Jakarta Sans throughout; Newsreader for pull quotes — both accepted by beehiiv |
| Ink | headings `#1a1c1c`, body `#4a453a`, muted `#817662` |
| Canvas | `#FAFAF7` page, `#FFFFFF` content card, `1px #E8E6DF` border, 16px radius |
| Measure | 640px, 40px padding, 1.65 line height |
| Buttons | `#1a1c1c`, white text, fully pilled, matching `.btn-press` on the site |
| Links | `#24487a` underlined — the brand slate, not beehiiv's default blue, and not the loud coral |
| Rules | hairline `#E8E6DF`, full width, 32px clear above and below |
| Quotes | Newsreader on cream, hairline border; the alternate styles use a `#f1bc31` accent |
| Link cards | cream, hairline, 12px radius — not beehiiv's grey Helvetica default |

Starter structure in the template body: *This week / The research / What it means in
practice / The caveat*. That is a scaffold, not a format decision — rewrite it freely.

**Email footer** (publication-wide, active). beehiiv appends the copyright line, the
Robina postal address and the unsubscribe link underneath:

> ADHDme Weekly — ADHD science, made useful.
> You are receiving this because you subscribed at adhdme.au.
> Written for general information. It is not medical advice, and it is not a substitute
> for care from your own clinician.

**Not set:** a header logo. There is no ADHDme wordmark image in this repo — only the
square app icon and the 1200x630 social card, neither of which is a masthead. The
publication name carries the header instead. Worth revisiting if a wordmark gets drawn.

**Untested:** no email has been rendered or sent, so these are the stored tokens rather
than verified pixels. Preview one in the beehiiv editor before the first real send, and
check the pill buttons and 16px radius in Outlook, which is the usual place both degrade.

---

## Byline, first issue, and the beehiiv website

**Byline** is **Stefan Thottunkal**, set two ways: the account profile name, and a guest
author attached to the first issue. `display_byline_in_email` was off by default and is
now on.

> Quirk worth remembering: `save_guest_author` returns an id like
> `guest_a1725d9e-…`, but `edit_post` rejects that and only accepts the **bare UUID**.
> `list_authors` also returns an empty list even with authors present, so do not trust it
> to tell you whether one exists.

**Issue #1 — draft, not scheduled.** *What stimulants actually do to sleep*
`post_957f3156-d91f-421a-bec3-922a0da5ff78`

The hook is that the short-term and long-term effects point opposite ways: a late dose
delays sleep onset, yet longitudinal data associates stimulant treatment with better
subjective sleep and lower insomnia odds — probably through symptom control rather than
sedation. Structure follows the template, with a caveat section on the confounding
(observational data, likely survivorship, self-report vs measured sleep) and two real
sources linked at the end.

> **Verify before sending.** The claims were drafted from search results, not from
> reading the papers. Check the specifics against the sources, and have someone
> clinically qualified read it — it discusses medication timing, which is exactly where
> a newsletter can do harm if it is loose.

**The beehiiv website** (`adhdme.beehiiv.com`) — home and subscribe pages now carry real
SEO titles, descriptions and social cards pointing at `assets/brand/og.png`, instead of
beehiiv's defaults.

Its **colours and fonts cannot be set through MCP.** `edit_page` exposes only SEO
metadata and navbar/footer toggles; there is no site-theme tool in this build. The site
still renders stock Instrument Sans / Inter on `--wt-primary-color: #030712`. To bring it
in line, in **Website Builder → Design**:

| Token | Value |
|---|---|
| Primary | `#1a1c1c` |
| Text on primary | `#FFFFFF` |
| Background | `#FAFAF7` |
| Text on background | `#1a1c1c` |
| Accent / border | `#E8E6DF` |
| Heading + body font | Plus Jakarta Sans |
| Accent font | Newsreader |

---

## Also set up (all free on Launch)

The brief assumed polls and surveys were Max-only. beehiiv's own gating flags say
otherwise for this account, so they are configured:

- **Poll** `poll_e7d300d2` — "Was this issue useful?", reusable at the end of any issue.
  Deliberately about the writing, not the reader: poll answers are stored per subscriber,
  so nothing here may touch health information.
- **Survey** `eab565ec` — *What would make ADHDme Weekly most useful?*, one multiple-choice
  question on content preference, backed by the `content_preference` custom field. It was
  first drafted as "What brought you to ADHDme Weekly?" and rewritten, because the obvious
  answers to that question are health disclosures attached to an email address.
- **Referral program** — enabled, `upcoming_milestone_only` layout. Milestones are
  deliberately empty: each one needs a reward, and what ADHDme offers is a product
  decision, not one to invent.

See `BEEHIIV-UPGRADE-TRACKER.md` for what Launch blocks and whether it is worth paying for.

---

## Template redesign (2026-09-20)

Rebuilt on the structure of the beehiiv stock template Stefan linked, in ADHDme's palette
rather than its beige. Order: ink masthead → centred standfirst → rule → `The *research*`
→ pull quote → `In *practice*` as 01/02/03 → cream caveat card → `Worth *a look*` product
grid → poll → cream `Coming *next week*` with a button → referral block.

Verified by reading the template back: sections, radii, the 2×2 columns, the
blockquote variant, the poll node and the referral block all survived the parse.

**Product recommendations** are four real tools — Goblin Tools, Tiimo, Notion Calendar,
Future ADHD — introduced as *"Popular, not proven — none of this is evidence-based, and
none of it is sponsored."* That framing is deliberate. This is a clinician-network brand,
and a section of viral products is the fastest way to undermine "ADHD science, made
useful" if it reads as endorsement.

Open items on that section:
- **Verify the URLs** before sending. `goblin.tools` and the Notion link are solid;
  `tiimo.com` and `futureadhd.com` were not checked.
- **No product images.** The stock template uses uploaded PNGs per product. Using the
  vendors' own images would be someone else's copyright, so the cards are typographic.
  Upload your own, or ask and I will generate them.
- **If these ever become affiliate links, they need a disclosure line**, not just the
  "not sponsored" note.

### The template post that went out

`post_fcd461bf` ("Newsletter Template") was **published with `platform: both`**, so it
emailed every free subscriber — the three test aliases and the one real Gmail address.
It cannot be unsent. Worth deleting the post so it does not sit in the public archive at
`/p/newsletter-template-0ecf225d657d342c`.

---

## Still requires manual action

1. ~~Publish both subscribe forms.~~ **Done.** Both are live and verified in a real
   browser: the primary renders a 52px pill control reading "Join ADHDme Weekly", the
   footer a 48px control reading "Join", both in Plus Jakarta Sans, no beehiiv chrome,
   no horizontal overflow and no console errors at 1440x900 and 390x844.

   Note for next time: in the form builder, **Save changes** only writes the draft.
   Publishing is the **arrow next to it → Publish**. The primary form's first draft was
   lost to exactly that distinction and had to be rebuilt.

2. **Delete the three test subscribers.** There is no MCP tool for this, so it is a
   dashboard job: **Subscribers** → select → Delete.
   - `info+beehiivtest@adhdme.au`
   - `info+bhembedtest@adhdme.au`
   - `info+bhtoast@adhdme.au`

   All three are plus-aliases of the account owner's own mailbox. No real person was
   subscribed. Leave `info@adhdme.au` alone — beehiiv added it as the account owner when
   the workspace was created, not as part of any test.

3. **Decide the sending address.** See [Open questions](#open-questions).

4. **Publish the automation** — only if the trial is real and you want to test it.
   <https://app.beehiiv.com/automations/fc706289-e260-4585-9a8d-5ecbab9d462f/workflow>

Nothing has been sent to anyone. No campaign, no real subscribers.

---

## Test results

Run against the real integrated embed on a local build of this repo, in Chrome via CDP.

| # | Check | Result |
|---|---|---|
| 1 | Submission succeeds | **Pass** — submitted through the embedded iframe on the page |
| 2 | Subscriber appears in beehiiv | **Pass** — `info+bhembedtest@adhdme.au`, active |
| 3 | Source identifiable as website signup | **Pass** — `embed: adhdme.au / website`; matched by the segment |
| 4 | Success message appears | **Pass** — a toast appears on the parent page for ~4s. It showed beehiiv's default text while the draft was unpublished; the branded "You're in. The next ADHDme Weekly will arrive in your inbox." is now live on both forms. |
| 5 | Mobile layout (390×844) | **Pass** — no horizontal overflow; primary 350x52px, footer 342x48px. |
| 6 | Desktop layout (1440×900) | **Pass** — no horizontal overflow; primary 520x52px, footer 320x48px. |
| 7 | Unsubscribe exists | **Pass** — beehiiv appends an unsubscribe link and the postal address to every email footer; the postal address is now set. Records carry `unsubscribed_on`. |
| 8 | Test subscriber receives the trial welcome | **No, by design** — the automation is a draft, so it never fired. `list_automation_journeys` returns 0 enrolments. |
| 9 | No console or page errors | **Pass** — zero exceptions, zero `console.error`, zero failed network requests at both viewports. |

---

## Open questions

**Sending address — decided.** Staying on beehiiv's default `@mail.beehiiv.com` sending
address for now (Stefan, 2026-09-19). Free, works today, no purchase. A custom sending
domain on adhdme.au is a paid feature and remains the upgrade path if deliverability or
brand fit becomes a problem. Sender *name* is `ADHDme`. For the record, the options were:

- **beehiiv default** — free, works today, but mail comes from a `@mail.beehiiv.com`
  address rather than the brand domain.
- **A custom sending domain on adhdme.au** (e.g. an existing mailbox) — better deliverability
  and brand fit, but beehiiv's custom sending domain is a **paid feature**, so it is not
  free-safe and nothing was purchased.
- `info@adhdme.au` already exists (it is the beehiiv account owner and the site's contact
  address) — usable as the **reply-to** without any custom-domain purchase.

**Time zone.** Was `Eastern Time (US & Canada)`, which is plainly wrong for an Australian
publication and would have scheduled every weekly send at the wrong hour. Set to `Sydney`
as the conventional national default. If sends should be anchored to Brisbane (no DST) or
Perth, change it — it is one field.
