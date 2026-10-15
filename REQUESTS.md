# Requests

The owner's requests, in one place, so none is lost between sessions or machines.
Rules are in CLAUDE.md under "Requests: log, update, finish". Newest first in each section.

Each item: `R<n>` · date asked · what was asked · status · what it needs next.
Status is one of: **open** (not started), **doing**, **blocked** (say exactly what unblocks it), **done** (say where: PR or commit).

## Open

### R10 · 2026-10-15 · Auto-onboard providers who email info@adhdme.au, with their photos · blocked
- Owner, 2026-10-15: check regularly and publish straight to live, no approval step. Built: Windows task `adhdme-provider-intake`, every 4 hours (prompt in ~/.claude/scheduled-tasks/, DR copy and pipeline-health check in Stefan-Brain cb15b90). Its first run read the collector Gmail headless and filed the two calendar invites from info@ as not-a-provider. It onboards anyone who writes once the forwarding below is on. Photos come from the provider's own site: the connector cannot download attachments.
- Blocked: no session can read info@adhdme.au. The Gmail connector reads only trivedisteven@gmail.com, and the account is not signed in to Gmail in any Chrome profile this machine can drive.
- Unblock: in info@adhdme.au Gmail, Settings → Forwarding → add trivedisteven@gmail.com (a session reads the confirmation from the connector), then forward the existing provider threads once. Every provider email then reaches the connector and can be onboarded the way R7 and R9 were.

### R4 · 2026-10-07 · Toni Ghuman: fill in the clinic details · blocked
- Live since PR #46 with what was supplied: name, title, bio, photo. Always last in Allied health; out of the navigator.
- Missing from neuromedclinic.au/antonia (host denied by the network policy): suburb and state, telehealth or in person, fees, phone, booking link.
- Owner decisions still open: keep "(Naturopathy)" off her BHSc? Drop "ADHD" from her page title ("ADHD neuroscientist")?

## Done

### R9 · 2026-10-15 · Kirsten Lightfoot: photo and a check against her own pages · done (78390e5)
- Her portrait at full resolution from her own Meet Your Coach page (it replaces 35ea8a8's copy of the same photo, which was a low-resolution circle crop); office in Arana Hills; group program corrected to $725 (her group-training page), the unpublished $188 course price removed.
- Her page says she is still studying the CMC, while her email signature lists it; the profile keeps the signature's wording.

### R7 · 2026-10-14 · Damien Margetts: photo, fees and a check against his own pages · done (78390e5)
- Portrait from his own coaching site, matched to his LinkedIn photo. Fees from his site: $99 for 30 minutes, $249 for a 60-minute strategy session, a free 15-minute call. Credentials now ACC (ICF), PAAC member, Executive MBA (RMIT). Book opens his booking page.
- The "ADHD ADHD coach" titles were fixed in 8a7b8a3; this rebuild carried the fix into llms.txt and the sitemap.

### R8 · 2026-10-15 · Onboard Kirsten Lightfoot, ADHD coach · done (PR #48)
- Coaches tab. Follow-ups in R9.

### R5 · 2026-10-08 · Onboard Damien, ADHD Coaching Australia · done (PR #47)
- Damien Margetts, Coaches tab. Follow-ups in R7.

### R6 · 2026-10-14 · A canonical planner that remembers requests across machines · done
- This file, the CLAUDE.md rules, and a SessionStart hook (.claude/settings.json) that prints the open items in every new session.

### R3 · 2026-10-07 · Independence and network counts across the backend SEO pages · done (PR #46)
- AHPRA count off the home hero; one generated line ("Australia's leading independent ADHD directory: N clinicians, N AHPRA-registered, N practices. We're not a practice. We match you to whoever fits best.") on every search page, the ADHD care hub, The Network's JSON-LD and llms.txt.

### R2 · 2026-10-07 · Navigator motion and scale refinements · done (PR #45)

### R1 · 2026-10-07 · Onboard Toni Ghuman as a neuroscientist, called Toni, always last in Allied health · done (PR #46)
- Live in production (checked 2026-10-14). Details still outstanding: see R4.
