# Requests

The owner's requests, in one place, so none is lost between sessions or machines.
Rules are in CLAUDE.md under "Requests: log, update, finish". Newest first in each section.

Each item: `R<n>` · date asked · what was asked · status · what it needs next.
Status is one of: **open** (not started), **doing**, **blocked** (say exactly what unblocks it), **done** (say where: PR or commit).

## Open

### R5 · 2026-10-08 · Onboard Damien, ADHD Coaching Australia · blocked
- Sources: https://www.souladvisor.com/practitioner/adhd-coaching-australia and https://adhdcoachingaustralia.com.au
- Blocked: the cloud environment's network policy denies both hosts (curl, WebFetch and search all failed, 2026-10-08 and 2026-10-14).
- Unblock either way: add both hosts under Allowed domains in the cloud environment's Network access, or run this on a machine that can reach them, or the owner pastes his headshot and page text.
- Then: Coaches tab, his own words only (full name, bio, training, location, online or in person, ages, fees, booking link); usual onboarding, checks, edge tests, merge to main.

### R4 · 2026-10-07 · Toni Ghuman: fill in the clinic details · blocked
- Live since PR #46 with what was supplied: name, title, bio, photo. Always last in Allied health; out of the navigator.
- Missing from neuromedclinic.au/antonia (host denied by the network policy): suburb and state, telehealth or in person, fees, phone, booking link.
- Owner decisions still open: keep "(Naturopathy)" off her BHSc? Drop "ADHD" from her page title ("ADHD neuroscientist")?

## Done

### R6 · 2026-10-14 · A canonical planner that remembers requests across machines · done
- This file, the CLAUDE.md rules, and a SessionStart hook (.claude/settings.json) that prints the open items in every new session.

### R3 · 2026-10-07 · Independence and network counts across the backend SEO pages · done (PR #46)
- AHPRA count off the home hero; one generated line ("Australia's leading independent ADHD directory: N clinicians, N AHPRA-registered, N practices. We're not a practice. We match you to whoever fits best.") on every search page, the ADHD care hub, The Network's JSON-LD and llms.txt.

### R2 · 2026-10-07 · Navigator motion and scale refinements · done (PR #45)

### R1 · 2026-10-07 · Onboard Toni Ghuman as a neuroscientist, called Toni, always last in Allied health · done (PR #46)
- Live in production (checked 2026-10-14). Details still outstanding: see R4.
