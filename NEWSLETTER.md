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

## Embed code for adhdme.au

**Not yet added to any page**, by instruction. Paste where the form should appear.

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

## Still requires manual action

1. **Publish the subscribe form.** *(blocking — do this first)*
   The MCP writes the **draft** theme; beehiiv only allows publishing from the website
   editor. **Right now the live form is still beehiiv's stock black/PT-Serif "Subscribe"
   form** — all 50 branded tokens are pending. Open
   <https://app.beehiiv.com/subscribe_form_builder/76750273-b34d-4b54-ad52-5fa242ea671b>
   → **Get embed code ▾** → **Publish**.
   While there, sanity-check the 44px field height in the live preview: beehiiv's stored
   default was `21px`, so it may measure the inner text box rather than the control.

2. **Set the email footer address.** *(blocking for any send)*
   Both the workspace default and the publication override are empty, and a physical
   postal address is legally required in the email footer (Australian Spam Act, CAN-SPAM).
   **No address was invented.** There is no ADHDme postal address anywhere in this repo —
   the only one present is GOALS Psychology's (Fortitude Valley QLD), which is a partner
   practice, not ADHDme. Provide the correct one.

3. **Decide the sending address.** See [Open questions](#open-questions).

4. **Publish the automation** — only if the trial is real and you want to test it.
   <https://app.beehiiv.com/automations/fc706289-e260-4585-9a8d-5ecbab9d462f/workflow>

5. **Add the embed to the site** once the above is done.

Nothing has been sent to anyone. No test campaign, no real subscribers.

---

## Open questions

**Sending address.** Sender *name* is set to `ADHDme` as instructed. The sending *address*
was not, because nothing appropriate is configured and inventing one was off the table.
The options:

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
