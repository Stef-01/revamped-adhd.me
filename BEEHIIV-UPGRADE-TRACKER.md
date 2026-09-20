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
| **RSS-to-Send** | no feeds configured; documented paid | Scale+ | No. Issues are hand-written. |
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

**Custom link parameters.** beehiiv can append parameters to every outbound link, so
clicks from the newsletter land in the site's own analytics already attributed. The site
runs PostHog. This is the cheapest real win left and it needs no content.

**Syndicate the archive to adhdme.au.** beehiiv publishes an RSS feed of every issue. The
site has a `learn.html` and a blog build script already. Pulling issues onto the site turns
a weekly email into indexed pages that bring in search traffic — the newsletter starts
feeding the site instead of only the other way round.

**The welcome email.** Copy is already written and sitting in this repo. Dashboard-only,
ten minutes, and it closes the one genuine gap in the free-safe core: right now a new
subscriber hears nothing until the next issue.

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
send history. At zero issues sent they would match nothing. Revisit after ~5 issues.

**Signup flows.** They only apply to the beehiiv-hosted subscribe page, not to the embedded
forms on adhdme.au, which is where the traffic will be. Low value for this setup.

**Products / paywalls / premium tiers.** Not the model.

**Podcast embeds.** Available, no podcast.

### Blocked by missing assets, not by beehiiv

**Publication social links** — ADHDme has no social accounts of its own. The only handles
on the site belong to the partner practices, and pointing the publication at those would
misattribute it.

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
