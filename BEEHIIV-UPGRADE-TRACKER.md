# beehiiv upgrade tracker — ADHDme Weekly

Last audited 2026-09-20. Workspace `Info's Hiiv`, plan **`launch`**, cap **2,500 subscribers**,
currently **5**.

> **Verdict today: do not upgrade.** Of everything Launch blocks, exactly one thing has any
> effect on readers (beehiiv branding in the footer), and one has a free substitute
> (automations → built-in Welcome Email). Nothing blocked is on the path between a signup on
> adhdme.au and a weekly issue landing in an inbox. Revisit when the list nears 2,500, or
> when there is a real reason to monetise.

---

## How this was tested

Not from marketing pages. Two sources, both from the account itself:

1. **beehiiv's own gating flags.** `learn_post_authoring` returns a `gating.available`
   boolean per widget, computed for this publication's plan.
2. **Write probes.** Attempting the change and recording the refusal verbatim.

Where a public pricing page disagrees with the account's own flag, the flag wins and the
disagreement is noted.

---

## Works today, free

Everything the operating model actually rests on.

| Feature | Evidence |
|---|---|
| Unlimited sends, up to 2,500 subscribers | plan cap `max_subscriptions: 2500` |
| Embedded subscribe forms + theming | two live, branded, verified in-browser |
| Signup-source attribution | segment matched a test signup as `embed: adhdme.au / website` |
| Segments | `seg_84ebe410` built and verified |
| Custom fields | `content_preference` created |
| Post templates + full email theming | `post_template_59b2aa21`, theme `c4e1dca5` |
| Publication website + SEO/social cards | home + subscribe pages written |
| **Polls** | flag `polls: available: true`; `poll_e7d300d2` created |
| **Surveys / forms** | `eab565ec` created with a question |
| **Referral program** | `referral_program: available: true`; enabled and configured |
| **HTML snippets in posts** | flag `custom_html_blocks: available: true` |
| **Podcast episode embeds** | flag `podcast_episode_embed_enabled: available: true` |
| **Ad Network** | flag `ad_network: available: true` — see the discrepancy note below |
| Unsubscribe, analytics, engagement data | beehiiv-native, always on |

The original brief assumed polls and surveys were Max-only. They are not, on this account.

---

## Blocked on Launch

| Feature | How it failed | Plan needed | Does ADHDme care? |
|---|---|---|---|
| **Remove beehiiv branding** | API refused: *"general_info.content_access.private_branding is not available for this publication"* | Max | Cosmetic. A line in the footer. The only reader-visible loss. |
| **Programmatic ads** | flag `ad_network_automated_ads: available: false` | Scale+ | No. Nothing to monetise at 5 subscribers. |
| **Direct Sponsorships** | flag `sponsor_network: available: false` | Scale+ | Not yet. Possibly later. |
| **Automations** | draft created but never publishable; beehiiv documents automations as Scale+ | Scale+ | **Has a free substitute** — the built-in Welcome Email does the one job that mattered. |
| **Custom sending domain** (`@adhdme.au`) | not attempted; documented paid | Scale+ | Deliverability and brand fit. The strongest case for upgrading, and still weak at this size. |
| **Paid subscriptions / tiers** | `list_tiers` empty; documented Scale+ | Scale+ | No. Not the model. |
| **RSS Ingestion** (RSS-to-Send) | `list_external_rss_feeds` returns 0; the RSS settings page shows "Unlock with Max plan" — **and still shows it on day 1 of the active Max trial**, so the trial does not unlock it | Max+ | No. Issues are hand-written. Note this is *inbound* RSS — outbound RSS is free and now generated, see below. |
| **Multiple publications / team seats** | not attempted | Scale+ / Enterprise | Not yet. One publication, one author. |

### Discrepancy worth knowing

beehiiv's public pricing writing says the Ad Network requires Scale or above. This
account's own gating flag returns `ad_network: available: true`. One of the two is wrong.
Do not build a revenue assumption on it without confirming in the dashboard.

---

## Not a plan problem

| Thing | Reality |
|---|---|
| beehiiv **website** colours and fonts | No site-theme tool exists in this MCP build at any plan. `edit_page` exposes only SEO metadata and navbar/footer toggles. Dashboard-only, regardless of upgrade. |
| Publishing a subscribe-form draft | Editor-only by design, at every plan. |
| Publishing a post or automation | Deliberately a human action. |

---

## What it would cost

Indicative, from beehiiv's 2026 pricing. Verify before paying — tiers move with list size.

| Plan | Monthly | Annual (per month) | Cap |
|---|---|---|---|
| Launch | free | free | 2,500 |
| Scale | from ~$49 | from ~$43 | 100,000 |
| Max | from ~$109 | from ~$96 | 100,000 |

At 5 subscribers, Max is roughly **$1,300/year to remove one line of footer branding**.

---

## Free, available, and deliberately not switched on

Audited 2026-09-20. These all work on Launch. Each is a decision, not a task.

### Worth doing next

**Custom link parameters — considered and declined.** beehiiv can append parameters to
every outbound link so clicks land in the site's own analytics already attributed. The
available parameter values include the subscriber's email hash and subscription ID,
which would be sent to *every* third-party site a reader clicks through to — goblin.tools,
notion.com, partner practices. That is a subscriber identifier leaking off a health-adjacent
list, for a marginal attribution gain. Declined 2026-09-20. Automatic UTM tagging was
switched on instead (`utm_source=adhdme-weekly`), which attributes the traffic without
carrying anything that identifies a person.

**Syndicate the archive to adhdme.au — feed is live.**

```
https://rss.beehiiv.com/feeds/256LXheLe8.xml
```

Generated 2026-09-20. Serves HTTP 200, `application/xml`, full `<content:encoded>` bodies,
channel image, categories and `<atom:link rel="self">`. The site has a `learn.html` and a
blog build script already; pointing them at this turns a weekly email into indexed pages.

Two things about it worth knowing before anything consumes it:

> **Resolved 2026-09-20.** The feed's only item was "Newsletter Template" — the internal
> template published to web by accident. It has been **archived**
> (`post_fcd461bf-e149-4477-bdfa-7142bfab8969`, status `archived`): the public page now
> returns 403, it is off the beehiiv homepage, and the feed rebuilt to **0 items**. The feed
> is clean and safe to consume; it will fill with real issues as they publish.
>
> Archiving is reversible from the post's row menu. Note the menu also offers *Delete* —
> that one is not.
>
> **The feed lags about two minutes behind a content change.** Immediately after archiving,
> the feed still served the old body with an unchanged `lastBuildDate`, which reads exactly
> like a frozen cache — it is not. `Cache-Control: max-age=0, private, must-revalidate` and
> `cf-cache-status: DYNAMIC`; beehiiv simply rebuilds server side on a short delay. Re-check
> before concluding anything from a feed read taken seconds after an edit.

> **The URL's token is random** (`256LXheLe8`) and is not derived from the publication name,
> slug or ID. It cannot be guessed — which is why the earlier probe of six plausible URL
> patterns returned six 404s. Deleting and regenerating mints a *new* token and breaks every
> consumer of the old one, so treat this URL as the durable reference. There is no MCP tool
> that reads it back; `get_publication_settings` still exposes no RSS key. If it is ever lost,
> it is at Settings → Publication → [RSS](https://app.beehiiv.com/settings/publication/rss).

Outbound RSS is free on Launch. It simply does not exist until generated — the earlier note
here claiming beehiiv "publishes an RSS feed of every issue" was wrong.


**The welcome email — live as of 2026-09-20.** This was the one genuine gap in the
free-safe core: a new subscriber heard nothing until the next issue. Now they get an
immediate email.

Set up as beehiiv's **built-in Welcome Email** (Settings → Publication → Emails → Preset
emails), *not* as an automation. That distinction is the whole point: the built-in welcome
email is free-safe and keeps working on Launch, whereas
`TRIAL TEST - ADHDme Weekly Welcome` (`aut_fc706289…`) is an automation and would stop the
day the account leaves a paid tier. The automation stays in draft and can now be deleted
without losing anything — its copy is reused here verbatim.

- Subject: `Welcome to ADHDme Weekly`
- Preview: `Weekly ADHD science, practical strategies and ideas worth testing.`
- Body: the four-line welcome, signed `ADHDme`
- Toggle enabled and confirmed persisted across a reload; published, no unsaved changes

It inherits the publication theme, so it already carries the masthead line, the
"you subscribed at adhdme.au" provenance line, the not-medical-advice disclaimer, the
Robina address and the unsubscribe footer. Nothing extra was written into the body.

It fires on **new** subscriptions only, so the five existing subscribers were not emailed.

### Judgement calls

**Recommendations — 17 ADHD publications are available.** beehiiv's own AI suggestions
returned empty (too new), but `discover_publications` found *Technically ADHD*, *The ADHD
Informed Parent*, *Personal ADHD Training*, *The Spicy Brain Social Club* and others.

Free growth, and often reciprocated. **Not enabled, on purpose.** A recommendation from a
clinician-network brand reads as endorsement, and several of these are tonally a long way
from ADHDme — "Neurospicy", "no-BS", personal-experience newsletters that may give
advice ADHDme would not stand behind. Same risk as the product block, with more of it,
because a publication keeps publishing after you have vouched for it.

If it is worth doing: pick one or two, read a few issues first, and revisit quarterly.

**Ad Network.** The account's own gating flag says `available: true`, though beehiiv's
public pricing says it needs Scale. Either way it is a brand decision before a revenue
one — ads inside a clinical newsletter change what the newsletter is.

**Referral milestones.** The program is on and configured, but has no milestones, because
each one needs a reward and what ADHDme gives away is a product decision.

### Premature

**Engagement segments** (re-engagement, highly-engaged). Free and useful — after there is
send history. One exists: **Unengaged — 30 days**
(`seg_3029a02e-8d82-4d90-9f3d-dda070dc3a69`), `status = 'active' AND
unique_opens(within: '1 month') = 0`.

> **Do not send to it yet.** The assumption when it was built was that it would match
> nobody until there was send history. It matches **all 5 subscribers** — "no opens in
> 30 days" is trivially true of everyone when nothing has ever been sent. Mailing it
> today would send a "we miss you" to the entire list, every one of whom signed up this
> week. It only becomes a re-engagement segment once roughly a month of issues have gone
> out. Revisit after ~5 issues.

beehiiv DSL gotcha worth keeping: `last_opened_or_clicked_days_ago` is an *automation
branch* condition and is rejected in a segment. `unique_opens(within: '30 days')` is the
segment form, and beehiiv silently normalises it to `within: '1 month'`.

**Signup flows.** They only apply to the beehiiv-hosted subscribe page, not to the embedded
forms on adhdme.au, which is where the traffic will be. Low value for this setup.

**Products / paywalls / premium tiers.** Not the model.

**Podcast embeds.** Available, no podcast.

### Blocked by missing assets, not by beehiiv

**Publication social links** — resolved 2026-09-20. ADHDme now has its own Instagram
(`@adhdme.australia`) and it is set on the beehiiv author profile. The remaining platforms
stay null on purpose: the other handles on the site belong to the partner practices, and
pointing the publication at those would misattribute it.

**Author avatar** — Stefan's byline still shows a generated gradient, because there is no
photograph in the repo.

---

## Triggers to revisit

Upgrade when one of these is true, not before:

1. **The list passes ~2,000.** Launch's cap is the only hard wall, and it arrives without warning.
2. **A sponsor is actually interested.** Then Scale pays for itself, and not a month earlier.
3. **Deliverability measurably suffers** on `@mail.beehiiv.com` — watch open rates and spam complaints over the first several issues before blaming the sending domain.
4. **The welcome sequence needs to be more than one email.** One email is free. A sequence is not.

Branding removal on its own is not a trigger.
