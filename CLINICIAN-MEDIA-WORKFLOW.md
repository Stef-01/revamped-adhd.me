# Clinician media workflow — for Claude in Chrome

A repeatable research pass over the ADHDme network's public media, producing three
attributable tips for the **From the network** block in ADHDme Weekly.

Run it in Claude in Chrome. Chrome has no filesystem, so the output is a block you paste
back into a Claude Code session (or into the beehiiv editor directly).

---

## Before anything else: the consent gate

**Nothing from this workflow publishes until the named clinician has approved the exact
wording.** Not the source material — the finished sentence as it will appear.

This is not caution for its own sake. Every person in the roster is an AHPRA-registered
health practitioner, and a newsletter that attributes clinical advice to them is
advertising a regulated health service:

- **Testimonials are prohibited** in advertising a regulated health service under s133 of
  the National Law. A clinician's own educational tip is not a testimonial. A reader
  saying "Kate changed my life" is, and must never appear in this block.
- Advertising must not **create an unreasonable expectation of benefit**, or encourage
  indiscriminate use of a service. "Three tips that fixed my focus" fails this. "Three
  things Kate suggests trying before the next appointment" does not.
- A tip must not read as **individual clinical advice**. It is general information.
- **Instagram posts and clinic copy are the practice's copyright.** Quote briefly with
  attribution and a link. Do not republish their images or lift whole captions.

If a clinician declines, or does not reply, the block runs without them. It is optional
furniture, not a dependency.

---

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
is a legitimate result and more useful than a stretched one.

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
