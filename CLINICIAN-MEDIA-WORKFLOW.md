# Clinician media workflow — for Claude in Chrome

A repeatable research pass over the ADHDme network's public media, producing three
attributable tips for the **From the network** block in ADHDme Weekly.

Run it in Claude in Chrome. Chrome has no filesystem, so the output is a block you paste
back into a Claude Code session (or into the beehiiv editor directly).

---

## The model: we draft, the provider QAs

Agreed with the practices. We write **both the questions and a draft of the answers**, and
the provider's job is to correct, comment and approve rather than to produce content from
a blank page. Less cognitive labour for them, a predictable pipeline for us.

This makes the approval step more important, not less. Their name goes on words we wrote
first, so:

**No pack publishes until the named provider has returned it with an approval.** Silence is
not approval. An edit is.

The rules that follow from attributing clinical content to an AHPRA-registered
practitioner:

- **Testimonials are prohibited** in advertising a regulated health service under s133 of
  the National Law. A clinician's own educational answer is not a testimonial. A reader
  saying "Paula changed my life" is, and must never appear in this block.
- Advertising must not **create an unreasonable expectation of benefit**. "Three tips that
  fixed my focus" fails. "Three things Paula suggests trying" does not.
- An answer is **general information**, never individual clinical advice.
- Draft answers must be **conservative and flagged**. Where we are unsure, the draft says
  so inline, so the provider is correcting a marked uncertainty rather than hunting for
  one.

### The loop

1. **Pick a provider** and a topic that plays to their specific credentials.
2. **Draft three questions and three answers.** Two to four sentences each, in ADHDme's
   voice, with a `CHECK:` note wherever we are guessing.
3. **Send the pack for QA.** They edit inline, comment, or reject.
4. **Publish only what comes back approved**, with their name, role, practice and a link.
5. **Keep the returned pack.** It is the evidence that they approved it.

Research the provider's public media first only when it helps write a better draft — it is
no longer the source of the content. Run 001 below establishes why: this network does not
publish, so there was nothing to harvest.

## The roster

Eleven practitioners, three practices. Sources are what the site's own structured data
records — do not go hunting beyond them without a reason.

| Clinician | Role | Practice profile | Social |
|---|---|---|---|
| Alice Bui | Provisional psychologist | [GOALS team](https://www.goalspsychology.com/our-team) | [@goals.psychology](https://www.instagram.com/goals.psychology/) |
| Ellie Putland | Psychologist | GOALS team | @goals.psychology |
| Flynn Simonis | Occupational therapist | GOALS team | @goals.psychology |
| Kate Row | Psychologist | GOALS team | @goals.psychology |
| Lachlan Avent | Psychologist | GOALS team | @goals.psychology |
| Lauren Poulos | Psychologist | GOALS team | @goals.psychology |
| Meera Lakhani | Educational & developmental psychologist | GOALS team | @goals.psychology |
| Samantha Courtney | Psychologist, eating disorders (CEDC-MH) | GOALS team | @goals.psychology |
| Paula Garrido | Clinical psychologist, ADHD-CCSP | [Wellness Psychology Clinic](https://wellnesspsychologyclinic.com.au/doctor/clinpsych-paula-garrido/) | [@wellnesspsychologyclinic.au](https://www.instagram.com/wellnesspsychologyclinic.au/) |
| Dr Anu Saxena | GP, MD FRACGP | [HealthEngine, Double Bay](https://healthengine.com.au/doctor/nsw/double-bay/dr-anusha-saxena/p160121) | — |
| Dr Anubhav Saxena | GP, MBBS FRACGP | [HealthEngine, Beecroft](https://healthengine.com.au/doctor/nsw/beecroft/dr-anubhav-saxena/p123180) | — |

Note the shape of this: eight of eleven share one practice Instagram. Expect to attribute
most finds to **GOALS Psychology** rather than an individual, unless a post names its
author. Do not guess which clinician wrote a practice post.

---

## The pass

Work one clinician at a time. Budget roughly ten minutes each.

**1. Practice profile.** Open their profile page. Note their stated specialisms and
anything they say about how they work. This is the safest source: the practice wrote it
and stands behind it.

**2. Practice social.** Open the Instagram profile and read the most recent ~20 posts
while logged out. You are looking for educational content — an explainer, a strategy, a
myth correction. Skip promotions, staff announcements, and anything with a client in it.

**3. Wider media.** Search for `"<full name>" ADHD` plus `podcast`, `interview`, `webinar`
or `article`. Only count results where the clinician is clearly the named source.

**4. Stop when you have three candidates or you have run out.** Three thin tips beat one
good one padded out.

### What counts as a usable tip

- Specific enough to act on this week.
- General information, not individualised advice.
- Sourced to something public you can link.
- Not a product endorsement.
- Not a claim about outcomes ("this will fix…").

### What to reject outright

- Anything about a named or identifiable patient.
- Testimonials or reviews, in either direction.
- Screenshots of paid or gated content.
- Anything behind a login.
- Diagnostic or dosing guidance. That belongs in a consultation, not a newsletter.

---

## Output format

Paste back exactly this. One block per clinician.

```
CLINICIAN: <full name>, <role>, <practice>
SOURCE:    <url>
DATE:      <when the source was published, or "undated">
STATUS:    needs approval

TIP 1: <one sentence, in ADHDme's voice, that the clinician would recognise as theirs>
  basis: "<short verbatim quote or close paraphrase from the source>"
TIP 2: ...
  basis: "..."
TIP 3: ...
  basis: "..."

CONCERNS: <anything that might breach the rules above, or "none">
```

If nothing usable turns up: `CLINICIAN: <name> — nothing usable found` and move on. That
is a legitimate result and more useful than a stretched one — and under the draft-and-QA
model it is not a blocker, because the content does not depend on the find.

---

## Then

1. Send the drafted tips to the clinician for approval, as they will appear.
2. On approval, set `STATUS: approved <date>` and paste into the **From the network**
   block in the ADHDme Weekly template.
3. Keep the source URL in the block. Attribution without a link is an assertion.
4. Rotate. One clinician per issue means roughly a quarter of cover before anyone repeats.

---

## Cadence

Run it once a month, not weekly. Eleven practitioners sharing three practice accounts will
not generate fresh material every seven days, and a block that recycles thin tips is worse
than no block.

---

## Run log

### Run 001 — 2026-09-20 — Paula Garrido + GOALS Psychology

**Result: nothing usable found. The block stays empty.**

Started with Paula Garrido as the most likely source: she is the only practitioner in the
roster with an ADHD-specific credential (ADHD-CCSP).

| Source | Checked | Finding |
|---|---|---|
| [Wellness Psychology Clinic profile](https://wellnesspsychologyclinic.com.au/doctor/clinpsych-paula-garrido/) | yes | Credentials and specialisms only. **No ADHD advice of any kind.** |
| [paulagarrido.com.au](https://paulagarrido.com.au/) | yes | Same. One passing mention of ADHD in a list of conditions. |
| [GOALS ADHD service page](https://www.goalspsychology.com/adhd) | yes | Service copy. Lists seven strategy *headings* — energy and attention, impulsivity, sleep routines, emotional regulation — but explains none of them, and credits no author. |
| [GOALS homepage / site](https://www.goalspsychology.com/) | yes | No blog, no articles, no resources section. |
| Web search, both names + ADHD | yes | Directory listings only: Psychology Today, HealthShare, HotDoc. No interviews, no podcasts, no articles. |
| Instagram, both practice accounts | **no** | Blocked. A logged-out server-side fetch returns a login wall for both. |

**What this tells us.** The two practice websites are marketing sites, not publishing
operations. There is no public, attributable, explained ADHD strategy from any named
practitioner in this network on the open web. Headings like "sleep routines" cannot become
a tip — writing the explanation ourselves and attributing it to a clinician would be
inventing their advice, which is the exact failure this workflow exists to prevent.

**What to do next, in order:**

1. **Run the Instagram step in Claude in Chrome.** It is the only surface not yet checked,
   the only one likely to hold educational content, and it needs a real logged-in browser.
   Server-side fetching cannot reach it — that is what this whole workflow is for.
2. **If Instagram is also thin, ask rather than research.** Send three questions to one
   clinician and publish their answers. That inverts the problem: instead of hunting for
   quotable material that may not exist, it produces original content the practitioner has
   already approved by writing it. It is faster, it is safer, and it is more interesting.
3. Either way, the **From the network** block stays out of an issue until something real
   and approved exists to put in it.

Paula Garrido remains the right first ask for step 2 — the ADHD-CCSP credential is the
strongest ADHD-specific qualification in the roster.

### Run 002 — 2026-09-20 — QA pack 001 drafted

Model switched to draft-and-QA (agreed with the practices). First pack written for Paula
Garrido: `qa-packs/pack-001-paula-garrido.md`. Three questions and three draft answers on
the ADHD / trauma / relationships overlap, each carrying a `CHECK:` note at the point we
were least certain.

Not sent yet. Not approved. Nothing from it publishes until it comes back edited.
