# Requests

The owner's requests, in one place, so none is lost between sessions or machines.
Rules are in CLAUDE.md under "Requests: log, update, finish". Newest first in each section.

Each item: `R<n>` · date asked · what was asked · status · what it needs next.
Status is one of: **open** (not started), **doing**, **blocked** (say exactly what unblocks it), **done** (say where: PR or commit).

## Open

### R7 · 2026-10-14 · Damien Margetts: photo, fees and a check against his own pages · blocked
- Live with what search results quoted from his site and his SoulAdvisor listing: founder and lead coach, adults, teens and families, online from Sippy Downs QLD, 1,500+ coaching hours, ICF, MBA (RMIT).
- Missing: his photograph (the portrait is the placeholder illustration), session fees, his booking page, and a read of his own pages to confirm the above. Both hosts are denied by the network policy.
- Unblock: allow adhdcoachingaustralia.com.au and www.souladvisor.com in the environment's Network access, or the owner sends his headshot and pricing. Replace the six assets/clinicians/damien-margetts* files with the real portrait; nothing else changes.

### R4 · 2026-10-07 · Toni Ghuman: fill in the clinic details · blocked
- Live since PR #46 with what was supplied: name, title, bio, photo. Always last in Allied health; out of the navigator.
- Missing from neuromedclinic.au/antonia (host denied by the network policy): suburb and state, telehealth or in person, fees, phone, booking link.
- Owner decisions still open: keep "(Naturopathy)" off her BHSc? Drop "ADHD" from her page title ("ADHD neuroscientist")?

## Done

### R5 · 2026-10-08 · Onboard Damien, ADHD Coaching Australia · done (PR #47)
- Damien Margetts, Coaches tab. Follow-ups in R7.

### R6 · 2026-10-14 · A canonical planner that remembers requests across machines · done
- This file, the CLAUDE.md rules, and a SessionStart hook (.claude/settings.json) that prints the open items in every new session.

### R3 · 2026-10-07 · Independence and network counts across the backend SEO pages · done (PR #46)
- AHPRA count off the home hero; one generated line ("Australia's leading independent ADHD directory: N clinicians, N AHPRA-registered, N practices. We're not a practice. We match you to whoever fits best.") on every search page, the ADHD care hub, The Network's JSON-LD and llms.txt.

### R2 · 2026-10-07 · Navigator motion and scale refinements · done (PR #45)

### R1 · 2026-10-07 · Onboard Toni Ghuman as a neuroscientist, called Toni, always last in Allied health · done (PR #46)
- Live in production (checked 2026-10-14). Details still outstanding: see R4.
